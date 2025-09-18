import gspread
import streamlit as st
from google.oauth2.service_account import Credentials

def get_sheet():
    """
    เปิด Google Sheet: UserManagement และแท็บ users
    ต้องมี header แถวแรก = Username | Password | Role
    """
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"], scopes=scope
    )
    client = gspread.authorize(creds)
    sheet = client.open("UserManagement").worksheet("users")  # 👈 Tab ต้องชื่อ users
    return sheet

def get_all_users():
    """
    คืนค่าผู้ใช้ทั้งหมดใน Google Sheet เป็น list ของ dict
    ตัวอย่าง: [{'Username': 'admin', 'Password': '1234', 'Role': 'Admin'}, ...]
    """
    sheet = get_sheet()
    return sheet.get_all_records()

def check_login(username: str, password: str):
    """
    ตรวจสอบ username + password กับ Google Sheet
    ถ้าพบ → return dict ของ user
    ถ้าไม่พบ → return None
    """
    users = get_all_users()
    for u in users:
        if u["Username"] == username and u["Password"] == password:
            return u
    return None

def add_user(username: str, password: str, role: str):
    """
    เพิ่มผู้ใช้ใหม่เข้า Google Sheet
    """
    sheet = get_sheet()
    sheet.append_row([username, password, role])
    return True

def delete_user(username: str):
    """
    ลบผู้ใช้ตาม Username จาก Google Sheet
    """
    sheet = get_sheet()
    records = sheet.get_all_records()
    for i, u in enumerate(records, start=2):  # เริ่มที่ row 2 (row 1 = header)
        if u["Username"] == username:
            sheet.delete_rows(i)
            return True
    return False
