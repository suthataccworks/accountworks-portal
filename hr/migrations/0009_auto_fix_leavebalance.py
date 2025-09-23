# hr/migrations/0009_auto_fix_leavebalance.py
from django.db import migrations

def fill_null_balances(apps, schema_editor):
    LeaveBalance = apps.get_model("hr", "LeaveBalance")
    # อัปเดต NULL -> 0 (ทำแบบ bulk ช่วยให้เร็วและไม่กินหน่วยความจำ)
    LeaveBalance.objects.filter(relax_leave__isnull=True).update(relax_leave=0)
    LeaveBalance.objects.filter(maternity_leave__isnull=True).update(maternity_leave=0)
    LeaveBalance.objects.filter(other_leave__isnull=True).update(other_leave=0)
    # กันค่าติดลบ (ถ้าเคยเกิด) -> 0
    LeaveBalance.objects.filter(annual_leave__lt=0).update(annual_leave=0)
    LeaveBalance.objects.filter(sick_leave__lt=0).update(sick_leave=0)
    LeaveBalance.objects.filter(personal_leave__lt=0).update(personal_leave=0)
    LeaveBalance.objects.filter(relax_leave__lt=0).update(relax_leave=0)
    LeaveBalance.objects.filter(maternity_leave__lt=0).update(maternity_leave=0)
    LeaveBalance.objects.filter(other_leave__lt=0).update(other_leave=0)

class Migration(migrations.Migration):

    dependencies = [
        ("hr", "0008_leavebalance_maternity_leave_and_more"),  # ปรับเลขให้ตรงของคุณ
    ]

    operations = [
        migrations.RunPython(fill_null_balances, reverse_code=migrations.RunPython.noop),
    ]
