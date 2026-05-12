# crm/services.py
from __future__ import annotations
from django.db import transaction
from django.utils import timezone
from django.utils.text import capfirst
import os
from .models import Cliente, Lead, Nota, NotaLead, Notifica, SchedaConsulenza


def _append_block(note: str | None, block: str) -> str:
    note = (note or "").strip()
    block = (block or "").strip()
    if not block:
        return note
    if block in note:
        return note
    sep = "\n\n---\n"
    return f"{note}{sep}{block}" if note else block


def _blocco_contesto_lead(lead: Lead) -> str:
    """Testo da appendere in Cliente.note con metadati non presenti come campi sul Cliente."""
    righe: list[str] = []
    if lead.provenienza:
        righe.append(f"Provenienza lead: {lead.get_provenienza_display()}")
    if lead.stato_operativo:
        righe.append(f"Stato lavorazione (al momento acquisizione): {lead.get_stato_operativo_display()}")
    if lead.motivazione_negativa:
        righe.append(f"Motivazione negativa (lead): {lead.motivazione_negativa}")
    if lead.appuntamento_previsto:
        righe.append(f"Appuntamento previsto (lead): {lead.appuntamento_previsto:%d/%m/%Y %H:%M}")
    if lead.primo_contatto:
        righe.append(f"Primo contatto (lead): {lead.primo_contatto:%d/%m/%Y %H:%M}")
    if not righe:
        return ""
    return "[Contesto da lead]\n" + "\n".join(righe)


def _applica_dati_lead_su_cliente(cliente: Cliente, lead: Lead, *, merge_su_esistente: bool) -> None:
    """Aggiorna il cliente con i dati anagrafici e commerciali del lead."""
    def set_field(name: str, value):
        if merge_su_esistente:
            cur = getattr(cliente, name)
            if cur not in (None, "", []):
                return
        setattr(cliente, name, value)

    set_field("nome", (lead.nome or "").strip() or cliente.nome)
    set_field("cognome", (lead.cognome or "").strip() or cliente.cognome)
    set_field("email", lead.email or None)
    set_field("telefono", lead.telefono or None)
    set_field("creditore_legale", lead.creditore_legale or "")
    set_field("creditore_legale_altro", lead.creditore_legale_altro or None)
    set_field("consulente", lead.consulente)

    blocchi: list[str] = []
    if lead.note_operatori and str(lead.note_operatori).strip():
        blocchi.append("[Note operatori (lead)]\n" + str(lead.note_operatori).strip())
    ctx = _blocco_contesto_lead(lead)
    if ctx:
        blocchi.append(ctx)
    for b in blocchi:
        cliente.note = _append_block(cliente.note, b)

    cliente.stato = "active"


@transaction.atomic
def converti_lead_in_cliente(lead: Lead, user=None) -> Cliente:
    """
    Converte un Lead in Cliente (idempotente se già convertito).

    - Se il lead ha già ``convertito_cliente``, restituisce quel cliente senza duplicare.
    - Altrimenti: dedup su email/telefono (riusa cliente esistente se trovato), altrimenti crea.
    - Copia campi allineati (credito, consulente, note) e le ``NotaLead`` in ``Nota`` sul cliente.
    - Collega le ``SchedaConsulenza`` ancora senza cliente al nuovo cliente.
    """
    if not isinstance(lead, Lead):
        raise TypeError("lead deve essere un'istanza di Lead")

    lead = Lead.objects.select_for_update().get(pk=lead.pk)

    if lead.convertito and lead.convertito_cliente_id:
        return Cliente.objects.get(pk=lead.convertito_cliente_id)

    # 1) dedup: email o telefono
    cliente = None
    if lead.email:
        cliente = Cliente.objects.filter(email__iexact=lead.email).order_by("id").first()
    if not cliente and lead.telefono:
        cliente = Cliente.objects.filter(telefono=lead.telefono).order_by("id").first()

    merge = bool(cliente)
    if not cliente:
        cliente = Cliente(
            nome=(lead.nome or "").strip() or "—",
            cognome=(lead.cognome or "").strip() or "—",
            email=lead.email or None,
            telefono=lead.telefono or None,
            stato="active",
        )

    _applica_dati_lead_su_cliente(cliente, lead, merge_su_esistente=merge)
    cliente.save()

    for nl in NotaLead.objects.filter(lead=lead).order_by("creato_il"):
        autore = nl.autore.get_username() if nl.autore_id else ""
        Nota.objects.create(
            cliente=cliente,
            autore=autore,
            testo=f"[Importata da lead #{lead.pk} · {nl.creato_il:%d/%m/%Y %H:%M}]\n{nl.testo}",
        )

    SchedaConsulenza.objects.filter(lead=lead, cliente__isnull=True).update(cliente=cliente)

    lead.convertito = True
    lead.convertito_il = timezone.now()
    lead.convertito_da = user if user and getattr(user, "is_authenticated", False) else None
    lead.convertito_cliente = cliente
    lead.stato = "positivo"
    lead.save(
        update_fields=[
            "convertito",
            "convertito_il",
            "convertito_da",
            "convertito_cliente",
            "stato",
        ]
    )

    return cliente


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