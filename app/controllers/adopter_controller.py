from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Dict, List, Optional

# Allow running this file directly for quick debugging (inject repo root into sys.path)
if __name__ == "__main__":
    ROOT = Path(__file__).resolve().parents[2]
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

from app.config import IMAGES_DIR
from app.models import database
from app.services import file_service


class AdopterController:
    """Coordinator for adopter flows so UI code stays focused on presentation."""

    def __init__(self, images_dir: Optional[str] = None):
        self.images_dir = Path(images_dir or IMAGES_DIR)
        try:
            self.images_dir.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass

    # --------------- Pets ---------------
    def list_pets(self, category: Optional[str] = None) -> List[Dict]:
        cat = (category or "all").strip().lower()
        try:
            if cat != "all" and hasattr(database, "get_pets_by_category"):
                return database.get_pets_by_category(cat)
        except Exception:
            pass
        try:
            return database.get_available_pets()
        except Exception:
            try:
                return database.get_all_pets()
            except Exception:
                return []

    # --------------- Requests ---------------
    def has_pending_request(self, adopter_id: int, pet_id: int) -> bool:
        if not adopter_id or not pet_id:
            return False
        try:
            return database.has_pending_request(adopter_id, pet_id)
        except Exception:
            return False

    def submit_request(self, adopter_id: int, pet_id: int, note: str, pet_name: str = "", notify: bool = True) -> None:
        if not adopter_id or not pet_id:
            raise ValueError("adopter_id and pet_id are required.")
        database.submit_adoption_request(adopter_id, pet_id, note)
        if notify:
            try:
                pet_label = pet_name or "the pet"
                database.create_notification(adopter_id, f"Adoption request submitted for {pet_label}.", role="adopter")
                database.notify_all_admins(f"New adoption request received for {pet_label}.")
            except Exception:
                pass

    def list_requests(self, adopter_id: int, status: Optional[str] = None) -> List[Dict]:
        if not adopter_id:
            return []
        try:
            requests = database.get_adopter_requests(adopter_id)
        except Exception:
            return []
        status_key = (status or "all").strip().lower()
        if status_key and status_key != "all":
            requests = [r for r in requests if str(r.get("status", "")).strip().lower() == status_key]
        return requests

    def get_request(self, request_id: int) -> Dict:
        if not request_id:
            raise ValueError("request_id is required.")
        return database.get_request_details(request_id)

    def delete_request(self, request_id: int, adopter_id: Optional[int] = None, allow_approved: bool = False) -> bool:
        if not request_id:
            raise ValueError("request_id is required.")
        if not allow_approved:
            try:
                details = database.get_request_details(request_id)
                if details and str(details.get("status") or "").lower() == "approved":
                    raise ValueError("Approved requests are kept for history.")
            except ValueError:
                raise
            except Exception:
                pass
        return database.delete_request(request_id, adopter_id=adopter_id)

    def cancel_request(self, request_id: int, adopter_id: Optional[int] = None) -> bool:
        if not request_id:
            raise ValueError("request_id is required.")
        return database.cancel_request(request_id, adopter_id=adopter_id)

    # --------------- Notifications ---------------
    def list_notifications(self, user_id: int) -> List[Dict]:
        if not user_id:
            return []
        try:
            return database.get_notifications_for_user(user_id, role="adopter")
        except Exception:
            return []

    def mark_notification_read(self, notification_id: int) -> None:
        if not notification_id:
            raise ValueError("notification_id is required.")
        database.mark_notification_read(notification_id)

    def clear_notifications(self, user_id: int) -> None:
        if not user_id:
            raise ValueError("user_id is required.")
        database.clear_notifications_for_user(user_id, role="adopter")

    def delete_notification(self, notification_id: int) -> None:
        if not notification_id:
            raise ValueError("notification_id is required.")
        database.delete_notification(notification_id)

    # --------------- History ---------------
    def adoption_history(self, adopter_id: int, category: Optional[str] = None) -> List[Dict]:
        if not adopter_id:
            return []
        try:
            hist = database.get_adoption_history_for_adopter(adopter_id)
        except Exception:
            return []
        cat = (category or "all").strip().lower()
        if cat == "all":
            return hist
        return [row for row in hist if str(row.get("category") or "").lower() == cat]

    # --------------- Profile ---------------
    def _save_photo(self, photo_path: str) -> str:
        if not photo_path:
            return ""
        try:
            return file_service.copy_photo_to_images(str(photo_path))
        except Exception:
            return photo_path

    def _remove_photo(self, photo_path: str) -> None:
        if not photo_path:
            return
        candidates = []
        if os.path.isabs(photo_path):
            candidates.append(photo_path)
        candidates.append(str(self.images_dir / photo_path))
        for path in candidates:
            try:
                if os.path.exists(path) and os.path.isfile(path):
                    os.remove(path)
                    break
            except Exception:
                continue

    def update_profile(
        self,
        users_id: int,
        name: str,
        email: str,
        phone_number: str,
        birthdate: str,
        photo_path: str,
        age: Optional[int] = None,
    ) -> Dict:
        if not users_id:
            raise ValueError("users_id is required.")
        # Normalize age: allow empty/None/N/A, otherwise ensure it is numeric.
        age_val = None
        if age not in (None, ""):
            try:
                if isinstance(age, str) and age.strip().lower() in ("n/a", "na", "none", "unknown"):
                    age_val = None
                else:
                    age_val = int(age)
            except Exception:
                raise ValueError("Age must be a number.")
        saved_photo = self._save_photo(photo_path) if photo_path else photo_path
        ok = database.update_user_profile(
            users_id,
            name,
            email,
            phone_number,
            birthdate,
            saved_photo,
            age_val,
        )
        if not ok:
            raise RuntimeError("Could not update user profile.")
        return {
            "users_id": users_id,
            "name": name,
            "email": email,
            "phone": phone_number,
            "phone_number": phone_number,
            "birthdate": birthdate,
            "photo_path": saved_photo,
            "age": age_val,
        }

    def delete_account(self, users_id: int, photo_path: str = "") -> None:
        if not users_id:
            raise ValueError("users_id is required.")
        database.delete_user(users_id)
        self._remove_photo(photo_path)

    # --------------- Admin profiles / ratings ---------------
    def admin_profiles(self) -> List[Dict]:
        try:
            return database.get_admin_profiles()
        except Exception:
            return []

    def notify_admins_rating(self, stars: int) -> None:
        try:
            database.notify_all_admins(f"New adopter rating: {stars} star(s).")
        except Exception:
            pass
