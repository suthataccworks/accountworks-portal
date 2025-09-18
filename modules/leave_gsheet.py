import gspread
import streamlit as st
from oauth2client.service_account import ServiceAccountCredentials
from gspread.exceptions import WorksheetNotFound, SpreadsheetNotFound

# =========================
# CONFIG & HELPERS
# =========================

# ใช้ Spreadsheet ID จาก Secrets (ต้องตั้งค่าใน Streamlit Cloud: leave_file_id = "xxxxxxxx")
LEAVE_FILE_ID = st.secrets.get("leave_file_id", "").strip()

def _require_file_id():
    if not LEAVE_FILE_ID:
        raise ValueError("ไม่พบค่า leave_file_id ใน st.secrets — โปรดตั้งค่า leave_file_id ให้ถูกต้อง")

def get_client():
    """
    Auth ด้วย Service Account จาก st.secrets["gcp_service_account"]
    (ควรใส่ private_key แบบ triple quotes ใน secrets เพื่อลดปัญหา \n)
    """
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(
        st.secrets["gcp_service_account"], scope
    )
    return gspread.authorize(creds)

def get_leave_sheet():
    """
    เปิดไฟล์ด้วย ID -> เปิด/สร้างแท็บ LeaveRequests (A1:F1 เป็น header)
    Column order:
      A: Username
      B: LeaveType
      C: StartDate  (YYYY-MM-DD)
      D: EndDate    (YYYY-MM-DD)
      E: Reason
      F: Status     (Pending/Approved/Rejected/Cancelled)
    """
    _require_file_id()
    client = get_client()
    try:
        sh = client.open_by_key(LEAVE_FILE_ID)
    except SpreadsheetNotFound:
        raise SpreadsheetNotFound("Spreadsheet ไม่พบ หรือ Service Account ไม่มีสิทธิ์ Editor (แชร์สิทธิ์ให้ client_email)")

    try:
        ws = sh.worksheet("LeaveRequests")
    except WorksheetNotFound:
        ws = sh.add_worksheet(title="LeaveRequests", rows=1000, cols=6)
        ws.update("A1:F1", [["Username", "LeaveType", "StartDate", "EndDate", "Reason", "Status"]])
    return ws

# =========================
# PUBLIC API (เรียกใช้จาก app.py)
# =========================

@st.cache_data(ttl=20)  # cache 20 วิ ลด quota
def get_all_leaves():
    """
    อ่านรายการคำขอลาทั้งหมด (list of dicts) + แทรก row_index (แถวจริงในชีต)
    """
    ws = get_leave_sheet()
    records = ws.get_all_records()
    for i, row in enumerate(records, start=2):  # row1 = header
        row["row_index"] = i
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
    """
    เพิ่มคำขอลาใหม่ (สถานะเริ่มต้น = Pending)
    start_date/end_date เป็น date object หรือ string YYYY-MM-DD ก็ได้ (จะบันทึกเป็น str)
    """
    ws = get_leave_sheet()
    ws.append_row([
        str(username or ""),
        str(leave_type or ""),
        str(start_date),
        str(end_date),
        str(reason or ""),
        "Pending",
    ])
    _clear_cache()
    try:
        # คำนวณจำนวนวันแบบคร่าวๆ (ถ้าเป็น string จะไม่ลบกันได้ ก็ข้าม)
        days = (end_date - start_date).days + 1  # type: ignore
        return True, f"✅ ส่งคำขอลาเรียบร้อย ({days} วัน)"
    except Exception:
        return True, "✅ ส่งคำขอลาเรียบร้อย"

def update_leave_request(row_index, new_type, new_start, new_end, new_reason):
    """
    ผู้ใช้แก้ไขคำขอลา (ต้องระบุตำแหน่งแถว row_index จาก get_all_leaves)
    """
    ws = get_leave_sheet()
    # อัปเดตแบบทีละเซลล์ (ง่าย และชัดเจน)
    ws.update_cell(row_index, 2, str(new_type or ""))   # B: LeaveType
    ws.update_cell(row_index, 3, str(new_start))        # C: StartDate
    ws.update_cell(row_index, 4, str(new_end))          # D: EndDate
    ws.update_cell(row_index, 5, str(new_reason or "")) # E: Reason
    _clear_cache()
    return True, "💾 อัปเดตคำขอลาเรียบร้อย"

def cancel_leave_request(row_index):
    """
    ผู้ใช้ยกเลิกคำขอ: ลบทั้งแถวออกไปเลย
    (ถ้าอยากเปลี่ยนเป็นสถานะ Cancelled แทนการลบ: ใช้ update_leave_status(row_index, 'Cancelled'))
    """
    ws = get_leave_sheet()
    ws.delete_rows(row_index)
    _clear_cache()
    return True, "🗑 ยกเลิกคำขอลาเรียบร้อยแล้ว"

def update_leave_status(row_index, status):
    """
    Admin อัปเดตสถานะ (Approved/Rejected/Cancelled)
    """
    ws = get_leave_sheet()
    ws.update_cell(row_index, 6, str(status or ""))  # F: Status
    _clear_cache()
    return True, f"📌 อัปเดตสถานะเป็น {status}"
