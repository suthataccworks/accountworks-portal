# modules/auth_supabase.py
import psycopg2
import os

# ดึงค่าจาก Environment Variables (ไปตั้งค่าใน Streamlit Cloud หรือ .env)
DB_URL = os.getenv("SUPABASE_DB_URL")

def get_connection():
    return psycopg2.connect(DB_URL)

def init_db():
    # Supabase เราสร้างตารางแล้ว เลยไม่ต้องทำอะไร
    pass

def get_user(username, password):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, username, password, role FROM users WHERE username=%s AND password=%s",
                (username, password))
    user = cur.fetchone()
    conn.close()
    return user

def get_all_users():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, username, role FROM users")
    users = cur.fetchall()
    conn.close()
    return users

def add_user(username, password, role="User"):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO users (username, password, role) VALUES (%s, %s, %s)",
                (username, password, role))
    conn.commit()
    conn.close()

def delete_user(username):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM users WHERE username=%s", (username,))
    conn.commit()
    conn.close()

def update_user(username, new_password, new_role):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE users SET password=%s, role=%s WHERE username=%s",
                (new_password, new_role, username))
    conn.commit()
    conn.close()
