from django import forms
from .models import Cliente, DocumentoCliente

class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = [
            "nome",
            "cognome",
            "email",
            "telefono",
            "residenza",
            "esperienza_finanziaria",
            "visure",
            "note",
            "stato",
        ]

class DocumentoForm(forms.ModelForm):
    class Meta:
        model: DocumentoCliente
        fields = [
            "file",
            "descrizione"
        ]