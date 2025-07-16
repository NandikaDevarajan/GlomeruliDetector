##############################################################################################
# Purpose: Convert TIFF images to PNG format.
# This class checks if the image is already in PNG format and returns the bytes.
# If the image is in TIFF format, it converts it to PNG and returns the PNG bytes.
##############################################################################################    

from PIL import Image
import io

class TiffToPngConverter:
    def __init__(self, image_path):
        self.image_path = image_path

    def convert_to_png_bytes(self):
        # Check by file extension first 
        if self.image_path.lower().endswith('.png'):
            with open(self.image_path, 'rb') as f:
                return f.read()
        # Otherwise, check by image format
        with Image.open(self.image_path) as img:
            if img.format == 'PNG':
                with open(self.image_path, 'rb') as f:
                    return f.read()
            with io.BytesIO() as output:
                img.save(output, format="PNG")
                png_bytes = output.getvalue()
        return png_bytes