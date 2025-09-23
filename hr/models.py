from django.db import models
from django.contrib.auth.models import User


class Team(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Employee(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    position = models.CharField(max_length=100, blank=True, default="")
    team = models.ForeignKey(
        Team, null=True, blank=True, on_delete=models.SET_NULL, related_name="members"
    )
    is_team_lead = models.BooleanField(default=False)

    class Meta:
        ordering = ["user__username"]
        # constraints = [
        #     models.UniqueConstraint(
        #         fields=["team"],
        #         condition=models.Q(is_team_lead=True),
        #         name="unique_team_lead_per_team",
        #     )
        # ]

    def __str__(self):
        return self.user.username


class LeaveBalance(models.Model):
    employee = models.OneToOneField(
        Employee, on_delete=models.CASCADE, related_name="balance"
    )
    annual_leave = models.PositiveIntegerField(default=10)
    sick_leave = models.PositiveIntegerField(default=30)
    personal_leave = models.PositiveIntegerField(default=5)
    # ✅ เพิ่มเติมสำหรับประเภทใหม่ (กำหนดนโยบายได้ตามใจ)
    relax_leave = models.PositiveIntegerField(default=0)
    maternity_leave = models.PositiveIntegerField(default=0)
    other_leave = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"Balance({self.employee.user.username})"


class LeaveRequest(models.Model):
    TYPE_CHOICES = [
        ("annual", "ลาพักร้อน"),
        ("sick", "ลาป่วย"),
        ("personal", "ลากิจ"),
        ("relax", "ลาพักผ่อนพิเศษ"),
        ("unpaid", "ลาไม่รับค่าตอบแทน"),
        ("maternity", "ลาคลอด"),
        ("other", "ลาอื่นๆ"),
    ]
    STATUS_CHOICES = [
        ("pending", "pending"),
        ("approved", "approved"),
        ("rejected", "rejected"),
    ]

    employee = models.ForeignKey(
        Employee, on_delete=models.CASCADE, related_name="requests"
    )
    leave_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.TextField(blank=True, default="")
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="pending"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    # กันตัดโควต้าซ้ำ (ใช้ร่วมกับ signals)
    deducted = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.employee.user.username} {self.leave_type} {self.status}"


# ---- วันหยุดบริษัท ----
class Holiday(models.Model):
    name = models.CharField(max_length=200)
    date = models.DateField(db_index=True)
    is_public = models.BooleanField(default=True)

    class Meta:
        ordering = ["date"]
        unique_together = [("name", "date")]

    def __str__(self):
        return f"{self.name} ({self.date})"


# ---- ประกาศบริษัท ----
class Announcement(models.Model):
    title = models.CharField(max_length=255)
    content = models.TextField()
    is_pinned = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    published_at = models.DateTimeField(null=True, blank=True, db_index=True)
    created_by = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL, related_name="announcements"
    )

    class Meta:
        ordering = ["-is_pinned", "-published_at", "-id"]

    def __str__(self):
        return self.title
