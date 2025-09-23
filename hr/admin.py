# hr/admin.py
from django.contrib import admin
from .models import Team, Employee, LeaveBalance, LeaveRequest, Holiday, Announcement


# ---------- Team ----------
@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)
    ordering = ("name",)


# ---------- Employee ----------
@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ("username", "position", "team", "is_team_lead")
    list_filter = ("team", "is_team_lead")
    search_fields = ("user__username", "user__first_name", "user__last_name")
    list_select_related = ("user", "team")
    ordering = ("user__username",)

    def username(self, obj):
        u = getattr(obj, "user", None)
        return getattr(u, "username", "-")
    username.short_description = "User"


# ---------- LeaveBalance ----------
def normalize_balances(modeladmin, request, queryset):
    """
    แก้ค่าให้ไม่เป็น NULL/ติดลบ แบบรวดเร็วจากหน้าแอดมิน
    """
    for b in queryset:
        # ให้มีค่าอย่างน้อยเป็น 0 ทุกฟิลด์
        for f in (
            "annual_leave",
            "sick_leave",
            "personal_leave",
            "relax_leave",
            "maternity_leave",
            "other_leave",
        ):
            v = getattr(b, f, 0) or 0
            if v < 0:
                v = 0
            setattr(b, f, v)
        b.save()
normalize_balances.short_description = "Normalize selected balances (NULL/negative → 0)"


@admin.register(LeaveBalance)
class LeaveBalanceAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "annual_leave",
        "sick_leave",
        "personal_leave",
        "relax_leave",
        "maternity_leave",
        "other_leave",
        "total_balance",
    )
    search_fields = (
        "employee__user__username",
        "employee__user__first_name",
        "employee__user__last_name",
    )
    list_select_related = ("employee", "employee__user")
    ordering = ("employee__user__username",)
    actions = [normalize_balances]

    def user(self, obj):
        u = getattr(obj.employee, "user", None)
        return getattr(u, "username", "-")
    user.short_description = "User"

    def total_balance(self, obj):
        vals = [
            getattr(obj, "annual_leave", 0) or 0,
            getattr(obj, "sick_leave", 0) or 0,
            getattr(obj, "personal_leave", 0) or 0,
            getattr(obj, "relax_leave", 0) or 0,
            getattr(obj, "maternity_leave", 0) or 0,
            getattr(obj, "other_leave", 0) or 0,
        ]
        return sum(vals)
    total_balance.short_description = "Total"


# ---------- LeaveRequest ----------
@admin.register(LeaveRequest)
class LeaveRequestAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "leave_type",
        "start_date",
        "end_date",
        "status",
        "deducted",
        "created_at",
    )
    list_filter = ("leave_type", "status", "employee__team")
    search_fields = (
        "employee__user__username",
        "employee__user__first_name",
        "employee__user__last_name",
        "reason",
    )
    list_select_related = ("employee", "employee__user", "employee__team")
    date_hierarchy = "start_date"
    ordering = ("-created_at",)

    def user(self, obj):
        u = getattr(obj.employee, "user", None)
        return getattr(u, "username", "-")
    user.short_description = "User"


# ---------- Holiday ----------
@admin.register(Holiday)
class HolidayAdmin(admin.ModelAdmin):
    list_display = ("name", "date", "is_public")
    list_filter = ("is_public",)
    search_fields = ("name",)
    ordering = ("date",)


# ---------- Announcement ----------
@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ("title", "is_pinned", "is_active", "published_at", "created_by")
    list_filter = ("is_pinned", "is_active")
    search_fields = ("title", "content")
    date_hierarchy = "published_at"
    ordering = ("-is_pinned", "-published_at", "-id")
