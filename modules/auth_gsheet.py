import gspread
import streamlit as st
from oauth2client.service_account import ServiceAccountCredentials
import datetime

LEAVE_FILE_ID = "1P1dt1syrcOEW_AyM3-i-fCMzUeMtCMUxLUdOUfK5LaQ"

def get_client():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp_service_account"], scope)
    return gspread.authorize(creds)

# ---------- Sheets ----------
def get_leave_sheet():
    client = get_client()
    return client.open_by_key(LEAVE_FILE_ID).worksheet("LeaveRequests")

def get_balance_sheet():
    client = get_client()
    return client.open_by_key(LEAVE_FILE_ID).worksheet("balance")

# ---------- Submit Leave ----------
def submit_leave(username, leave_type, start_date, end_date, reason):
    days = (end_date - start_date).days + 1
    if not check_leave_balance(username, leave_type, days):
        return False, f"❌ วันลาคงเหลือไม่พอ ({leave_type})"

    sheet = get_leave_sheet()
    sheet.append_row([username, leave_type, str(start_date), str(end_date), reason, "Pending"])
    deduct_leave_balance(username, leave_type, days)
    return True, f"✅ ส่งคำขอลาเรียบร้อย ({days} วัน)"

# ---------- Check Balance ----------
def check_leave_balance(username, leave_type, days):
    sheet = get_balance_sheet()
    records = sheet.get_all_records()
    for row in records:
        if row["Username"] == username:
            if int(row[leave_type]) >= days:
                return True
    return False

def deduct_leave_balance(username, leave_type, days):
    sheet = get_balance_sheet()
    records = sheet.get_all_records()
    for i, row in enumerate(records, start=2):
        if row["Username"] == username:
            new_value = int(row[leave_type]) - days
            col_index = list(row.keys()).index(leave_type) + 1
            sheet.update_cell(i, col_index, new_value)
            break

# ---------- Get All ----------
def get_all_leaves():
    sheet = get_leave_sheet()
    return sheet.get_all_records()

# ---------- Update Status (Admin) ----------
def update_leave_status(username, start_date, status):
    sheet = get_leave_sheet()
    records = sheet.get_all_records()
    for i, row in enumerate(records, start=2):
        if row["Username"] == username and row["StartDate"] == str(start_date):
            sheet.update_cell(i, 6, status)  # col6 = Status
            break

# ---------- Update Leave Request (User) ----------
def update_leave_request(username, old_start, new_type, new_start, new_end, new_reason):
    sheet = get_leave_sheet()
    records = sheet.get_all_records()
    for i, row in enumerate(records, start=2):
        if row["Username"] == username and row["StartDate"] == str(old_start) and row["Status"] == "Pending":
            sheet.update(f"B{i}", new_type)          # LeaveType
            sheet.update(f"C{i}", str(new_start))    # StartDate
            sheet.update(f"D{i}", str(new_end))      # EndDate
            sheet.update(f"E{i}", new_reason)        # Reason
            return True, "✅ อัปเดตคำขอลาเรียบร้อยแล้ว"
    return False, "❌ ไม่สามารถแก้ไขคำขอที่อนุมัติ/ปฏิเสธแล้ว"

# ---------- Cancel Leave Request (User) ----------
def cancel_leave_request(username, start_date):
    sheet = get_leave_sheet()
    records = sheet.get_all_records()
    for i, row in enumerate(records, start=2):
        if row["Username"] == username and row["StartDate"] == str(start_date) and row["Status"] == "Pending":
            sheet.delete_rows(i)
            return True, "🗑 ยกเลิกคำขอลาเรียบร้อยแล้ว"
    return False, "❌ ไม่สามารถยกเลิกคำขอที่อนุมัติ/ปฏิเสธแล้ว"
