import os
import shutil
from app.config import IMAGES_DIR


def copy_photo_to_images(path: str) -> str:
    """
    Copy a user-selected photo into the shared images directory.
    Returns just the filename so DB can store the relative path.
    """
    if not path:
        return ""
    try:
        os.makedirs(IMAGES_DIR, exist_ok=True)
        filename = os.path.basename(path)
        dest_path = IMAGES_DIR / filename
        if os.path.abspath(path) != os.path.abspath(dest_path):
            shutil.copy2(path, dest_path)
        return filename
    except Exception:
        return path
