import gspread
import streamlit as st
from oauth2client.service_account import ServiceAccountCredentials

def get_sheet():
    """
    เปิด Google Sheet: UserManagement (ไฟล์และแท็บชื่อเดียวกัน)
    ต้องมี header: Username | Password | Role
    """
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp_service_account"], scope)
    client = gspread.authorize(creds)
    return client.open("UserManagement").worksheet("UserManagement")

# ----------- ดึงผู้ใช้ทั้งหมด -----------
def get_all_users(mask_password: bool = False):
    sheet = get_sheet()
    users = sheet.get_all_records()
    if mask_password:
        for u in users:
            u["Password"] = "******"
    return users

# ----------- ตรวจสอบการ Login -----------
def check_login(username: str, password: str):
    users = get_all_users()
    for u in users:
        if str(u["Username"]).strip().lower() == str(username).strip().lower() and str(u["Password"]).strip() == str(password).strip():
            return u
    return None

# ----------- เพิ่มผู้ใช้ใหม่ -----------
def add_user(username: str, password: str, role: str):
    users = get_all_users()
    for u in users:
        if u["Username"].lower() == username.lower():
            return False, "❌ Username นี้มีอยู่แล้ว"
    sheet = get_sheet()
    sheet.append_row([username, password, role])
    return True, f"✅ เพิ่มผู้ใช้ {username} เรียบร้อยแล้ว"

# ----------- ลบผู้ใช้ -----------
def delete_user(username: str):
    sheet = get_sheet()
    records = sheet.get_all_records()
    for i, u in enumerate(records, start=2):
        if u["Username"] == username:
            sheet.delete_rows(i)
            return True, f"🗑 ลบผู้ใช้ {username} เรียบร้อยแล้ว"
    return False, "❌ ไม่พบ Username ที่ต้องการลบ"

# ----------- อัปเดตผู้ใช้ -----------
def update_user(username: str, new_password: str, new_role: str):
    sheet = get_sheet()
    records = sheet.get_all_records()
    for i, u in enumerate(records, start=2):
        if u["Username"] == username:
            if new_password:
                sheet.update(f"B{i}", new_password)
            if new_role:
                sheet.update(f"C{i}", new_role)
            return True, f"✅ อัปเดต {username} เรียบร้อยแล้ว"
    return False, "❌ ไม่พบ Username ที่ต้องการอัปเดต"
