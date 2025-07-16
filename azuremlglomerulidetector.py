################################################################################
# Purpose: This module provides a class to interact with the Glomeruli Azure Auto ML model 
# hosted on Azure. It allows users to send an image to the model and receive a 
# JSON response with the model's predictions including the polygon coordinates of detected glomeruli.
# It handles image encoding, request sending, and response parsing.
# Assumption: Image is in tif format it will be converted to PNG before sending.
################################################################################

import base64
import os
import json
import requests
from Tiff2png import TiffToPngConverter
from constants import Constants

class AzureMLGlomeruliDetector:
    #Constructor
    def __init__(self, image_path):
        self.image_path = image_path

    #
    def get_json_response(self):
        converter = TiffToPngConverter(self.image_path)
        image_bytes = converter.convert_to_png_bytes()
        base64_image = base64.b64encode(image_bytes).decode('utf-8')
        request_obj = {
            "input_data": {
                "columns": ["image"],
                "index": [0],
                "data": [base64_image]
            },
            "@params": {}
        }
        json_request = json.dumps(request_obj)
        headers = {
            "Authorization": f"Bearer {Constants.API_KEY}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        response = requests.post(Constants.END_POINT_URL, data=json_request, headers=headers)
        if response.status_code == 200:
            return response.text
        else:
            raise Exception(f"Request failed with status {response.status_code}: {response.text}")
