# modules/auth_gsheet.py
import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import bcrypt
from typing import List, Dict, Tuple, Optional

# ====== CONFIG via st.secrets ======
# st.secrets["gcp_service_account"] = {... service account JSON ...}
# st.secrets["USERS_SHEET_ID"] = "<spreadsheet-id ของตาราง Users>"
# st.secrets["USERS_SHEET_NAME"] = "Users"   # ถ้าไม่ตั้ง จะใช้ worksheet แรก

USERS_HEADER = [
    "Username", "PasswordHash", "Role", "DisplayName", "Email", "Department", "Status"
]

def _client():
    scope = ["https://www.googleapis.com/auth/spreadsheets"]
    creds_dict = st.secrets["gcp_service_account"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    return gspread.authorize(creds)

def _ws_users():
    gc = _client()
    sid = st.secrets["USERS_SHEET_ID"]
    sh = gc.open_by_key(sid)
    wname = st.secrets.get("USERS_SHEET_NAME", None)
    ws = sh.worksheet(wname) if wname else sh.get_worksheet(0)
    _ensure_users_header(ws)
    return ws

def _ensure_users_header(ws):
    current = ws.row_values(1)
    if not current:
        ws.append_row(USERS_HEADER, value_input_option="RAW")
    else:
        # เติมหัวที่ขาด (กันกรณีหัวไม่ครบ)
        need_update = False
        for i, h in enumerate(USERS_HEADER, start=1):
            if (len(current) < i) or (current[i-1].strip() != h):
                need_update = True
                break
        if need_update:
            ws.update("1:1", [USERS_HEADER])  # เขียนหัวใหม่ทั้งแถว

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

def get_all_users(mask_password: bool = True) -> List[Dict]:
    ws = _ws_users()
    users = _dicts_with_row_index(ws)
    # normalize Role, Status
    for u in users:
        u["Role"] = (u.get("Role") or "user").strip()
        u["Status"] = (u.get("Status") or "Active").strip()
        if mask_password and "PasswordHash" in u:
            u["PasswordHash"] = "********"
    return users

# ====== PASSWORD HELPERS ======
def _hash_password(plain: str) -> str:
    if not plain:
        raise ValueError("ว่างไม่ได้")
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()

def _verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode(), hashed.encode())
    except Exception:
        return False

# ====== CRUD ======
def add_user(username: str, password: str, role: str = "User") -> Tuple[bool, str]:
    if not username or not password:
        return False, "กรุณากรอก Username / Password ให้ครบ"
    uname = str(username).strip().lower()

    ws = _ws_users()
    users = _dicts_with_row_index(ws)
    for u in users:
        if str(u.get("Username","")).strip().lower() == uname:
            return False, f"มีผู้ใช้นี้อยู่แล้ว: {username}"

    hashed = _hash_password(password)
    role_norm = str(role or "User").strip().title()
    row = [
        username,             # Username
        hashed,               # PasswordHash
        role_norm,            # Role
        username,             # DisplayName (ตั้งต้น = username)
        "",                   # Email
        "",                   # Department
        "Active"              # Status
    ]
    ws.append_row(row, value_input_option="RAW")
    return True, f"เพิ่มผู้ใช้ {username} สำเร็จ"

def update_user(username: str, new_password: Optional[str], new_role: Optional[str]) -> Tuple[bool, str]:
    if not username:
        return False, "กรุณาระบุ Username"
    uname = str(username).strip().lower()

    ws = _ws_users()
    rows = ws.get_all_values()
    header = rows[0] if rows else USERS_HEADER
    # mapping col index
    col_idx = {h: i for i, h in enumerate(header)}

    found_row = None
    row_no = None
    for i in range(1, len(rows)):  # เริ่มจากแถวที่ 2 (index 1)
        r = rows[i]
        ru = (r[col_idx["Username"]] if col_idx.get("Username") is not None and col_idx["Username"] < len(r) else "").strip().lower()
        if ru == uname:
            found_row = r
            row_no = i + 1
            break

    if not found_row:
        return False, f"ไม่พบผู้ใช้ {username}"

    # เตรียมค่าใหม่
    new_vals = found_row[:] + [""] * (len(header) - len(found_row))
    if new_password:
        new_vals[col_idx["PasswordHash"]] = _hash_password(new_password)
    if new_role:
        new_vals[col_idx["Role"]] = str(new_role).strip().title()

    ws.update(f"{row_no}:{row_no}", [new_vals])
    return True, f"อัปเดตผู้ใช้ {username} สำเร็จ"

def delete_user(username: str) -> Tuple[bool, str]:
    if not username:
        return False, "กรุณาระบุ Username"
    uname = str(username).strip().lower()

    ws = _ws_users()
    users = _dicts_with_row_index(ws)
    for u in users:
        if str(u.get("Username","")).strip().lower() == uname:
            ws.delete_rows(u["row_index"])
            return True, f"ลบผู้ใช้ {username} สำเร็จ"
    return False, f"ไม่พบผู้ใช้ {username}"

# ====== LOGIN ======
def check_login(username: str, password: str) -> Optional[Dict]:
    """คืน dict ของผู้ใช้เฉพาะเมื่อยืนยันได้จาก Google Sheet เท่านั้น"""
    if not username or not password:
        return None
    uname = str(username).strip().lower()

    ws = _ws_users()
    users = _dicts_with_row_index(ws)

    for u in users:
        ru = str(u.get("Username","")).strip().lower()
        if ru == uname:
            pw_hash = str(u.get("PasswordHash","") or "")
            if pw_hash and _verify_password(password, pw_hash):
                out = dict(u)
                out["_verified"] = True
                out["_source"] = "gsheet"
                return out
            else:
                return None  # เจอผู้ใช้แต่รหัสผ่านไม่ตรง

    return None
