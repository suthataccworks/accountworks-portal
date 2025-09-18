# modules/leave_gsheet.py
import os, datetime as dt
from typing import Tuple, List, Dict, Any

try:
    import streamlit as st
except Exception:
    class _Dummy:
        secrets = {}
        def warning(self, *a, **k): pass
    st = _Dummy()  # type: ignore

DATA_DIR = "./_local_data"
os.makedirs(DATA_DIR, exist_ok=True)

SPREADSHEET_KEY = st.secrets.get("SPREADSHEET_KEY")
LEAVE_SHEET_NAME = st.secrets.get("LEAVE_REQUESTS_SHEET_NAME", "LeaveRequests")

def _get_gspread_client():
    try:
        from google.oauth2.service_account import Credentials
        import gspread
        info = st.secrets["gcp_service_account"]
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ]
        creds = Credentials.from_service_account_info(info, scopes=scopes)
        return gspread.authorize(creds)
    except Exception:
        return None

GS = _get_gspread_client()

def _open_ws():
    if GS and SPREADSHEET_KEY:
        sh = GS.open_by_key(SPREADSHEET_KEY)
        try:
            return sh.worksheet(LEAVE_SHEET_NAME)
        except Exception:
            sh.add_worksheet(title=LEAVE_SHEET_NAME, rows=2000, cols=20)
            return sh.worksheet(LEAVE_SHEET_NAME)
    return None

def _csv_path() -> str:
    return os.path.join(DATA_DIR, f"{LEAVE_SHEET_NAME}.csv")

def _ensure_header(ws):
    # if empty sheet, create header
    vals = ws.get_all_values()
    if not vals:
        header = ["Username","LeaveType","StartDate","EndDate","Reason","Status","CreatedAt","UpdatedAt"]
        ws.append_row(header)

def _read_all() -> List[Dict[str, Any]]:
    import pandas as pd
    ws = _open_ws()
    if ws is not None:
        vals = ws.get_all_values()
        if not vals:
            _ensure_header(ws)
            vals = ws.get_all_values()
        header, rows = vals[0], vals[1:]
        data = []
        for i, r in enumerate(rows, start=2):  # row index in sheet
            rec = {header[j]: (r[j] if j < len(r) else "") for j in range(len(header))}
            rec["row_index"] = i
            data.append(rec)
        return data
    # CSV fallback
    p = _csv_path()
    if not os.path.exists(p):
        import pandas as pd
        df = pd.DataFrame(columns=["Username","LeaveType","StartDate","EndDate","Reason","Status","CreatedAt","UpdatedAt"])
        df.to_csv(p, index=False, encoding="utf-8-sig")
    import pandas as pd
    df = pd.read_csv(p).fillna("")
    data = df.to_dict(orient="records")
    # emulate row_index (header is row 1)
    for i, rec in enumerate(data, start=2):
        rec["row_index"] = i
    return data

def _write_all(records: List[Dict[str, Any]]) -> Tuple[bool, str]:
    import pandas as pd
    cols = ["Username","LeaveType","StartDate","EndDate","Reason","Status","CreatedAt","UpdatedAt"]
    df = pd.DataFrame([{k:v for k,v in r.items() if k in cols} for r in records], columns=cols)
    ws = _open_ws()
    if ws is not None:
        try:
            ws.clear()
            ws.update([df.columns.tolist()] + df.fillna("").values.tolist())
            return True, "อัปเดตคำขอลาสำเร็จ"
        except Exception as e:
            return False, f"อัปเดตชีตไม่สำเร็จ: {e}"
    try:
        df.to_csv(_csv_path(), index=False, encoding="utf-8-sig")
        return True, "อัปเดต CSV สำเร็จ"
    except Exception as e:
        return False, f"บันทึก CSV ไม่สำเร็จ: {e}"

# ===== Public APIs used by app.py =====
def submit_leave(username: str, leave_type: str, start_date: dt.date, end_date: dt.date, reason: str) -> Tuple[bool, str]:
    now = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ws = _open_ws()
    if ws is not None:
        _ensure_header(ws)
        try:
            ws.append_row([
                username, leave_type,
                start_date.isoformat(), end_date.isoformat(),
                reason, "Pending", now, now
            ])
            return True, "ส่งคำขอลาเรียบร้อย"
        except Exception as e:
            return False, f"เพิ่มแถวในชีตไม่สำเร็จ: {e}"
    # CSV fallback
    recs = _read_all()
    recs.append({
        "Username": username, "LeaveType": leave_type,
        "StartDate": start_date.isoformat(), "EndDate": end_date.isoformat(),
        "Reason": reason, "Status": "Pending",
        "CreatedAt": now, "UpdatedAt": now
    })
    return _write_all(recs)

def get_all_leaves() -> List[Dict[str, Any]]:
    return _read_all()

def update_leave_request(row_index: int, leave_type: str, start_date: dt.date, end_date: dt.date, reason: str) -> Tuple[bool, str]:
    ws = _open_ws()
    now = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if ws is not None:
        try:
            # col mapping based on header
            header = ws.row_values(1)
            col_map = {name:i+1 for i,name in enumerate(header)}
            ws.update_cell(row_index, col_map["LeaveType"], leave_type)
            ws.update_cell(row_index, col_map["StartDate"], start_date.isoformat())
            ws.update_cell(row_index, col_map["EndDate"], end_date.isoformat())
            ws.update_cell(row_index, col_map["Reason"], reason)
            ws.update_cell(row_index, col_map["UpdatedAt"], now)
            return True, "อัปเดตคำขอเรียบร้อย"
        except Exception as e:
            return False, f"อัปเดตชีตไม่สำเร็จ: {e}"
    # CSV fallback
    recs = _read_all()
    for r in recs:
        if int(r.get("row_index", -1)) == int(row_index):
            r["LeaveType"] = leave_type
            r["StartDate"] = start_date.isoformat()
            r["EndDate"] = end_date.isoformat()
            r["Reason"] = reason
            r["UpdatedAt"] = now
            break
    return _write_all(recs)

def cancel_leave_request(row_index: int) -> Tuple[bool, str]:
    return update_leave_status(row_index, "Cancelled")

def update_leave_status(row_index: int, status: str) -> Tuple[bool, str]:
    ws = _open_ws()
    now = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if ws is not None:
        try:
            header = ws.row_values(1)
            col_map = {name:i+1 for i,name in enumerate(header)}
            ws.update_cell(row_index, col_map["Status"], status)
            ws.update_cell(row_index, col_map["UpdatedAt"], now)
            return True, "อัปเดตสถานะเรียบร้อย"
        except Exception as e:
            return False, f"อัปเดตสถานะไม่สำเร็จ: {e}"
    # CSV fallback
    recs = _read_all()
    for r in recs:
        if int(r.get("row_index", -1)) == int(row_index):
            r["Status"] = status
            r["UpdatedAt"] = now
            break
    return _write_all(recs)
