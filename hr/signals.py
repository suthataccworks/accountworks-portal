# hr/signals.py
from django.db.models.signals import pre_save, post_delete
from django.dispatch import receiver
from django.db import transaction

from .models import LeaveRequest, LeaveBalance


def _days(lr: LeaveRequest) -> int:
    """จำนวนวันแบบรวมวันต้น-วันท้าย (inclusive)"""
    return (lr.end_date - lr.start_date).days + 1


def _apply(balance: LeaveBalance, leave_type: str, delta: int) -> None:
    """
    ปรับยอดคงเหลือของ balance ตามประเภทลา
    delta เป็นจำนวนวันที่จะ + / - (ค่าลบ = ตัดโควต้า)
    """
    if leave_type == "annual":
        balance.annual_leave = max(0, balance.annual_leave + delta)
    elif leave_type == "sick":
        balance.sick_leave = max(0, balance.sick_leave + delta)
    elif leave_type == "personal":
        balance.personal_leave = max(0, balance.personal_leave + delta)


@receiver(pre_save, sender=LeaveRequest)
def leave_request_pre_save(sender, instance: LeaveRequest, **kwargs):
    """
    ตัดโควต้าเฉพาะตอนเปลี่ยนสถานะเป็น approved ครั้งแรก (deducted=False → True)
    และ 'คืน' โควต้าถ้าสถานะเปลี่ยนออกจาก approved (และเคยตัดแล้ว)
    """
    # ถ้ายังไม่มีพนักงาน/ยังไม่มี pk (สร้างใหม่) -> ยังไม่ทำอะไรจนกว่าจะมีการอนุมัติ
    if not instance.employee_id:
        return
    if not instance.pk:
        return

    # ensure balance เสมอ
    balance, _ = LeaveBalance.objects.get_or_create(employee=instance.employee)

    try:
        prev = LeaveRequest.objects.get(pk=instance.pk)
    except LeaveRequest.DoesNotExist:
        return

    became_approved = prev.status != "approved" and instance.status == "approved"
    left_approved = prev.status == "approved" and instance.status != "approved"

    days = _days(instance)

    with transaction.atomic():
        if became_approved and not instance.deducted:
            _apply(balance, instance.leave_type, -days)  # ตัดโควต้า
            balance.save(update_fields=["annual_leave", "sick_leave", "personal_leave"])
            instance.deducted = True

        elif left_approved and instance.deducted:
            _apply(balance, prev.leave_type, +days)  # คืนโควต้า
            balance.save(update_fields=["annual_leave", "sick_leave", "personal_leave"])
            instance.deducted = False


@receiver(post_delete, sender=LeaveRequest)
def leave_request_post_delete(sender, instance: LeaveRequest, **kwargs):
    """
    ถ้าลบคำขอที่เคยอนุมัติแล้ว (และเคยตัดไปแล้ว) -> คืนโควต้าให้
    """
    if (
        instance.employee_id
        and instance.status == "approved"
        and instance.deducted
    ):
        try:
            balance = LeaveBalance.objects.get(employee=instance.employee)
        except LeaveBalance.DoesNotExist:
            return
        _apply(balance, instance.leave_type, +_days(instance))
        balance.save(update_fields=["annual_leave", "sick_leave", "personal_leave"])
