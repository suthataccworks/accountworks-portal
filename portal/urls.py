# portal/urls.py
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),

    # แอป HR ทั้งหมด
    path('', include('hr.urls')),

    # auth views (login/logout/password change/reset)
    path('', include('django.contrib.auth.urls')),
]
