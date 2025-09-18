import httpx
import streamlit as st
from supabase import create_client

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def get_all_users():
    result = supabase.table("users").select("id, username, role").execute()
    return result.data

def test_connection():
    """
    ใช้ทดสอบว่าเชื่อมต่อ Supabase ได้จริงหรือไม่
    """
    url = f"{SUPABASE_URL}/rest/v1/"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}"
    }
    try:
        r = httpx.get(url, headers=headers, timeout=10.0)
        print("Status:", r.status_code)
        print("Response:", r.text[:200])
    except Exception as e:
        print("❌ Connect error:", e)
