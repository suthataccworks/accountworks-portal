import gspread
import streamlit as st
from oauth2client.service_account import ServiceAccountCredentials
import datetime

LEAVE_FILE_ID = "1P1dt1syrcOEW_AyM3-i-fCMzUeMtCMUxLUdOUfK5LaQ"

def get_client():
    scope = ["https://spreadsheets.google.com/feeds","https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(
        st.secrets["gcp_service_account"], scope
    )
    return gspread.authorize(creds)

def get_leave_sheet():
    client = get_client()
    return client.open_by_key(LEAVE_FILE_ID).worksheet("LeaveManagement")  # ✅ ใช้แท็บเดียว

# ----------- Submit Leave -----------
def submit_leave(username, leave_type, start_date, end_date, reason):
    days = (datetime.datetime.fromisoformat(str(end_date)) - datetime.datetime.fromisoformat(str(start_date))).days + 1

    # ตรวจสอบวันลาคงเหลือก่อน
    if not check_leave_balance(username, leave_type, days):
        return False, f"❌ วันลาคงเหลือไม่พอ ({leave_type})"

    # เพิ่มคำขอลาใน sheet (เพิ่มต่อท้าย)
    sheet = get_leave_sheet()
    sheet.append_row([username, leave_type, str(start_date), str(end_date), reason, "Pending"])

    # หักวันลาออกจาก Balance
    deduct_leave_balance(username, leave_type, days)

    return True, f"✅ ส่งคำขอลาเรียบร้อย ({days} วัน)"

# ----------- Check Leave Balance -----------
def check_leave_balance(username, leave_type, days):
    sheet = get_leave_sheet()
    records = sheet.get_all_records()
    for i, row in enumerate(records, start=2):
        if row["Username"] == username:
            if int(row[leave_type]) >= days:
                return True
            else:
                return False
    return False

# ----------- Deduct Leave Balance -----------
def deduct_leave_balance(username, leave_type, days):
    sheet = get_leave_sheet()
    records = sheet.get_all_records()
    for i, row in enumerate(records, start=2):
        if row["Username"] == username:
            new_value = int(row[leave_type]) - days
            col_index = list(row.keys()).index(leave_type) + 1
            sheet.update_cell(i, col_index, new_value)
            break
