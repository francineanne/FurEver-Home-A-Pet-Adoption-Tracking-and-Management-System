"""
Compatibility wrapper so callers can import pet helpers via app.services.pet_components.
All logic lives in app.widgets.pet_components.
"""
from app.widgets.pet_components import *  # noqa: F401,F403
