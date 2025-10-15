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

def notifica_documento_caricato(*, actor, cliente, documento):
    """
    Crea una notifica quando viene caricato un documento.
    - `actor`: User che ha caricato
    - `cliente`: Cliente destinatario
    - `documento`: istanza di DocumentoCliente appena salvata
    """
    # Label "umana" della categoria (usa choices se disponibili)
    if hasattr(documento, "get_categoria_display"):
        categoria_label = documento.get_categoria_display()
    else:
        categoria_label = capfirst(str(getattr(documento, "categoria", "")))

    # Nome leggibile del file/documento
    doc_name = (
        getattr(documento, "descrizione", None)
        or (os.path.basename(documento.file.name) if getattr(documento, "file", None) else "Documento")
    )

    # Nome dell’utente che ha caricato
    actor_name = (getattr(actor, "get_full_name", lambda: "")() or getattr(actor, "username", "Utente"))

    testo = f"{actor_name} ha aggiunto un documento in {categoria_label} al cliente: {cliente.nome} {cliente.cognome} ({doc_name})."

    # Se hai l’enum Notifica.Tipo, usa quello; altrimenti metti la stringa "documento"
    tipo_val = getattr(getattr(Notifica, "Tipo", None), "DOCUMENTO", "documento")

    Notifica.objects.create(
        tipo=tipo_val,
        cliente=cliente,
        actor=actor,
        testo=testo,
        payload={
            "doc_id": documento.id,
            "categoria": getattr(documento, "categoria", None),
            "documento_nome": doc_name,
            "cliente_id": cliente.id,
        },
    )