import shutil
import sqlite3
import sys
import tempfile
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.controllers import AdopterController
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


class AdopterControllerTests(unittest.TestCase):
    def setUp(self):
        self.tmpdir, self.db_path = setup_temp_db()
        # make sure at least one dog is available for list_pets("dog") tests
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("UPDATE pets SET status='available' WHERE pet_id=1")
        # seed a cat adoption history entry for a known adopter
        cur.execute(
            """
            INSERT INTO users (name, email, password, role, age, birthdate, phone_number, photo_path)
            VALUES (?, ?, ?, 'adopter', ?, ?, ?, ?)
            """,
            ("History User", "history@test.com", "secret12", 28, "1997-01-01", "999", ""),
        )
        adopter_id = cur.lastrowid
        cur.execute(
            """
            INSERT INTO pets (name, category, breed, age, sex, vaccinated, status, description, photo_path)
            VALUES ('History Cat', 'cat', 'mix', 3, 'female', 'yes', 'adopted', 'History cat entry', '')
            """
        )
        cat_id = cur.lastrowid
        cur.execute(
            """
            INSERT INTO adoption_history (adopter_id, pet_id, pet_name, category, breed, sex, adopted_at, adopter_name)
            VALUES (?, ?, ?, ?, ?, ?, datetime('now'), ?)
            """,
            (adopter_id, cat_id, "History Cat", "cat", "mix", "female", "History User"),
        )
        conn.commit()
        conn.close()
        self.ctrl = AdopterController()
        self.history_user_id = adopter_id

    def tearDown(self):
        self.tmpdir.cleanup()

    def test_list_pets_filters_category(self):
        dogs = self.ctrl.list_pets("dog")
        self.assertTrue(len(dogs) > 0)
        self.assertTrue(all((p.get("category") or "").lower() == "dog" for p in dogs))

    def test_adoption_history_filters_cat(self):
        cats = self.ctrl.adoption_history(self.history_user_id, "cat")
        self.assertTrue(len(cats) > 0)
        self.assertTrue(all((row.get("category") or "").lower() == "cat" for row in cats))

    def test_update_profile_persists(self):
        # add a test user
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO users (name, email, password, role, age, birthdate, phone_number, photo_path)
            VALUES (?, ?, ?, 'adopter', ?, ?, ?, ?)
            """,
            ("Temp User", "temp@test.com", "pw", 20, "2004-01-01", "123456", ""),
        )
        user_id = cur.lastrowid
        conn.commit()
        conn.close()

        updated = self.ctrl.update_profile(
            user_id,
            "Temp User Updated",
            "temp@test.com",
            "999",
            "2004-01-01",
            "",
            21,
        )
        self.assertEqual(updated["name"], "Temp User Updated")
        # verify DB
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("SELECT name, phone_number, age FROM users WHERE users_id=?", (user_id,))
        row = cur.fetchone()
        conn.close()
        self.assertEqual(row[0], "Temp User Updated")
        self.assertEqual(row[1], "999")
        self.assertEqual(row[2], 21)

    def test_delete_account_removes_user_and_requests(self):
        # create user + pending request
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO users (name, email, password, role, age, birthdate, phone_number, photo_path)
            VALUES (?, ?, ?, 'adopter', ?, ?, ?, ?)
            """,
            ("Delete Me", "deleteme@test.com", "pw", 22, "2003-01-01", "555", ""),
        )
        user_id = cur.lastrowid
        cur.execute(
            "INSERT INTO adoption_requests (adopter_id, pet_id, information, status, created_at) VALUES (?, ?, ?, 'pending', datetime('now'))",
            (user_id, 1, "test"),
        )
        conn.commit()
        conn.close()

        self.ctrl.delete_account(user_id, "")

        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM users WHERE users_id=?", (user_id,))
        user_row = cur.fetchone()
        cur.execute("SELECT 1 FROM adoption_requests WHERE adopter_id=?", (user_id,))
        req_row = cur.fetchone()
        conn.close()
        self.assertIsNone(user_row)
        self.assertIsNone(req_row)


if __name__ == "__main__":
    unittest.main()
