# crea la Notifica per la Sidebar
from .models import Notifica

def notifiche_sidebar(request):
    """
    Espone:
      - notifiche_sidebar: le ultime 10 notifiche ordinate per data
      - notifiche_unread_count: conteggio non lette
    """
    if not request.user.is_authenticated:
        return {}
    try:
        qs = Notifica.objects.order_by("-created_at")[:10]
        unread = Notifica.objects.filter(is_read=False).count()
    except Exception:
        qs = []
        unread = 0

    return {
        "notifiche_sidebar": qs,
        "notifiche_unread_count": unread,
    }