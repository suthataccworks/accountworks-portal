# hr/templatetags/aw_tags.py
from django import template

register = template.Library()

@register.filter
def has_group(user, group_name: str):
    if not getattr(user, "is_authenticated", False):
        return False
    return user.groups.filter(name__iexact=group_name).exists()
