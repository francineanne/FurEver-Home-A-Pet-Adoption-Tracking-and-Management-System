import sqlite3
from datetime import datetime
import os
import sys
from pathlib import Path

# Allow running directly for debugging; inject repo root into sys.path
if __name__ == "__main__":
    ROOT = Path(__file__).resolve().parents[2]
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

from app.config import DB_PATH as CONFIG_DB_PATH, BASE_DIR, IMAGES_DIR

DB_PATH = str(CONFIG_DB_PATH)

_SOCIAL_COLUMNS_ENSURED = False
_ADOPTION_INFO_COLUMN = None
_ADOPTION_HISTORY_ENSURED = False


def _ensure_admin_social_columns():
    """
    Add facebook/instagram URL columns to admin + admin_pending if they don't exist.
    """
    global _SOCIAL_COLUMNS_ENSURED
    if _SOCIAL_COLUMNS_ENSURED:
        return

    conn = connect()
    cur = conn.cursor()
    tables_ok = True

    for table in ("admin", "admin_pending"):
        try:
            cur.execute(f"PRAGMA table_info({table})")
            cols = {row[1] for row in cur.fetchall()}
            # If the table doesn't exist yet, skip and try again next time.
            if not cols:
                tables_ok = False
                continue
            if "facebook_url" not in cols:
                cur.execute(f"ALTER TABLE {table} ADD COLUMN facebook_url TEXT")
            if "instagram_url" not in cols:
                cur.execute(f"ALTER TABLE {table} ADD COLUMN instagram_url TEXT")
        except Exception:
            tables_ok = False

    try:
        conn.commit()
    finally:
        conn.close()

    if tables_ok:
        _SOCIAL_COLUMNS_ENSURED = True

# --------------------------------------------------
# CONNECT
# --------------------------------------------------
def connect():
    conn = sqlite3.connect(DB_PATH, timeout=10, check_same_thread=False)
    try:
        conn.execute("PRAGMA busy_timeout=5000")
        conn.execute("PRAGMA journal_mode=WAL")
    except Exception:
        pass
    return conn


def _get_adoption_info_column(cursor):
    """
    Ensure we reference the adoption request note column even if renamed.
    Prefers 'information'; falls back to 'reason' for older DBs.
    Attempts a rename from reason->information when possible.
    """
    global _ADOPTION_INFO_COLUMN
    if _ADOPTION_INFO_COLUMN:
        return _ADOPTION_INFO_COLUMN

    cursor.execute("PRAGMA table_info(adoption_requests)")
    cols = [row[1] for row in cursor.fetchall()]
    if "information" in cols:
        _ADOPTION_INFO_COLUMN = "information"
        return _ADOPTION_INFO_COLUMN

    if "reason" in cols:
        try:
            cursor.execute("ALTER TABLE adoption_requests RENAME COLUMN reason TO information")
            cursor.connection.commit()
            _ADOPTION_INFO_COLUMN = "information"
            return _ADOPTION_INFO_COLUMN
        except Exception:
            _ADOPTION_INFO_COLUMN = "reason"
            return _ADOPTION_INFO_COLUMN

    # default fallback if neither exists (should not happen)
    _ADOPTION_INFO_COLUMN = "information"
    return _ADOPTION_INFO_COLUMN


