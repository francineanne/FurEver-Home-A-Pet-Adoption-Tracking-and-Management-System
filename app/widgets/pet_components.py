import logging
from pathlib import Path
from PIL import Image, ImageOps
import customtkinter as ctk

from app.config import IMAGES_DIR

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(message)s")


def load_pet_image(path, size=(200, 200)):
    """
    Safely load and resize an image. If path doesn't exist, return a placeholder.
    Accepts absolute paths, bare filenames, or paths that already include 'images/'.
    """
    try:
        if not path:
            raise FileNotFoundError("Image path is empty.")

        incoming = Path(path)

        if incoming.is_absolute():
            full_path = incoming
        elif "images" in incoming.parts:
            # DB may store "images/filename.jpg" -> normalize to shared images dir
            full_path = IMAGES_DIR / incoming.name
        else:
            full_path = IMAGES_DIR / incoming

        if not full_path.exists() or not full_path.is_file():
            raise FileNotFoundError(f"Image file not found at: {full_path}")

        img = Image.open(full_path).convert("RGBA")
        img = ImageOps.contain(img, size)
        logging.debug(f"Image loaded successfully from: {full_path}")

        return ctk.CTkImage(light_image=img, size=size)

    except Exception as e:
        logging.error(f"Error loading image: {str(e)}")  # Log the error for debugging
        # Create a simple placeholder image (gray square with optional text, but since it's an image, just the color)
        placeholder_img = Image.new("RGBA", size, (220, 220, 220, 255))  # Gray placeholder
        logging.debug(f"Using placeholder image due to error: {str(e)}")
        return ctk.CTkImage(light_image=placeholder_img, size=size)
