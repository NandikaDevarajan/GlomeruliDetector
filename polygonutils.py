################################################################################
# Purpose: This module provides utility functions for polygon operations such 
# as calculating area, removing nested polygons, and determining label positions.
################################################################################

from typing import List, Tuple
from shapely.geometry import Polygon, Point

class PolygonUtils:
    @staticmethod
    def calculate_polygon_area(polygon: List[Tuple[float, float]]) -> float:
        """
        Calculate the area of a polygon using the Shoelace formula.
        """
        if not polygon or len(polygon) < 3:
            return 0.0

        area = 0.0
        n = len(polygon)

        for i in range(n):
            x1, y1 = polygon[i]
            x2, y2 = polygon[(i + 1) % n]
            area += (x1 * y2) - (x2 * y1)

        return abs(area) / 2.0

    @staticmethod
    def remove_nested_polygons(polygons: List[List[Tuple[float, float]]]) -> List[List[Tuple[float, float]]]:
        """
        Remove nested polygons from a list of polygons.
        """
        filtered = []
        for i, current_polygon in enumerate(polygons):
            is_nested = False
            current_shape = Polygon(current_polygon)

            for j, other_polygon in enumerate(polygons):
                if i == j:
                    continue

                other_shape = Polygon(other_polygon)

                # Check if all points of current_polygon are inside other_polygon
                all_inside = all(Point(pt).within(other_shape) for pt in current_polygon)

                if all_inside:
                    is_nested = True
                    break

            if not is_nested:
                filtered.append(current_polygon)

        return filtered

    @staticmethod
    def get_top_left_label_position(points: List[Tuple[float, float]]) -> Tuple[float, float]:
        """
        Get the top-left position for labeling a polygon.
        """
        if not points:
            return (0.0, 0.0)

        min_x = min(pt[0] for pt in points)
        min_y = min(pt[1] for pt in points)

        return (min_x + 5, min_y - 15)  # Slightly offset for visibility