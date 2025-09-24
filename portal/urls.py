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

# portal/urls.py
from django.shortcuts import redirect

def root_router(request):
    if not request.user.is_authenticated:
        return redirect("auth:login")
    # อย่า redirect ไป hr:app_dashboard เพราะมันคือ path "" == "/"
    return redirect("hr:leave_dashboard")  # เส้นนี้คือ /dashboard/ ไม่ชน root อีก


urlpatterns = [
    path("admin/", admin.site.urls),

    # auth ของ Django ใส่ namespace 'auth'
    path("accounts/", include(("django.contrib.auth.urls", "auth"), namespace="auth")),

    # ทางลัด /login → /accounts/login (เผื่อจำสั้น)
    path("login/", RedirectView.as_view(pattern_name="auth:login", permanent=False), name="login-shortcut"),

    # ✅ จับ root "/" ตรงนี้ก่อน แล้วค่อย include เส้นทางของ HR
    path("", root_router, name="root"),

    # เส้นทางของ HR (ต้องมา *หลัง* root_router)
    path("", include(("hr.urls", "hr"), namespace="hr")),

    # one-click approve/reject
    path("email/leave/approve/", hr_views.email_approve_leave, name="email_approve_leave"),
    path("email/leave/reject/",  hr_views.email_reject_leave,  name="email_reject_leave"),

    # healthcheck
    path("ping/", ping),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
