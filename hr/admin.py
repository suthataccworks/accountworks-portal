from django.contrib import admin
from .models import Team, Employee, LeaveBalance, LeaveRequest, Holiday, Announcement


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ("user", "team", "is_team_lead", "position")
    list_filter = ("team", "is_team_lead")
    search_fields = ("user__username", "user__first_name", "user__last_name", "position")


@admin.register(LeaveBalance)
class LeaveBalanceAdmin(admin.ModelAdmin):
    list_display = ("employee", "annual_leave", "sick_leave", "personal_leave")
    search_fields = ("employee__user__username",)


@admin.register(LeaveRequest)
class LeaveRequestAdmin(admin.ModelAdmin):
    list_display = ("employee", "leave_type", "start_date", "end_date", "status", "deducted")
    list_filter = ("leave_type", "status")
    search_fields = ("employee__user__username", "employee__user__first_name", "employee__user__last_name")


# ถ้าคุณมี Holiday/Announcement อยู่แล้วและ register ไปก่อนหน้าแล้ว จะคงไว้แบบนี้ก็ได้
@admin.register(Holiday)
class HolidayAdmin(admin.ModelAdmin):
    list_display = ("name", "date", "is_public")
    list_filter = ("is_public",)
    search_fields = ("name",)


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ("title", "is_pinned", "is_active", "published_at", "created_by")
    list_filter = ("is_pinned", "is_active")
    search_fields = ("title", "content")
