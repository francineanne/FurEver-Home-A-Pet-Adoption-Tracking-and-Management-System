from .auth_controller import AuthController  # noqa: F401
from .admin_controller import AdminController  # noqa: F401
from .adopter_controller import AdopterController  # noqa: F401

# Allow direct execution for quick sanity checks:
# python app/controllers/__init__.py  -> prints available controllers
if __name__ == "__main__":
    import sys
    from pathlib import Path

    ROOT = Path(__file__).resolve().parents[1]
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

    print("Controllers loaded:")
    for name in ("AuthController", "AdminController", "AdopterController"):
        print(f" - {name}")
