##############################################################################################
# Purpose: This module serves as the main entry point for the Glomeruli Detector application.
# It detects whether the input is a single image file or a folder containing images,
# and processes the images accordingly using the appropriate detector classes.
# It provides usage instructions if the input is not specified correctly.
##############################################################################################

import os
import sys
from folderdetector import FolderDetector
from singlefiledetector import SingleFileDetector

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python gdetector.py image_full_path_or_folder_path")
        print('Single File Ex: python gdetector.py "C:\\some\\path\\to\\image.tif"')
        print('Folder Ex: python gdetector.py "C:\\some\\path\\to\\folder"')
        sys.exit(1)

input_path = sys.argv[1]
print(f"Input path: {input_path}")

if os.path.isfile(input_path):
    if not os.path.exists(input_path):
        print(f"Error: File '{input_path}' does not exist.")
        sys.exit(1)
    singlefiledetector = SingleFileDetector()
    singlefiledetector.process_image(input_path)
    print('Completed processing successfully!')
elif os.path.isdir(input_path):
    if not os.path.exists(input_path):
        print(f"Error: Folder '{input_path}' does not exist.")
        sys.exit(1)
    folderDetector = FolderDetector()
    folderDetector.process_image(input_path)
    print('Completed processing folder successfully!')

