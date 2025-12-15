# Restore db_scan logic into app/services/db_scan.py
import sqlite3

conn = sqlite3.connect("fureverhome.db")
cur = conn.cursor()

def show_table(name):
    print(f"\n===== TABLE: {name} =====")
    try:
        cur.execute(f"PRAGMA table_info({name});")
        print("STRUCTURE:", cur.fetchall())

        cur.execute(f"SELECT * FROM {name} LIMIT 10;")
        rows = cur.fetchall()
        print("FIRST ROWS:", rows if rows else "(empty)")
    except Exception as e:
        print("ERROR:", e)


tables = ["users", "pets", "adoption_requests", "notifications"]

for t in tables:
    show_table(t)

conn.close()
