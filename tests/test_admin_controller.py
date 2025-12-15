import shutil
import sqlite3
import sys
import tempfile
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.controllers import AdminController
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


class AdminControllerTests(unittest.TestCase):
    def setUp(self):
        self.tmpdir, db_path = setup_temp_db()
        # Seed at least one cat so category filter always has data
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO pets (name, category, breed, age, sex, vaccinated, status, description, photo_path)
            VALUES ('Test Cat', 'cat', 'mix', 2, 'female', 'yes', 'available', 'Friendly test cat', '')
            """
        )
        # ensure at least one dog exists; if not, add one
        cur.execute("SELECT pet_id, name, category, breed, sex FROM pets WHERE LOWER(category)='dog' LIMIT 1")
        dog_row = cur.fetchone()
        if not dog_row:
            cur.execute(
                """
                INSERT INTO pets (name, category, breed, age, sex, vaccinated, status, description, photo_path)
                VALUES ('Test Dog', 'dog', 'mix', 3, 'male', 'yes', 'available', 'Friendly test dog', '')
                """
            )
            dog_id = cur.lastrowid
            dog_name = "Test Dog"
            dog_breed = "mix"
            dog_sex = "male"
        else:
            dog_id = dog_row[0]
            dog_name = dog_row[1]
            dog_breed = dog_row[3]
            dog_sex = dog_row[4]

        # seed adoption history with a dog entry for filtering
        cur.execute(
            """
            INSERT INTO adoption_history (adopter_id, pet_id, pet_name, category, breed, sex, adopted_at, adopter_name)
            VALUES (1, ?, ?, 'dog', ?, ?, datetime('now'), 'History User')
            """,
            (dog_id, dog_name, dog_breed, dog_sex),
        )
        conn.commit()
        conn.close()
        self.ctrl = AdminController()

    def tearDown(self):
        self.tmpdir.cleanup()

    def test_list_pets_filters_category(self):
        cats = self.ctrl.list_pets("cat")
        self.assertTrue(len(cats) > 0)
        self.assertTrue(all((p.get("category") or "").lower() == "cat" for p in cats))

    def test_adoption_history_filters_category(self):
        dogs = self.ctrl.adoption_history("dog")
        self.assertTrue(len(dogs) > 0)
        self.assertTrue(all((row.get("category") or "").lower() == "dog" for row in dogs))


if __name__ == "__main__":
    unittest.main()
