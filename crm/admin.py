from django.contrib import admin
from .models import Cliente, DocumentoCliente, Pratiche, ProfiloUtente

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ("nome", "cognome", "email", "telefono", "stato", "data_creazione")
    search_fields = ("nome", "cognome", "email", "telefono")
    list_filter = ("stato", "data_creazione")

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