def _ensure_adoption_history_table():
    """
    Ensure adoption_history table exists for history snapshots.
    """
    global _ADOPTION_HISTORY_ENSURED
    if _ADOPTION_HISTORY_ENSURED:
        return
    conn = connect()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS adoption_history (
                id INTEGER PRIMARY KEY,
                adopter_id INTEGER,
                pet_id INTEGER,
                pet_name TEXT,
                category TEXT,
                breed TEXT,
                sex TEXT,
                adopted_at TEXT,
                adopter_name TEXT
            )
            """
        )
        conn.commit()
        _ADOPTION_HISTORY_ENSURED = True
    finally:
        conn.close()


def _backfill_adoption_history(cur, adopter_id=None):
    """
    If history is empty for an adopter (or globally), seed it from approved adoption_requests.
    """
    query = "SELECT COUNT(*) FROM adoption_history"
    params = ()
    if adopter_id is not None:
        query += " WHERE adopter_id=?"
        params = (adopter_id,)
    cur.execute(query, params)
    if cur.fetchone()[0]:
        return
    cur.execute(
        """
        INSERT OR IGNORE INTO adoption_history (
            adopter_id, pet_id, pet_name, category, breed, sex, adopted_at, adopter_name
        )
        SELECT ar.adopter_id,
               ar.pet_id,
               COALESCE(p.name, '(Removed Pet)'),
               p.category,
               p.breed,
               p.sex,
               ar.created_at,
               u.name
        FROM adoption_requests ar
        LEFT JOIN pets p ON ar.pet_id = p.pet_id
        LEFT JOIN users u ON ar.adopter_id = u.users_id
        WHERE LOWER(TRIM(ar.status))='approved'
        """
        + (" AND ar.adopter_id=?" if adopter_id is not None else ""),
        params,
    )

# --------------------------------------------------
# LOGIN (Admin + Adopter)
# --------------------------------------------------
def login_user(email, password, role):
    _ensure_admin_social_columns()

    conn = connect()
    cur = conn.cursor()

    # ADMIN LOGIN
    if role == "admin":
        cur.execute("""
            SELECT admin_id, name, age, birthdate, phone_number, email, password, photo_path, facebook_url, instagram_url
            FROM admin
            WHERE email=? AND password=?
        """, (email, password))
        row = cur.fetchone()
        conn.close()

        if row:
            return {
                "id": row[0],
                "name": row[1],
                "age": row[2],
                "birthdate": row[3],
                "phone": row[4],  # This is phone_number in DB
                "email": row[5],
                "password": row[6],
                "photo_path": row[7],  # Now included
                "facebook_url": row[8],
                "instagram_url": row[9],
                "role": "admin"
            }
        return None

    # ADOPTER LOGIN (unchanged)
    else:
        cur.execute("""
            SELECT users_id, name, email, password, age, birthdate, phone_number, photo_path
            FROM users
            WHERE email=? AND password=?
        """, (email, password))
        row = cur.fetchone()
        conn.close()

        if row:
            return {
                "users_id": row[0],
                "name": row[1],
                "email": row[2],
                "password": row[3],
                "age": row[4],
                "birthdate": row[5],
                "phone": row[6],
                "photo_path": row[7],
                "role": "adopter"
            }
        return None

# NEW: Update admin profile (optional, for better organization)
def update_admin(admin_id, name, age, email, phone_number, birthdate, photo_path, facebook_url=None, instagram_url=None):
    _ensure_admin_social_columns()
    conn = connect()
    cur = conn.cursor()
    try:
        cur.execute("""
            UPDATE admin
            SET name=?, age=?, email=?, phone_number=?, birthdate=?, photo_path=?, facebook_url=?, instagram_url=?
            WHERE admin_id=?
        """, (name, age, email, phone_number, birthdate, photo_path, facebook_url, instagram_url, admin_id))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error updating admin: {e}")
        return False
    finally:
        conn.close()

# --------------------------------------------------
# SUMMARY STATS
# --------------------------------------------------
def get_summary_stats():
    conn = connect()
    cur = conn.cursor()

    # Total available pets
    cur.execute("SELECT COUNT(*) FROM pets WHERE status='available'")
    total_pets = cur.fetchone()[0]

    # Total adoption requests
    cur.execute("SELECT COUNT(*) FROM adoption_requests")
    total_requests = cur.fetchone()[0]

    # Total adoptions (assuming there's a status or table for completed adoptions)
    # If adoptions are marked in adoption_requests with status='approved', count those
    cur.execute("SELECT COUNT(*) FROM adoption_requests WHERE LOWER(TRIM(status))='approved'")
    total_adoptions = cur.fetchone()[0]

    conn.close()
    return {
        "total_pets": total_pets,
        "total_requests": total_requests,
        "total_adoptions": total_adoptions
    }

def _resolve_pet_image(image_value, pet_name, photo_path=None):
    """
    Returns an absolute path to a pet image.
    - If the DB value (image/photo_path) points to a real file, use it.
    - Otherwise try to find an image in the images/ folder that matches the pet name.
    - Fall back to a placeholder (handled later by the UI loader).
    """
    # Use project-root aware paths so lookups work regardless of the current module location.
    base_dir = str(BASE_DIR)
    images_dir = str(IMAGES_DIR)

    def check_candidate(path_value):
        if not path_value:
            return None
        if os.path.isabs(path_value):
            candidate = path_value
        else:
            # First try relative to repo root, then fall back to images/
            candidate = os.path.join(base_dir, path_value)
            if not os.path.exists(candidate):
                candidate = os.path.join(images_dir, path_value)
        if os.path.exists(candidate) and os.path.isfile(candidate):
            return candidate
        return None

    # 1) Use photo_path if present
    resolved = check_candidate(photo_path)
    if resolved:
        return resolved

    # 2) Use the legacy image field if passed
    resolved = check_candidate(image_value)
    if resolved:
        return resolved

    # 2) Try to match a filename based on the pet name
    if pet_name:
        safe_name = "".join(ch.lower() for ch in pet_name if ch.isalnum())
        for ext in (".jpg", ".jpeg", ".png", ".gif"):
            candidate = os.path.join(images_dir, f"{safe_name}{ext}")
            if os.path.exists(candidate) and os.path.isfile(candidate):
                return candidate

    # 3) Let the UI show its own placeholder
    return None

# --------------------------------------------------
# PETS
# --------------------------------------------------
def get_available_pets():
    conn = connect()
    cur = conn.cursor()
    cur.execute("""
        SELECT pet_id, name, category, breed, age, sex, vaccinated, status, description, photo_path
        FROM pets
        WHERE status='available'
    """)
    rows = cur.fetchall()
    conn.close()

    return [
        {
            "id": r[0],
            "name": r[1],
            "category": r[2],
            "breed": r[3],
            "age": r[4],
            "sex": r[5],
            "vaccinated": r[6],
            "status": r[7],
            "description": r[8],
            "photo_path": r[9],
            "image": _resolve_pet_image(None, r[1], r[9]),
        } for r in rows
    ]

def get_pets_by_category(category):
    conn = connect()
    cur = conn.cursor()
    # Ensure case-insensitive category filtering
    cur.execute("""
        SELECT pet_id, name, category, breed, age, sex, vaccinated, status, description, photo_path
        FROM pets
        WHERE LOWER(category)=? AND status='available'
    """, (category.lower(),))
    rows = cur.fetchall()
    conn.close()

    return [
        {
            "id": r[0],
            "name": r[1],
            "category": r[2],
            "breed": r[3],
            "age": r[4],
            "sex": r[5],
            "vaccinated": r[6],
            "status": r[7],
            "description": r[8],
            "photo_path": r[9],
            "image": _resolve_pet_image(None, r[1], r[9]),
        } for r in rows
    ]

def get_pet_by_id(pet_id):
    conn = connect()
    cur = conn.cursor()
    cur.execute("""
        SELECT pet_id, name, category, breed, age, sex, vaccinated, status, description, photo_path
        FROM pets
        WHERE pet_id=?
    """, (pet_id,))
    row = cur.fetchone()
    conn.close()
    if row:
        return {
            "id": row[0],
            "name": row[1],
            "category": row[2],
            "breed": row[3],
            "age": row[4],
            "sex": row[5],
            "vaccinated": row[6],
            "status": row[7],
            "description": row[8],
            "photo_path": row[9],
            "image": _resolve_pet_image(None, row[1], row[9]),
        }
    return None

def delete_pet(pet_id):
    conn = connect()
    cur = conn.cursor()
    try:
        # Remove only non-approved requests; keep approved rows for history
        cur.execute("DELETE FROM adoption_requests WHERE pet_id=? AND status!='approved'", (pet_id,))
        cur.execute("DELETE FROM pets WHERE pet_id=?", (pet_id,))
        conn.commit()
    finally:
        conn.close()

def add_pet(name, category, breed, age, sex, image=None, description=None, photo_path=None, status="available", vaccinated=None):
    """
    Insert a new pet. Keeps photo_path in sync (image kept for legacy callers).
    """
    conn = connect()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO pets (name, category, breed, age, sex, vaccinated, status, description, photo_path)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (name, category, breed, age, sex, vaccinated, status, description, photo_path or image),
    )
    conn.commit()
    conn.close()


def get_all_pets():
    """
    Convenience wrapper for UIs that expect all pets (uses available pets).
    """
    try:
        return get_available_pets()
    except Exception:
        return []

def update_pet(pet_id, name, breed, age, sex, image=None, description=None, photo_path=None, category=None, vaccinated=None, status=None):
    """
    Update a pet record with the fields we edit from the UI.
    Keeps photo_path in sync for legacy callers.
    """
    conn = connect()
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE pets
        SET name=?, breed=?, age=?, sex=?, description=?, photo_path=?, category=COALESCE(?, category), vaccinated=COALESCE(?, vaccinated), status=COALESCE(?, status)
        WHERE pet_id=?
        """,
        (name, breed, age, sex, description, photo_path or image, category, vaccinated, status, pet_id),
    )
    conn.commit()
    conn.close()

