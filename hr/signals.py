# hr/signals.py
from __future__ import annotations

from django.db import transaction
from django.db.models.signals import post_save, pre_save, post_delete
from django.dispatch import receiver

from .models import Employee, LeaveBalance, LeaveRequest

# 🔔 เพิ่ม: ฟังก์ชันส่งอีเมล
from .emails import (
    send_leave_request_to_approvers,
    send_leave_status_to_requester,
)

# ========= Helper =========
def _calc_days(start, end) -> int:
    """คำนวณจำนวนวันแบบ inclusive (รวมปลายทาง)"""
    return (end - start).days + 1


# แผนที่ชนิดการลา -> ชื่อฟิลด์ใน LeaveBalance ที่ต้องหักโควตา
BALANCE_FIELD_MAP = {
    "annual": "annual_leave",
    "sick": "sick_leave",
    "personal": "personal_leave",
    "relax": "relax_leave",
    "maternity": "maternity_leave",
    "other": "other_leave",
    # หมายเหตุ: "unpaid" ไม่หักโควตา จึงไม่ใส่ในแมป
}


def _get_or_create_balance_locked(employee: Employee) -> LeaveBalance:
    """
    ดึง/สร้าง LeaveBalance โดยล็อกแถวเพื่อป้องกัน race condition
    ใช้ภายใน transaction.atomic() เสมอ
    """
    bal, _ = LeaveBalance.objects.select_for_update().get_or_create(employee=employee)
    return bal


def _apply_refund(bal: LeaveBalance, days: int, field_name: str | None):
    if not field_name or days <= 0:
        return
    cur = getattr(bal, field_name, 0) or 0
    setattr(bal, field_name, cur + days)


def _apply_deduct(bal: LeaveBalance, days: int, field_name: str | None):
    if not field_name or days <= 0:
        return
    cur = getattr(bal, field_name, 0) or 0
    new_val = cur - days
    if new_val < 0:
        # ป้องกันค่าติดลบ (ปรับตามนโยบาย: จะ raise ValidationError ก็ได้)
        new_val = 0
    setattr(bal, field_name, new_val)


# ========= Employee: สร้าง Balance อัตโนมัติ =========
@receiver(post_save, sender=Employee)
def create_balance_for_employee(sender, instance: Employee, created, **kwargs):
    if created:
        LeaveBalance.objects.get_or_create(employee=instance)


# ========= LeaveRequest: ตัด/คืนโควตาเมื่อมีการแก้ไข =========
@receiver(pre_save, sender=LeaveRequest)
def handle_leave_deduction_on_update(sender, instance: LeaveRequest, **kwargs):
    """
    ทำงานตอนก่อนบันทึก LeaveRequest:
    - ถ้าใบเดิมเคยถูกหัก (approved + deducted=True) -> คืนของเดิมก่อน
    - ถ้าค่าใหม่คือ approved และยังไม่ deducted -> หักใหม่
    - รองรับกรณีแก้ 'สถานะ', 'ช่วงวัน', หรือ 'ประเภทการลา'
    - เก็บค่า _old_status ไว้เพื่อใช้แจ้งอีเมลหลังบันทึก (post_save)
    หมายเหตุ: เราใช้ pre_save เพื่อมองเห็นค่าเดิม (old) ได้สะดวก
    """
    # เรคคอร์ดใหม่ (ยังไม่มี pk) ให้ไปพิจารณาใน post_save แทน
    if not instance.pk:
        return

    old = LeaveRequest.objects.get(pk=instance.pk)
    # ⭐ เก็บสถานะเดิมไว้ ใช้ใน post_save เพื่อตรวจจับการเปลี่ยนสถานะ
    instance._old_status = old.status

    with transaction.atomic():
        bal = _get_or_create_balance_locked(instance.employee)

        old_days = _calc_days(old.start_date, old.end_date)
        new_days = _calc_days(instance.start_date, instance.end_date)

        old_field = BALANCE_FIELD_MAP.get(old.leave_type)
        new_field = BALANCE_FIELD_MAP.get(instance.leave_type)

        # 1) ถ้าเดิมถูกหักโควตาไว้ (approved + deducted=True) -> คืนให้ก่อน
        if old.deducted and old.status == "approved":
            _apply_refund(bal, old_days, old_field)
            instance.deducted = False  # เคลียร์สถานะ deducted เพื่อให้พิจารณาหักใหม่

        # 2) ถ้าค่าใหม่คือ approved และยังไม่ deducted -> หักใหม่
        if instance.status == "approved" and not instance.deducted:
            if new_field is not None:  # unpaid ไม่มีในแมป -> ไม่หัก
                _apply_deduct(bal, new_days, new_field)
            instance.deducted = True

        bal.save()


