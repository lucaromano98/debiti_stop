# crm/services.py
from __future__ import annotations
from django.db import transaction
from django.utils import timezone
from django.utils.text import capfirst
import os
from .models import Cliente, Lead, Notifica

@transaction.atomic
def converti_lead_in_cliente(lead: Lead, user=None) -> Cliente:
    """
    Converte un Lead in Cliente (idempotente):
    - se trova un Cliente con stessa email o telefono, riusa quello
    - altrimenti ne crea uno nuovo
    - collega il lead al cliente e marca il lead come convertito
    """
    if not isinstance(lead, Lead):
        raise TypeError("lead deve essere un'istanza di Lead")

    # 1) dedup semplice: email o telefono
    cliente = None
    if lead.email:
        cliente = Cliente.objects.filter(email__iexact=lead.email).order_by("id").first()
    if not cliente and lead.telefono:
        cliente = Cliente.objects.filter(telefono=lead.telefono).order_by("id").first()

    # 2) crea se non trovato
    if not cliente:
        cliente = Cliente.objects.create(
            nome=lead.nome or "",
            cognome=lead.cognome or "",
            email=lead.email or None,
            telefono=lead.telefono or None,
            stato="active",  # oppure "inactive" se preferisci
        )

    # 3) marca lead come convertito e collega
    lead.convertito = True
    lead.convertito_il = timezone.now()
    lead.convertito_da = user if user and getattr(user, "is_authenticated", False) else None
    lead.convertito_cliente = cliente
    lead.stato = "positivo"
    lead.save(update_fields=["convertito", "convertito_il", "convertito_da", "convertito_cliente", "stato"])

    return cliente

# crm/services.py
def notifica_documento_caricato(
    *, 
    actor=None, 
    cliente=None, 
    documento=None,       # può essere None nei caricamenti multipli
    count: int = 1, 
    categoria_label: str | None = None,
    subtitle: str | None = None,  # sottotitolo/descrizione opzionale
    documento_ids: list[int] | None = None,  # ids multipli facoltativi
):
    # Nome utente
    actor_name = None
    if actor is not None:
        fn = getattr(actor, "get_full_name", lambda: "")() or ""
        actor_name = fn.strip() or getattr(actor, "username", None)
    actor_name = actor_name or "Qualcuno"

    # Cliente
    cli_label = None
    if cliente is not None:
        base = f"{getattr(cliente, 'nome', '')} {getattr(cliente, 'cognome', '')}".strip()
        cli_label = base or f"Cliente #{getattr(cliente, 'pk', 'sconosciuto')}"
    cli_label = cli_label or "cliente sconosciuto"

    # Categoria (se non passata, prendo dal documento)
    if categoria_label is None and documento is not None and hasattr(documento, "get_categoria_display"):
        categoria_label = documento.get_categoria_display()

    # Parte "N file"
    file_part = "un file" if count == 1 else f"{count} file"
    cat_part = f" ({categoria_label})" if categoria_label else ""

    testo = f"{actor_name} ha caricato {file_part}{cat_part} in {cli_label}"

    try:
        Notifica.objects.create(
            tipo=Notifica.Tipo.DOCUMENTO,
            actor=actor,
            cliente=cliente,
            documento=documento,  # può restare None per i batch
            testo=testo,
            payload={
                "count": count,
                "subtitle": subtitle,
                "documento_id": getattr(documento, "id", None),
                "documento_ids": documento_ids or [],
            },
        )
    except Exception:
        # mai bloccare il flusso per una notifica
        pass