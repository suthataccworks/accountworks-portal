from django.urls import path
from . import views

urlpatterns = [
    path("", views.app_dashboard, name="app_dashboard"),

    # Leave
    path("dashboard/", views.leave_dashboard, name="leave_dashboard"),
    path("leave-request/", views.leave_request, name="leave_request"),
    path("manage/", views.manage_requests, name="manage_requests"),
    path("requests/<int:pk>/status/", views.update_request_status, name="update_request_status"),

    # Overview
    path("overview/", views.menu_overview, name="menu_overview"),

    # Holidays
    path("holidays/", views.menu_holidays, name="menu_holidays"),
    path("holidays/add/", views.holiday_add, name="holiday_add"),
    path("holidays/<int:pk>/edit/", views.holiday_edit, name="holiday_edit"),
    path("holidays/<int:pk>/delete/", views.holiday_delete, name="holiday_delete"),

    # Announcements
    path("announcements/", views.menu_announcements, name="menu_announcements"),
    path("announcements/add/", views.announcement_add, name="announcement_add"),
    path("announcements/<int:pk>/", views.announcement_detail, name="announcement_detail"),
    path("announcements/<int:pk>/edit/", views.announcement_edit, name="announcement_edit"),
    path("announcements/<int:pk>/delete/", views.announcement_delete, name="announcement_delete"),

    # Placeholders
    path("courier/", views.menu_courier, name="menu_courier"),
    path("myteam/", views.menu_myteam, name="menu_myteam"),
]