# --------------------------------------------------
# USERS
# --------------------------------------------------
def get_user_by_id(user_id):
    conn = connect()
    cur = conn.cursor()
    cur.execute("SELECT users_id, name, email, password, role, age, birthdate, phone_number, photo_path, image FROM users WHERE users_id=?", (user_id,))
    row = cur.fetchone()
    conn.close()
    if row:
        return {
            "users_id": row[0],
            "name": row[1],
            "email": row[2],
            "password": row[3],
            "role": row[4],
            "age": row[5],
            "birthdate": row[6],
            "phone": row[7],
            "photo_path": row[8],
            "image": row[9],
        }
    return None

# --------------------------------------------------
# ADOPTION REQUESTS
# --------------------------------------------------
def get_all_requests():
    conn = connect()
    cur = conn.cursor()
    info_col = _get_adoption_info_column(cur)
    cur.execute(f"""
        SELECT ar.id, ar.adopter_id, ar.pet_id, ar.status, ar.created_at, ar.{info_col} as reason,
               u.name as adopter_name, u.photo_path as adopter_photo, u.email as adopter_email, u.phone_number,
               p.name as pet_name, p.photo_path, p.vaccinated, p.status,
               p.category, p.breed, p.age, p.sex
        FROM adoption_requests ar
        JOIN users u ON ar.adopter_id = u.users_id
        JOIN pets p ON ar.pet_id = p.pet_id
    """)
    rows = cur.fetchall()
    conn.close()
    result = []
    for r in rows:
        pet_photo = r[10]
        pet_image = None  # legacy DBs may not have an image column
        resolved = _resolve_pet_image(pet_image, r[9], pet_photo)
        vaccinated = r[11]
        pet_status = r[12]
        pet_category = r[13]
        pet_breed = r[14]
        pet_age = r[15]
        pet_sex = r[16]
        result.append({
            "id": r[0],
            "adopter_id": r[1],
            "pet_id": r[2],
            "status": r[3],
            "created_at": r[4],
            "reason": r[5],
            "adopter_name": r[6],
            "adopter_photo": r[7],
            "adopter_email": r[8],
            "adopter_phone": r[9],
            "pet_name": r[10],
            "pet_photo": pet_photo,
            "pet_image": pet_image,
            "pet_image_resolved": resolved,
            "vaccinated": vaccinated,
            "pet_status": pet_status,
            "category": pet_category,
            "breed": pet_breed,
            "age": pet_age,
            "sex": pet_sex,
        })
    return result

