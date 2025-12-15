"""
Compatibility wrapper so callers can import database helpers via app.services.database.
All logic lives in app.models.database.
"""
from app.models.database import *  # noqa: F401,F403
