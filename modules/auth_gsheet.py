import gspread
import streamlit as st
from oauth2client.service_account import ServiceAccountCredentials


def get_sheet():
    """
    เปิด Google Sheet: UserManagement (ไฟล์และแท็บชื่อเดียวกัน)
    """
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp_service_account"], scope)
    client = gspread.authorize(creds)
    sheet = client.open("UserManagement").worksheet("UserManagement")
    return sheet


def get_all_users():
    """ดึงผู้ใช้ทั้งหมด"""
    sheet = get_sheet()
    return sheet.get_all_records()


def check_login(username: str, password: str):
    """ตรวจสอบ username + password"""
    users = get_all_users()
    for u in users:
        if u["Username"] == username and u["Password"] == password:
            return u
    return None


def add_user(username: str, password: str, role: str):
    """เพิ่มผู้ใช้ใหม่"""
    sheet = get_sheet()
    sheet.append_row([username, password, role])
    return True


def delete_user(username: str):
    """ลบผู้ใช้ตาม Username"""
    sheet = get_sheet()
    records = sheet.get_all_records()
    for i, u in enumerate(records, start=2):  # row 1 = header
        if u["Username"] == username:
            sheet.delete_rows(i)
            return True
    return False


def update_user(username: str, new_password: str, new_role: str):
    """อัปเดตรหัสผ่านและ role ของผู้ใช้"""
    sheet = get_sheet()
    records = sheet.get_all_records()
    for i, u in enumerate(records, start=2):
        if u["Username"] == username:
            sheet.update(f"B{i}", new_password)  # คอลัมน์ B = Password
            sheet.update(f"C{i}", new_role)     # คอลัมน์ C = Role
            return True
    return False