def approve_request(req_id):
    _ensure_adoption_history_table()
    conn = connect()
    cur = conn.cursor()
    # Fetch request details first
    cur.execute("SELECT adopter_id, pet_id FROM adoption_requests WHERE id=?", (req_id,))
    row = cur.fetchone()
    if not row:
        conn.close()
        return None

    adopter_id, pet_id = row
    cur.execute("UPDATE adoption_requests SET status='approved' WHERE id=?", (req_id,))
    # Mark pet as adopted/unavailable
    try:
        cur.execute("UPDATE pets SET status='adopted' WHERE pet_id=?", (pet_id,))
    except Exception:
        pass
    # Snapshot into adoption_history for reporting/UI
    try:
        cur.execute(
            """
        INSERT OR IGNORE INTO adoption_history (
            adopter_id, pet_id, pet_name, category, breed, sex, adopted_at, adopter_name
        )
        SELECT u.users_id, p.pet_id, p.name, p.category, p.breed, p.sex, datetime('now','localtime'), u.name
        FROM users u, pets p
        WHERE u.users_id=? AND p.pet_id=?
        """,
        (adopter_id, pet_id),
    )
    except Exception:
        pass
    conn.commit()
    conn.close()
    return {"adopter_id": adopter_id, "pet_id": pet_id}

def decline_request(req_id, reason):
    conn = connect()
    cur = conn.cursor()
    info_col = _get_adoption_info_column(cur)
    cur.execute(f"UPDATE adoption_requests SET status='declined', {info_col}=? WHERE id=?", (reason, req_id))
    conn.commit()
    conn.close()

def get_request_details(req_id):
    conn = connect()
    cur = conn.cursor()
    info_col = _get_adoption_info_column(cur)
    cur.execute(
        f"""
        SELECT ar.id, ar.adopter_id, ar.pet_id, ar.status, ar.created_at, ar.{info_col} as reason,
               u.name as adopter_name, u.photo_path as adopter_photo, u.email as adopter_email, u.phone_number,
               p.name as pet_name, p.photo_path as pet_photo, p.vaccinated, p.status,
               p.category, p.breed, p.age, p.sex
        FROM adoption_requests ar
        JOIN users u ON ar.adopter_id = u.users_id
        JOIN pets p ON ar.pet_id = p.pet_id
        WHERE ar.id=?
        """,
        (req_id,),
    )
    row = cur.fetchone()
    conn.close()
    if not row:
        return None
    pet_photo = row[11]
    pet_image = None
    resolved = _resolve_pet_image(pet_image, row[10], pet_photo)
    vaccinated = row[12]
    pet_status = row[13]
    pet_category = row[14]
    pet_breed = row[15]
    pet_age = row[16]
    pet_sex = row[17]
    return {
        "id": row[0],
        "adopter_id": row[1],
        "pet_id": row[2],
        "status": row[3],
        "created_at": row[4],
        "reason": row[5],
        "adopter_name": row[6],
        "adopter_photo": row[7],
        "adopter_email": row[8],
        "adopter_phone": row[9],
        "pet_name": row[10],
        "pet_photo": row[11],
        "pet_image": pet_image,
        "pet_image_resolved": resolved,
        "vaccinated": vaccinated,
        "pet_status": pet_status,
        "category": pet_category,
        "breed": pet_breed,
        "age": pet_age,
        "sex": pet_sex,
    }

