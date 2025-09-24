# hr/utils/emailing.py
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.template import TemplateDoesNotExist
from django.utils.html import strip_tags
from django.conf import settings


def send_html_mail(
    subject: str,
    to_emails: list[str],
    template_name: str,
    context: dict,
    from_email: str | None = None,
    cc: list[str] | None = None,
    bcc: list[str] | None = None,
) -> int:
    """
    ส่งอีเมล HTML พร้อมข้อความธรรมดาสำรอง
    - ถ้า template plain_fallback.txt ไม่มี: จะ fallback เป็น strip_tags จาก HTML
    - จะ raise error ถ้า SMTP ผิด (เราไม่ได้ใช้ fail_silently เพื่อให้เห็นปัญหาใน logs)
    """
    if not to_emails:
        return 0

    html = render_to_string(template_name, context or {})

    # พยายามใช้ plain fallback ถ้ามี
    try:
        text = render_to_string("emails/plain_fallback.txt", context or {})
    except TemplateDoesNotExist:
        text = strip_tags(html)

    msg = EmailMultiAlternatives(
        subject=subject,
        body=text,
        from_email=from_email or getattr(settings, "DEFAULT_FROM_EMAIL", None),
        to=to_emails,
        cc=cc or [],
        bcc=bcc or [],
    )
    msg.attach_alternative(html, "text/html")
    # .send() จะคืนจำนวนผู้รับที่ส่งสำเร็จ (int) หรือ raise error ถ้า SMTP ผิด
    return msg.send()
