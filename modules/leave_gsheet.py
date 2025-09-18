import gspread
import streamlit as st
from oauth2client.service_account import ServiceAccountCredentials
import datetime

# Spreadsheet ID (LeaveManagement)
LEAVE_FILE_ID = "1P1dt1syrcOEW_AyM3-i-fCMzUeMtCMUxLUdOUfK5LaQ"

def get_client():
    scope = ["https://spreadsheets.google.com/feeds","https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp_service_account"], scope)
    return gspread.authorize(creds)

# ----------- Sheets -----------
def get_leave_sheet():
    client = get_client()
    return client.open_by_key(LEAVE_FILE_ID).worksheet("LeaveRequests")  # ✅ เก็บคำขอลา

def get_balance_sheet():
    client = get_client()
    return client.open_by_key(LEAVE_FILE_ID).worksheet("balance")  # ✅ วันลาคงเหลือ

# ----------- Submit Leave -----------
def submit_leave(username, leave_type, start_date, end_date, reason):
    days = (datetime.date.fromisoformat(str(end_date)) - datetime.date.fromisoformat(str(start_date))).days + 1

    # ตรวจสอบวันลาคงเหลือ
    if not check_leave_balance(username, leave_type, days):
        return False, f"❌ วันลาคงเหลือไม่พอ ({leave_type})"

    # บันทึกคำขอลา
    sheet = get_leave_sheet()
    sheet.append_row([username, leave_type, str(start_date), str(end_date), reason, "Pending"])

    # หักวันลาออกจาก balance (เฉพาะตอนที่อนุมัติจะดีกว่า แต่ตอนนี้หักเลย)
    deduct_leave_balance(username, leave_type, days)

    return True, f"✅ ส่งคำขอลาเรียบร้อย ({days} วัน)"

# ----------- Check Balance -----------
def check_leave_balance(username, leave_type, days):
    sheet = get_balance_sheet()
    records = sheet.get_all_records()
    for i, row in enumerate(records, start=2):
        if row["Username"] == username:
            if int(row.get(leave_type, 0)) >= days:
                return True
            return False
    return False

# ----------- Deduct Balance -----------
def deduct_leave_balance(username, leave_type, days):
    sheet = get_balance_sheet()
    records = sheet.get_all_records()
    for i, row in enumerate(records, start=2):
        if row["Username"] == username:
            new_value = int(row.get(leave_type, 0)) - days
            col_index = list(row.keys()).index(leave_type) + 1
            sheet.update_cell(i, col_index, new_value)
            break

# ----------- Get All Leaves -----------
def get_all_leaves():
    sheet = get_leave_sheet()
    return sheet.get_all_records()

# ----------- Update Status (อนุมัติ/ไม่อนุมัติ) -----------
def update_leave_status(username, start_date, status):
    sheet = get_leave_sheet()
    records = sheet.get_all_records()
    for i, row in enumerate(records, start=2):
        if row["Username"] == username and row["StartDate"] == str(start_date):
            sheet.update_cell(i, 6, status)  # คอลัมน์ 6 = Status
            return True, f"อัปเดตสถานะเป็น {status}"
    return False, "❌ ไม่พบคำขอนี้"

# ----------- Update Leave Request (User แก้ไข) -----------
def update_leave_request(username, old_start_date, leave_type, new_start, new_end, reason):
    sheet = get_leave_sheet()
    records = sheet.get_all_records()
    for i, row in enumerate(records, start=2):
        if row["Username"] == username and row["StartDate"] == str(old_start_date):
            sheet.update(f"B{i}", leave_type)     # LeaveType
            sheet.update(f"C{i}", str(new_start)) # StartDate
            sheet.update(f"D{i}", str(new_end))   # EndDate
            sheet.update(f"E{i}", reason)         # Reason
            return True, "✅ อัปเดตคำขอลาเรียบร้อย"
    return False, "❌ ไม่พบคำขอลา"

# ----------- Cancel Leave Request -----------
def cancel_leave_request(username, start_date):
    sheet = get_leave_sheet()
    records = sheet.get_all_records()
    for i, row in enumerate(records, start=2):
        if row["Username"] == username and row["StartDate"] == str(start_date) and row["Status"] == "Pending":
            sheet.delete_rows(i)
            return True, "🗑 ยกเลิกคำขอลาเรียบร้อย"
    return False, "❌ ไม่สามารถยกเลิกคำขอได้"
