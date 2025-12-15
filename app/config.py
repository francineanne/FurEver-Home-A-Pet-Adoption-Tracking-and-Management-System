from pathlib import Path

# Project root (folder that contains assets, images, db, main.py)
BASE_DIR = Path(__file__).resolve().parent.parent

# Common locations
ASSETS_DIR = BASE_DIR / "assets"
IMAGES_DIR = BASE_DIR / "images"
DB_PATH = BASE_DIR / "fureverhome.db"

# UI defaults
APP_TITLE = "FurEver Home"
WINDOW_SIZE = "1366x768"
BG_COLOR = "#00156A"
