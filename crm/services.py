# crm/services.py
from django.db import transaction
from django.utils import timezone

def converti_lead_in_cliente(lead, user):
    """
    Converte un Lead in Cliente in modo idempotente e tracciato:
    - Se esiste già un Cliente (email o telefono), lo riutilizza.
    - Se non esiste, lo crea.
    - Trasferisce eventuali note_operatori come Nota del Cliente (se hai il modello Nota).
    - Marca il lead come convertito e archiviato, con chi/quando/cliente di destinazione.
    Ritorna il Cliente.
    """
    from .models import Cliente, Nota  # import locale per evitare cicli

    with transaction.atomic():
        # 1) Trova o crea cliente
        cliente = None
        if lead.email:
            cliente = Cliente.objects.filter(email__iexact=lead.email).first()
        if not cliente and lead.telefono:
            cliente = Cliente.objects.filter(telefono=lead.telefono).first()

        if not cliente:
            cliente = Cliente.objects.create(
                nome=lead.nome,
                cognome=lead.cognome,
                email=lead.email,
                telefono=lead.telefono,
                stato="active",
                note=lead.note_operatori or "",
            )

        # 2) Porta le note del lead come Nota cliente (opzionale ma utile)
        if lead.note_operatori:
            Nota.objects.create(
                cliente=cliente,
                autore_nome=user.get_username(),
                testo=f"[Da LEAD] {lead.note_operatori}",
            )

        # 3) Marca il lead come convertito/archiviato (no delete fisica)
        lead.convertito = True
        lead.convertito_il = timezone.now()
        lead.convertito_da = user
        lead.convertito_cliente = cliente
        lead.is_archiviato = True
        lead.stato = "positivo"
        lead.save(update_fields=[
            "convertito", "convertito_il", "convertito_da",
            "convertito_cliente", "is_archiviato", "stato"
        ])

        return cliente

