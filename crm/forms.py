from django import forms
from .models import Cliente, DocumentoCliente, Pratiche, Nota, Lead

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
        fields = ["categoria", "file", "descrizione"]

    def clean_file(self):
        f = self.cleaned_data.get("file")
        if not f:
            return f
        max_mb = 10
        if f.size > max_mb * 1024 * 1024:
            raise forms.ValidationError(f"Il file è troppo grande (>{max_mb} MB).")
        ctype = getattr(f, "content_type", "").lower()
        allowed = {"application/pdf", "image/png", "image/jpg", "image/jpeg"}
        if ctype not in allowed and not ctype.startswith("image/jpeg"):
            raise forms.ValidationError("Formato non valido. Consenti solo PDF, PNG, JPG/JPEG.")
        return f


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

class LeadForm(forms.ModelForm):
    class Meta:
        model = Lead
        fields = [
            "nome", "cognome", "telefono", "email",
            "stato",
            "consulenza_effettuata", "no_risposta", "messaggio_inviato",
            "in_acquisizione",
            "appuntamento_previsto",  
            "richiamare_il",          
            "motivazione_negativa",
            "note_operatori",
        ] 
        widgets = {
            "appuntamento_previsto": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "richiamare_il": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "motivazione_negativa": forms.Textarea(attrs={"rows": 3}),
            "note_operatori": forms.Textarea(attrs={"rows": 3}),  
        }   

    def clean(self):
        cleaned = super().clean()
        stato = cleaned.get("stato")
        no_risposta = cleaned.get("no_risposta")
        messaggio_inviato = cleaned.get("messaggio_inviato")
        motivazione_negativa = cleaned.get("motivazione_negativa")
        appuntamento_previsto = cleaned.get("appuntamento_previsto")
        richiamare_il = cleaned.get("richiamare_il")

        # Se stato = negativo → motivazione obbligatoria
        if stato == "negativo" and not motivazione_negativa:
            self.add_error("motivazione_negativa", "Inserisci la motivazione per l’esito negativo.")

        # Se no risponde → puoi marcare "messaggio inviato" (non obbligatorio, ma coerente)
        if no_risposta is True and messaggio_inviato is False:
            # Non lo rendo obbligatorio, ma puoi decidere di forzarlo:
            # self.add_error("messaggio_inviato", "Spunta 'Messaggio inviato' se il lead non risponde.")
            pass

        # Se serve agenda: almeno uno tra appuntamento_previsto o richiamare_il
        if not appuntamento_previsto and not richiamare_il and stato == "in_corso":
            # Non obbligo, ma consigliato: se vuoi renderlo obbligatorio togli il commento:
            # self.add_error("richiamare_il", "Imposta una data/ora di richiamo o un appuntamento.")
            pass

        return cleaned