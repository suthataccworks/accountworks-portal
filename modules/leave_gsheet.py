import gspread
import streamlit as st
from oauth2client.service_account import ServiceAccountCredentials
import datetime

# ใส่ Spreadsheet ID ของ LeaveManagement
LEAVE_FILE_ID = "1P1dt1syrcOEW_AyM3-i-fCMzUeMtCMUxLUdOUfK5LaQ"  # 👈 เปลี่ยนเป็น ID ของไฟล์ LeaveManagement จริง

def get_client():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(
        st.secrets["gcp_service_account"], scope
    )
    return gspread.authorize(creds)

# ----------- Leave Requests Sheet -----------
def get_leave_sheet():
    client = get_client()
    return client.open_by_key(LEAVE_FILE_ID).worksheet("LeaveRequests")

# ----------- Balance Sheet -----------
def get_balance_sheet():
    client = get_client()
    return client.open_by_key(LEAVE_FILE_ID).worksheet("balance")

# ----------- Submit Leave -----------
def submit_leave(username, leave_type, start_date, end_date, reason):
    days = (end_date - start_date).days + 1

    # ตรวจสอบวันลาคงเหลือ
    if not check_leave_balance(username, leave_type, days):
        return False, f"❌ วันลาคงเหลือไม่พอ ({leave_type})"

    # บันทึกคำขอ
    leave_sheet = get_leave_sheet()
    leave_sheet.append_row([
        username,
        leave_type,
        str(start_date),
        str(end_date),
        reason,
        "Pending"
    ])

    # หักวันลา
    deduct_leave_balance(username, leave_type, days)

    return True, f"✅ ส่งคำขอลาเรียบร้อย ({days} วัน)"

# ----------- Check Leave Balance -----------
def check_leave_balance(username, leave_type, days):
    sheet = get_balance_sheet()
    records = sheet.get_all_records()
    for row in records:
        if row["Username"] == username:
            return int(row.get(leave_type, 0)) >= days
    return False

# ----------- Deduct Leave Balance -----------
def deduct_leave_balance(username, leave_type, days):
    sheet = get_balance_sheet()
    records = sheet.get_all_records()
    for i, row in enumerate(records, start=2):
        if row["Username"] == username:
            new_value = int(row.get(leave_type, 0)) - days
            col_index = list(row.keys()).index(leave_type) + 1
            sheet.update_cell(i, col_index, new_value)
            break

# ----------- Get All Leaves (filter by role) -----------
def get_user_leaves(username, role):
    sheet = get_leave_sheet()
    records = sheet.get_all_records()
    if role.lower() == "admin":
        return records
    return [r for r in records if r["Username"] == username]

# ----------- Update Status (Admin Approve/Reject) -----------
def update_leave_status(username, start_date, status):
    sheet = get_leave_sheet()
    records = sheet.get_all_records()
    for i, row in enumerate(records, start=2):
        if row["Username"] == username and row["StartDate"] == str(start_date) and row["Status"] == "Pending":
            sheet.update_cell(i, 6, status)  # col6 = Status
            return True, f"อัปเดตคำขอ {username} → {status}"
    return False, "❌ ไม่พบคำขอ"

# ----------- Update Leave Request (User Edit) -----------
def update_leave_request(username, old_start, new_type, new_start, new_end, new_reason):
    sheet = get_leave_sheet()
    records = sheet.get_all_records()
    for i, row in enumerate(records, start=2):
        if row["Username"] == username and row["StartDate"] == str(old_start) and row["Status"] == "Pending":
            sheet.update(f"B{i}", new_type)        # LeaveType
            sheet.update(f"C{i}", str(new_start))  # StartDate
            sheet.update(f"D{i}", str(new_end))    # EndDate
            sheet.update(f"E{i}", new_reason)      # Reason
            return True, "✅ แก้ไขคำขอเรียบร้อยแล้ว"
    return False, "❌ ไม่สามารถแก้ไขได้"

# ----------- Delete Leave Request -----------
def delete_leave_request(username, start_date):
    sheet = get_leave_sheet()
    records = sheet.get_all_records()
    for i, row in enumerate(records, start=2):
        if row["Username"] == username and row["StartDate"] == str(start_date) and row["Status"] == "Pending":
            sheet.delete_rows(i)
            return True, "🗑 ยกเลิกคำขอเรียบร้อยแล้ว"
    return False, "❌ ไม่สามารถยกเลิกได้"
