# hr/views.py
from __future__ import annotations

import csv
from datetime import datetime
from typing import Optional

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from django.http import (
    HttpResponse,
    HttpResponseForbidden,
    HttpResponseNotAllowed,
    HttpResponseBadRequest,
)
    # noqa: E122
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.timezone import make_naive
from django.core.paginator import Paginator
from django.views.decorators.http import require_GET
from django.core.signing import SignatureExpired, BadSignature
from django.conf import settings

from .forms import LeaveRequestForm, HolidayForm, AnnouncementForm
from .models import (
    Team,
    Employee,
    LeaveBalance,
    LeaveRequest,
    Holiday,
    Announcement,
)

User = get_user_model()

# =========================
# Utils
# =========================
def _parse_date(s: Optional[str]):
    if not s:
        return None
    try:
        return datetime.fromisoformat(s).date()
    except Exception:
        return None


def _parse_int(s: Optional[str]):
    if not s:
        return None
    try:
        return int(s)
    except Exception:
        return None


def _is_org_manager(user) -> bool:
    return user.is_authenticated and (
        user.is_staff or user.groups.filter(name__iexact="manager").exists()
    )


def _is_team_lead(user) -> bool:
    try:
        return Employee.objects.get(user=user).is_team_lead
    except Employee.DoesNotExist:
        return False


def _is_manager_or_admin(user) -> bool:
    return _is_org_manager(user)


def _visible_requests_for(user, base_qs):
    if _is_org_manager(user):
        return base_qs

    if _is_team_lead(user):
        try:
            me = Employee.objects.select_related("team").get(user=user)
        except Employee.DoesNotExist:
            return base_qs.none()
        if not me.team:
            return base_qs.none()
        return base_qs.filter(employee__team=me.team).exclude(employee=me)

    return base_qs.none()


def render_ctx(request, template_name, ctx=None):
    base = {"is_manager_or_admin": _is_manager_or_admin(request.user)}
    if ctx:
        base.update(ctx)
    return render(request, template_name, base)


# =========================
# Dashboards
# =========================
@login_required
def app_dashboard(request):
    today = timezone.localdate()

    qs_h = Holiday.objects.filter(date__gte=today).order_by("date")[:6]
    upcoming_holidays = [
        {"name": h.name, "date": h.date, "days_left": (h.date - today).days}
        for h in qs_h
    ]

    latest_announcements = (
        Announcement.objects.filter(is_active=True)
        .order_by("-is_pinned", "-published_at", "-id")[:3]
    )

    pending_count = 0
    if _is_org_manager(request.user):
        pending_count = LeaveRequest.objects.filter(status="pending").count()
    elif _is_team_lead(request.user):
        me = Employee.objects.filter(user=request.user).select_related("team").first()
        if me and me.team_id:
            pending_count = LeaveRequest.objects.filter(
                status="pending", employee__team=me.team
            ).exclude(employee=me).count()

    return render_ctx(
        request,
        "hr/home_dashboard.html",
        {
            "upcoming_holidays": upcoming_holidays,
            "latest_announcements": latest_announcements,
            "pending_count": pending_count,
        },
    )


# =========================
# Leave
# =========================
LEAVE_KPIS = [
    ("annual",    "🌴", "Annual leave",   "annual_leave"),
    ("sick",      "🤒", "Sick leave",     "sick_leave"),
    ("personal",  "🏠", "Personal leave", "personal_leave"),
    ("relax",     "😌", "Relax leave",    "relax_leave"),
    ("maternity", "👶", "Maternity leave","maternity_leave"),
    ("other",     "🗂", "Other leave",    "other_leave"),
]


@login_required
def leave_dashboard(request):
    employee, _ = Employee.objects.get_or_create(
        user=request.user,
        defaults={"position": "", "team": None, "is_team_lead": False},
    )

    balance, _ = LeaveBalance.objects.get_or_create(
        employee=employee,
        defaults={
            "annual_leave": 10,
            "sick_leave": 30,
            "personal_leave": 3,
            "relax_leave": 0,
            "maternity_leave": 0,
            "other_leave": 0,
        },
    )

    balance_cards = []
    for key, emoji, label, field in LEAVE_KPIS:
        value = getattr(balance, field, 0) or 0
        balance_cards.append({"key": key, "emoji": emoji, "label": label, "value": value})

    requests_qs = employee.requests.all().order_by("-start_date", "-created_at")
    return render_ctx(
        request,
        "hr/leave_dashboard.html",
        {"balance_cards": balance_cards, "requests": requests_qs},
    )


