##############################################################################################
# Purpose: This module defines the GlomeruliResultParser class, which processes JSON output from
# the AzureMLGlomeruliDetector, calculates areas of detected glomeruli, and formats the results
# for output in a structured way.
# ##############################################################################################


from polygondrawer import PolygonDrawer
from polygonutils import PolygonUtils
from constants import Constants
from PIL import Image
import os

class GlomeruliResultParser:
    def __init__(self, json_response, image_path):
        """
        json_response: str (JSON output from AzureMLGlomeruliDetector)
        image_path: str (path to the image for scaling and file name)
        """
        self.json_response = json_response
        self.image_path = image_path
        self.file_name = os.path.basename(image_path)

    def parse(self):
        drawer = PolygonDrawer(self.json_response)
        polygons = drawer.parse_polygons()
        if not polygons:
            return {
                'file_name': self.file_name,
                'num_glomeruli': 0,
                'areas': [],
                'total_area': 0.0
            }
        # Get image size for scaling
        with Image.open(self.image_path) as img:
            img_width, img_height = img.size
        areas = []
        for polygon in polygons:
            scaled_polygon = [
                (pt[0] * img_width, pt[1] * img_height)
                for pt in polygon
            ]
            area_in_pixels = PolygonUtils.calculate_polygon_area(scaled_polygon)
            area_microns = area_in_pixels * Constants.PIXEL_TO_MICRON_FACTOR * Constants.PIXEL_TO_MICRON_FACTOR
            areas.append(area_microns)
        total_area = sum(areas)
        return {
            'file_name': self.file_name,
            'num_glomeruli': len(areas),
            'total_area': total_area,
            'areas': areas
            
        }

    def as_table_row(self):
        parsed = self.parse()
        areas_str = ', '.join(f"{a:.2f}" for a in parsed['areas'])
        return [
            parsed['file_name'],
            parsed['num_glomeruli'],
            f"{parsed['total_area']:.2f}",
            areas_str
        ]