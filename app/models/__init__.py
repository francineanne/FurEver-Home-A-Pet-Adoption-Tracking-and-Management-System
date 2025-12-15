from .database import *  # noqa: F401,F403

# Allow running this file directly for quick sanity checks
if __name__ == "__main__":
    import sys
    from pathlib import Path

    ROOT = Path(__file__).resolve().parents[1]
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

    print("Models package ready (database imported).")
