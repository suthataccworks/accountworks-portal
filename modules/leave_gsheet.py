import gspread
import streamlit as st
from oauth2client.service_account import ServiceAccountCredentials
from gspread.exceptions import WorksheetNotFound, SpreadsheetNotFound

# ใช้ค่า ID จาก secrets
LEAVE_FILE_ID = st.secrets.get("1P1dt1syrcOEW_AyM3-i-fCMzUeMtCMUxLUdOUfK5LaQ", "").strip()

def _require_file_id():
    if not LEAVE_FILE_ID:
        raise ValueError("ไม่พบค่า leave_file_id ใน st.secrets — โปรดตั้งค่าให้ถูกต้อง")

def get_client():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp_service_account"], scope)
    return gspread.authorize(creds)

def get_leave_sheet():
    _require_file_id()
    client = get_client()
    try:
        sh = client.open_by_key(LEAVE_FILE_ID)
    except SpreadsheetNotFound:
        raise SpreadsheetNotFound("Spreadsheet ไม่พบ หรือ service account ไม่มีสิทธิ์ Editor")

    # ให้ชื่อแท็บที่ใช้คือ LeaveRequests
    try:
        ws = sh.worksheet("LeaveRequests")
    except WorksheetNotFound:
        # สร้างแท็บ + ตั้งหัวตารางให้เลย
        ws = sh.add_worksheet(title="LeaveRequests", rows=1000, cols=6)
        ws.update("A1:F1", [["Username", "LeaveType", "StartDate", "EndDate", "Reason", "Status"]])
    return ws

# --- Cache read 20 วินาที ลด quota ---
@st.cache_data(ttl=20)
def get_all_leaves():
    ws = get_leave_sheet()
    records = ws.get_all_records()
    # แทรก row_index สำหรับอ้างอิงแถวจริง
    for i, row in enumerate(records, start=2):
        row["row_index"] = i
        # ทำให้คีย์ที่คาดว่าจะมีแน่ๆปลอดภัย
        row.setdefault("Username", "")
        row.setdefault("LeaveType", "")
        row.setdefault("StartDate", "")
        row.setdefault("EndDate", "")
        row.setdefault("Reason", "")
        row.setdefault("Status", "")
    return records

def _clear_cache():
    try:
        get_all_leaves.clear()
    except Exception:
        pass

def submit_leave(username, leave_type, start_date, end_date, reason):
    ws = get_leave_sheet()
    ws.append_row([username, leave_type, str(start_date), str(end_date), str(reason or ""), "Pending"])
    _clear_cache()
    days = (end_date - start_date).days + 1
    return True, f"✅ ส่งคำขอลาเรียบร้อย ({days} วัน)"

def update_leave_request(row_index, new_type, new_start, new_end, new_reason):
    ws = get_leave_sheet()
    # Batch update เพื่อลดจำนวน API calls
    ws.update_cell(row_index, 2, new_type)
    ws.update_cell(row_index, 3, str(new_start))
    ws.update_cell(row_index, 4, str(new_end))
    ws.update_cell(row_index, 5, str(new_reason or ""))
    _clear_cache()
    return True, "💾 อัปเดตคำขอลาเรียบร้อย"

def cancel_leave_request(row_index):
    ws = get_leave_sheet()
    ws.delete_rows(row_index)
    _clear_cache()
    return True, "🗑 ยกเลิกคำขอลาเรียบร้อยแล้ว"

def update_leave_status(row_index, status):
    ws = get_leave_sheet()
    ws.update_cell(row_index, 6, status)
    _clear_cache()
    return True, f"📌 อัปเดตสถานะเป็น {status}"
