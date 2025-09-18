from supabase import create_client, Client
import os
import bcrypt

# ดึงค่าจาก Streamlit Secrets
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def init_db():
    # Supabase มีตารางอยู่แล้ว ไม่ต้องทำอะไร
    pass

def add_user(username, password, role="User"):
    """เพิ่มผู้ใช้ใหม่ (เข้ารหัสด้วย bcrypt)"""
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    supabase.table("users").insert({"username": username, "password": hashed, "role": role}).execute()

def get_user(username, password):
    """ตรวจสอบ user โดยเปรียบเทียบ bcrypt"""
    result = supabase.table("users").select("*").eq("username", username).execute()
    if result.data:
        user = result.data[0]
        if bcrypt.checkpw(password.encode("utf-8"), user["password"].encode("utf-8")):
            return (user["id"], user["username"], user["password"], user["role"])
    return None

def get_all_users():
    """คืนค่า (id, username, role) ของผู้ใช้ทั้งหมด"""
    result = supabase.table("users").select("id, username, role").execute()
    return [(u["id"], u["username"], u["role"]) for u in result.data]

def delete_user(username):
    supabase.table("users").delete().eq("username", username).execute()

def update_user(username, new_password, new_role):
    """อัปเดต password + role"""
    hashed = bcrypt.hashpw(new_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    supabase.table("users").update({"password": hashed, "role": new_role}).eq("username", username).execute()
