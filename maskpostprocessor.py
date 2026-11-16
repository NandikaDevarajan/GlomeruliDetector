################################################################################
# Purpose: Turn the probability mask produced by the local segmentation model into the same
# polygons the Azure ML endpoint returns, so the rest of the application does not change.
#
# Everything here is plain numpy on purpose: the shipped application only needs numpy, Pillow,
# shapely and onnxruntime, with no OpenCV or scipy to install.
#
# The steps are: threshold the probability map, label the connected blobs, fill any holes,
# drop blobs that are too small to be a glomerulus, trace the outer boundary of each blob and
# simplify it into a polygon.
################################################################################

import numpy as np

# Clockwise 8-neighbourhood, used by the boundary tracer.
_NEIGHBOURS = [(-1, 0), (-1, 1), (0, 1), (1, 1), (1, 0), (1, -1), (0, -1), (-1, -1)]


class MaskPostProcessor:
    def __init__(self, mask_threshold=0.5, min_area_pixels=0.0, simplify_tolerance=1.0,
                 smoothing_window=5):
        self.mask_threshold = mask_threshold
        self.min_area_pixels = min_area_pixels
        self.simplify_tolerance = simplify_tolerance
        self.smoothing_window = smoothing_window
        self._source_size = None

    # ------------------------------------------------------------------ public

    def extract_objects(self, probabilities):
        """
        probabilities: 2D float array in [0, 1] with the model probability per pixel.

        Returns a list of dicts with the normalised polygon (coordinates in 0..1 relative to
        the probability map), the normalised bounding box, the mean probability inside the
        blob used as a confidence score, and the blob area in probability-map pixels.
        """
        height, width = probabilities.shape
        binary = probabilities >= self.mask_threshold
        if not binary.any():
            return []

        labels, count = self.label_components(binary)
        source_width, source_height = self._source_size or (width, height)

        objects = []
        for index in range(1, count + 1):
            component = self.fill_holes(labels == index)
            if component.sum() < 10:
                continue

            contour = self.trace_outer_contour(component)
            if len(contour) < 3:
                continue
            contour = self.smooth_contour(contour, self.smoothing_window)
            contour = self.simplify_contour(contour, self.simplify_tolerance)
            if len(contour) < 3:
                continue

            # Filter on the area of the polygon that will be reported, not on the area of the
            # blob it came from, so the configured minimum means what the output says.
            polygon = [(float(x) / width, float(y) / height) for y, x in contour]
            area = self.polygon_area(
                [(x * source_width, y * source_height) for x, y in polygon]
            )
            if area < self.min_area_pixels:
                continue

            ys, xs = np.nonzero(component)
            objects.append({
                "polygon": polygon,
                "box": {
                    "topX": float(xs.min()) / width,
                    "topY": float(ys.min()) / height,
                    "bottomX": float(xs.max() + 1) / width,
                    "bottomY": float(ys.max() + 1) / height,
                },
                "score": float(probabilities[component].mean()),
                "area_source_pixels": area,
            })

        objects.sort(key=lambda item: item["score"], reverse=True)
        return objects

    @staticmethod
    def polygon_area(points):
        """Shoelace area, matching how the application measures a detection."""
        if len(points) < 3:
            return 0.0
        coordinates = np.asarray(points, dtype=np.float64)
        x, y = coordinates[:, 0], coordinates[:, 1]
        return float(abs(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1))) / 2.0)

    def set_source_size(self, source_width, source_height):
        """Record the size of the original image so the area filter works in its pixels."""
        self._source_size = (source_width, source_height)

    # ----------------------------------------------------------------- helpers

    @staticmethod
    def label_components(mask):
        """
        Label 8-connected components with a run-length union-find scan.

        Row by row, each horizontal run of foreground pixels is matched against the runs of the
        previous row; overlapping runs are merged. This touches each run once instead of each
        pixel repeatedly, which keeps it fast without scipy.
        """
        height, width = mask.shape
        parent = [0]

        def find(node):
            while parent[node] != node:
                parent[node] = parent[parent[node]]
                node = parent[node]
            return node

        def union(left, right):
            left, right = find(left), find(right)
            if left == right:
                return left
            if left > right:
                left, right = right, left
            parent[right] = left
            return left

        run_rows = []
        previous_runs = []
        for y in range(height):
            row = mask[y].astype(np.int8)
            edges = np.diff(np.concatenate(([0], row, [0])))
            starts = np.flatnonzero(edges == 1)
            ends = np.flatnonzero(edges == -1)

            current_runs = []
            for start, end in zip(starts, ends):
                label = 0
                for previous_start, previous_end, previous_label in previous_runs:
                    # Runs are [start, end); touching diagonally still counts as connected.
                    if previous_start <= end and start <= previous_end:
                        root = find(previous_label)
                        label = root if label == 0 else union(label, root)
                if label == 0:
                    label = len(parent)
                    parent.append(label)
                current_runs.append((int(start), int(end), label))

            run_rows.append((y, current_runs))
            previous_runs = current_runs

        # Compact the surviving roots into 1..n and paint them.
        remap = {}
        labels = np.zeros((height, width), np.int32)
        for y, runs in run_rows:
            for start, end, label in runs:
                root = find(label)
                if root not in remap:
                    remap[root] = len(remap) + 1
                labels[y, start:end] = remap[root]

        return labels, len(remap)

    @classmethod
    def fill_holes(cls, component):
        """Fill background pockets fully enclosed by a component."""
        padded = np.pad(component, 1)
        background_labels, count = cls.label_components(~padded)
        if count == 0:
            return component
        outside = background_labels[0, 0]
        holes = (background_labels != outside) & (background_labels != 0)
        return (padded | holes)[1:-1, 1:-1]

    @staticmethod
    def trace_outer_contour(component):
        """
        Moore neighbourhood boundary tracing, returning the outer contour as (y, x) points.

        Tracing starts at the first foreground pixel in raster order and walks clockwise,
        stopping once it re-enters that pixel from the same direction.
        """
        points = np.argwhere(component)
        if len(points) == 0:
            return []
        start = (int(points[0][0]), int(points[0][1]))

        height, width = component.shape
        current = start
        # The pixel to the west of the start is background, so it is a valid backtrack point.
        backtrack = (start[0], start[1] - 1)
        initial_state = (current, backtrack)

        contour = [start]
        for _ in range(8 * component.size):
            offset = (backtrack[0] - current[0], backtrack[1] - current[1])
            try:
                index = _NEIGHBOURS.index(offset)
            except ValueError:
                break

            moved = False
            for step in range(1, 9):
                candidate_offset = _NEIGHBOURS[(index + step) % 8]
                candidate = (current[0] + candidate_offset[0], current[1] + candidate_offset[1])
                if 0 <= candidate[0] < height and 0 <= candidate[1] < width and component[candidate]:
                    previous_offset = _NEIGHBOURS[(index + step - 1) % 8]
                    backtrack = (current[0] + previous_offset[0], current[1] + previous_offset[1])
                    current = candidate
                    moved = True
                    break

            if not moved:
                break
            if (current, backtrack) == initial_state:
                break
            contour.append(current)

        return contour

    @staticmethod
    def smooth_contour(contour, window):
        """Moving average along a closed contour, to take the stair-steps off the boundary."""
        if window < 3 or len(contour) < window:
            return [(float(y), float(x)) for y, x in contour]
        points = np.asarray(contour, dtype=np.float64)
        half = window // 2
        padded = np.concatenate([points[-half:], points, points[:half]])
        kernel = np.ones(window) / window
        smoothed = np.stack([
            np.convolve(padded[:, 0], kernel, mode="valid"),
            np.convolve(padded[:, 1], kernel, mode="valid"),
        ], axis=1)
        return [(float(y), float(x)) for y, x in smoothed[:len(points)]]

    @classmethod
    def simplify_contour(cls, contour, tolerance):
        """Ramer-Douglas-Peucker simplification of a closed contour."""
        if tolerance <= 0 or len(contour) < 4:
            return contour
        points = list(contour)
        # Split the closed loop at its two most distant points so each half simplifies cleanly.
        simplified = cls._rdp(points + [points[0]], tolerance)
        if len(simplified) > 1 and simplified[0] == simplified[-1]:
            simplified = simplified[:-1]
        return simplified

    @classmethod
    def _rdp(cls, points, tolerance):
        if len(points) < 3:
            return list(points)
        start, end = np.asarray(points[0]), np.asarray(points[-1])
        segment = end - start
        length = float(np.hypot(*segment))

        coordinates = np.asarray(points[1:-1])
        if length == 0:
            distances = np.hypot(*(coordinates - start).T)
        else:
            distances = np.abs(
                segment[1] * (start[0] - coordinates[:, 0]) - segment[0] * (start[1] - coordinates[:, 1])
            ) / length

        farthest = int(np.argmax(distances))
        if distances[farthest] <= tolerance:
            return [points[0], points[-1]]

        split = farthest + 1
        left = cls._rdp(points[:split + 1], tolerance)
        right = cls._rdp(points[split:], tolerance)
        return left[:-1] + right
