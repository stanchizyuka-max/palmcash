"""
Custom template filters for audit views
"""
from django import template

register = template.Library()


@register.filter
def replace_underscore(value):
    """Replace underscores with spaces"""
    if value:
        return str(value).replace('_', ' ')
    return value


@register.filter
def action_display(value):
    """Convert action name to display format"""
    if value:
        return str(value).replace('_', ' ').title()
    return value
