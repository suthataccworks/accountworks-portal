# hr/emails.py
from __future__ import annotations

from typing import List, Iterable, Optional
from urllib.parse import urlencode

from django.conf import settings
from django.urls import reverse, NoReverseMatch
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db.models import Q

from .utils.emailing import send_html_mail
from .utils.tokens import make_leave_action_token
from .models import LeaveRequest, Employee  # ปรับให้ตรงกับโปรเจกต์ถ้าชื่อไม่เหมือน

User = get_user_model()


# =========================
# URL helpers (รองรับหลายชื่อตามโปรเจกต์)
# =========================
def _reverse_with_fallback(candidates: list[str]) -> str:
    """
    พยายาม reverse ให้ได้สักชื่อหนึ่งตามลำดับ
    เช่น ["hr:email_approve", "hr:email_approve_leave"]
    """
    last_err: Optional[Exception] = None
    for name in candidates:
        try:
            return reverse(name)
        except NoReverseMatch as e:
            last_err = e
            continue
    # ถ้าไม่มีสักชื่อ ให้ raise error สุดท้ายเพื่อเดบักง่าย
    if last_err:
        raise last_err
    raise NoReverseMatch("No url name candidates provided")


# =========================
# Helpers: คัดเลือก Approvers
# =========================
def _team_lead_users_for(employee: Employee) -> List[User]:
    """
    หาหัวหน้าทีมของพนักงานคนนี้ (ภายในทีมเดียวกัน) จาก Employee.is_team_lead=True
    """
    if not employee or not employee.team_id:
        return []
    leads = (
        Employee.objects.select_related("user")
        .filter(team_id=employee.team_id, is_team_lead=True)
        .exclude(user__isnull=True)
    )
    return [e.user for e in leads if e.user and e.user.email]


def _org_approver_users() -> List[User]:
    """
    ผู้อนุมัติระดับองค์กร:
    - อยู่กลุ่ม 'manager' (ไม่แคร์ตัวพิมพ์)
    - หรือเป็น staff/superuser
    """
    qs = User.objects.filter(is_active=True).filter(
        Q(groups__name__iexact="manager") | Q(is_staff=True) | Q(is_superuser=True)
    ).distinct()
    return [u for u in qs if u.email]


def _dedup_keep_order(users: Iterable[User]) -> List[User]:
    seen = set()
    out: List[User] = []
    for u in users:
        if not u or not getattr(u, "email", None):
            continue
        key = str(u.email).strip().lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(u)
    return out


def _approver_users_for(leave: LeaveRequest) -> List[User]:
    """
    นโยบายผู้รับ:
    - พยายามส่งให้ 'หัวหน้าทีม' ก่อน
    - ถ้าไม่พบหัวหน้าทีมเลย ให้ fallback ไป 'ผู้อนุมัติระดับองค์กร' (manager/staff/superuser)
    - กันไม่ให้ส่งกลับไปหา 'ผู้ยื่น' เอง
    """
    if not leave or not leave.employee_id:
        return []

    emp = leave.employee
    leads = _team_lead_users_for(emp)
    users = leads if leads else _org_approver_users()

    result = _dedup_keep_order(users)

    # กันส่งถึงผู้ยื่นเอง
    req_email = ""
    try:
        req_email = (emp.user.email or "").strip().lower()
    except Exception:
        pass
    if req_email:
        result = [u for u in result if str(u.email).strip().lower() != req_email]
    return result


def _approver_emails_for(leave: LeaveRequest) -> List[str]:
    return [u.email for u in _approver_users_for(leave) if u.email]


# =========================
# Email: แจ้ง Approver เมื่อมีคำขอใหม่
# =========================
def send_leave_request_to_approvers(leave: LeaveRequest) -> int:
    """
    ส่งอีเมลคำขอลาใหม่ถึงผู้อนุมัติ (หัวหน้าทีมก่อน; ถ้าไม่มีค่อย fallback)
    จะ 'ส่งแยกทีละคน' เพื่อฝังโทเค็น (approve/reject) ที่ผูกกับอีเมลผู้รับรายนั้น
    """
    users = _approver_users_for(leave)
    if not users:
        return 0

    # เตรียมข้อมูลทั่วไป
    site = getattr(settings, "SITE_URL", "http://127.0.0.1:8000")

    # รองรับได้ทั้งสองแบบชื่อ url
    approve_path = _reverse_with_fallback(["hr:email_approve", "hr:email_approve_leave"])
    reject_path  = _reverse_with_fallback(["hr:email_reject",  "hr:email_reject_leave"])

    emp = leave.employee
    requester = emp.user if emp and getattr(emp, "user", None) else None
    requester_name = (requester.get_full_name() or requester.username) if requester else "-"

    # แปลงประเภทลาให้เป็น display ชื่อ (รองรับทั้งมี method หรือไม่มี)
    get_disp = getattr(leave, "get_leave_type_display", None)
    leave_type_disp = get_disp() if callable(get_disp) else str(getattr(leave, "leave_type", "") or "")

    subject = f"[คำขอลาใหม่] {requester_name} • {leave.start_date}–{leave.end_date} • {leave_type_disp}"

    created_at = getattr(leave, "created_at", None)
    try:
        created_at = timezone.localtime(created_at) if created_at else timezone.localtime()
    except Exception:
        created_at = timezone.localtime()

    team_name = "-"
    try:
        team_name = getattr(emp.team, "name", "-") if emp and emp.team_id else "-"
    except Exception:
        pass

    sent = 0
    for u in users:
        # สร้างโทเค็นรายผู้รับ (ระบุอีเมลของผู้รับในโทเค็น)
        t_approve = make_leave_action_token(leave.id, "approve", u.email)
        t_reject = make_leave_action_token(leave.id, "reject", u.email)
        approve_url = f"{site}{approve_path}?{urlencode({'t': t_approve})}"
        reject_url  = f"{site}{reject_path}?{urlencode({'t': t_reject})}"

        ctx = {
            "leave": leave,
            "employee_name": requester_name,
            "team_name": team_name,
            "leave_type": leave_type_disp,
            "start_date": leave.start_date,
            "end_date": leave.end_date,
            "reason": getattr(leave, "reason", "") or "-",
            "approve_url": approve_url,
            "reject_url": reject_url,
            "site_url": site,
            "created_at": created_at,
            "subject": subject,  # เผื่อใช้ใน plain_fallback
        }

        # ส่งทีละคนเพื่อให้แต่ละฉบับมีโทเค็นเฉพาะรายบุคคล
        ok = send_html_mail(subject, [u.email], "emails/leave_request.html", ctx)
        if ok:
            sent += 1

    return sent


