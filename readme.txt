# Instructions

To run this program, you need to have Python installed on your system.
You can download Python from the official website: https://www.python.org/downloads/

Follow these steps:
1. Go to the Python downloads page.
2. Download the latest version suitable for your operating system (Windows, macOS, or Linux).
3. Run the installer and follow the on-screen instructions.
    - On Windows, make sure to check the box that says "Add Python to PATH" before clicking "Install Now".
4. After installation, open a terminal or command prompt and run `python --version` to verify the installation.

## Install Required Packages

To install the required Python packages, run the following commands in your terminal or command prompt:

pip install Pillow
pip install requests Pillow
pip install shapely

## Running the Program

To run the `gdetector.py` program, use the following command in your terminal or command prompt:

python gdetector.py "Image_Full_Path"
(or)
python gdetector.py "Image_Folder"

Note: Folder will recursively look at all the tiff images

Configuration Constants:
END_POINT_URL
The URL of the Azure ML endpoint.
Change this if your endpoint URL changes.

API_KEY
The API key for authenticating with the Azure ML endpoint.
Replace with your actual API key as needed.

PIXEL_TO_MICRON_FACTOR
Conversion factor from pixels to microns (default: 0.7634).
Adjust this if your imaging system uses a different pixel-to-micron ratio.
You can calculate this by dividing pixel/micrometers. 
Default value used is 100/130=0.7634

MIN_CONFIDENCE_SCORE
Minimum confidence score for polygon detection (default: 0.80).
Increase to be more selective, decrease to include more detections.
Confidence score comes from the Azure ML model.

OUTPUT_DIR
Directory name for saving processed images (default: "mloutput").
Change this to organize outputs in a different folder.
Once the image has been processed, creating a subfolder where image located
and drawing all the detected glomeruli with the area calculated.
You can skip that if you use SKIP_DRAWING to true.

SKIP_DRAWING
Boolean flag to skip drawing polygons on images (default: False).
Set to False if you want to enable drawing polygons on output images.

CORRECTION_FACTOR
Placeholder for any correction factor needed in calculations (default: 1.0).
Adjust this if you need to apply a correction to area or other calculations.
If the area calculated needs to be increased or decreased then we can tweak this value.

