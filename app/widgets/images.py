from pathlib import Path
from typing import Tuple
from PIL import Image, ImageOps
import customtkinter as ctk

from app.config import ASSETS_DIR


def safe_ctk_image(name_or_path: str, size: Tuple[int, int]):
    """
    Load an image safely, resize to `size`, and return a CTkImage.
    Accepts a bare filename (looked up in assets/) or an absolute/relative path.
    Falls back to a blank image on error to avoid crashes.
    """
    try:
        path = Path(name_or_path)
        if not path.is_absolute():
            path = ASSETS_DIR / path
        img = Image.open(path).convert("RGBA")
        img = ImageOps.contain(img, size)
    except Exception:
        img = Image.new("RGBA", size, (255, 255, 255, 0))
    return ctk.CTkImage(img, size=size)
