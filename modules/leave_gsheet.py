# -*- coding: utf-8 -*-
"""
leave_store.py  (แทนที่ไฟล์เดิมของคุณได้เลย)
- ใช้ gspread + google.oauth2.service_account
- สร้าง/เปิดชีต LeaveRequests อัตโนมัติ
- มี helper สำหรับอ่าน/เพิ่ม/แก้ไข/ยกเลิก/อัปเดตสถานะ
"""

from __future__ import annotations
import datetime as dt
from typing import Any, Dict, List, Tuple

import gspread
import streamlit as st
from gspread.exceptions import WorksheetNotFound, SpreadsheetNotFound
from google.oauth2.service_account import Credentials

# =========================
# CONFIG
# =========================

SHEET_NAME = "LeaveRequests"
HEADERS = ["Username", "LeaveType", "StartDate", "EndDate", "Reason", "Status"]  # A..F
# Scopes: อ่าน/เขียนชีต + อ่านไฟล์ไดรฟ์ (เปิดด้วย ID)
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.readonly",
]

LEAVE_FILE_ID = (st.secrets.get("leave_file_id") or "").strip()


# =========================
# INTERNAL HELPERS
# =========================

def _require_file_id() -> None:
    if not LEAVE_FILE_ID:
        raise ValueError("ไม่พบค่า leave_file_id ใน st.secrets — โปรดตั้งค่า leave_file_id ให้ถูกต้อง")


def _normalize_sa_info(sa_dict: Dict[str, Any]) -> Dict[str, Any]:
    """ทำให้ private_key ถูกฟอร์แมตเสมอ (รองรับกรณี secrets วางเป็น \\n)"""
    sa = dict(sa_dict or {})
    key = str(sa.get("private_key", "") or "")
    if not key:
        raise RuntimeError("Service Account private_key is empty. ตรวจสอบ st.secrets['gcp_service_account'].private_key")

    # แปลง "\\n" ให้เป็น newline จริง
    if "\\n" in key:
        key = key.replace("\\n", "\n")
    key = key.strip()

    if not (key.startswith("-----BEGIN PRIVATE KEY-----") and key.endswith("-----END PRIVATE KEY-----")):
        raise RuntimeError("private_key format ดูไม่ถูกต้อง: ควรเป็นก้อน PKCS8 ครบหัว/ท้าย และใช้ \\n แทนขึ้นบรรทัด")

    sa["private_key"] = key
    return sa


def _gs_client() -> gspread.Client:
    sa_info = _normalize_sa_info(st.secrets.get("gcp_service_account", {}))
    creds = Credentials.from_service_account_info(sa_info, scopes=SCOPES)
    return gspread.authorize(creds)


def _open_spreadsheet() -> gspread.Spreadsheet:
    _require_file_id()
    client = _gs_client()
    try:
        return client.open_by_key(LEAVE_FILE_ID)
    except SpreadsheetNotFound:
        raise SpreadsheetNotFound(
            "ไม่พบสเปรดชีตจาก leave_file_id หรือ Service Account ไม่มีสิทธิ์เข้าถึง "
            "(แชร์ไฟล์ให้ client_email ของ Service Account อย่างน้อย Viewer/Editor)"
        )


def _ensure_worksheet(sh: gspread.Spreadsheet) -> gspread.Worksheet:
    """เปิดชีตชื่อ SHEET_NAME ถ้าไม่มีให้สร้าง + ใส่หัวตาราง A1:F1"""
    try:
        ws = sh.worksheet(SHEET_NAME)
    except WorksheetNotFound:
        ws = sh.add_worksheet(title=SHEET_NAME, rows=1000, cols=len(HEADERS))
        ws.update(f"A1:{chr(ord('A') + len(HEADERS) - 1)}1", [HEADERS])
    return ws


def _to_str_date(x: Any) -> str:
    """รับ date/datetime/string -> คืน string YYYY-MM-DD"""
    if isinstance(x, (dt.date, dt.datetime)):
        return x.date().isoformat() if isinstance(x, dt.datetime) else x.isoformat()
    return str(x or "")


