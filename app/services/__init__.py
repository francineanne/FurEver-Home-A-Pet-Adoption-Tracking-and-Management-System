from .email_service import send_otp_email  # noqa: F401
from .file_service import copy_photo_to_images  # noqa: F401

# Allow running this file directly for quick sanity checks
if __name__ == "__main__":
    import sys
    from pathlib import Path

    ROOT = Path(__file__).resolve().parents[1]
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

    print("Services package ready (email_service, file_service imported).")
