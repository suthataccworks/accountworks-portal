# hr/context_processors.py
from .models import Employee, LeaveRequest

def role_flags(request):
    user = request.user
    is_org_manager = False
    is_team_lead = False
    team_id = None

    if user.is_authenticated:
        # ผู้จัดการทั้งองค์กร (แอดมินหรืออยู่กลุ่ม manager)
        is_org_manager = user.is_staff or user.groups.filter(name__iexact="manager").exists()
        try:
            emp = Employee.objects.select_related("team").get(user=user)
            is_team_lead = bool(emp.is_team_lead)
            team_id = emp.team_id
        except Employee.DoesNotExist:
            pass

    is_approver = is_org_manager or is_team_lead

    # ป้ายตัวเลขคำขอค้างอนุมัติ
    pending_count = 0
    if user.is_authenticated:
        if is_org_manager:
            pending_count = LeaveRequest.objects.filter(status="pending").count()
        elif is_team_lead and team_id:
            pending_count = (
                LeaveRequest.objects
                .filter(status="pending", employee__team_id=team_id)
                .exclude(employee__user=user)
                .count()
            )

    return {
        "is_manager_or_admin": is_org_manager,  # คงไว้ให้ของเดิมใช้
        "is_team_lead": is_team_lead,
        "is_approver": is_approver,             # ✅ ใช้ตัวนี้โชว์เมนูอนุมัติ
        "pending_count": pending_count,          # ✅ ใช้ทำ badge
    }
