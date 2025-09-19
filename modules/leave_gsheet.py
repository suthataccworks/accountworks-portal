# modules/leave_gsheet.py
import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from typing import List, Dict, Tuple
import datetime

# ====== CONFIG via st.secrets ======
# st.secrets["gcp_service_account"] = {...}
# st.secrets["LEAVES_SHEET_ID"] = "<spreadsheet-id ของตาราง Leaves>"
# st.secrets["LEAVES_SHEET_NAME"] = "Leaves"  # ถ้าไม่ตั้ง จะใช้ worksheet แรก

LEAVES_HEADER = [
    "Timestamp", "Username", "LeaveType", "StartDate", "EndDate", "Reason", "Status"
]

def _client():
    scope = ["https://www.googleapis.com/auth/spreadsheets"]
    creds_dict = st.secrets["gcp_service_account"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    return gspread.authorize(creds)

def _ws_leaves():
    gc = _client()
    sid = st.secrets["LEAVES_SHEET_ID"]
    sh = gc.open_by_key(sid)
    wname = st.secrets.get("LEAVES_SHEET_NAME", None)
    ws = sh.worksheet(wname) if wname else sh.get_worksheet(0)
    _ensure_leaves_header(ws)
    return ws

def _ensure_leaves_header(ws):
    current = ws.row_values(1)
    if not current:
        ws.append_row(LEAVES_HEADER, value_input_option="RAW")
    else:
        # เติมหัวที่ขาด
        need_update = False
        for i, h in enumerate(LEAVES_HEADER, start=1):
            if (len(current) < i) or (current[i-1].strip() != h):
                need_update = True
                break
        if need_update:
            ws.update("1:1", [LEAVES_HEADER])

def _rows_to_dicts(rows: List[List[str]]) -> List[Dict]:
    if not rows: return []
    header = rows[0]
    out = []
    for r in rows[1:]:
        d = {header[i]: (r[i] if i < len(r) else "") for i in range(len(header))}
        out.append(d)
    return out

def _dicts_with_row_index(ws) -> List[Dict]:
    rows = ws.get_all_values()
    dicts = _rows_to_dicts(rows)
    for idx, d in enumerate(dicts, start=2):
        d["row_index"] = idx
    return dicts

def _to_iso(d: datetime.date | str) -> str:
    if isinstance(d, datetime.date):
        return d.isoformat()
    s = str(d).strip()
    # พยายาม parse กรณีเป็นสตริง
    try:
        return datetime.date.fromisoformat(s).isoformat()
    except Exception:
        return s  # ปล่อยเป็นเดิม ถ้า parse ไม่ได้

# ====== PUBLIC APIS ======
def submit_leave(username: str, leave_type: str, start_date: datetime.date, end_date: datetime.date, reason: str) -> Tuple[bool, str]:
    if not username:
        return False, "ไม่พบ Username"
    if not leave_type:
        return False, "กรุณาเลือกประเภทการลา"

    ws = _ws_leaves()
    now = datetime.datetime.now().isoformat(timespec="seconds")
    row = [
        now,
        username,
        str(leave_type).strip(),
        _to_iso(start_date),
        _to_iso(end_date),
        str(reason or "").strip(),
        "Pending"
    ]
    ws.append_row(row, value_input_option="RAW")
    return True, "ส่งคำขอลาสำเร็จ ✅"

def get_all_leaves() -> List[Dict]:
    ws = _ws_leaves()
    items = _dicts_with_row_index(ws)
    return items

def update_leave_request(row_index: int, leave_type: str, start_date: datetime.date, end_date: datetime.date, reason: str) -> Tuple[bool, str]:
    if not row_index or row_index < 2:
        return False, "row_index ไม่ถูกต้อง"

    ws = _ws_leaves()
    # อ่านแถวเดิมมาก่อน เพื่อคงค่า Timestamp/Username/Status
    row_vals = ws.row_values(row_index)
    header = ws.row_values(1)
    idx_map = {h: i for i, h in enumerate(header)}  # 0-based

    # เตรียมแถวใหม่ (fill ให้ครบความยาว header)
    new_vals = row_vals[:] + [""] * (len(header) - len(row_vals))
    # อัปเดตเฉพาะฟิลด์ที่อนุญาต
    if "LeaveType" in idx_map: new_vals[idx_map["LeaveType"]] = str(leave_type).strip()
    if "StartDate" in idx_map: new_vals[idx_map["StartDate"]] = _to_iso(start_date)
    if "EndDate"   in idx_map: new_vals[idx_map["EndDate"]]   = _to_iso(end_date)
    if "Reason"    in idx_map: new_vals[idx_map["Reason"]]    = str(reason or "").strip()

    # หากสถานะถูกเปลี่ยนไปแล้ว (เช่น Approved) ไม่ควรให้แก้ผ่านเมธอดนี้ แต่ให้ตรวจที่ UI แล้ว (ทำไว้แล้ว)
    ws.update(f"{row_index}:{row_index}", [new_vals])
    return True, "อัปเดตคำขอลาสำเร็จ 💾"

def cancel_leave_request(row_index: int) -> Tuple[bool, str]:
    if not row_index or row_index < 2:
        return False, "row_index ไม่ถูกต้อง"
    ws = _ws_leaves()
    header = ws.row_values(1)
    idx_map = {h: i for i, h in enumerate(header)}
    row_vals = ws.row_values(row_index)
    new_vals = row_vals[:] + [""] * (len(header) - len(row_vals))
    if "Status" in idx_map: new_vals[idx_map["Status"]] = "Cancelled"
    ws.update(f"{row_index}:{row_index}", [new_vals])
    return True, "ยกเลิกคำขอลาสำเร็จ ❌"

def update_leave_status(row_index: int, new_status: str) -> Tuple[bool, str]:
    if not row_index or row_index < 2:
        return False, "row_index ไม่ถูกต้อง"
    status = str(new_status or "").strip().title()
    if status not in ("Approved","Rejected","Pending","Cancelled"):
        return False, "สถานะไม่ถูกต้อง"
    ws = _ws_leaves()
    header = ws.row_values(1)
    idx_map = {h: i for i, h in enumerate(header)}
    row_vals = ws.row_values(row_index)
    new_vals = row_vals[:] + [""] * (len(header) - len(row_vals))
    if "Status" in idx_map: new_vals[idx_map["Status"]] = status
    ws.update(f"{row_index}:{row_index}", [new_vals])
    return True, f"อัปเดตสถานะเป็น {status} เรียบร้อย ✅"
