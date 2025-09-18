# modules/auth_gsheet.py
import os, hashlib, hmac, time
from typing import Tuple, List, Dict, Any, Optional

try:
    import streamlit as st
except Exception:
    # fallback dummy for scripts
    class _Dummy:
        secrets = {}
        def warning(self, *a, **k): pass
        def error(self, *a, **k): pass
    st = _Dummy()  # type: ignore

# ===== CONFIG =====
DATA_DIR = "./_local_data"
os.makedirs(DATA_DIR, exist_ok=True)

SPREADSHEET_KEY = st.secrets.get("SPREADSHEET_KEY")
USERS_SHEET_NAME = st.secrets.get("USERS_SHEET_NAME", "Users")
PASSWORD_SALT = st.secrets.get("PASSWORD_SALT", "change-me-please")

# ===== GSpread Client (google-auth) =====
def _get_gspread_client():
    try:
        from google.oauth2.service_account import Credentials
        import gspread
        info = st.secrets["gcp_service_account"]  # must exist
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ]
        creds = Credentials.from_service_account_info(info, scopes=scopes)
        return gspread.authorize(creds)
    except KeyError as e:
        # secrets missing -> fallback to CSV
        return None
    except Exception as e:
        # any auth error -> fallback to CSV but surface cause
        st.warning(f"ไม่สามารถสร้าง gspread client: {e}")
        return None

GS = _get_gspread_client()

def _open_ws(sheet_name: str):
    if GS and SPREADSHEET_KEY:
        try:
            sh = GS.open_by_key(SPREADSHEET_KEY)
        except Exception as e:
            raise RuntimeError(
                f"เปิดสเปรดชีตไม่สำเร็จ (ตรวจ SPREADSHEET_KEY และ share ให้ service account): {e}"
            )
        try:
            return sh.worksheet(sheet_name)
        except Exception:
            # auto-create if missing
            sh.add_worksheet(title=sheet_name, rows=1000, cols=20)
            return sh.worksheet(sheet_name)
    return None

def _csv_path(name: str) -> str:
    return os.path.join(DATA_DIR, f"{name}.csv")

def _read_users() -> List[Dict[str, Any]]:
    import pandas as pd
    ws = _open_ws(USERS_SHEET_NAME)
    if ws is not None:
        rows = ws.get_all_records()
        return rows
    # CSV fallback
    p = _csv_path(USERS_SHEET_NAME)
    if not os.path.exists(p):
        # seed with admin/admin
        import pandas as pd
        df = pd.DataFrame([{"Username":"admin","Password":"admin","Role":"Admin"}])
        df.to_csv(p, index=False, encoding="utf-8-sig")
    import pandas as pd
    return pd.read_csv(p).fillna("").to_dict(orient="records")

def _write_users(rows: List[Dict[str, Any]]) -> Tuple[bool, str]:
    import pandas as pd
    ws = _open_ws(USERS_SHEET_NAME)
    df = pd.DataFrame(rows)
    if ws is not None:
        try:
            ws.clear()
            ws.update([df.columns.tolist()] + df.fillna("").values.tolist())
            return True, "บันทึกผู้ใช้สำเร็จ"
        except Exception as e:
            return False, f"อัปเดตชีตไม่สำเร็จ: {e}"
    # CSV fallback
    try:
        df.to_csv(_csv_path(USERS_SHEET_NAME), index=False, encoding="utf-8-sig")
        return True, "บันทึกผู้ใช้สำเร็จ (CSV)"
    except Exception as e:
        return False, f"บันทึก CSV ไม่สำเร็จ: {e}"

# ===== Password helpers (sha256 + salt) =====
def _hash_pw(pw: str) -> str:
    # HMAC-SHA256 with server-side salt (simple, no bcrypt dependency)
    return hmac.new(PASSWORD_SALT.encode("utf-8"), pw.encode("utf-8"), hashlib.sha256).hexdigest()

def _check_pw(plain: str, row: Dict[str, Any]) -> bool:
    # support either PasswordHash or plain Password (for backward compatibility)
    ph = str(row.get("PasswordHash") or "").strip()
    if ph:
        return hmac.compare_digest(_hash_pw(plain), ph)
    # fallback to plain text column
    return str(row.get("Password", "")).strip() == plain

# ===== Public APIs used by app.py =====
def check_login(username: str, password: str) -> Optional[Dict[str, Any]]:
    users = _read_users()
    if not users:
        raise RuntimeError("ไม่พบตาราง Users (หรือไม่มีข้อมูล)")

    target = None
    for r in users:
        if str(r.get("Username","")).strip().lower() == username.strip().lower():
            target = r
            break

    if target is None:
        return None
    if not _check_pw(password, target):
        return None

    # normalize fields
    role = str(target.get("Role","User")).strip()
    return {"Username": target.get("Username"), "Role": role}

def get_all_users(mask_password: bool=True):
    rows = _read_users()
    if mask_password:
        for r in rows:
            if "Password" in r and r["Password"]:
                r["Password"] = "••••••"
            if "PasswordHash" in r and r["PasswordHash"]:
                r["PasswordHash"] = "••••••"
    return rows

def add_user(username: str, password: str, role: str) -> Tuple[bool, str]:
    if not username or not password:
        return False, "กรอก Username/Password ให้ครบ"
    rows = _read_users()
    if any(str(r.get("Username","")).lower() == username.strip().lower() for r in rows):
        return False, "มีผู้ใช้นี้อยู่แล้ว"
    rows.append({
        "Username": username.strip(),
        "Password": "",                 # store hash instead
        "PasswordHash": _hash_pw(password),
        "Role": role.strip() or "User",
    })
    return _write_users(rows)

def update_user(username: str, new_password: str, new_role: str) -> Tuple[bool, str]:
    rows = _read_users()
    found = False
    for r in rows:
        if str(r.get("Username","")).strip().lower() == username.strip().lower():
            found = True
            if new_password:
                r["Password"] = ""
                r["PasswordHash"] = _hash_pw(new_password)
            if new_role:
                r["Role"] = new_role
            break
    if not found:
        return False, "ไม่พบผู้ใช้"
    return _write_users(rows)

def delete_user(username: str) -> Tuple[bool, str]:
    rows = _read_users()
    new_rows = [r for r in rows if str(r.get("Username","")).strip().lower() != username.strip().lower()]
    if len(new_rows) == len(rows):
        return False, "ไม่พบผู้ใช้ที่จะลบ"
    return _write_users(new_rows)
