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


class AdminController:
    """Coordinator for admin flows so UI code can stay thin."""

    def __init__(self, images_dir: Optional[str] = None):
        self.images_dir = Path(images_dir or IMAGES_DIR)
        try:
            self.images_dir.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass

    # --------------- Dashboard ---------------
    def dashboard_snapshot(self) -> Dict[str, object]:
        """
        Return ready-to-display data for the admin dashboard.
        Includes raw lists plus lightweight aggregates for counts.
        """
        pets = database.get_available_pets()
        requests = database.get_all_requests()
        history = database.get_adoption_history()

        status_counts: Dict[str, int] = {}
        for req in requests:
            status = str(req.get("status") or "pending").strip().lower()
            if status == "declined":
                status = "rejected"
            status_counts[status] = status_counts.get(status, 0) + 1

        availability: Dict[str, int] = {}
        for pet in pets:
            cat = (pet.get("category") or "Other").title()
            availability[cat] = availability.get(cat, 0) + 1

        return {
            "pets": pets,
            "requests": requests,
            "adoption_history": history,
            "stats": {
                "available_pets": len(pets),
                "requests": len(requests),
                "adoptions": len(history),
                "requests_by_status": status_counts,
                "availability": availability,
            },
        }

    # --------------- Requests ---------------
    def list_requests(self, status: Optional[str] = None) -> List[Dict]:
        """
        Fetch adoption requests, optionally filtered by status.
        Status accepts Pending/Approved/Rejected/Declined/All (case-insensitive).
        """
        requests = database.get_all_requests()
        status_key = (status or "all").strip().lower()
        if status_key and status_key != "all":
            normalized = "rejected" if status_key in ("declined", "rejected") else status_key

            def _normalize_status(value: str) -> str:
                val = (value or "pending").strip().lower()
                return "rejected" if val == "declined" else val

            requests = [req for req in requests if _normalize_status(req.get("status")) == normalized]
        return requests

    def get_request(self, request_id: int) -> Dict:
        if not request_id:
            raise ValueError("request_id is required.")
        return database.get_request_details(request_id)

    def approve_request(self, request_id: int, notify: bool = True) -> Dict[str, int]:
        """
        Approve a request and optionally notify the adopter.
        Returns adopter_id/pet_id when successful.
        """
        if not request_id:
            raise ValueError("request_id is required.")
        result = database.approve_request(request_id)
        if not result:
            raise ValueError("Request not found.")

        if notify:
            try:
                details = database.get_request_details(request_id)
                adopter_id = (details or {}).get("adopter_id") or result.get("adopter_id")
                pet_name = (details or {}).get("pet_name") or "the pet"
                if adopter_id:
                    msg = (
                        f"Your adoption request for {pet_name} was approved. "
                        "You can download the adoption form from My Requests and follow the next steps provided."
                    )
                    database.create_notification(adopter_id, msg, role="adopter")
            except Exception:
                pass
        return result

    def decline_request(self, request_id: int, reason: str = "", notify: bool = True) -> None:
        if not request_id:
            raise ValueError("request_id is required.")
        details = database.get_request_details(request_id)
        database.decline_request(request_id, reason or "")
        if notify:
            adopter_id = (details or {}).get("adopter_id")
            pet_name = (details or {}).get("pet_name") or "the pet"
            if adopter_id:
                try:
                    msg_reason = f" {reason}".rstrip() if reason else ""
                    msg = f"Your adoption request for {pet_name} was declined.{msg_reason}"
                    database.create_notification(adopter_id, msg, role="adopter")
                except Exception:
                    pass

    def delete_request(self, request_id: int, allow_approved: bool = False) -> bool:
        """
        Delete a request. Approved requests are preserved unless allow_approved=True.
        """
        if not request_id:
            raise ValueError("request_id is required.")
        if not allow_approved:
            details = database.get_request_details(request_id)
            if details and str(details.get("status") or "").lower() == "approved":
                raise ValueError("Approved requests are kept for history.")
        return database.delete_request(request_id)

    # --------------- Notifications ---------------
    def list_notifications(self, admin_id: int) -> List[Dict]:
        if not admin_id:
            raise ValueError("admin_id is required.")
        return database.get_notifications_for_user(admin_id, role="admin")

    def mark_notification_read(self, notification_id: int) -> None:
        if not notification_id:
            raise ValueError("notification_id is required.")
        database.mark_notification_read(notification_id)

    def clear_notifications(self, admin_id: int) -> None:
        if not admin_id:
            raise ValueError("admin_id is required.")
        database.clear_notifications_for_user(admin_id, role="admin")

    def delete_notification(self, notification_id: int) -> None:
        if not notification_id:
            raise ValueError("notification_id is required.")
        database.delete_notification(notification_id)

    # --------------- Pending admins ---------------
    def list_pending_admins(self) -> List[Dict]:
        return database.get_pending_admins()

    def approve_pending_admin(self, pending_id: int) -> bool:
        if not pending_id:
            raise ValueError("pending_id is required.")
        return database.approve_pending_admin(pending_id)

    def decline_pending_admin(self, pending_id: int) -> bool:
        if not pending_id:
            raise ValueError("pending_id is required.")
        return database.decline_pending_admin(pending_id)

    # --------------- Pets ---------------
    def list_pets(self, category: Optional[str] = None) -> List[Dict]:
        """
        Return available pets, optionally filtered by category (dog/cat).
        """
        cat = (category or "all").strip().lower()
        if cat == "all":
            return database.get_available_pets()
        if hasattr(database, "get_pets_by_category"):
            return database.get_pets_by_category(cat)
        return database.get_available_pets()

    def _save_photo(self, photo_path: str) -> str:
        """
        Copy a photo into the shared images dir and return the stored filename/path.
        Falls back to the provided path if copying fails.
        """
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

    def add_pet(
        self,
        name: str,
        category: str,
        breed: str,
        age: int,
        sex: str,
        description: str = "",
        image_path: str = "",
        status: str = "available",
        vaccinated: Optional[int] = None,
    ) -> Dict[str, object]:
        if not all([name, category, breed, age, sex]):
            raise ValueError("Name, category, breed, age, and sex are required.")
        try:
            age_val = int(age)
        except Exception:
            raise ValueError("Age must be a number.")
        saved_image = self._save_photo(image_path)
        vaccinated_val = "yes" if vaccinated in (True, 1, "1", "true", "yes", "Yes") else "no"
        database.add_pet(
            name=name,
            category=category.lower(),
            breed=breed,
            age=age_val,
            sex=sex,
            vaccinated=vaccinated_val,
            status=status or "available",
            image=saved_image,
            description=description or "",
            photo_path=saved_image,
        )
        return {
            "name": name,
            "category": category,
            "breed": breed,
            "age": age_val,
            "sex": sex,
            "description": description,
            "photo_path": saved_image,
            "status": status or "available",
            "vaccinated": vaccinated_val,
        }

    def update_pet(
        self,
        pet_id: int,
        name: str,
        breed: str,
        age: int,
        sex: str,
        description: str = "",
        image_path: str = "",
        current_photo: str = "",
        category: Optional[str] = None,
        status: Optional[str] = None,
        vaccinated: Optional[int] = None,
    ) -> None:
        if not pet_id:
            raise ValueError("pet_id is required.")
        try:
            age_val = int(age)
        except Exception:
            raise ValueError("Age must be a number.")
        saved_image = self._save_photo(image_path) or current_photo
        vaccinated_val = None
        if vaccinated is not None:
            vaccinated_val = "yes" if vaccinated in (True, 1, "1", "true", "yes", "Yes") else "no"
        database.update_pet(
            pet_id,
            name,
            breed,
            age_val,
            sex,
            saved_image,
            description or "",
            saved_image,
            category.lower() if category else None,
            vaccinated_val,
            status,
        )
        if current_photo and saved_image and saved_image != current_photo:
            self._remove_photo(current_photo)

    def delete_pet(self, pet_id: int, photo_path: str = "", remove_photo: bool = True) -> None:
        if not pet_id:
            raise ValueError("pet_id is required.")
        database.delete_pet(pet_id)
        if remove_photo and photo_path:
            self._remove_photo(photo_path)

    # --------------- History ---------------
    def adoption_history(self, category: Optional[str] = None) -> List[Dict]:
        history = database.get_adoption_history()
        cat = (category or "all").strip().lower()
        if cat == "all":
            return history
        return [row for row in history if str(row.get("category") or "").lower() == cat]

    # --------------- Profile ---------------
    def update_admin_profile(
        self,
        admin_id: int,
        name: str,
        age: Optional[int],
        email: str,
        phone_number: str,
        birthdate: str,
        photo_path: str = "",
        facebook_url: str = "",
        instagram_url: str = "",
        current_password: str = "",
    ) -> Dict:
        if not admin_id:
            raise ValueError("admin_id is required.")
        age_val = None
        if age not in (None, ""):
            try:
                age_val = int(age)
            except Exception:
                raise ValueError("Age must be a number.")
        saved_photo = self._save_photo(photo_path) if photo_path else photo_path
        ok = database.update_admin(
            admin_id,
            name,
            age_val,
            email,
            phone_number,
            birthdate,
            saved_photo,
            facebook_url,
            instagram_url,
        )
        if not ok:
            raise RuntimeError("Could not update admin profile.")
        refreshed = None
        try:
            if current_password:
                refreshed = database.login_user(email, current_password, "admin")
        except Exception:
            refreshed = None
        return refreshed or {
            "id": admin_id,
            "name": name,
            "age": age_val,
            "email": email,
            "phone": phone_number,
            "birthdate": birthdate,
            "photo_path": saved_photo,
            "facebook_url": facebook_url,
            "instagram_url": instagram_url,
        }

    def delete_admin_account(self, admin_id: int, photo_path: str = "", remove_photo: bool = True) -> None:
        if not admin_id:
            raise ValueError("admin_id is required.")
        database.delete_admin(admin_id)
        if remove_photo and photo_path:
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

    # --------------- About ---------------
    def admin_profiles(self) -> List[Dict]:
        return database.get_admin_profiles()