# ========= LeaveRequest: เคสสร้างใหม่ (created=True) =========
@receiver(post_save, sender=LeaveRequest)
def handle_leave_deduction_on_create(sender, instance: LeaveRequest, created, **kwargs):
    """
    ครอบกรณี 'สร้างใบคำขอใหม่' ที่มีสถานะ approved ตั้งแต่แรก
    (ปกติ flow คุณจะสร้างเป็น pending จึงไม่เข้าเงื่อนไขนี้บ่อย)
    และเพิ่ม: ส่งอีเมลแจ้ง Approver เมื่อมีคำขอใหม่เสมอ
    """
    if created:
        # หักโควตาทันทีถ้าสร้างมาเป็น approved
        if instance.status == "approved" and not instance.deducted:
            field = BALANCE_FIELD_MAP.get(instance.leave_type)
            if field is not None:  # unpaid ไม่หัก
                with transaction.atomic():
                    bal = _get_or_create_balance_locked(instance.employee)
                    days = _calc_days(instance.start_date, instance.end_date)
                    _apply_deduct(bal, days, field)
                    bal.save()
                    instance.deducted = True
                    instance.save(update_fields=["deducted"])

        # 🔔 ส่งเมลแจ้ง Approver เมื่อมีคำขอใหม่
        try:
            send_leave_request_to_approvers(instance)
        except Exception:
            # อย่าทำให้การบันทึกล้มเหลวเพราะอีเมล—จับไว้เฉยๆ
            pass


# ========= LeaveRequest: แจ้งผู้ยื่นเมื่อ "สถานะเปลี่ยน" =========
@receiver(post_save, sender=LeaveRequest)
def notify_requester_on_status_change(sender, instance: LeaveRequest, created, **kwargs):
    """
    ถ้าไม่ใช่เรคคอร์ดใหม่ และสถานะเปลี่ยนจากเดิม -> ส่งเมลแจ้งผู้ยื่น
    ใช้ค่า _old_status ที่เซ็ตไว้ใน pre_save
    """
    if created:
        return
    old_status = getattr(instance, "_old_status", None)
    if old_status is not None and old_status != instance.status:
        try:
            send_leave_status_to_requester(instance)
        except Exception:
            pass


# ========= LeaveRequest: ลบใบคำขอ (คืนโควตาถ้าเคยหัก) =========
@receiver(post_delete, sender=LeaveRequest)
def handle_leave_refund_on_delete(sender, instance: LeaveRequest, **kwargs):
    """
    ถ้าลบใบคำขอที่อยู่ในสถานะ approved และเคยหักโควตาไว้ (deducted=True)
    ให้คืนโควตากลับ
    """
    if instance.status != "approved" or not instance.deducted:
        return

    field = BALANCE_FIELD_MAP.get(instance.leave_type)
    if field is None:
        # unpaid หรือประเภทที่ไม่หัก
        return

    with transaction.atomic():
        # อาจไม่มี balance (ในทางทฤษฎี) จึง get_or_create
        bal, _ = LeaveBalance.objects.get_or_create(employee=instance.employee)
        bal = LeaveBalance.objects.select_for_update().get(pk=bal.pk)
        days = _calc_days(instance.start_date, instance.end_date)
        _apply_refund(bal, days, field)
        bal.save()
