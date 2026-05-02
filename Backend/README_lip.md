# Sinhala Lip Reading / Sign Language Training System

This project provides two ways to run a lip-reading training workflow:

- A Flask web app for webcam-based training and prediction
- A PyQt desktop UI built from the included `.ui` files

The main web entry point is [`webmain.py`](webmain.py), and the desktop entry point is [`main_ui_system.py`](main_ui_system.py).

## Features

- Live webcam capture with MediaPipe-based facial landmark annotation
- Practice video playback for each letter/word class
- Timed recording and prediction against the trained model
- Sinhala display labels for the supported classes

## Project Layout

- `webmain.py` - Flask web application
- `main_ui_system.py` - PyQt desktop application
- `Predict_realtime.py` - Loads the trained model and runs predictions
- `feture_extract.py` - Feature extraction / landmark processing
- `video_to_csv.py` - Converts recorded video into CSV features
- `trainScript.py` - Model training script
- `requirements.txt` - Python dependencies
- `templates/index.html` - Web UI template
- `static/` - CSS and JavaScript for the web UI
- `dataset_video/` and `extracted_data_csv/` - Training assets
- `sinhala_lip_reading_model.h5` - Saved model used by the app

## Requirements

- Windows
- Python 3.10.x
- Webcam
- A working copy of the model file `sinhala_lip_reading_model.h5`

## Setup

Create and activate a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\activate
```

Install dependencies:

```powershell
pip install -r requirements.txt
```

If you already tried installing with older incompatible packages, reinstall cleanly:

```powershell
pip install -r requirements.txt --force-reinstall
```

## Run the Web App

```powershell
python webmain.py
```

Open the app in your browser at:

- http://localhost:5100

The console may print `5000`, but the app actually runs on port `5100`.

## Run the Desktop App

```powershell
python main_ui_system.py
```

This starts the PyQt interface defined by [`dissignerUI.ui`](dissignerUI.ui).

## Notes

- The project expects the webcam to be available and not used by another app.
- The prediction code reads `extracted_data_csv/` to rebuild label encoding.
- Practice videos are loaded from `practis_letters/`.
- If model loading fails with Keras compatibility errors, use the repository version of `Predict_realtime.py`, which strips unsupported config fields during load.

## Troubleshooting

If `pip install -r requirements.txt` fails, confirm you are using Python 3.10 and the `.venv` environment is activated.

If `python webmain.py` fails on `numpy`, `flask`, or `tensorflow`, reinstall the requirements inside the active virtual environment.

If the webcam does not start:

- Close other camera apps
- Try a different camera index in [`webmain.py`](webmain.py)
- Make sure Windows camera permissions are enabled

## License

No license file is included in this repository.