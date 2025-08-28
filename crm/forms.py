from django import forms
from .models import Cliente, DocumentoCliente, Pratiche, Nota

class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = [
            "nome", "cognome", "email", "telefono",
            "residenza", "esperienza_finanziaria", "visure",
            "note", "stato",
        ]

class DocumentoForm(forms.ModelForm):
    class Meta:
        model = DocumentoCliente
        fields = ["file", "descrizione"]

class PraticaForm(forms.ModelForm):
    class Meta:
        model = Pratiche
        fields = ["titolo", "descrizione", "importo", "pratica_attiva"]

class NotaForm(forms.ModelForm):
    class Meta:
        model = Nota
        fields = ["autore_nome", "testo"]
        widgets = {
            "testo": forms.Textarea(attrs={"rows": 4}),
        }
