import secrets
from typing import Dict

# Allow running this file directly for quick debugging (inject repo root into sys.path)
if __name__ == "__main__":
    import sys
    from pathlib import Path

    ROOT = Path(__file__).resolve().parents[2]
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

from app.models import database
from app.services import email_service


class AuthController:
    """
    Centralized auth/signup logic so views stay thin.
    Handles login, OTP issuance/verification, and signup routing.
    """

    def __init__(self):
        self._otp_cache: Dict[str, Dict[str, str]] = {}

    @staticmethod
    def _require_eight_chars(password: str):
        if len(password) != 8:
            raise ValueError("Password must be exactly 8 characters long.")

    # ---------------------------- LOGIN ----------------------------
    def login(self, email: str, password: str, role_key: str):
        email = (email or "").strip()
        password = (password or "").strip()
        role_key = (role_key or "adopter").lower()

        if not email or not password:
            raise ValueError("Please enter both email and password.")
        self._require_eight_chars(password)

        user = database.login_user(email, password, role_key)
        if not user:
            raise ValueError("Invalid credentials. Please try again.")
        return user

    # ---------------------------- PASSWORD RESET ----------------------------
    def request_otp(self, email: str, role: str):
        email = (email or "").strip()
        role = (role or "adopter").lower()
        if not email:
            raise ValueError("Please enter your email.")

        user = database.get_user_by_email(email, role)
        if not user:
            raise ValueError("No account found with that email for the selected role.")

        code = f"{secrets.randbelow(1_000_000):06d}"
        email_service.send_otp_email(email, code)
        self._otp_cache[email] = {"code": code, "role": role}
        return code

    def reset_password(self, email: str, role: str, code_entered: str, new_password: str):
        email = (email or "").strip()
        role = (role or "adopter").lower()
        code_entered = (code_entered or "").strip()
        new_password = (new_password or "").strip()

        if not code_entered or not new_password:
            raise ValueError("OTP and new password are required.")
        self._require_eight_chars(new_password)

        cached = self._otp_cache.get(email)
        if not cached or cached.get("code") != code_entered or cached.get("role") != role:
            raise ValueError("Invalid OTP. Please check the code sent to your email.")

        ok = database.update_password_by_email(email, role, new_password)
        if not ok:
            raise RuntimeError("Could not update password. Please try again.")

        self._otp_cache.pop(email, None)
        return True

    # ---------------------------- SIGNUP ----------------------------
    def signup(
        self,
        role: str,
        name: str,
        email: str,
        password: str,
        confirm: str,
        phone: str,
        birthdate: str,
        photo_path: str = "",
        facebook_url: str = "",
        instagram_url: str = "",
    ):
        role_key = "admin" if (role or "").lower().startswith("admin") else "adopter"
        name = (name or "").strip()
        email = (email or "").strip()
        password = (password or "").strip()
        confirm = (confirm or "").strip()
        phone = (phone or "").strip()
        birthdate = (birthdate or "").strip()
        photo_path = (photo_path or "").strip()
        facebook_url = (facebook_url or "").strip()
        instagram_url = (instagram_url or "").strip()

        if not all([name, email, password, confirm]):
            raise ValueError("Required fields missing.")
        if password != confirm:
            raise ValueError("Passwords do not match.")
        self._require_eight_chars(password)

        if role_key == "admin":
            # If no admins exist, auto-create the first admin; otherwise require approval.
            try:
                has_admins = len(database.get_admin_profiles()) > 0
            except Exception:
                has_admins = True  # fall back to pending flow if uncertain

            if has_admins:
                database.create_pending_admin(
                    name,
                    email,
                    password,
                    phone,
                    birthdate,
                    photo_path,
                    facebook_url=facebook_url,
                    instagram_url=instagram_url,
                )
            else:
                database.create_admin_user(
                    name,
                    email,
                    password,
                    phone,
                    birthdate,
                    photo_path,
                    facebook_url=facebook_url,
                    instagram_url=instagram_url,
                )
            return role_key

        database.create_adopter_user(name, email, password, phone, birthdate, photo_path)
        return role_key
