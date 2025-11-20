# crm/templatetags/dict_extras.py
import os
from django import template
register = template.Library()

@register.filter
def get_item(d, key):
    try:
        return d.get(key, [])
    except Exception:
        return []


@register.filter
def pretty_filename(path: str) -> str:
    """
    Da 'client_2/contratti/1763651206_ci-domenico-ferraiuolo.jpg'
    torna 'CI DOMENICO FERRAIUOLO.JPG'
    """
    if not path:
        return ""

    base = os.path.basename(path)  # es: '1763651206_ci-domenico-ferraiuolo.jpg'
    name, ext = os.path.splitext(base)

    # rimuovo eventuale prefisso numerico tipo '1763651206_'
    parts = name.split("_", 1)
    if len(parts) == 2 and parts[0].isdigit():
        name = parts[1]

    # tratto -> spazio
    name = name.replace("-", " ")

    # tutto maiuscolo + estensione
    return f"{name}{ext}".upper()
