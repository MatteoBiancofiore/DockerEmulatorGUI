# gui/assets.py
import sys
from pathlib import Path
from PIL import Image, ImageTk

# Determine the base directory depending on whether the script is frozen or not
if getattr(sys, 'frozen', False):
    # if frozen (e.g., PyInstaller) the base dir is the temp folder created by PyInstaller
    BASE_DIR = Path(sys._MEIPASS)
else:
    # if not frozen, use the script's directory
    BASE_DIR = Path(__file__).parent.parent

# Images directory
IMAGE_DIR = BASE_DIR / "images"


def load_image(path, size=(20, 20)):
    try:
        img = Image.open(path)
        img = img.resize(size)
        return ImageTk.PhotoImage(img)
    except (FileNotFoundError, OSError):
        return None
