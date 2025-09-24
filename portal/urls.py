# portal/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse
from django.shortcuts import redirect
from django.views.generic.base import RedirectView

from hr import views as hr_views

def ping(_request):
    return HttpResponse("pong")

# ผู้ใช้ยังไม่ล็อกอิน → ไปหน้า Login, ล็อกอินแล้ว → ไปแดชบอร์ด (/dashboard/)
def root_router(request):
    if not request.user.is_authenticated:
        return redirect("auth:login")
    return redirect("hr:leave_dashboard")

urlpatterns = [
    path("admin/", admin.site.urls),

    # Django auth + ตั้ง namespace เป็น 'auth'
    path("accounts/", include(("django.contrib.auth.urls", "auth"), namespace="auth")),

    # ทางลัด /login → /accounts/login
    path("login/", RedirectView.as_view(pattern_name="auth:login", permanent=False), name="login-shortcut"),

    # ✅ จับ '/' ก่อน แล้วค่อย include เส้นทางของ HR
    path("", root_router, name="root"),

    # เส้นทางของแอป HR (มี /dashboard/ เป็นต้น)
    path("", include(("hr.urls", "hr"), namespace="hr")),

    # one-click approve/reject via email (public)
    path("email/leave/approve/", hr_views.email_approve_leave, name="email_approve_leave"),
    path("email/leave/reject/",  hr_views.email_reject_leave,  name="email_reject_leave"),

    # healthcheck
    path("ping/", ping),
]

# เสิร์ฟ media ตอน DEBUG
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
