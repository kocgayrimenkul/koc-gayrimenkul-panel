from django import template
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter
def percentage(value, total):
    """
    Verilen değerin toplam içindeki yüzdesini hesaplar
    Örnek: {{ 5|percentage:20 }} -> %25
    """
    try:
        if int(total) > 0:
            percent = float(value) / float(total) * 100
            return f"%{percent:.1f}"
        return "%0"
    except (ValueError, ZeroDivisionError):
        return "%0" 