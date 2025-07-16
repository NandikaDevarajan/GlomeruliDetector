##############################################################################################
# Purpose: This module provides a class to process a single image file for glomeruli detection.
# It uses the AzureMLGlomeruliDetector to get predictions, draws polygons on the image
# and saves the results in a CSV file.
##############################################################################################

import os
from datetime import datetime

from constants import Constants
from polygondrawer import PolygonDrawer
from azuremlglomerulidetector import AzureMLGlomeruliDetector
from resultparser import GlomeruliResultParser  

class FolderDetector:
    def process_image(self, input_image_folder):
        output_csv_path = self.get_results_csv_path()
        with open(output_csv_path, 'w') as csv_file:
            csv_file.write("File Name,Number of Glomeruli,Total Areas (microns),G1,G2,G3,G4,G5,G6,G7,G8,G9,G10\n")
        for root, dirs, files in os.walk(input_image_folder):
            if os.path.basename(root) == Constants.OUTPUT_DIR:
                continue
            for file in files:
                if file.lower().endswith(('.tif', '.tiff')):
                    file_path = os.path.join(root, file)
                    self.process_file(file_path, output_csv_path)
        print(f"Saving results to: {output_csv_path}")

    def process_file(self, file_path, output_csv_path):
        from time import time
        detector = AzureMLGlomeruliDetector(file_path)
        root_folder = os.path.basename(os.path.dirname(file_path))
        file_name = os.path.basename(file_path)
        print("*****************************************************************************")
        print(f"Processing image: {root_folder}\\{file_name}")
        start_time = time()
        json_response=detector.get_json_response()
        drawer = PolygonDrawer(json_response)
        drawer.draw_polygons(file_path)
        with open(output_csv_path, 'a') as csv_file:
            parser = GlomeruliResultParser(json_response, file_path)
            result = parser.as_table_row()
            print(f"Number of Glomeruli: {result[1]}")
            print(f"Total Area in microns: {result[2]}")
            csv_file.write(','.join(map(str, result)) + '\n')
        end_time = time()
        print(f"Time taken: {end_time - start_time:.2f} seconds")
        print("*****************************************************************************")

    def get_results_csv_path(self):
        """
        Creates a 'results' folder if it doesn't exist and returns a path for the output CSV file
        in the format output-mmddyyyyss.csv (month, day, year, seconds).
        """
        results_dir = os.path.join(os.getcwd(), 'results')
        os.makedirs(results_dir, exist_ok=True)
        now = datetime.now()
        timestamp = now.strftime('%m%d%Y%S')
        output_file = f"output-{timestamp}.csv"
        return os.path.join(results_dir, output_file)


