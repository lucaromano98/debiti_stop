from django.db import models
from django.contrib.auth.models import User


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
    return f"client_{instance.cliente.id}/{filename}"

class DocumentoCliente(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name="documenti")
    file = models.FileField(upload_to=client_directory_path)
    descrizione = models.CharField(max_length=255, blank=True, null=True)
    caricato_il = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Documento di {self.cliente} - {self.file.name}"


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



