from django.db import models
from django.contrib.auth.models import User
from django.core.validators import FileExtensionValidator
from django.utils.text import slugify
from django.conf import settings
import os 
import time 



# --- CLIENTI ---
class Cliente(models.Model):
    STATUS_CHOICES = (
        ("active", "Attivo"),
        ("inactive", "Non Attivo"),
        ("legal", "Legale"),
    )

    nome = models.CharField(max_length=100)
    cognome = models.CharField(max_length=100)
    email = models.EmailField(blank=True, null=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    residenza = models.TextField(blank=True, null=True)
    esperienza_finanziaria = models.TextField(blank=True, null=True)
    visure = models.TextField(blank=True, null=True)
    note = models.TextField(blank=True, null=True)
    stato = models.CharField(max_length=10, choices=STATUS_CHOICES, default="active")
    data_creazione = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nome} {self.cognome}"


# --- DOCUMENTI ---

def client_directory_path(instance, filename):
    # media/client_<id>/<categoria>/<filename>
    cliente = instance.cliente
    slug = slugify(f"{cliente.nome} - {cliente.cognome}") or f"cliente-{cliente.id}"
    base, ext = os.path.splitext(filename)
    safe_name = f"{int(time.time())}_{slugify(base)}{ext.lower()}"
    return f"client_{instance.cliente.id}/{instance.categoria}/{filename}"

class DocumentoCliente(models.Model):
    CATEGORIE = (
        ("anagrafici", "Documenti anagrafici"),
        ("pratiche", "Pratiche"),
        ("legali", "Atti legali"),
    )

    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name="documenti")
    categoria = models.CharField(max_length=20, choices=CATEGORIE, default="anagrafici")
    file = models.FileField(
        upload_to=client_directory_path,
        validators=[FileExtensionValidator(allowed_extensions=["pdf", "png", "jpg", "jpeg"])]
    )
    descrizione = models.CharField(max_length=255, blank=True, null=True)
    caricato_il = models.DateTimeField(auto_now_add=True)


# --- PRATICHE ---
class Pratiche(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name="pratiche")
    titolo = models.CharField(max_length=200, blank=True, null=True)
    descrizione = models.TextField(blank=True, null=True)
    importo = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    pratica_attiva = models.BooleanField(default=True)
    data_creazione = models.DateTimeField(auto_now_add=True)
    aggiornata_il = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Pratica #{self.id} - {self.cliente.nome} {self.cliente.cognome}"


# --- PROFILO UTENTE ---
class ProfiloUtente(models.Model):
    RUOLI = (
        ('admin', 'Admin'),
        ('operatore', 'Operatore'),
    )

    utente = models.OneToOneField(User, on_delete=models.CASCADE)
    ruolo = models.CharField(max_length=20, choices=RUOLI, default='operatore')

    def __str__(self):
        return f"{self.utente.username} - {self.ruolo}"
    

# --- NOTES OPERATORI ---

class Nota(models.Model):
    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.CASCADE,
        related_name="note_entries"   # NON deve essere "note"
    )
    autore_nome = models.CharField(max_length=100)
    testo = models.TextField()
    creata_il = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Nota {self.id} per {self.cliente} – {self.autore_nome}"



# --- LEAD ---

class Lead(models.Model):
    STATO_CHOICES = (
        ("in_corso", "In corso"),
        ("negativo", "Esito negativo"),
        ("positivo", "Esito positivo"),
    )

    nome = models.CharField(max_length=100)
    cognome = models.CharField(max_length=100)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)

    stato = models.CharField(max_length=20, choices=STATO_CHOICES, default="in_corso")
    appuntamento_previsto = models.DateTimeField(blank=True, null=True)
    motivazione_negativa = models.TextField(blank=True, null=True)

    note_operatori = models.TextField(blank=True, null=True)

    # --- AUDIT/Conversione/Archiviazione ---
    convertito = models.BooleanField(default=False)
    convertito_il = models.DateTimeField(null=True, blank=True)
    convertito_da = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="lead_convertiti"
    )
    convertito_cliente = models.ForeignKey(
        "Cliente", null=True, blank=True, on_delete=models.SET_NULL, related_name="da_lead"
    )
    is_archiviato = models.BooleanField(default=False)

    creato_il = models.DateTimeField(auto_now_add=True)

     # NUOVI CAMPI
    consulenza_effettuata = models.BooleanField(default=False)   # spunta se la consulenza è stata fatta
    no_risposta = models.BooleanField(default=False)             # il lead non risponde
    messaggio_inviato = models.BooleanField(default=False)       # se no_risposta=True, spunta quando invii messaggio

    in_acquisizione = models.BooleanField(default=False)         # per separare i “clienti in acquisizione”

    richiamare_il = models.DateTimeField(null=True, blank=True) # data/ora per richiamare

    class Meta:
        indexes = [
            models.Index(fields=["stato"]),
            models.Index(fields=["convertito", "is_archiviato"]),
        ]

    def __str__(self):
        return f"{self.nome} {self.cognome} ({self.get_stato_display()})"

