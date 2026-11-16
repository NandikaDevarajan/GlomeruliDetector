# Glomeruli Detector

Finds glomeruli in microscopy images, outlines each one, and reports how many there are and
how much area they cover.

This folder is everything you need. The model is in models/ and runs on this machine, so
there is no account to create, no key to enter and no network connection required. Copy the
whole folder wherever you like and run it from there.


## 1. Install Python

Download Python 3.10 or newer from https://www.python.org/downloads/ and run the installer.

On Windows, tick "Add Python to PATH" on the first screen of the installer before clicking
Install Now. It is easy to miss and everything else depends on it.

Check it worked by opening a terminal (Command Prompt or PowerShell on Windows) and running:

  python --version


## 2. Install what the program needs

In a terminal, change into this folder and run:

  pip install -r requirements.txt

That installs Pillow, numpy, shapely and onnxruntime. It takes a minute or two the first
time and never needs doing again.

If you are never going to use the cloud mode described in section 6, you can ignore any
mention of "requests" in that file.


## 3. Run it

One image:

  python gdetector.py "C:\path\to\image.tif"

A whole folder, including everything in its sub-folders:

  python gdetector.py "C:\path\to\folder"

Quote the path. Without quotes a folder name containing a space is read as two arguments and
the program will say it cannot find anything.

Typical output:

  Input path: C:\slides\71125_2.tif
  Detection mode: local model (models\glomeruli_unet.onnx)
  Processing image: 71125_2.tif
  Output image saved to: C:\slides\mloutput\71125_2.tif
  Number of Glomeruli: 8
  Total Area in microns: 101153.69
  Saving results to: ...\results\output-1030202608.csv
  Time taken: 0.54 seconds


## 4. What you get back

Two things.

A drawn copy of every image, in a folder called mloutput beside the images themselves. Each
glomerulus is outlined in red with its area written next to it in yellow. Your original files
are never modified.

A CSV in the results folder beside this readme, named with the date and time of the run, so
one run never overwrites another. One row per image, with the file name, the number of
glomeruli and the total area in square microns.

Open the CSV in Excel or anything else that reads CSV.


## 5. Reading the numbers

The area is reported in square microns, converted from pixels using PIXEL_TO_MICRON_FACTOR in
constants.py. The default is 0.7634 microns per pixel.

That one number applies to every image, so it has to match your imaging system. If it does
not, every area is wrong by the square of the ratio. If your microscope gives 0.85 microns
per pixel and the factor is left at 0.7634, the areas come out about 19% too small.

To check yours: open an image in whatever software your scanner provides and find its
reported pixel size, or divide a known distance in microns by the same distance in pixels.
Then set the factor accordingly:

  PIXEL_TO_MICRON_FACTOR = 0.85

Counts are not affected by this. Only areas.


## 6. Settings

All of them live in constants.py. Open it in any text editor, change a value, save, and the
next run uses it. The ones worth knowing:

MIN_CONFIDENCE_SCORE          default 0.80
  How sure the model has to be before a detection is reported. Raise it towards 0.9 if you
  are getting detections you do not agree with; lower it towards 0.7 if glomeruli are being
  left out.

LOCAL_MASK_THRESHOLD          default 0.5
  Where the boundary of each detection is drawn. Lower it if the outlines sit inside the
  glomeruli and look too tight; raise it if they spill out into the surrounding tissue.

LOCAL_MIN_AREA_MICRONS        default 1000
  The smallest thing that will be reported, in square microns. Raise it to suppress small
  spurious detections.

PIXEL_TO_MICRON_FACTOR        default 0.7634
  Section 5.

SKIP_DRAWING                  default False
  Set it to True to get only the CSV and skip writing the drawn images. Noticeably faster on
  a large folder.

OUTPUT_DIR                    default "mloutput"
  The name of the folder the drawn images go into.

CORRECTION_FACTOR             default 1.0
  Multiplies every reported area. Leave it at 1.0 unless you have a reason not to.

DETECTION_MODE                default "local"
  "local" uses the model in models/, which is what this folder is set up for. "cloud" sends
  each image to an Azure ML endpoint instead, and then END_POINT_URL and API_KEY have to be
  filled in. Most people should leave this alone.


## 7. Using a different model

models/ holds two files that belong together:

  glomeruli_unet.onnx    the model
  glomeruli_unet.json    its input size, normalisation and the scores it reached

If you are sent an updated model, replace both files, keeping the names. Nothing else needs
to change. The .json is how the program knows how to feed the .onnx, so a model without its
matching .json will not load.

models/glomeruli_unet.history.json, if present, is a record of how the model was trained. The
program does not read it.


## 8. If something goes wrong

"python is not recognised"
  Python is not on PATH. Reinstall it with the "Add Python to PATH" box ticked, or use the
  full path to python.exe.

"No module named onnxruntime" (or numpy, PIL, shapely)
  Step 2 has not been run, or was run for a different Python installation. Run
  "pip install -r requirements.txt" again from this folder.

"Local model not found at ..."
  models/glomeruli_unet.onnx is missing. Make sure you copied the whole folder, models/
  included.

Nothing is detected on images that clearly have glomeruli
  The images may be a stain the model has not been trained on, in which case it tends to
  return nothing at all rather than something approximate. Lowering MIN_CONFIDENCE_SCORE is
  worth trying first; if that changes nothing, the model needs training on your stain.

The outlines look right but the areas look wrong
  Section 5. It is almost always PIXEL_TO_MICRON_FACTOR.

It is slow
  Expect roughly a fifth of a second per image. If it is much slower, set
  LOCAL_USE_TEST_TIME_AUGMENTATION to False in constants.py, which is about twice as fast
  and gives slightly less steady outlines. SKIP_DRAWING = True also helps on large folders.


## 9. What is in this folder

  gdetector.py                  what you run
  constants.py                  every setting
  models/                       the model and its metadata
  requirements.txt              what pip installs
  readme.txt                    this file

  detectorfactory.py            chooses local or cloud
  localglomerulidetector.py     runs the model
  azuremlglomerulidetector.py   calls the Azure endpoint, in cloud mode
  maskpostprocessor.py          turns the model output into outlines
  folderdetector.py             the folder run
  singlefiledetector.py         the single image run
  polygondrawer.py              draws the outlines and the area labels
  polygonutils.py               area arithmetic
  resultparser.py               assembles the per-image result
  csvgenerator.py               writes the CSV
  Tiff2png.py                   image conversion used by cloud mode

Nothing outside this folder is needed to detect anything. The rest of the repository exists
to train new models and to draw the annotations they are trained on; see the readme at the
top level.
