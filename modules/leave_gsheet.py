import gspread
import streamlit as st
from oauth2client.service_account import ServiceAccountCredentials
import datetime

# Spreadsheet ID ของ LeaveManagement
LEAVE_FILE_ID = "1P1dt1syrcOEW_AyM3-i-fCMzUeMtCMUxLUdOUfK5LaQ"

def get_client():
    scope = ["https://spreadsheets.google.com/feeds","https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp_service_account"], scope)
    return gspread.authorize(creds)

def get_leave_sheet():
    client = get_client()
    return client.open_by_key(LEAVE_FILE_ID).worksheet("LeaveRequests")

# เพิ่มคำขอลา
def submit_leave(username, leave_type, start_date, end_date, reason):
    days = (datetime.date.fromisoformat(str(end_date)) - datetime.date.fromisoformat(str(start_date))).days + 1
    sheet = get_leave_sheet()
    sheet.append_row([username, leave_type, str(start_date), str(end_date), reason, "Pending"])
    return True, f"✅ ส่งคำขอลาเรียบร้อย ({days} วัน)"

# ดึงรายการคำขอลาพร้อม row_index
def get_all_leaves():
    sheet = get_leave_sheet()
    records = sheet.get_all_records()
    results = []
    for i, row in enumerate(records, start=2):
        row["row_index"] = i
        results.append(row)
    return results

# อัปเดตสถานะ (Admin)
def update_leave_status(row_index, status):
    sheet = get_leave_sheet()
    sheet.update_cell(row_index, 6, status)
    return True, f"อัปเดตสถานะเป็น {status}"

# ผู้ใช้แก้ไขคำขอลา
def update_leave_request(row_index, new_type, new_start, new_end, new_reason):
    sheet = get_leave_sheet()
    sheet.update_cell(row_index, 2, new_type)      # LeaveType
    sheet.update_cell(row_index, 3, str(new_start)) # StartDate
    sheet.update_cell(row_index, 4, str(new_end))   # EndDate
    sheet.update_cell(row_index, 5, new_reason)     # Reason
    return True, "✅ อัปเดตคำขอลาเรียบร้อยแล้ว"

# ผู้ใช้ยกเลิกคำขอ
def cancel_leave_request(row_index):
    sheet = get_leave_sheet()
    sheet.delete_rows(row_index)
    return True, "❌ ยกเลิกคำขอลาเรียบร้อยแล้ว"
