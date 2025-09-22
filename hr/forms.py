# hr/forms.py
from django import forms
from django.utils import timezone
from .models import LeaveRequest, Holiday, Announcement  # ใช้งาน LeaveRequest + (ตัวอื่นยังอยู่ได้)

class LeaveRequestForm(forms.ModelForm):
    class Meta:
        model = LeaveRequest
        fields = ["leave_type", "start_date", "end_date", "reason"]
        widgets = {
            "leave_type": forms.Select(attrs={"class": "form-select"}),
            "start_date": forms.DateInput(
                attrs={"type": "date", "class": "form-control", "id": "id_start_date"}
            ),
            "end_date": forms.DateInput(
                attrs={"type": "date", "class": "form-control", "id": "id_end_date"}
            ),
            "reason": forms.Textarea(
                attrs={
                    "rows": 6,
                    "class": "form-control",
                    "id": "id_reason",
                    "maxlength": "1000",
                    "placeholder": "รายละเอียดสั้น ๆ (ถ้ามี)",
                }
            ),
        }

    # --- Validation เพิ่มเติมฝั่งเซิร์ฟเวอร์ ---
    def clean(self):
        cleaned = super().clean()
        start = cleaned.get("start_date")
        end = cleaned.get("end_date")
        today = timezone.localdate()

        if start and start < today:
            self.add_error("start_date", "ห้ามเลือกย้อนหลังก่อนวันนี้")
        if start and end and end < start:
            self.add_error("end_date", "End date ต้องเป็นวันเดียวกันหรือหลังจาก Start date")

        return cleaned


# (คงไว้สำหรับฟอร์มอื่นที่คุณใช้อยู่)
class HolidayForm(forms.ModelForm):
    class Meta:
        from .models import Holiday
        model = Holiday
        fields = ["name", "date", "is_public"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
        }

class AnnouncementForm(forms.ModelForm):
    class Meta:
        from .models import Announcement
        model = Announcement
        fields = ["title", "content", "is_pinned", "is_active"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "content": forms.Textarea(attrs={"class": "form-control", "rows": 8}),
        }