@login_required
def leave_request(request):
    employee = get_object_or_404(Employee, user=request.user)

    if request.method == "POST":
        form = LeaveRequestForm(request.POST)
        if form.is_valid():
            lr: LeaveRequest = form.save(commit=False)
            lr.employee = employee
            lr.status = "pending"
            if Holiday.objects.filter(date__range=[lr.start_date, lr.end_date]).exists():
                messages.warning(
                    request,
                    "⚠ มีวันหยุดบริษัทอยู่ในช่วงที่เลือก วันหยุดจะไม่ถูกนับเป็นวันลา",
                )
            lr.save()
            messages.success(request, "ส่งคำขอลาสำเร็จ ✅")
            return redirect("leave_dashboard")
        messages.error(request, "กรุณาตรวจสอบฟอร์มอีกครั้ง")
    else:
        form = LeaveRequestForm()

    return render_ctx(request, "hr/leave_request.html", {"form": form})


# =========================
# Manage Requests
# =========================
@login_required
def manage_requests(request):
    if not (_is_org_manager(request.user) or _is_team_lead(request.user)):
        return HttpResponseForbidden("เฉพาะหัวหน้าทีม/Manager/Admin")

    if request.method == "POST":
        pk = request.POST.get("pk")
        action = request.POST.get("action")
        lr = get_object_or_404(
            LeaveRequest.objects.select_related(
                "employee", "employee__user", "employee__team"
            ),
            pk=pk,
        )

        allowed_qs = _visible_requests_for(request.user, LeaveRequest.objects.all())
        if not allowed_qs.filter(pk=lr.pk).exists():
            messages.error(request, "คุณไม่มีสิทธิ์อนุมัติคำขอนี้")
            return redirect("manage_requests")

        if lr.status != "pending":
            messages.info(request, "คำขอไม่อยู่ในสถานะ pending แล้ว")
            return redirect("manage_requests")

        if action == "approve":
            lr.status = "approved"
            lr.save()
            messages.success(request, "อนุมัติแล้ว")
        elif action == "reject":
            lr.status = "rejected"
            lr.save()
            messages.info(request, "ปฏิเสธแล้ว")
        else:
            messages.error(request, "ไม่รู้จัก action")
        return redirect(request.META.get("HTTP_REFERER") or "manage_requests")

    qs = LeaveRequest.objects.select_related(
        "employee", "employee__user", "employee__team"
    )
    qs = _visible_requests_for(request.user, qs)

    status = (request.GET.get("status") or "").strip().lower()
    show_all = request.GET.get("all") == "1"

    if not show_all:
        if status in {"pending", "approved", "rejected"}:
            qs = qs.filter(status=status)
        else:
            qs = qs.filter(status="pending")

    items = qs.order_by("-created_at")
    return render_ctx(
        request,
        "hr/manage_requests.html",
        {"items": items, "status": status or "pending", "show_all": show_all},
    )


@login_required
def update_request_status(request, pk: int):
    if not (_is_org_manager(request.user) or _is_team_lead(request.user)):
        return HttpResponseForbidden("เฉพาะหัวหน้าทีม/Manager/Admin")
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])

    lr = get_object_or_404(LeaveRequest, pk=pk)
    allowed_qs = _visible_requests_for(request.user, LeaveRequest.objects.all())
    if not allowed_qs.filter(pk=lr.pk).exists():
        messages.error(request, "คุณไม่มีสิทธิ์อนุมัติคำขอนี้")
        return redirect("manage_requests")

    action = request.POST.get("action")
    if action == "approve":
        lr.status = "approved"
        lr.save()
        messages.success(request, "อนุมัติแล้ว")
    elif action == "reject":
        lr.status = "rejected"
        lr.save()
        messages.info(request, "ปฏิเสธแล้ว")
    else:
        messages.error(request, "ไม่รู้จัก action")
    return redirect("manage_requests")


