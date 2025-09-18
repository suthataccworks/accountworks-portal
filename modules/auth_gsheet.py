import gspread
import streamlit as st
from oauth2client.service_account import ServiceAccountCredentials

def get_sheet():
    """
    เปิด Google Sheet ชื่อ UserManagement และ tab users
    """
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(
        st.secrets["gcp_service_account"], scope
    )
    client = gspread.authorize(creds)
    sheet = client.open("UserManagement").worksheet("users")  # 👈 ต้องมี tab ชื่อ users
    return sheet

def get_all_users():
    """
    คืนค่าผู้ใช้ทั้งหมดใน Google Sheet เป็น list ของ dict
    """
    sheet = get_sheet()
    return sheet.get_all_records()

def check_login(username, password):
    """
    ตรวจสอบ username + password กับ Google Sheet
    """
    users = get_all_users()
    for u in users:
        if u["Username"] == username and u["Password"] == password:
            return u  # ตัวอย่าง: {'Username': 'admin', 'Password': '1234', 'Role': 'Admin'}
    return None
