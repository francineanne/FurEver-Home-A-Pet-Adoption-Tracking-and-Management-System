import shutil
import sqlite3
import sys
import tempfile
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.controllers.auth_controller import AuthController
from app.models import database


def setup_temp_db():
    tmpdir = tempfile.TemporaryDirectory()
    db_path = Path(tmpdir.name) / "test.db"
    shutil.copy2("fureverhome.db", db_path)
    database.DB_PATH = str(db_path)
    database._ADOPTION_INFO_COLUMN = None
    database._ADOPTION_HISTORY_ENSURED = False
    database._SOCIAL_COLUMNS_ENSURED = False
    return tmpdir, db_path


class AuthControllerTests(unittest.TestCase):
    def setUp(self):
        self.tmpdir, self.db_path = setup_temp_db()
        self.auth = AuthController()
        # seed known admin and adopter
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO admin (name, age, birthdate, phone_number, email, password, photo_path, facebook_url, instagram_url)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            ("Test Admin", 30, "1990-01-01", "000", "admin@test.com", "secret12", "", "", ""),
        )
        cur.execute(
            """
            INSERT INTO users (name, email, password, role, age, birthdate, phone_number, photo_path)
            VALUES (?, ?, ?, 'adopter', ?, ?, ?, ?)
            """,
            ("Test User", "user@test.com", "secret12", 25, "1999-01-01", "111", ""),
        )
        conn.commit()
        conn.close()

    def tearDown(self):
        self.tmpdir.cleanup()

    def test_login_adopter_success(self):
        user = self.auth.login("user@test.com", "secret12", "adopter")
        self.assertEqual(user["role"], "adopter")
        self.assertEqual(user["email"], "user@test.com")

    def test_login_admin_success(self):
        user = self.auth.login("admin@test.com", "secret12", "admin")
        self.assertEqual(user["role"], "admin")
        self.assertEqual(user["email"], "admin@test.com")

    def test_login_invalid_credentials(self):
        with self.assertRaises(ValueError):
            self.auth.login("user@test.com", "wrong", "adopter")


if __name__ == "__main__":
    unittest.main()