def cancel_request(req_id, adopter_id=None):
    """
    Cancel a pending request. If adopter_id is provided, enforce ownership.
    """
    conn = connect()
    cur = conn.cursor()
    try:
        if adopter_id is not None:
            cur.execute(
                "UPDATE adoption_requests SET status='cancelled' WHERE id=? AND adopter_id=? AND status='pending'",
                (req_id, adopter_id),
            )
        else:
            cur.execute(
                "UPDATE adoption_requests SET status='cancelled' WHERE id=? AND status='pending'",
                (req_id,),
            )
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()

def delete_request(req_id, adopter_id=None):
    """
    Hard-delete a request (adopter-owned or any if adopter_id not provided).
    Approved requests are preserved for history.
    """
    conn = connect()
    cur = conn.cursor()
    try:
        # Do not delete approved requests to preserve adoption history
        if adopter_id is not None:
            cur.execute("DELETE FROM adoption_requests WHERE id=? AND adopter_id=? AND status!='approved'", (req_id, adopter_id))
        else:
            cur.execute("DELETE FROM adoption_requests WHERE id=? AND status!='approved'", (req_id,))
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()
# Submit a new adoption request (used by adopter flow)
def submit_adoption_request(adopter_id, pet_id, note):
    conn = connect()
    cur = conn.cursor()
    info_col = _get_adoption_info_column(cur)
    cur.execute(
        f"""
        INSERT INTO adoption_requests (adopter_id, pet_id, {info_col}, status, created_at)
        VALUES (?, ?, ?, 'pending', datetime('now','localtime'))
        """,
        (adopter_id, pet_id, note),
    )
    conn.commit()
    conn.close()
    return True


def has_pending_request(adopter_id, pet_id):
    """
    Check if the adopter already has a pending request for the given pet.
    """
    conn = connect()
    cur = conn.cursor()
    cur.execute(
        "SELECT 1 FROM adoption_requests WHERE adopter_id=? AND pet_id=? AND status='pending' LIMIT 1",
        (adopter_id, pet_id),
    )
    row = cur.fetchone()
    conn.close()
    return bool(row)

def get_adoption_history_for_adopter(adopter_id):
    _ensure_adoption_history_table()
    conn = connect()
    cur = conn.cursor()
    info_col = _get_adoption_info_column(cur)
    _backfill_adoption_history(cur, adopter_id=adopter_id)
    cur.execute(
        f"""
        SELECT
            COALESCE(ah.pet_name, p.name, '(Removed Pet)') as pet_name,
            COALESCE(ah.category, p.category) as category,
            COALESCE(ah.breed, p.breed) as breed,
            p.age,
            COALESCE(ah.sex, p.sex) as sex,
            p.vaccinated,
            p.status,
            p.description,
            p.photo_path,
            ah.adopted_at,
            ar.{info_col} as reason
        FROM adoption_history ah
        LEFT JOIN pets p ON ah.pet_id = p.pet_id
        LEFT JOIN adoption_requests ar
            ON ar.pet_id = ah.pet_id
            AND ar.adopter_id = ah.adopter_id
            AND LOWER(TRIM(ar.status))='approved'
        WHERE ah.adopter_id=?
        ORDER BY ah.adopted_at DESC
    """,
        (adopter_id,),
    )
    rows = cur.fetchall()
    conn.close()
    return [
        {
            "pet_name": r[0],
            "category": r[1],
            "breed": r[2],
            "age": r[3],
            "sex": r[4],
            "vaccinated": r[5],
            "status": r[6],
            "description": r[7],
            "photo_path": r[8],
            "adopted_at": r[9],
            "reason": r[10] if len(r) > 10 else None,
        }
        for r in rows
    ]

# Requests for a specific adopter
def get_adopter_requests(adopter_id):
    conn = connect()
    cur = conn.cursor()
    info_col = _get_adoption_info_column(cur)
    cur.execute(
        f"""
        SELECT ar.id, ar.pet_id, ar.status, ar.created_at, ar.{info_col} as reason, p.name as pet_name, p.photo_path, p.vaccinated, p.status,
               p.category, p.breed, p.age, p.sex
        FROM adoption_requests ar
        JOIN pets p ON ar.pet_id = p.pet_id
        WHERE ar.adopter_id=?
        ORDER BY ar.created_at DESC
        """,
        (adopter_id,),
    )
    rows = cur.fetchall()
    conn.close()
    return [
        {
            "id": r[0],
            "pet_id": r[1],
            "status": r[2],
            "created_at": r[3],
            "reason": r[4],
            "pet_name": r[5],
            "pet_photo": r[6],
            "pet_image": None,
            "pet_image_resolved": _resolve_pet_image(None, r[5], r[6]),
            "vaccinated": r[7],
            "pet_status": r[8],
            "category": r[9],
            "breed": r[10],
            "age": r[11],
            "sex": r[12],
        }
        for r in rows
    ]

