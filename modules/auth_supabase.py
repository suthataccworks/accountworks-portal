# modules/auth_supabase.py
import psycopg2
import os
import bcrypt

# ดึงค่าจาก Environment Variables (ไปตั้งค่าใน Streamlit Cloud หรือ .env)
DB_URL = os.getenv("SUPABASE_DB_URL")

def get_connection():
    return psycopg2.connect(DB_URL)

def init_db():
    # Supabase เราสร้างตารางแล้ว เลยไม่ต้องทำอะไร
    pass

# ---------------- USER FUNCTIONS ----------------

def add_user(username, password, role="User"):
    """เพิ่มผู้ใช้ใหม่ โดยเข้ารหัส password ด้วย bcrypt"""
    conn = get_connection()
    cur = conn.cursor()
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    cur.execute("INSERT INTO users (username, password, role) VALUES (%s, %s, %s)",
                (username, hashed, role))
    conn.commit()
    conn.close()

def get_user(username, password):
    """ตรวจสอบ user โดยเปรียบเทียบ bcrypt hash"""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, username, password, role FROM users WHERE username=%s", (username,))
    user = cur.fetchone()
    conn.close()

    if user and bcrypt.checkpw(password.encode("utf-8"), user[2].encode("utf-8")):
        return user
    return None

def get_all_users():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, username, role FROM users")
    users = cur.fetchall()
    conn.close()
    return users

def delete_user(username):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM users WHERE username=%s", (username,))
    conn.commit()
    conn.close()

def update_user(username, new_password, new_role):
    """อัปเดตรหัสผ่าน + role"""
    conn = get_connection()
    cur = conn.cursor()
    hashed = bcrypt.hashpw(new_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    cur.execute("UPDATE users SET password=%s, role=%s WHERE username=%s",
                (hashed, new_role, username))
    conn.commit()
    conn.close()
