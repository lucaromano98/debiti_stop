# crm/templatetags/qparams.py
from django import template

register = template.Library()

@register.simple_tag(takes_context=True)
def qurl(context, **updates):
    request = context["request"]
    params = request.GET.copy()
    for k, v in updates.items():
        if v in (None, ""):
            params.pop(k, None)
        else:
            params[k] = v
    query = params.urlencode()
    path = request.path
    return f"{path}?{query}" if query else path
