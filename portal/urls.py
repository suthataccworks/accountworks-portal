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

    # เส้น auth มาตรฐานของ Django (login/logout/password reset)
    path("accounts/", include("django.contrib.auth.urls")),

    # รวมเส้นทางของแอป HR ไว้ที่ root (namespace = "hr")
    path("", include(("hr.urls", "hr"), namespace="hr")),

    # one-click approve/reject (กันพลาด namespace)
    path("email/leave/approve", hr_views.email_approve_leave),
    path("email/leave/reject",  hr_views.email_reject_leave),

    # healthcheck
    path("ping", ping),
]

# เสิร์ฟ media เฉพาะตอน DEBUG
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
