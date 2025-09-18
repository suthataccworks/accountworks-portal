import gspread
import streamlit as st
from oauth2client.service_account import ServiceAccountCredentials
import datetime

# Spreadsheet ID
LEAVE_FILE_ID = "1P1dt1syrcOEW_AyM3-i-fCMzUeMtCMUxLUdOUfK5LaQ"  # 👉 ใส่ ID จริง

# ---------------- AUTH ----------------
def get_client():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(
        st.secrets["gcp_service_account"], scope
    )
    return gspread.authorize(creds)

def get_leave_sheet():
    client = get_client()
    return client.open_by_key(LEAVE_FILE_ID).worksheet("LeaveRequests")

# ---------------- CACHE READ ----------------
@st.cache_data(ttl=60)  # cache 60 วินาที
def load_all_leaves():
    sheet = get_leave_sheet()
    return sheet.get_all_records()

# ---------------- SUBMIT ----------------
def submit_leave(username, leave_type, start_date, end_date, reason):
    sheet = get_leave_sheet()
    days = (end_date - start_date).days + 1
    sheet.append_row([
        username,
        leave_type,
        str(start_date),
        str(end_date),
        days,
        reason,
        "Pending"
    ])
    load_all_leaves.clear()  # clear cache
    return True, f"✅ ส่งคำขอลา {days} วันสำเร็จ"

# ---------------- READ ----------------
def get_user_leaves(username, role="user"):
    all_leaves = load_all_leaves()
    if role.lower() == "admin":
        return all_leaves
    else:
        return [row for row in all_leaves if row["Username"] == username]

# ---------------- UPDATE ----------------
def update_leave_request(username, start_date, new_type, new_start, new_end, new_reason):
    sheet = get_leave_sheet()
    records = sheet.get_all_records()
    for i, row in enumerate(records, start=2):  # row1 header
        if (
            row["Username"] == username
            and row["StartDate"] == str(start_date)
            and row["Status"] == "Pending"
        ):
            days = (new_end - new_start).days + 1
            sheet.update(f"B{i}", new_type)        # LeaveType
            sheet.update(f"C{i}", str(new_start))  # StartDate
            sheet.update(f"D{i}", str(new_end))    # EndDate
            sheet.update(f"E{i}", days)            # Days
            sheet.update(f"F{i}", new_reason)      # Reason
            load_all_leaves.clear()
            return True, "✅ แก้ไขคำขอลาสำเร็จ"
    return False, "❌ ไม่พบคำขอที่แก้ไขได้"

# ---------------- CANCEL ----------------
def cancel_leave_request(username, start_date):
    sheet = get_leave_sheet()
    records = sheet.get_all_records()
    for i, row in enumerate(records, start=2):
        if (
            row["Username"] == username
            and row["StartDate"] == str(start_date)
            and row["Status"] == "Pending"
        ):
            sheet.update(f"G{i}", "Cancelled")  # col G = Status
            load_all_leaves.clear()
            return True, "🛑 ยกเลิกคำขอลาสำเร็จ"
    return False, "❌ ไม่พบคำขอที่ยกเลิกได้"

# ---------------- APPROVE / REJECT ----------------
def update_leave_status(username, start_date, status):
    sheet = get_leave_sheet()
    records = sheet.get_all_records()
    for i, row in enumerate(records, start=2):
        if (
            row["Username"] == username
            and row["StartDate"] == str(start_date)
            and row["Status"] == "Pending"
        ):
            sheet.update(f"G{i}", status)  # col G = Status
            load_all_leaves.clear()
            return True, f"📌 อัปเดตสถานะเป็น {status}"
    return False, "❌ ไม่พบคำขอ"
