################################################################################
# Purpose: This module provides a class to draw polygons on an image based 
# on a JSON response from the Glomeruli Azure Auto ML model. # It parses the JSON 
# response to extract polygon coordinates, scales them to the image size, and 
# draws them on the image.
# Sample Json file can be found in sampleresult.json
################################################################################

import os
import json
from PIL import Image, ImageDraw
from constants import Constants
from polygonutils import PolygonUtils

class PolygonDrawer:
   
    def __init__(self, json_response):
        self.json_response = json_response

    def parse_polygons(self):
        polygons = []
        root_items = json.loads(self.json_response)

        if not root_items:
            return polygons

        for root_item in root_items:
            if "boxes" not in root_item:
                continue

            for box in root_item["boxes"]:
                if "polygon" not in box or box["score"] < Constants.MIN_CONFIDENCE_SCORE:
                    continue

                for poly_coords in box["polygon"]:
                    points_list = [
                        (poly_coords[i], poly_coords[i + 1])
                        for i in range(0, len(poly_coords), 2)
                    ]
                    if points_list:
                        polygons.append(points_list)

        return polygons

    def draw_polygons(self, image_path):
        polygons = self.parse_polygons()
        if not polygons:
            print("No polygons to draw on image.")
            return

        output_dir = os.path.join(os.path.dirname(image_path), Constants.OUTPUT_DIR)
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, os.path.basename(image_path))

        with Image.open(image_path) as img:
            draw = ImageDraw.Draw(img)
            img_width, img_height = img.size

            for polygon in polygons:
                scaled_polygon = [
                    (pt[0] * img_width, pt[1] * img_height)
                    for pt in polygon
                ]

                # Calculate area and centroid 
                area_in_pixels = PolygonUtils.calculate_polygon_area(scaled_polygon)
                centroid = PolygonUtils.get_top_left_label_position(scaled_polygon)
                area_microns = area_in_pixels * Constants.PIXEL_TO_MICRON_FACTOR * Constants.PIXEL_TO_MICRON_FACTOR
                area_microns = area_microns * Constants.CORRECTION_FACTOR
            
                draw.text(centroid, f"{area_microns:.2f} um^2", fill="yellow")
                if len(scaled_polygon) > 1:
                    draw.polygon(scaled_polygon, outline="red")
                elif len(scaled_polygon) == 1:
                    pt = scaled_polygon[0]
                    draw.ellipse([pt[0] - 3, pt[1] - 3, pt[0] + 3, pt[1] + 3], outline="red")
            if Constants.SKIP_DRAWING:
                return
            img.save(output_path)
            print(f"Output image saved to: {output_path}")