def _days_inclusive(start: Any, end: Any) -> int | None:
    """คำนวณจำนวนวันแบบคร่าว ๆ (รวมต้น-ท้าย) ถ้าเป็นสตริง/แปลงไม่ได้ ให้คืน None"""
    def _coerce(d):
        if isinstance(d, dt.datetime):
            return d.date()
        if isinstance(d, dt.date):
            return d
        if isinstance(d, str):
            try:
                return dt.date.fromisoformat(d)
            except ValueError:
                return None
        return None

    s = _coerce(start)
    e = _coerce(end)
    if s and e:
        return (e - s).days + 1
    return None


def _clear_cache():
    try:
        get_all_leaves.clear()
    except Exception:
        pass


# =========================
# WORKSHEET ACCESSOR
# =========================

def _get_leave_ws() -> gspread.Worksheet:
    sh = _open_spreadsheet()
    return _ensure_worksheet(sh)


# =========================
# PUBLIC API (เรียกใช้จาก app.py)
# =========================

@st.cache_data(ttl=20)
def get_all_leaves() -> List[Dict[str, Any]]:
    """
    อ่านรายการคำขอลาทั้งหมดเป็น list[dict] + แทรก row_index (แถวจริงในชีต)
    """
    ws = _get_leave_ws()
    # ถ้าไฟล์เพิ่งสร้างใหม่ อาจยังไม่มี header -> บังคับให้มี
    first_row = ws.row_values(1)
    if first_row != HEADERS:
        ws.update(f"A1:{chr(ord('A') + len(HEADERS) - 1)}1", [HEADERS])

    records = ws.get_all_records()  # อ่านทั้งหมด (ยึดบรรทัดแรกเป็น header)
    for i, row in enumerate(records, start=2):  # header อยู่แถว 1
        row["row_index"] = i
        # default ช่องว่างป้องกัน KeyError
        for h in HEADERS:
            row.setdefault(h, "")
    return records


def submit_leave(username: str, leave_type: str, start_date: Any, end_date: Any, reason: str) -> Tuple[bool, str]:
    """
    เพิ่มคำขอลาใหม่ (เริ่มด้วยสถานะ = Pending)
    start_date/end_date: date | datetime | "YYYY-MM-DD"
    """
    ws = _get_leave_ws()
    payload = [
        str(username or ""),
        str(leave_type or ""),
        _to_str_date(start_date),
        _to_str_date(end_date),
        str(reason or ""),
        "Pending",
    ]
    # ใช้ USER_ENTERED เผื่อมีสูตร/format ในอนาคต
    ws.append_row(payload, value_input_option="USER_ENTERED")
    _clear_cache()

    days = _days_inclusive(start_date, end_date)
    if days is not None:
        return True, f"✅ ส่งคำขอลาเรียบร้อย ({days} วัน)"
    return True, "✅ ส่งคำขอลาเรียบร้อย"


def update_leave_request(row_index: int, new_type: str, new_start: Any, new_end: Any, new_reason: str) -> Tuple[bool, str]:
    """
    ผู้ใช้แก้ไขคำขอลา (อัปเดตคอลัมน์ B..E แบบ batch เพื่อลด API calls)
    """
    ws = _get_leave_ws()
    values = [[
        str(new_type or ""),
        _to_str_date(new_start),
        _to_str_date(new_end),
        str(new_reason or "")
    ]]
    ws.update(f"B{row_index}:E{row_index}", values, value_input_option="USER_ENTERED")
    _clear_cache()
    return True, "💾 อัปเดตคำขอลาเรียบร้อย"


def cancel_leave_request(row_index: int) -> Tuple[bool, str]:
    """
    ผู้ใช้ยกเลิกคำขอ: ลบทั้งแถว (ถ้าจะเก็บประวัติ ให้ใช้ update_leave_status(row_index, 'Cancelled') แทน)
    """
    ws = _get_leave_ws()
    ws.delete_rows(row_index)
    _clear_cache()
    return True, "🗑 ยกเลิกคำขอลาเรียบร้อยแล้ว"


def update_leave_status(row_index: int, status: str) -> Tuple[bool, str]:
    """
    Admin/หัวหน้า อัปเดตสถานะ (Approved/Rejected/Cancelled)
    """
    ws = _get_leave_ws()
    ws.update_cell(row_index, 6, str(status or ""))  # F: Status
    _clear_cache()
    return True, f"📌 อัปเดตสถานะเป็น {status}"
