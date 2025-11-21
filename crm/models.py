# crm/models.py
from __future__ import annotations

import os
import time
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.db import models
from django.utils.text import slugify


# --- CONSULENTI ---
class Consulente(models.Model):
    nome = models.CharField(max_length=120, unique=True)
    is_active = models.BooleanField(default=True)
    creato_il = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["nome"]

    def __str__(self) -> str:
        return self.nome


# --- CLIENTI ---
class Cliente(models.Model):
    STATUS_CHOICES = (
        ("active", "Attivo"),
        ("inactive", "Non Attivo"),
        ("legal", "Legale"),
        ("istanza", "Istanza di visibilità"),
        ("stragiudiziale", "Stragiudiziale"),
    )

    nome = models.CharField(max_length=100)
    cognome = models.CharField(max_length=100)
    email = models.EmailField(blank=True, null=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    residenza = models.TextField(blank=True, null=True)
    esperienza_finanziaria = models.TextField(blank=True, null=True)
    visure = models.TextField(blank=True, null=True)  # mantengo per compatibilità
    note = models.TextField(blank=True, null=True)

    stato = models.CharField(max_length=50, choices=STATUS_CHOICES, default="active", db_index=True)
    data_creazione = models.DateTimeField(auto_now_add=True)

    # Flag istanza
    istanza_visibilita = models.BooleanField(default=False, verbose_name="Istanza di visibilità")
    documenti_inviati = models.BooleanField(default=False)
    perizia_inviata = models.BooleanField(default=False)

    def __str__(self) -> str:
        return f"{self.nome} {self.cognome}"


# --- DOCUMENTI ---
def client_directory_path(instance: "DocumentoCliente", filename: str) -> str:
    """
    media/client_<id>/<categoria>/<safe_filename>
    """
    cliente = instance.cliente
    base, ext = os.path.splitext(filename)
    safe_name = f"{int(time.time())}_{slugify(base)}{ext.lower()}"
    return f"client_{cliente.id}/{instance.categoria}/{safe_name}"


class DocumentoCliente(models.Model):
    class Categoria(models.TextChoices):
        ANAGRAFICI        = "anagrafici",          "Documenti anagrafici"
        SCHED_CON         = "scheda_consulenza",   "Scheda Consulenza"
        CONTRATTI         = "contratti",           "Stragiudiziario"
        VISURE            = "visure",              "Visure"
        RISC_ISTANZA      = "riscontro_istanza",   "Riscontro Istanza"
        PROP_TRANSATTIVA  = "proposta_transattiva","Proposta transattiva"
        DECR_INGIUNTIVO   = "decreto_ingiuntivo",  "Decreto ingiuntivo"
        PRECETTO          = "precetto",            "Precetto"
        PIGNORAMENTO      = "pignoramento",        "Pignoramento"
        MANDATO           = "mandato",             "Mandato"
        OPPOSIZIONE       = "opposizione",         "Opposizione"
        PREVENTIVI        = "preventivi",          "Preventivi"
        ALTRO             = "altro",               "Altro"
        PROVVEDIMENTI     = "provvedimento",       "Provvedimenti"
        RICHI_ISTANZA     = "richiesta_istanza",   "Richiesta Istanza"
        RECLAMO           = "reclamo",             "Reclamo"
        

        # --- legacy per compatibilità con dati già salvati ---
        PRATICHE_LEGACY   = "pratiche",            "LEGACY – Pratiche"
        LEGALI_LEGACY     = "legali",              "LEGACY – Atti legali"

    cliente = models.ForeignKey("Cliente", on_delete=models.CASCADE, related_name="documenti")
    categoria = models.CharField(
        max_length=32,
        choices=Categoria.choices,
        default=Categoria.ANAGRAFICI,
        db_index=True,
    )
    file = models.FileField(
        upload_to=client_directory_path,
        validators=[FileExtensionValidator(allowed_extensions=["pdf", "png", "jpg", "jpeg"])],
    )
    descrizione = models.CharField(max_length=255, blank=True, null=True)
    caricato_il = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-caricato_il",)
        indexes = [
            models.Index(fields=["cliente", "categoria"]),
            models.Index(fields=["cliente", "caricato_il"]),
        ]

    def clean(self):
        super().clean()
        legacy = {
            self.Categoria.PRATICHE_LEGACY,
            self.Categoria.LEGALI_LEGACY,
        }
        # blocca NUOVE creazioni con categorie legacy
        if self.pk is None and self.categoria in legacy:
            raise ValidationError("Categoria legacy non utilizzabile per nuovi caricamenti.")

    def __str__(self) -> str:
        return f"Documento {self.id} · {self.categoria} · {self.cliente}"


# --- PRATICHE ---
class Pratiche(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name="pratiche")
    titolo = models.CharField(max_length=200, blank=True, null=True)
    descrizione = models.TextField(blank=True, null=True)
    importo = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    pratica_attiva = models.BooleanField(default=True)
    data_creazione = models.DateTimeField(auto_now_add=True)
    aggiornata_il = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"Pratica #{self.id} - {self.cliente.nome} {self.cliente.cognome}"


# --- PROFILO UTENTE ---
class ProfiloUtente(models.Model):
    RUOLI = (
        ("admin", "Admin"),
        ("operatore", "Operatore"),
        ("legale", "Legale"),
    )
    utente = models.OneToOneField(User, on_delete=models.CASCADE)
    ruolo = models.CharField(max_length=20, choices=RUOLI, default="operatore")

    def __str__(self) -> str:
        return f"{self.utente.username} - {self.ruolo}"


# --- NOTE OPERATORI ---
class Nota(models.Model):
    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.CASCADE,
        related_name="note_entries",
    )
    # nuovo nome Python, stessa colonna DB di prima
    autore = models.CharField(max_length=100, db_column='autore_nome', blank=True)
    testo = models.TextField()
    creata_il = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Nota {self.id} per {self.cliente} – {self.autore}"


