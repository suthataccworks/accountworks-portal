# hr/management/commands/send_today_leave_digest.py
from django.core.management.base import BaseCommand
from hr.emails import send_daily_digest

class Command(BaseCommand):
    help = "Send daily digest of today's approved leaves to team leads/managers"

    def handle(self, *args, **options):
        try:
            sent = send_daily_digest()
            self.stdout.write(self.style.SUCCESS(f"Daily digest sent ({sent or 0})"))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Daily digest failed: {e}"))
            raise
