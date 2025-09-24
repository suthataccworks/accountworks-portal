# portal/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse
from hr import views as hr_views

def ping(_request):
    return HttpResponse("pong")

urlpatterns = [
    path("admin/", admin.site.urls),

    # ✅ ใส่ namespace ให้ auth เพื่อตัดปัญหาชื่อซ้ำ ('login', 'logout', ฯลฯ)
    path("accounts/", include(("django.contrib.auth.urls", "auth"), namespace="auth")),

    # ✅ รวมเส้นทาง HR (ตั้งชื่อ namespace='hr' ไว้อยู่แล้ว)
    path("", include(("hr.urls", "hr"), namespace="hr")),

    # one-click approve/reject (เติม / ปลายทางให้ชัด)
    path("email/leave/approve/", hr_views.email_approve_leave, name="email_approve_leave"),
    path("email/leave/reject/",  hr_views.email_reject_leave,  name="email_reject_leave"),

    # healthcheck
    path("ping/", ping),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
