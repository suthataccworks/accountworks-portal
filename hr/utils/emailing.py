# hr/utils/emailing.py
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings

def send_html_mail(subject, to_emails, template_name, context, from_email=None, cc=None, bcc=None):
    """ส่งอีเมล HTML พร้อมข้อความธรรมดาสำรอง"""
    if not to_emails:
        return 0
    html = render_to_string(template_name, context)
    text = render_to_string("emails/plain_fallback.txt", context)
    msg = EmailMultiAlternatives(
        subject=subject,
        body=text,
        from_email=from_email or settings.DEFAULT_FROM_EMAIL,
        to=to_emails,
        cc=cc or [],
        bcc=bcc or [],
    )
    msg.attach_alternative(html, "text/html")
    return msg.send()
