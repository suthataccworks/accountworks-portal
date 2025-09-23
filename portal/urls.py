# portal/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# สำหรับผูกเส้นอีเมลแบบตรง (เผื่อ namespace พลาด)
from hr import views as hr_views

urlpatterns = [
    path("admin/", admin.site.urls),

    # เส้น auth มาตรฐานของ Django (login/logout/password reset ฯลฯ)
    path("accounts/", include("django.contrib.auth.urls")),

    # รวมทุกเส้นทางของแอป HR ที่ root และตั้ง namespace = "hr"
    path("", include(("hr.urls", "hr"), namespace="hr")),

    # ผูก one-click approve/reject แบบตรงกันพลาด
    path("email/leave/approve", hr_views.email_approve_leave),
    path("email/leave/reject",  hr_views.email_reject_leave),
]

# เสิร์ฟ media ใน dev เท่านั้น
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
