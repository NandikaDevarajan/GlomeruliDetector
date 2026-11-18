################################################################################
# Purpose: Run glomeruli detection locally with the ONNX model that ships in models/, with no
# Azure ML endpoint and no network access.
#
# This class is a drop-in replacement for AzureMLGlomeruliDetector: get_json_response() returns
# the same JSON shape the Azure ML endpoint returns, so PolygonDrawer and GlomeruliResultParser
# consume it unchanged.
#
# The model is a U-Net that predicts, for every pixel, the probability that it belongs to a
# glomerulus. MaskPostProcessor turns that probability map into one polygon per glomerulus.
# The score reported for each polygon is the mean probability inside it, so the existing
# MIN_CONFIDENCE_SCORE setting keeps working the same way.
################################################################################

import json
import os

import numpy as np
from PIL import Image

from constants import Constants
from maskpostprocessor import MaskPostProcessor

DEFAULT_METADATA = {
    "input_name": "image",
    "output_name": "logits",
    "input_width": 512,
    "input_height": 512,
    "scale": 1.0 / 255.0,
    "mean": [0.5, 0.5, 0.5],
    "std": [0.5, 0.5, 0.5],
    "output_activation": "sigmoid",
    "classes": ["glomeruli"],
}


class LocalGlomeruliDetector:
    # One ONNX session per model path, shared across images so folder runs load it once.
    _sessions = {}

    def __init__(self, image_path, model_path=None):
        self.image_path = image_path
        self.model_path = model_path or Constants.LOCAL_MODEL_PATH
        if not os.path.isabs(self.model_path):
            self.model_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), self.model_path)

    # ------------------------------------------------------------------ public

    def get_json_response(self):
        """Detect glomeruli and return the result as an Azure ML style JSON string."""
        session, metadata = self._get_session()
        image, source_size = self._load_image()
        probabilities = self._predict(session, metadata, image)

        processor = MaskPostProcessor(
            mask_threshold=Constants.LOCAL_MASK_THRESHOLD,
            min_area_pixels=self._min_area_pixels(),
            simplify_tolerance=Constants.LOCAL_POLYGON_SIMPLIFY_TOLERANCE,
        )
        processor.set_source_size(*source_size)
        objects = processor.extract_objects(probabilities)

        label = metadata.get("classes", ["glomeruli"])[0]
        boxes = []
        for item in objects:
            flat_polygon = [coordinate for point in item["polygon"] for coordinate in point]
            boxes.append({
                "box": item["box"],
                "label": label,
                "score": round(item["score"], 6),
                "polygon": [[round(coordinate, 6) for coordinate in flat_polygon]],
            })

        return json.dumps([{"boxes": boxes}])

    # ----------------------------------------------------------------- helpers

    def _get_session(self):
        """Create the ONNX session once and reuse it for every image in a run."""
        cached = LocalGlomeruliDetector._sessions.get(self.model_path)
        if cached:
            return cached

        if not os.path.exists(self.model_path):
            raise FileNotFoundError(
                f"Local model not found at '{self.model_path}'. "
                f"Train one with 'python ModelTrainer/train_model.py', or set "
                f"Constants.DETECTION_MODE to 'cloud' to use the Azure ML endpoint."
            )

        try:
            import onnxruntime
        except ImportError as error:
            raise ImportError(
                "onnxruntime is required for local detection. Install it with "
                "'pip install onnxruntime'."
            ) from error

        options = onnxruntime.SessionOptions()
        options.graph_optimization_level = onnxruntime.GraphOptimizationLevel.ORT_ENABLE_ALL
        session = onnxruntime.InferenceSession(
            self.model_path, options, providers=["CPUExecutionProvider"]
        )

        metadata = dict(DEFAULT_METADATA)
        metadata_path = os.path.splitext(self.model_path)[0] + ".json"
        if os.path.exists(metadata_path):
            with open(metadata_path, "r", encoding="utf-8") as handle:
                metadata.update(json.load(handle))

        cached = (session, metadata)
        LocalGlomeruliDetector._sessions[self.model_path] = cached
        return cached

    def _load_image(self):
        """Read the first frame of the image (later TIFF frames are thumbnails) as RGB."""
        with Image.open(self.image_path) as image:
            image.seek(0)
            rgb = image.convert("RGB")
            return rgb.copy(), rgb.size

    def _predict(self, session, metadata, image):
        """Run the model and return a probability map at the model input resolution."""
        width = int(metadata["input_width"])
        height = int(metadata["input_height"])
        resized = image.resize((width, height), Image.BILINEAR)

        array = np.asarray(resized, dtype=np.float32) * float(metadata["scale"])
        array = (array - np.asarray(metadata["mean"], np.float32)) / np.asarray(metadata["std"], np.float32)
        tensor = np.transpose(array, (2, 0, 1))[None, ...]

        input_name = session.get_inputs()[0].name
        if Constants.LOCAL_USE_TEST_TIME_AUGMENTATION:
            # Average the prediction over the image and its flips; this steadies the boundary
            # and costs a few hundred milliseconds per image.
            variants = [
                (tensor, lambda a: a),
                (tensor[:, :, :, ::-1], lambda a: a[:, ::-1]),
                (tensor[:, :, ::-1, :], lambda a: a[::-1, :]),
                (tensor[:, :, ::-1, ::-1], lambda a: a[::-1, ::-1]),
            ]
        else:
            variants = [(tensor, lambda a: a)]

        accumulated = np.zeros((height, width), np.float32)
        for variant, undo in variants:
            logits = session.run(None, {input_name: np.ascontiguousarray(variant)})[0]
            accumulated += undo(self._activate(logits[0, 0], metadata))
        return accumulated / len(variants)

    @staticmethod
    def _activate(logits, metadata):
        if metadata.get("output_activation", "sigmoid") == "sigmoid":
            return 1.0 / (1.0 + np.exp(-logits))
        return logits

    @staticmethod
    def _min_area_pixels():
        """Smallest accepted detection, converted from microns to original image pixels."""
        factor = Constants.PIXEL_TO_MICRON_FACTOR
        if factor <= 0:
            return 0.0
        return Constants.LOCAL_MIN_AREA_MICRONS / (factor * factor)
