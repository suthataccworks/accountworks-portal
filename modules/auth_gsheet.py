import gspread
import streamlit as st
from oauth2client.service_account import ServiceAccountCredentials

# 📌 ใส่ Spreadsheet ID ของ UserManagement (ดึงจาก URL)
# เช่น https://docs.google.com/spreadsheets/d/XXXXXX/edit#gid=0 → เอา XXXXXX
USER_FILE_ID = "1W5pjti9_Lg1VoSVSge6jJnDD0rECP3kQwvK6C7WHQT8"

# 📌 ใส่ชื่อแท็บที่เก็บ User
USER_SHEET_NAME = "UserManagement"


def get_sheet():
    """
    เปิด Google Sheet ด้วย Spreadsheet ID และชื่อแท็บ
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
    return client.open_by_key(USER_FILE_ID).worksheet(USER_SHEET_NAME)


# ----------- ดึงผู้ใช้ทั้งหมด -----------
def get_all_users(mask_password: bool = False):
    try:
        sheet = get_sheet()
        users = sheet.get_all_records()
        if mask_password:
            for u in users:
                u["Password"] = "******"
        return users
    except Exception as e:
        st.error(f"⚠️ Error ดึงข้อมูลผู้ใช้: {e}")
        return []


# ----------- ตรวจสอบการ Login -----------
def check_login(username: str, password: str):
    users = get_all_users()
    for u in users:
        if u["Username"] == username and u["Password"] == password:
            return u
    return None


# ----------- เพิ่มผู้ใช้ใหม่ -----------
def add_user(username: str, password: str, role: str):
    users = get_all_users()
    for u in users:
        if u["Username"].lower() == username.lower():
            return False, "❌ Username นี้มีอยู่แล้ว"
    try:
        sheet = get_sheet()
        sheet.append_row([username, password, role])
        return True, f"✅ เพิ่มผู้ใช้ {username} เรียบร้อยแล้ว"
    except Exception as e:
        return False, f"⚠️ Error: {e}"


# ----------- ลบผู้ใช้ -----------
def delete_user(username: str):
    try:
        sheet = get_sheet()
        records = sheet.get_all_records()
        for i, u in enumerate(records, start=2):  # row 1 = header
            if u["Username"] == username:
                sheet.delete_rows(i)
                return True, f"🗑 ลบผู้ใช้ {username} เรียบร้อยแล้ว"
        return False, "❌ ไม่พบ Username ที่ต้องการลบ"
    except Exception as e:
        return False, f"⚠️ Error: {e}"


# ----------- อัปเดตผู้ใช้ -----------
def update_user(username: str, new_password: str, new_role: str):
    try:
        sheet = get_sheet()
        records = sheet.get_all_records()
        for i, u in enumerate(records, start=2):
            if u["Username"] == username:
                if new_password:
                    sheet.update(f"B{i}", new_password)  # คอลัมน์ B = Password
                if new_role:
                    sheet.update(f"C{i}", new_role)  # คอลัมน์ C = Role
                return True, f"✅ อัปเดต {username} เรียบร้อยแล้ว"
        return False, "❌ ไม่พบ Username ที่ต้องการอัปเดต"
    except Exception as e:
        return False, f"⚠️ Error: {e}"


# ----------- ค้นหาผู้ใช้ -----------
def search_users(keyword: str = "", role: str = None):
    users = get_all_users(mask_password=True)
    keyword = keyword.lower().strip()

    filtered = []
    for u in users:
        if keyword in u["Username"].lower() and (role is None or u["Role"] == role):
            filtered.append(u)

    return filtered
