import sqlite3
import bcrypt

# แก้ตรงนี้ 👉 ให้ใช้ users.db
DB_FILE = "users.db"

# ================= Database Init =================
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password BLOB NOT NULL,
            role TEXT NOT NULL DEFAULT 'User'
        )
    """)
    conn.commit()

    # migrate: ถ้ายังไม่มี column role → เพิ่มให้
    try:
        c.execute("ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'User'")
        conn.commit()
    except Exception:
        pass  # column role มีแล้ว

    conn.close()

# ================= User Management =================
def add_user(username, password, role="User"):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    c.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", (username, hashed, role))
    conn.commit()
    conn.close()

def get_user(username, password):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id, username, password, role FROM users WHERE username=?", (username,))
    row = c.fetchone()
    conn.close()
    if row and bcrypt.checkpw(password.encode("utf-8"), row[2]):
        return row  # (id, username, hashed_password, role)
    return None

def get_all_users():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    try:
        c.execute("SELECT id, username, role FROM users")
    except Exception:
        # fallback กรณี table เก่ายังไม่มี role
        c.execute("SELECT id, username FROM users")
        rows = [(r[0], r[1], "User") for r in c.fetchall()]
        conn.close()
        return rows
    rows = c.fetchall()
    conn.close()
    return rows

def delete_user(username):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM users WHERE username=?", (username,))
    conn.commit()
    conn.close()

def update_user(username, new_password=None, new_role=None):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    if new_password:
        hashed = bcrypt.hashpw(new_password.encode("utf-8"), bcrypt.gensalt())
        if new_role:
            c.execute("UPDATE users SET password=?, role=? WHERE username=?", (hashed, new_role, username))
        else:
            c.execute("UPDATE users SET password=? WHERE username=?", (hashed, username))
    else:
        if new_role:
            c.execute("UPDATE users SET role=? WHERE username=?", (new_role, username))
    conn.commit()
    conn.close()
