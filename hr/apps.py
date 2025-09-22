# hr/apps.py
from django.apps import AppConfig

class HrConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "hr"

    def ready(self):
        # โหลด signals เสมอเมื่อแอปพร้อม
        from . import signals  # noqa: F401