# =========================
# Email: แจ้งผู้ยื่นเมื่อสถานะเปลี่ยน
# =========================
def send_leave_status_to_requester(leave: LeaveRequest) -> int:
    user = getattr(getattr(leave, "employee", None), "user", None)
    email = getattr(user, "email", None)
    if not email:
        return 0

    site = getattr(settings, "SITE_URL", "http://127.0.0.1:8000")
    leave_url = site + reverse("hr:leave_detail", args=[leave.pk])

    # รองรับทั้งโมเดลที่มี get_status_display() และไม่มี
    get_disp = getattr(leave, "get_status_display", None)
    status_disp = get_disp() if callable(get_disp) else getattr(leave, "status", "-")

    ctx = {
        "leave": leave,
        "leave_url": leave_url,
        "site_url": site,
        "status_display": status_disp,
        "subject": f"[อัปเดตคำขอลา] สถานะ: {status_disp}",
    }
    subject = ctx["subject"]
    return send_html_mail(subject, [email], "emails/leave_status.html", ctx)


# =========================
# Daily digest
# =========================
def build_today_items():
    """
    ดึงรายการลาของ 'วันนี้' ที่อนุมัติแล้ว
    - ใช้ status__iexact เพื่อครอบทั้ง 'approved' / 'APPROVED'
    - ถ้าไม่มี field total_days ในโมเดล ให้คำนวณสด
    """
    today = timezone.localdate()
    qs = (
        LeaveRequest.objects.filter(
            status__iexact="approved", start_date__lte=today, end_date__gte=today
        )
        .select_related("employee", "employee__user")
    )

    items = []
    for lr in qs:
        try:
            total_days = getattr(lr, "total_days", None)
            if total_days is None:
                total_days = (lr.end_date - lr.start_date).days + 1
        except Exception:
            total_days = (lr.end_date - lr.start_date).days + 1

        try:
            name = (lr.employee.user.get_full_name() or lr.employee.user.username)
        except Exception:
            name = "-"

        get_disp = getattr(lr, "get_leave_type_display", None)
        leave_type = get_disp() if callable(get_disp) else str(getattr(lr, "leave_type", "") or "")

        items.append(
            {
                "name": name,
                "leave_type": leave_type,
                "start": lr.start_date,
                "end": lr.end_date,
                "total_days": total_days,
            }
        )
    return today, items


def _digest_recipients() -> List[str]:
    """
    รวมผู้รับสรุปรายวัน:
    - Group 'manager'
    - หัวหน้าทีม (Employee.is_team_lead=True)
    - staff/superuser (fallback)
    """
    emails: List[str] = []

    # กลุ่ม manager
    try:
        emails += list(
            User.objects.filter(groups__name__iexact="manager")
            .exclude(email="")
            .values_list("email", flat=True)
        )
    except Exception:
        pass

    # หัวหน้าทีม
    try:
        lead_user_ids = list(
            Employee.objects.filter(is_team_lead=True).values_list("user_id", flat=True)
        )
        if lead_user_ids:
            emails += list(
                User.objects.filter(id__in=lead_user_ids)
                .exclude(email="")
                .values_list("email", flat=True)
            )
    except Exception:
        pass

    # staff/superuser
    emails += list(
        User.objects.filter(Q(is_staff=True) | Q(is_superuser=True))
        .exclude(email="")
        .values_list("email", flat=True)
    )

    # unique & keep order
    seen = set()
    uniq = []
    for e in emails:
        if not e:
            continue
        key = e.strip().lower()
        if key in seen:
            continue
        seen.add(key)
        uniq.append(e)
    return uniq


def send_daily_digest() -> int:
    today, items = build_today_items()
    to_emails = _digest_recipients()
    if not to_emails:
        return 0

    site = getattr(settings, "SITE_URL", "http://127.0.0.1:8000")
    ctx = {
        "today": today,
        "items": items,
        "site_url": site,
        "subject": f"[สรุปวันนี้] ผู้ที่ลางาน {today.isoformat()}",
    }
    subject = ctx["subject"]
    return send_html_mail(subject, to_emails, "emails/daily_digest.html", ctx)