# --------------------------------------------------
# PASSWORD RESET HELPERS
# --------------------------------------------------
def get_user_by_email(email, role):
    """
    Fetch a user/admin by email for password reset checks.
    Returns a dict with id, name, email, role if found, else None.
    """
    conn = connect()
    cur = conn.cursor()
    role = (role or "").lower()

    if role == "admin":
        cur.execute("""
            SELECT admin_id, name, email
            FROM admin
            WHERE email=?
        """, (email,))
        row = cur.fetchone()
        conn.close()
        if row:
            return {"id": row[0], "name": row[1], "email": row[2], "role": "admin"}
        return None

    # default to adopter/users
    cur.execute("""
        SELECT users_id, name, email
        FROM users
        WHERE email=?
    """, (email,))
    row = cur.fetchone()
    conn.close()
    if row:
        return {"id": row[0], "name": row[1], "email": row[2], "role": "adopter"}
    return None


def update_password_by_email(email, role, new_password):
    """
    Update password for either admin or adopter based on role + email.
    Returns True if a row was updated, False otherwise.
    """
    conn = connect()
    cur = conn.cursor()
    role = (role or "").lower()

    if role == "admin":
        cur.execute("UPDATE admin SET password=? WHERE email=?", (new_password, email))
    else:
        cur.execute("UPDATE users SET password=? WHERE email=?", (new_password, email))

    conn.commit()
    updated = cur.rowcount > 0
    conn.close()
    return updated

def update_user_profile(users_id, name, email, phone_number, birthdate, photo_path, age=None):
    conn = connect()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            UPDATE users
            SET name=?, email=?, phone_number=?, birthdate=?, photo_path=?, age=?
            WHERE users_id=?
            """,
            (name, email, phone_number, birthdate, photo_path, age, users_id),
        )
        conn.commit()
        return True
    except Exception as e:
        print(f"Error updating user: {e}")
        return False
    finally:
        conn.close()

# --------------------------------------------------
# SIGNUP / PENDING ADMINS
# --------------------------------------------------
def _ensure_admin_pending_table():
    conn = connect()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS admin_pending (
            pending_id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            password TEXT NOT NULL,
            phone_number TEXT,
            birthdate TEXT,
            photo_path TEXT,
            facebook_url TEXT,
            instagram_url TEXT,
            status TEXT DEFAULT 'pending',
            created_at TEXT DEFAULT (datetime('now','localtime'))
        )
        """
    )
    conn.commit()
    conn.close()
    _ensure_admin_social_columns()


def create_pending_admin(
    name,
    email,
    password,
    phone_number=None,
    birthdate=None,
    photo_path=None,
    facebook_url=None,
    instagram_url=None,
):
    _ensure_admin_pending_table()
    _ensure_admin_social_columns()
    conn = connect()
    cur = conn.cursor()
    created_local = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S")
    cur.execute(
        """
        INSERT INTO admin_pending (name, email, password, phone_number, birthdate, photo_path, facebook_url, instagram_url, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?)
        """,
        (name, email, password, phone_number, birthdate, photo_path, facebook_url, instagram_url, created_local),
    )
    conn.commit()
    conn.close()
    return True


def get_pending_admins():
    _ensure_admin_pending_table()
    _ensure_admin_social_columns()
    conn = connect()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT pending_id, name, email, phone_number, birthdate, photo_path, facebook_url, instagram_url, status, created_at
        FROM admin_pending
        ORDER BY created_at DESC
        """
    )
    rows = cur.fetchall()
    conn.close()
    return [
        {
            "pending_id": r[0],
            "name": r[1],
            "email": r[2],
            "phone_number": r[3],
            "birthdate": r[4],
            "photo_path": r[5],
            "facebook_url": r[6],
            "instagram_url": r[7],
            "status": r[8],
            "created_at": r[9],
        }
        for r in rows
    ]


def approve_pending_admin(pending_id):
    _ensure_admin_pending_table()
    _ensure_admin_social_columns()
    conn = connect()
    cur = conn.cursor()
    cur.execute(
        "SELECT name, email, password, phone_number, birthdate, photo_path, facebook_url, instagram_url FROM admin_pending WHERE pending_id=?",
        (pending_id,),
    )
    row = cur.fetchone()
    if not row:
        conn.close()
        return False
    name, email, password, phone, birth, photo, fb_url, ig_url = row
    cur.execute(
        """
        INSERT INTO admin (name, email, password, phone_number, birthdate, photo_path, facebook_url, instagram_url)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (name, email, password, phone, birth, photo, fb_url, ig_url),
    )
    cur.execute("DELETE FROM admin_pending WHERE pending_id=?", (pending_id,))
    conn.commit()
    conn.close()
    return True


