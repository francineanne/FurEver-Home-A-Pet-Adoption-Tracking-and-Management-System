import sqlite3

conn = sqlite3.connect("fureverhome.db")
cur = conn.cursor()

print("\n===== ADMIN TABLE STRUCTURE =====")
try:
    cur.execute("PRAGMA table_info(admin);")
    print(cur.fetchall())
except Exception as e:
    print("Error reading admin table:", e)

print("\n===== ADMIN ROWS =====")
try:
    cur.execute("SELECT * FROM admin;")
    print(cur.fetchall())
except Exception as e:
    print("Error selecting admin rows:", e)

conn.close()
