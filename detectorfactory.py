################################################################################
# Purpose: Pick the detector that matches Constants.DETECTION_MODE.
#
#   "local" -> LocalGlomeruliDetector, running the ONNX model in models/ on this machine
#   "cloud" -> AzureMLGlomeruliDetector, calling the Azure ML endpoint as before
#
# Both detectors expose get_json_response() and return the same JSON shape, so the rest of the
# application does not care which one it was given. The imports are deliberately lazy so that
# local mode does not need 'requests' and cloud mode does not need 'onnxruntime'.
################################################################################

from constants import Constants

LOCAL = "local"
CLOUD = "cloud"


class DetectorFactory:
    @staticmethod
    def create(image_path):
        mode = (Constants.DETECTION_MODE or CLOUD).strip().lower()

        if mode == LOCAL:
            from localglomerulidetector import LocalGlomeruliDetector
            return LocalGlomeruliDetector(image_path)

        if mode == CLOUD:
            from azuremlglomerulidetector import AzureMLGlomeruliDetector
            return AzureMLGlomeruliDetector(image_path)

        raise ValueError(
            f"Unknown DETECTION_MODE '{Constants.DETECTION_MODE}'. Use '{LOCAL}' or '{CLOUD}'."
        )

    @staticmethod
    def describe():
        """Short description of the active mode, for the run banner."""
        mode = (Constants.DETECTION_MODE or CLOUD).strip().lower()
        if mode == LOCAL:
            return f"local model ({Constants.LOCAL_MODEL_PATH})"
        return f"Azure ML endpoint ({Constants.END_POINT_URL})"