def decline_pending_admin(pending_id):
    _ensure_admin_pending_table()
    conn = connect()
    cur = conn.cursor()
    cur.execute("DELETE FROM admin_pending WHERE pending_id=?", (pending_id,))
    conn.commit()
    conn.close()
    return True

# --------------------------------------------------
# DELETE ACCOUNTS
# --------------------------------------------------
def delete_admin(admin_id):
    conn = connect()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM admin WHERE admin_id=?", (admin_id,))
        conn.commit()
        return True
    finally:
        conn.close()

def delete_user(user_id):
    conn = connect()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM users WHERE users_id=?", (user_id,))
        cur.execute("DELETE FROM adoption_requests WHERE adopter_id=?", (user_id,))
        conn.commit()
        return True
    finally:
        conn.close()


def create_adopter_user(name, email, password, phone_number=None, birthdate=None, photo_path=None):
    conn = connect()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO users (name, email, password, role, age, birthdate, phone_number, photo_path)
        VALUES (?, ?, ?, 'adopter', NULL, ?, ?, ?)
        """,
        (name, email, password, birthdate, phone_number, photo_path),
    )
    conn.commit()
    conn.close()
    return True


def create_admin_user(
    name,
    email,
    password,
    phone_number=None,
    birthdate=None,
    photo_path=None,
    facebook_url=None,
    instagram_url=None,
):
    """
    Create an admin directly (used for first/admin bootstrap when none exist).
    """
    _ensure_admin_social_columns()
    conn = connect()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO admin (name, email, password, phone_number, birthdate, photo_path, facebook_url, instagram_url)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (name, email, password, phone_number, birthdate, photo_path, facebook_url, instagram_url),
    )
    conn.commit()
    conn.close()
    return True


def get_admin_profiles():
    """
    Return all admins with optional social links for About Us/profile displays.
    """
    _ensure_admin_social_columns()
    conn = connect()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT admin_id, name, email, phone_number, birthdate, photo_path, facebook_url, instagram_url
        FROM admin
        ORDER BY admin_id ASC
        """
    )
    rows = cur.fetchall()
    conn.close()
    return [
        {
            "admin_id": r[0],
            "name": r[1],
            "email": r[2],
            "phone_number": r[3],
            "birthdate": r[4],
            "photo_path": r[5],
            "facebook_url": r[6],
            "instagram_url": r[7],
        }
        for r in rows
    ]
# --------------------------------------------------
# ADOPTION HISTORY
# --------------------------------------------------
def get_adoption_history():
    _ensure_adoption_history_table()
    conn = connect()
    cur = conn.cursor()
    _backfill_adoption_history(cur, adopter_id=None)
    cur.execute("""
        SELECT
            COALESCE(ah.pet_name, p.name, '(Removed Pet)') as pet_name,
            COALESCE(ah.category, p.category) as category,
            COALESCE(ah.breed, p.breed) as breed,
            p.age,
            COALESCE(ah.sex, p.sex) as sex,
            p.vaccinated,
            p.status,
            p.description,
            p.photo_path,
            ah.adopted_at as adopted_at,
            COALESCE(ah.adopter_name, u.name) as adopter_name,
            u.email as adopter_email
        FROM adoption_history ah
        LEFT JOIN pets p ON ah.pet_id = p.pet_id
        LEFT JOIN users u ON ah.adopter_id = u.users_id
        ORDER BY ah.adopted_at DESC
    """)
    rows = cur.fetchall()
    conn.close()
    return [
        {
            "pet_name": r[0],
            "category": r[1],
            "breed": r[2],
            "age": r[3],
            "sex": r[4],
            "vaccinated": r[5],
            "status": r[6],
            "description": r[7],
            "photo_path": r[8],
            "adopted_at": r[9],
            "adopter_name": r[10],
            "adopter_email": r[11],
        }
        for r in rows
    ]

# --------------------------------------------------
# MOST ADOPTED BREEDS
# --------------------------------------------------
def get_most_adopted_breeds():
    conn = connect()
    cur = conn.cursor()
    cur.execute("""
        SELECT p.breed, COUNT(*) as count
        FROM adoption_requests ar
        JOIN pets p ON ar.pet_id = p.pet_id
        WHERE LOWER(TRIM(ar.status))='approved'
        GROUP BY p.breed
        ORDER BY count DESC
        LIMIT 5
    """)
    rows = cur.fetchall()
    conn.close()
    return rows

