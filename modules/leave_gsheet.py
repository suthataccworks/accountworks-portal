import gspread
import streamlit as st
from oauth2client.service_account import ServiceAccountCredentials
import datetime

def get_client():
    scope = ["https://spreadsheets.google.com/feeds","https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(
        st.secrets["gcp_service_account"], scope
    )
    return gspread.authorize(creds)

# ----------- Leave Requests Sheet -----------
def get_leave_sheet():
    client = get_client()
    return client.open("LeaveManagement").worksheet("LeaveRequests")  # ✅ เก็บคำขอลา

# ----------- Employee Balance Sheet (ใน LeaveManagement) -----------
def get_balance_sheet():
    client = get_client()
    return client.open("LeaveManagement").worksheet("balance")  # ✅ วันลาคงเหลือ

# ----------- Submit Leave -----------
def submit_leave(username, leave_type, start_date, end_date, reason):
    days = (datetime.datetime.fromisoformat(end_date) - datetime.datetime.fromisoformat(start_date)).days + 1
    
    # ตรวจสอบวันลาคงเหลือก่อน
    if not check_leave_balance(username, leave_type, days):
        return False, f"❌ วันลาคงเหลือไม่พอ ({leave_type})"

    # บันทึกคำขอลา
    leave_sheet = get_leave_sheet()
    leave_sheet.append_row([username, leave_type, start_date, end_date, reason, "Pending"])

    # หักวันลาออกจาก Balance
    deduct_leave_balance(username, leave_type, days)

    return True, f"✅ ส่งคำขอลาเรียบร้อย ({days} วัน)"

# ----------- Check Leave Balance -----------
def check_leave_balance(username, leave_type, days):
    sheet = get_balance_sheet()
    records = sheet.get_all_records()
    for i, row in enumerate(records, start=2):  # start=2 เพราะ row1 = header
        if row["Username"] == username:
            if row[leave_type] >= days:
                return True
            else:
                return False
    return False

# ----------- Deduct Leave Balance -----------
def deduct_leave_balance(username, leave_type, days):
    sheet = get_balance_sheet()
    records = sheet.get_all_records()
    for i, row in enumerate(records, start=2):
        if row["Username"] == username:
            new_value = row[leave_type] - days
            sheet.update_cell(i, list(row.keys()).index(leave_type)+1, new_value)
            break

# ----------- Get All Leaves -----------
def get_all_leaves():
    sheet = get_leave_sheet()
    return sheet.get_all_records()

# ----------- Update Status -----------
def update_leave_status(username, status):
    sheet = get_leave_sheet()
    records = sheet.get_all_records()
    for i, row in enumerate(records, start=2):
        if row["Username"] == username and row["Status"] == "Pending":
            sheet.update_cell(i, 6, status)  # col6 = Status
            break
