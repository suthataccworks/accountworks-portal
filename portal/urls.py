# portal/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse
from django.shortcuts import redirect
from hr import views as hr_views

def ping(_request): return HttpResponse("pong")

def root_router(request):
    # ยังไม่ล็อกอิน → ไปหน้า login
    if not request.user.is_authenticated:
        return redirect("auth:login")
    # ล็อกอินแล้ว → ไปแดชบอร์ด
    return redirect("hr:app_dashboard")

urlpatterns = [
    path("admin/", admin.site.urls),

    # auth (มี namespace เพื่อเลี่ยงชนชื่อ)
    path("accounts/", include(("django.contrib.auth.urls", "auth"), namespace="auth")),

    # ✅ จับ '/' ก่อน แล้วค่อยรวมเส้นทาง HR
    path("", root_router, name="root"),
    path("", include(("hr.urls", "hr"), namespace="hr")),

    path("email/leave/approve/", hr_views.email_approve_leave, name="email_approve_leave"),
    path("email/leave/reject/",  hr_views.email_reject_leave,  name="email_reject_leave"),

    path("ping/", ping),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
