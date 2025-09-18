import streamlit as st
from supabase import create_client

# อ่านค่าจาก Streamlit Secrets (แทน .env)
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("❌ Missing SUPABASE_URL or SUPABASE_KEY in Streamlit secrets")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def get_all_users():
    result = supabase.table("users").select("id, username, role").execute()
    return result.data