# --- LEAD ---
class Lead(models.Model):
    class Provenienza(models.TextChoices):
        TIKTOK = "tiktok", "TikTok"
        META = "meta", "Meta (Facebook/Instagram)"
        GOOGLE = "google", "Google"
        PASSAPAROLA = "passaparola", "Passaparola"

    STATO_CHOICES = (
        ("in_corso", "In corso"),
        ("negativo", "Esito negativo"),
        ("positivo", "Esito positivo"),
    )

    # Anagrafica base
    nome = models.CharField(max_length=100)
    cognome = models.CharField(max_length=100)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)

    # Stato/Fasi
    stato = models.CharField(max_length=20, choices=STATO_CHOICES, default="in_corso", db_index=True)
    appuntamento_previsto = models.DateTimeField(blank=True, null=True)
    motivazione_negativa = models.TextField(blank=True, null=True)
    note_operatori = models.TextField(blank=True, null=True)

    # Nuovi campi
    provenienza = models.CharField(
        max_length=20,
        choices=Provenienza.choices,
        blank=True,
        default="",
        help_text="Da quale canale/social proviene il lead",
    )
    consulente = models.ForeignKey(
        Consulente,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="leads",
        help_text="Chi farà la consulenza",
    )
    primo_contatto = models.DateTimeField(null=True, blank=True, help_text="Data/ora del primo contatto")

    # Audit/Conversione/Archiviazione
    convertito = models.BooleanField(default=False)
    convertito_il = models.DateTimeField(null=True, blank=True)
    convertito_da = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="lead_convertiti",
    )
    convertito_cliente = models.ForeignKey(
        "Cliente",
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="da_lead",
    )
    is_archiviato = models.BooleanField(default=False)
    creato_il = models.DateTimeField(auto_now_add=True)

    # Flag operativi
    consulenza_effettuata = models.BooleanField(default=False)
    no_risposta = models.BooleanField(default=False)
    messaggio_inviato = models.BooleanField(default=False)
    in_acquisizione = models.BooleanField(default=False)
    richiamare_il = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["stato"]),
            models.Index(fields=["convertito", "is_archiviato"]),
        ]

    def __str__(self) -> str:
        return f"{self.nome} {self.cognome} ({self.get_stato_display()})"


# --- NOTIFICHE ---
UserModel = get_user_model()

class Notifica(models.Model):
    class Tipo(models.TextChoices):
        DOCUMENTO = "documento", "Documento"
        GENERICA  = "generica",  "Generica"

    tipo = models.CharField(max_length=20, choices=Tipo.choices, default=Tipo.GENERICA)

    actor = models.ForeignKey(
        UserModel, null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="notifiche_generate"
    )
    cliente = models.ForeignKey(
        "crm.Cliente", null=True, blank=True,
        on_delete=models.CASCADE,
        related_name="notifiche"
    )
    documento = models.ForeignKey(
        "crm.DocumentoCliente", null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="notifiche"
    )

    testo = models.CharField(max_length=500, blank=True)
    payload = models.JSONField(blank=True, null=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        base = self.testo or ""
        return f"[{self.get_tipo_display()}] {base}"


# --- SCHEDA DI CONSULENZA ---
class SchedaConsulenza(models.Model):
    cliente = models.ForeignKey(
        Cliente, null=True, blank=True,
        on_delete=models.CASCADE,
        related_name="schede_consulenza"
    )
    lead = models.ForeignKey(
        Lead, null=True, blank=True,
        on_delete=models.CASCADE,
        related_name="schede_consulenza"
    )
    compilata_da = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL
    )
    created_at = models.DateTimeField(auto_now_add=True)

    # MVP – campi semplici
    obiettivo = models.CharField(max_length=255, blank=True)
    occupazione = models.CharField(max_length=120, blank=True)
    esposizione_patrimoniale = models.TextField(blank=True)
    esposizione_finanziaria  = models.TextField(blank=True)
    esposizione_totale = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    ha_cqs = models.BooleanField(default=False)            # cessione del quinto
    ha_equitalia = models.BooleanField(default=False)
    note = models.TextField(blank=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self) -> str:
        target = (
            f"Cliente #{self.cliente_id}" if self.cliente_id
            else f"Lead #{self.lead_id}" if self.lead_id
            else "Senza target"
        )
        return f"SchedaConsulenza({target})"
