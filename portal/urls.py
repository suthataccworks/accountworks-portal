# portal/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# ใช้ view ของแอป HR สำหรับเส้นทางอนุมัติ/ปฏิเสธแบบ one-click
from hr import views as hr_views

urlpatterns = [
    # แอดมิน
    path("admin/", admin.site.urls),

    # หน้า login/logout/password reset มาตรฐานของ Django
    # (จะได้ URL name 'login' สำหรับ @login_required)
    path("accounts/", include("django.contrib.auth.urls")),

    # รวมทุกเส้นทางของแอป HR ไว้ที่ root (namespace = "hr")
    path("", include(("hr.urls", "hr"), namespace="hr")),

    # ผูกเส้น one-click แบบตรง (กันพลาด namespace/include หรือ proxy เติม/ตัด slash)
    path("email/leave/approve", hr_views.email_approve_leave),
    path("email/leave/reject",  hr_views.email_reject_leave),
]

# เสิร์ฟไฟล์สื่อในโหมดพัฒนาเท่านั้น
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
