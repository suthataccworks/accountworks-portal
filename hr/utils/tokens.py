# hr/utils/tokens.py
from __future__ import annotations
import os
from typing import Tuple, Dict, Any

from django.core import signing

# เกลือสำหรับโทเค็น (ปรับชื่อได้ แต่ควรคงเดิมหลัง deploy)
SALT = "hr.leave.email.action"

# อายุโทเค็น (วินาที) ค่าเริ่มต้น = 14 วัน
TOKEN_MAX_AGE = int(os.getenv("LEAVE_TOKEN_MAX_AGE", "1209600"))  # 14*24*60*60

__all__ = [
    "make_leave_action_token",
    "validate_leave_action_token",
]


def make_leave_action_token(leave_id: int, action: str, actor_email: str) -> str:
    """
    สร้างโทเค็นสำหรับลิงก์ในอีเมล
    - leave_id: ไอดีใบลา
    - action: "approve" หรือ "reject"
    - actor_email: อีเมลของผู้ที่จะกดลิงก์ (กันส่งต่อ)
    """
    if action not in {"approve", "reject"}:
        raise ValueError("action must be 'approve' or 'reject'")

    payload = {
        "leave_id": int(leave_id),
        "action": action,
        "actor": (actor_email or "").strip().lower(),
    }
    return signing.dumps(payload, salt=SALT)


def validate_leave_action_token(token: str) -> Tuple[bool, Dict[str, Any]]:
    """
    ตรวจสอบโทเค็นจากลิงก์ในอีเมล
    คืนค่า (ok, data|reason)
    - ok=True  -> data = {"leave_id":..., "action":..., "actor": ...}
    - ok=False -> data = {"reason": "..."}
    """
    if not token:
        return False, {"reason": "missing"}

    try:
        data = signing.loads(token, salt=SALT, max_age=TOKEN_MAX_AGE)
    except signing.SignatureExpired:
        return False, {"reason": "expired"}
    except signing.BadSignature:
        return False, {"reason": "bad-signature"}
    except Exception as e:
        return False, {"reason": f"error:{type(e).__name__}"}

    # ตรวจโครงสร้างขั้นต่ำ
    action = data.get("action")
    if action not in {"approve", "reject"}:
        return False, {"reason": "bad-action"}

    if "leave_id" not in data:
        return False, {"reason": "missing-leave-id"}

    # ทำความสะอาดอีเมลผู้กด
    actor = (data.get("actor") or "").strip().lower()
    data["actor"] = actor

    return True, data
