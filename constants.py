class Constants:
    # Example endpoint URL
    END_POINT_URL = "https://replacethis.westus.inference.ml.azure.com/score"
    # Example API key for authentication
    # Note: Replace with your actual API key
    API_KEY = ""
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
    

