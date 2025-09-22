#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
from django.apps import AppConfig

class HrConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "hr"

    def ready(self):
        import hr.signals


def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'portal.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