# =========================
# Overview + CSV
# =========================
@login_required
def menu_overview(request):
    if not (_is_org_manager(request.user) or _is_team_lead(request.user)):
        return HttpResponseForbidden("เฉพาะหัวหน้าทีม/Manager/Admin")

    q = (request.GET.get("q") or "").strip()
    type_filter = (request.GET.get("type") or "").strip().lower()
    status_filter = (request.GET.get("status") or "").strip().lower()

    start_str = request.GET.get("start")
    end_str = request.GET.get("end")
    cstart_str = request.GET.get("cstart")
    cend_str = request.GET.get("cend")

    days_min = _parse_int(request.GET.get("days_min"))
    days_max = _parse_int(request.GET.get("days_max"))

    start_dt = _parse_date(start_str)
    end_dt = _parse_date(end_str)
    cstart_dt = _parse_date(cstart_str)
    cend_dt = _parse_date(cend_str)

    qs = LeaveRequest.objects.select_related("employee__user", "employee__team").all()
    qs = _visible_requests_for(request.user, qs)

    if q:
        qs = qs.filter(
            Q(employee__user__first_name__icontains=q)
            | Q(employee__user__last_name__icontains=q)
            | Q(employee__user__username__icontains=q)
        )

    VALID_TYPES = {"annual", "sick", "personal", "relax", "unpaid", "maternity", "other"}
    if type_filter in VALID_TYPES:
        qs = qs.filter(leave_type=type_filter)

    if status_filter in {"pending", "approved", "rejected"}:
        qs = qs.filter(status=status_filter)

    if start_dt:
        qs = qs.filter(end_date__gte=start_dt)
    if end_dt:
        qs = qs.filter(start_date__lte=end_dt)

    if cstart_dt:
        qs = qs.filter(created_at__date__gte=cstart_dt)
    if cend_dt:
        qs = qs.filter(created_at__date__lte=cend_dt)

    rows = []
    for r in qs:
        u = r.employee.user
        days = (r.end_date - r.start_date).days + 1
        rows.append(
            {
                "first_name": u.first_name or "",
                "last_name": u.last_name or "",
                "username": u.username,
                "leave_type": r.leave_type,
                "start_date": r.start_date,
                "end_date": r.end_date,
                "days": days,
                "reason": (r.reason or "").strip(),
                "status": r.status,
                "created_at": make_naive(r.created_at),
            }
        )

    if days_min is not None:
        rows = [x for x in rows if x["days"] >= days_min]
    if days_max is not None:
        rows = [x for x in rows if x["days"] <= days_max]

    stats_type = qs.values("leave_type").annotate(total=Count("id")).order_by("leave_type")
    stats_status = qs.values("status").annotate(total=Count("id")).order_by("status")

    if request.GET.get("export") == "csv":
        resp = HttpResponse(content_type="text/csv; charset=UTF-8")
        resp["Content-Disposition"] = 'attachment; filename="leave_detail_report.csv"'
        w = csv.writer(resp)
        w.writerow(
            [
                "First Name",
                "Last Name",
                "Username",
                "Leave Type",
                "Start Date",
                "End Date",
                "Days",
                "Reason",
                "Status",
                "Created At",
            ]
        )
        for r in rows:
            w.writerow(
                [
                    r["first_name"],
                    r["last_name"],
                    r["username"],
                    r["leave_type"],
                    r["start_date"],
                    r["end_date"],
                    r["days"],
                    r["reason"].replace("\r", " ").replace("\n", " "),
                    r["status"],
                    r["created_at"].strftime("%Y-%m-%d %H:%M"),
                ]
            )
        return resp

    return render_ctx(
        request,
        "hr/overview.html",
        {
            "stats_type": stats_type,
            "stats_status": stats_status,
            "rows": rows,
            "q": q,
            "type": type_filter,
            "status": status_filter,
            "start": start_str or "",
            "end": end_str or "",
            "cstart": cstart_str or "",
            "cend": cend_str or "",
            "days_min": request.GET.get("days_min") or "",
            "days_max": request.GET.get("days_max") or "",
        },
    )