# --------------------------------------------------
# ADOPTION TREND
# --------------------------------------------------
def get_adoption_trend():
    conn = connect()
    cur = conn.cursor()
    cur.execute("""
        SELECT DATE(created_at), COUNT(*)
        FROM adoption_requests
        WHERE LOWER(TRIM(status))='approved'
        GROUP BY DATE(created_at)
        ORDER BY DATE(created_at)
    """)
    rows = cur.fetchall()
    conn.close()
    return rows

# --------------------------------------------------
# NOTIFICATIONS
# --------------------------------------------------
def _notification_schema(cursor):
    """
    Detect notification table columns so we can support older DBs.
    Returns (date_col, has_read_flag, has_role_flag).
    """
    cursor.execute("PRAGMA table_info(notifications)")
    cols = [row[1] for row in cursor.fetchall()]
    date_col = "created_at" if "created_at" in cols else "date"
    has_is_read = "is_read" in cols
    has_role = "role" in cols
    return date_col, has_is_read, has_role


ADMIN_ID_OFFSET = 1_000_000

def _encode_user_id(user_id, role, has_role):
    """
    For schemas without a role column, offset admin ids to avoid collisions with adopters.
    """
    if has_role or role != "admin":
        return user_id
    try:
        return int(user_id) + ADMIN_ID_OFFSET
    except Exception:
        return user_id


def create_notification(user_id, message, role=None):
    conn = connect()
    cur = conn.cursor()
    date_col, has_is_read, has_role = _notification_schema(cur)
    encoded_user_id = _encode_user_id(user_id, role, has_role)
    columns = ["user_id", "message", date_col]
    values = [encoded_user_id, message, datetime.now().isoformat(sep=" ", timespec="seconds")]

    if has_is_read:
        columns.append("is_read")
        values.append(0)
    if has_role:
        columns.append("role")
        values.append(role or "")

    placeholders = ", ".join(["?"] * len(columns))
    cur.execute(f"INSERT INTO notifications ({', '.join(columns)}) VALUES ({placeholders})", values)
    conn.commit()
    conn.close()


# Convenience aliases for notifier calls used elsewhere
add_notification = create_notification


def get_notifications(user_id=None, role=None):
    conn = connect()
    cur = conn.cursor()
    date_col, has_is_read, has_role = _notification_schema(cur)
    encoded_user_id = _encode_user_id(user_id, role, has_role) if user_id is not None else None
    read_col = "is_read" if has_is_read else "0 as is_read"
    role_col = "role" if has_role else "'' as role"
    select_cols = f"id, user_id, message, {date_col} as created_at, {read_col}, {role_col}"

    if user_id is not None and has_role and role is not None:
        cur.execute(
            f"SELECT {select_cols} FROM notifications WHERE user_id=? AND role=? ORDER BY {date_col} DESC",
            (user_id, role),
        )
    elif user_id is not None:
        cur.execute(f"SELECT {select_cols} FROM notifications WHERE user_id=? ORDER BY {date_col} DESC", (encoded_user_id,))
    else:
        cur.execute(f"SELECT {select_cols} FROM notifications ORDER BY {date_col} DESC")

    rows = cur.fetchall()
    conn.close()

    return [
        {"id": r[0], "user_id": r[1], "message": r[2], "created_at": r[3], "is_read": bool(r[4]), "role": r[5]}
        for r in rows
    ]


def get_notifications_for_user(user_id, role=None):
    return get_notifications(user_id, role)


def mark_notification_read(notification_id):
    conn = connect()
    cur = conn.cursor()
    date_col, has_is_read, _ = _notification_schema(cur)
    try:
        if has_is_read:
            cur.execute("UPDATE notifications SET is_read=1 WHERE id=?", (notification_id,))
        else:
            # Older schema without is_read: remove the row instead.
            cur.execute("DELETE FROM notifications WHERE id=?", (notification_id,))
        conn.commit()
    finally:
        conn.close()


def clear_notifications_for_user(user_id, role=None):
    conn = connect()
    cur = conn.cursor()
    try:
        date_col, has_is_read, has_role = _notification_schema(cur)
        encoded = _encode_user_id(user_id, role, has_role)
        cur.execute("DELETE FROM notifications WHERE user_id=?", (encoded,))
        conn.commit()
    finally:
        conn.close()


def delete_notification(notification_id):
    conn = connect()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM notifications WHERE id=?", (notification_id,))
        conn.commit()
    finally:
        conn.close()


def notify_all_admins(message):
    """
    Add a notification for every admin user. Falls back to user_id=1 if no admins are found.
    """
    conn = connect()
    cur = conn.cursor()
    cur.execute("SELECT admin_id FROM admin")
    admin_ids = [row[0] for row in cur.fetchall()]
    conn.close()
    if not admin_ids:
        return
    for admin_id in admin_ids:
        try:
            create_notification(admin_id, message, role="admin")
        except Exception:
            continue
