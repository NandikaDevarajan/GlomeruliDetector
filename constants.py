import os


class Constants:
    # Where detection runs: "local" uses the ONNX model in models/ on this machine,
    # "cloud" calls the Azure ML endpoint configured below.
    DETECTION_MODE = "local"

    # ----------------------------------------------------------------- cloud mode
    # Example endpoint URL
    END_POINT_URL = "https://replacethis.westus.inference.ml.azure.com/score"
    # Example API key for authentication
    # Note: Replace with your actual API key
    API_KEY = ""

    # ----------------------------------------------------------------- local mode
    # ONNX model used when DETECTION_MODE is "local". A relative path is resolved
    # against the folder this file lives in.
    LOCAL_MODEL_PATH = os.path.join("models", "glomeruli_unet.onnx")
    # Probability above which a pixel counts as part of a glomerulus.
    # Lower it to grow detections, raise it to tighten them.
    LOCAL_MASK_THRESHOLD = 0.5
    # Detections smaller than this are discarded as noise.
    LOCAL_MIN_AREA_MICRONS = 1000.0
    # How aggressively the traced outline is simplified, in model pixels.
    # 0 keeps every boundary point, larger values give smoother polygons.
    LOCAL_POLYGON_SIMPLIFY_TOLERANCE = 1.0
    # Average the prediction over the image and its mirrored copies. Steadier
    # boundaries at the cost of a few hundred milliseconds per image.
    LOCAL_USE_TEST_TIME_AUGMENTATION = True

    # ----------------------------------------------------------------- shared
    # Conversion factor from pixels to microns (100:130 pixels to microns ratio 100/130=0.7634)
    PIXEL_TO_MICRON_FACTOR = 0.7634
    # Minimum Confidence score  for polygon detection
    MIN_CONFIDENCE_SCORE = 0.80
    # Output directory for saving processed images
    OUTPUT_DIR = "mloutput"
    # Flag to skip if you want to skip drawing polygons on the image
    SKIP_DRAWING = False
    # Placeholder for any correction factor needed in calculations
    CORRECTION_FACTOR = 1.0
