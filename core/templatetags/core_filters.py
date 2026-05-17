from django import template


register = template.Library()


@register.filter
def friendly_number(value):
    try:
        value = int(value)
    except (TypeError, ValueError):
        return "0"
    if value >= 1000:
        return f"{value // 1000}K+"
    if value >= 100:
        return f"{value}+"
    return str(value)
