# crea la Notifica per la Sidebar
from .models import Notifica


# Slug URL -> (slug, label) per sidebar Lead – positivi sopra, negativi sotto, "Attività non di competenza" ultima
SIDEBAR_LEAD_STATI = [
    ("nuovo", "Nuovo"),
    ("no-risposta", "Senza risposta"),
    ("segreteria", "Segreteria"),
    ("ha-staccato-lui", "Ha staccato lui"),
    ("consulenza-effettuata", "Consulenza effettuata"),
    ("attesa-contatti", "Attesa contatti"),
    ("non-contattare", "Non contattare"),
    ("numero-errato", "Numero errato"),
    ("blocco-chiamate", "Blocco chiamate"),
    ("cliente-non-interessato", "Cliente non interessato"),
    ("non-competenza", "Attività non di competenza"),
]


def notifiche_sidebar(request):
    """
    Espone:
      - notifiche_sidebar: le ultime 10 notifiche ordinate per data
      - notifiche_unread_count: conteggio non lette
    """
    if not request.user.is_authenticated:
        return {"sidebar_lead_stati": SIDEBAR_LEAD_STATI}
    try:
        qs = Notifica.objects.order_by("-created_at")[:10]
        unread = Notifica.objects.filter(is_read=False).count()
    except Exception:
        qs = []
        unread = 0

    return {
        "notifiche_sidebar": qs,
        "notifiche_unread_count": unread,
        "sidebar_lead_stati": SIDEBAR_LEAD_STATI,
    }