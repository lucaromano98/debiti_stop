from django.contrib import admin
from .models import Cliente, DocumentoCliente, Pratiche, ProfiloUtente, Lead, Consulente, NotaLead

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ("nome", "cognome", "email", "telefono", "stato", "fase", "data_creazione")
    search_fields = ("nome", "cognome", "email", "telefono")
    list_filter = ("stato", "fase", "data_creazione")

@admin.register(DocumentoCliente)
class DocumentoClienteAdmin(admin.ModelAdmin):
    list_display = ("cliente", "file", "descrizione", "caricato_il")
    search_fields = ("cliente__nome", "cliente__cognome", "descrizione")

@admin.register(Pratiche)
class PraticheAdmin(admin.ModelAdmin):
    list_display = ("cliente", "titolo", "importo", "pratica_attiva", "data_creazione")
    search_fields = ("titolo", "cliente__nome", "cliente__cognome")
    list_filter = ("pratica_attiva", "data_creazione")

@admin.register(ProfiloUtente)
class ProfiloUtenteAdmin(admin.ModelAdmin):
    list_display = ("utente", "ruolo")
    list_filter = ("ruolo",)

@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ("id", "nome", "cognome", "stato", "appuntamento_previsto", "primo_contatto","creato_il")
    list_filter = ("stato", "provenienza", "consulente", "creato_il")
    search_fields = ("nome", "cognome", "telefono", "email")

@admin.register(NotaLead)
class NotaLeadAdmin(admin.ModelAdmin):
    list_display = ("id", "lead", "autore", "creato_il")
    list_filter = ("creato_il",)
    search_fields = ("testo", "lead__nome", "lead__cognome")
    raw_id_fields = ("lead", "autore")


@admin.register(Consulente)
class ConsulenteAdmin(admin.ModelAdmin):
    list_display = ("nome", "is_active", "creato_il")
    list_filter = ("is_active",)
    search_fields = ("nome",)