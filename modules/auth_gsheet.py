import gspread
import streamlit as st
from oauth2client.service_account import ServiceAccountCredentials


def get_sheet():
    """
    เปิด Google Sheet: UserManagement (ไฟล์และแท็บชื่อเดียวกัน)
    ต้องมี header: Username | Password | Role
    """
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(
        st.secrets["gcp_service_account"], scope
    )
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
    username = username.strip().lower()
    password = password.strip()

    users = get_all_users()
    for u in users:
        if u["Username"].strip().lower() == username and u["Password"].strip() == password:
            return u
    return None


# ----------- เพิ่มผู้ใช้ใหม่ -----------
def add_user(username: str, password: str, role: str):
    username = username.strip()
    password = password.strip()
    role = role.strip()

    users = get_all_users()
    for u in users:
        if u["Username"].strip().lower() == username.lower():
            return False, f"❌ Username '{username}' มีอยู่แล้ว"

    sheet = get_sheet()
    sheet.append_row([username, password, role])
    return True, f"✅ เพิ่มผู้ใช้ {username} เรียบร้อยแล้ว"


# ----------- ลบผู้ใช้ -----------
def delete_user(username: str):
    username = username.strip().lower()

    sheet = get_sheet()
    records = sheet.get_all_records()
    for i, u in enumerate(records, start=2):  # row 1 = header
        if u["Username"].strip().lower() == username:
            sheet.delete_rows(i)
            return True, f"🗑 ลบผู้ใช้ {username} เรียบร้อยแล้ว"
    return False, "❌ ไม่พบ Username ที่ต้องการลบ"


# ----------- อัปเดตผู้ใช้ -----------
def update_user(username: str, new_password: str, new_role: str):
    username = username.strip().lower()

    sheet = get_sheet()
    records = sheet.get_all_records()
    for i, u in enumerate(records, start=2):
        if u["Username"].strip().lower() == username:
            if new_password.strip():
                sheet.update(f"B{i}", new_password.strip())  # คอลัมน์ B = Password
            if new_role.strip():
                sheet.update(f"C{i}", new_role.strip())      # คอลัมน์ C = Role
            return True, f"✅ อัปเดต {username} เรียบร้อยแล้ว"
    return False, "❌ ไม่พบ Username ที่ต้องการอัปเดต"


# ----------- ค้นหาผู้ใช้ -----------
def search_users(keyword: str = "", role: str = None):
    users = get_all_users(mask_password=True)
    keyword = keyword.lower().strip()

    filtered = []
    for u in users:
        if keyword in u["Username"].lower() and (role is None or u["Role"] == role):
            filtered.append(u)

    return filtered
