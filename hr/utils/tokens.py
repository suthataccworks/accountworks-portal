# hr/utils/tokens.py
from django.core.signing import TimestampSigner

_signer = TimestampSigner()

def make_leave_action_token(leave_id: int, action: str, actor_email: str) -> str:
    """
    สร้างโทเค็นลงนาม/มีอายุ: "{leave_id}:{action}:{actor_email}"
    action: "approve" | "reject"
    """
    payload = f"{int(leave_id)}:{action.lower()}:{actor_email.strip().lower()}"
    return _signer.sign(payload)

def parse_leave_action_token(token: str, max_age_seconds: int = 3 * 24 * 3600):
    """
    คืนค่า: (leave_id:int, action:str, actor_email:str)
    โยน SignatureExpired/BadSignature หากหมดอายุหรือผิดลายเซ็น
    """
    value = _signer.unsign(token, max_age=max_age_seconds)
    leave_id_str, action, actor_email = value.split(":", 3)
    return int(leave_id_str), action, actor_email