# =========================
# Holidays (CRUD)
# =========================
@login_required
def menu_holidays(request):
    holidays = Holiday.objects.order_by("date")
    return render_ctx(request, "hr/holidays.html", {"holidays": holidays})


@login_required
def holiday_add(request):
    if not _is_org_manager(request.user):
        return HttpResponseForbidden("เฉพาะ Manager/Admin")
    form = HolidayForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "เพิ่มวันหยุดสำเร็จ ✅")
        return redirect("menu_holidays")
    return render_ctx(request, "hr/holiday_form.html", {"form": form, "title": "เพิ่มวันหยุด"})


@login_required
def holiday_edit(request, pk: int):
    if not _is_org_manager(request.user):
        return HttpResponseForbidden("เฉพาะ Manager/Admin")
    holiday = get_object_or_404(Holiday, pk=pk)
    form = HolidayForm(request.POST or None, instance=holiday)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "แก้ไขวันหยุดสำเร็จ ✅")
        return redirect("menu_holidays")
    return render_ctx(request, "hr/holiday_form.html", {"form": form, "title": "แก้ไขวันหยุด"})


@login_required
def holiday_delete(request, pk: int):
    if not _is_org_manager(request.user):
        return HttpResponseForbidden("เฉพาะ Manager/Admin")
    holiday = get_object_or_404(Holiday, pk=pk)
    if request.method == "POST":
        holiday.delete()
        messages.info(request, "ลบวันหยุดแล้ว 🗑")
        return redirect("menu_holidays")
    return render_ctx(request, "hr/holiday_confirm_delete.html", {"holiday": holiday})


# =========================
# Announcements (CRUD)
# =========================
@login_required
def menu_announcements(request):
    q = (request.GET.get("q") or "").strip()
    show_all = _is_org_manager(request.user)

    qs = Announcement.objects.all()
    if not show_all:
        qs = qs.filter(is_active=True)
    if q:
        qs = qs.filter(Q(title__icontains=q) | Q(content__icontains=q))
    qs = qs.order_by("-is_pinned", "-published_at", "-id")

    items = Paginator(qs, 8).get_page(request.GET.get("page"))
    return render_ctx(
        request,
        "hr/announcements_list.html",
        {"items": items, "q": q, "show_all": show_all},
    )


@login_required
def announcement_detail(request, pk: int):
    a = get_object_or_404(Announcement, pk=pk)
    if not a.is_active and not _is_org_manager(request.user):
        return HttpResponseForbidden("ประกาศนี้ปิดการแสดงผล")
    return render_ctx(request, "hr/announcements_detail.html", {"a": a})


@login_required
def announcement_add(request):
    if not _is_org_manager(request.user):
        return HttpResponseForbidden("เฉพาะ Manager/Admin")
    form = AnnouncementForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        obj: Announcement = form.save(commit=False)
        obj.created_by = request.user
        obj.published_at = timezone.now()
        obj.save()
        messages.success(request, "สร้างประกาศสำเร็จ ✅")
        return redirect("menu_announcements")
    return render_ctx(request, "hr/announcements_form.html", {"form": form, "title": "สร้างประกาศ"})


@login_required
def announcement_edit(request, pk: int):
    if not _is_org_manager(request.user):
        return HttpResponseForbidden("เฉพาะ Manager/Admin")
    a = get_object_or_404(Announcement, pk=pk)
    form = AnnouncementForm(request.POST or None, instance=a)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "อัปเดตประกาศสำเร็จ ✅")
        return redirect("announcement_detail", pk=a.pk)
    return render_ctx(request, "hr/announcements_form.html", {"form": form, "title": "แก้ไขประกาศ"})


@login_required
def announcement_delete(request, pk: int):
    if not _is_org_manager(request.user):
        return HttpResponseForbidden("เฉพาะ Manager/Admin")
    a = get_object_or_404(Announcement, pk=pk)
    if request.method == "POST":
        a.delete()
        messages.info(request, "ลบประกาศแล้ว 🗑")
        return redirect("menu_announcements")
    return render_ctx(request, "hr/announcements_confirm_delete.html", {"a": a})


# =========================
# Placeholder menus
# =========================
@login_required
def menu_courier(request):
    return render_ctx(request, "hr/overview.html", {"placeholder": "Courier booking – coming soon"})


