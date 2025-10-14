from django import forms
from .models import Cliente, DocumentoCliente, Pratiche, Nota, Lead, Consulente


# =========================
# Cliente
# =========================
class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = [
            "nome", "cognome", "email", "telefono",
            "residenza", "esperienza_finanziaria", "visure",
            "note", "stato",
        ]


# =========================
# Documento
# =========================
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


# =========================
# Pratica
# =========================
class PraticaForm(forms.ModelForm):
    class Meta:
        model = Pratiche
        fields = ["titolo", "descrizione", "importo", "pratica_attiva"]


# =========================
# Nota
# =========================
class NotaForm(forms.ModelForm):
    class Meta:
        model = Nota
        fields = ["autore_nome", "testo"]
        widgets = {
            "testo": forms.Textarea(attrs={"rows": 4}),
        }


# =========================
# Lead
# =========================
class LeadForm(forms.ModelForm):
    class Meta:
        model = Lead
        fields = [
            # anagrafica
            "nome", "cognome", "telefono", "email",
            # stato/fasi
            "stato",
            "consulenza_effettuata", "no_risposta", "messaggio_inviato",
            "in_acquisizione",
            "appuntamento_previsto",
            "richiamare_il",
            "motivazione_negativa",
            "note_operatori",
            # nuovi campi
            "provenienza", "consulente", "primo_contatto",
        ]
        widgets = {
            # base
            "nome": forms.TextInput(attrs={"class": "input input-bordered w-full"}),
            "cognome": forms.TextInput(attrs={"class": "input input-bordered w-full"}),
            "telefono": forms.TextInput(attrs={"class": "input input-bordered w-full"}),
            "email": forms.EmailInput(attrs={"class": "input input-bordered w-full"}),

            # stato/fasi
            "stato": forms.Select(attrs={"class": "select select-bordered w-full"}),
            "appuntamento_previsto": forms.DateTimeInput(
                attrs={"type": "datetime-local", "class": "input input-bordered w-full"}
            ),
            "richiamare_il": forms.DateTimeInput(
                attrs={"type": "datetime-local", "class": "input input-bordered w-full"}
            ),
            "motivazione_negativa": forms.Textarea(
                attrs={"rows": 3, "class": "textarea textarea-bordered w-full"}
            ),
            "note_operatori": forms.Textarea(
                attrs={"rows": 3, "class": "textarea textarea-bordered w-full"}
            ),

            # nuovi
            "provenienza": forms.Select(attrs={"class": "select select-bordered w-full"}),
            "consulente": forms.Select(attrs={"class": "select select-bordered w-full"}),
            "primo_contatto": forms.DateTimeInput(
                attrs={"type": "datetime-local", "class": "input input-bordered w-full"}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Evita KeyError: usa get prima di manipolare il campo
        field = self.fields.get("consulente")
        if field is not None:
            field.queryset = Consulente.objects.filter(is_active=True).order_by("nome")
            field.required = False

        field = self.fields.get("provenienza")
        if field is not None:
            field.required = False

        field = self.fields.get("primo_contatto")
        if field is not None:
            field.required = False
            field.input_formats = [
                "%Y-%m-%dT%H:%M",  # HTML5 datetime-local
                "%Y-%m-%d %H:%M",
                "%d/%m/%Y %H:%M",
            ]

        field = self.fields.get("appuntamento_previsto")
        if field is not None:
            field.input_formats = [
                "%Y-%m-%dT%H:%M",
                "%Y-%m-%d %H:%M",
                "%d/%m/%Y %H:%M",
            ]

        field = self.fields.get("richiamare_il")
        if field is not None:
            field.input_formats = [
                "%Y-%m-%dT%H:%M",
                "%Y-%m-%d %H:%M",
                "%d/%m/%Y %H:%M",
            ]

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

        # Se no risponde e non marchi messaggio inviato (solo warning potenziale)
        # if no_risposta and not messaggio_inviato:
        #     self.add_error("messaggio_inviato", "Spunta 'Messaggio inviato' se il lead non risponde.")

        # Se vuoi forzare agenda operativa in 'in_corso':
        # if stato == "in_corso" and not appuntamento_previsto and not richiamare_il:
        #     self.add_error("richiamare_il", "Imposta una data/ora di richiamo o un appuntamento.")

        return cleaned