@login_required
def menu_myteam(request):
    return render_ctx(request, "hr/overview.html", {"placeholder": "My Team – coming soon"})


# =========================
# One-click approve/reject via email
# =========================
def _is_approver_email(actor_email: str) -> bool:
    if not actor_email:
        return False
    u = User.objects.filter(email__iexact=actor_email.strip()).first()
    if not u:
        return False
    if u.is_staff or u.is_superuser:
        return True
    if u.groups.filter(name__iexact="manager").exists():
        return True
    try:
        if Employee.objects.filter(user=u, is_team_lead=True).exists():
            return True
    except Exception:
        pass
    return False


def _apply_action(lr: LeaveRequest, action: str, actor_email: str) -> bool:
    if getattr(settings, "APPROVAL_REQUIRE_PERMISSION", True):
        if not _is_approver_email(actor_email):
            return False

    action = (action or "").lower()
    user = User.objects.filter(email__iexact=actor_email).first()

    if action == "approve":
        lr.status = "approved"
        if hasattr(lr, "approved_at"):
            lr.approved_at = timezone.now()
        if user and hasattr(lr, "approved_by"):
            lr.approved_by = user
    elif action == "reject":
        lr.status = "rejected"
        if hasattr(lr, "rejected_at"):
            lr.rejected_at = timezone.now()
        if user and hasattr(lr, "rejected_by"):
            lr.rejected_by = user
    else:
        return False

    lr.save()
    return True


# --- NEW: หน้า public แสดงผลหลังคลิกอีเมล ---
def email_action_result(request, pk: int):
    lr = get_object_or_404(
        LeaveRequest.objects.select_related("employee__user", "employee__team"),
        pk=pk,
    )
    return render(request, "hr/leave_action_result.html", {"leave": lr})


@require_GET
def email_approve_leave(request):
    from .utils.tokens import parse_leave_action_token

    token = request.GET.get("t")
    if not token:
        return HttpResponseBadRequest("missing token")
    try:
        leave_id, action, actor_email = parse_leave_action_token(token)
    except SignatureExpired:
        return HttpResponseForbidden("ลิงก์หมดอายุแล้ว")
    except BadSignature:
        return HttpResponseForbidden("ลิงก์ไม่ถูกต้อง")

    lr = get_object_or_404(LeaveRequest, pk=leave_id)
    if not _apply_action(lr, "approve", actor_email):
        return HttpResponseForbidden("คุณไม่มีสิทธิ์ดำเนินการ")

    return redirect("hr:email_action_result", pk=lr.pk)


@require_GET
def email_reject_leave(request):
    from .utils.tokens import parse_leave_action_token

    token = request.GET.get("t")
    if not token:
        return HttpResponseBadRequest("missing token")
    try:
        leave_id, action, actor_email = parse_leave_action_token(token)
    except SignatureExpired:
        return HttpResponseForbidden("ลิงก์หมดอายุแล้ว")
    except BadSignature:
        return HttpResponseForbidden("ลิงก์ไม่ถูกต้อง")

    lr = get_object_or_404(LeaveRequest, pk=leave_id)
    if not _apply_action(lr, "reject", actor_email):
        return HttpResponseForbidden("คุณไม่มีสิทธิ์ดำเนินการ")

    return redirect("hr:email_action_result", pk=lr.pk)


# =========================
# Leave detail (internal – ต้องล็อกอิน)
# =========================
@login_required
def leave_detail(request, pk: int):
    lr = get_object_or_404(
        LeaveRequest.objects.select_related("employee__user", "employee__team"),
        pk=pk,
    )

    can_view = False
    if _is_org_manager(request.user):
        can_view = True
    elif _is_team_lead(request.user):
        me_emp = Employee.objects.filter(user=request.user).select_related("team").first()
        if me_emp and me_emp.team_id and lr.employee.team_id == me_emp.team_id:
            can_view = True
        if lr.employee.user_id == request.user.id:
            can_view = True
    else:
        can_view = (lr.employee.user_id == request.user.id)

    if not can_view:
        return HttpResponseForbidden("คุณไม่มีสิทธิ์เข้าถึงคำขอนี้")

    return render_ctx(request, "hr/leave_detail.html", {"leave": lr})
