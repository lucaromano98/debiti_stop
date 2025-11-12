from django import forms
from django.forms.widgets import ClearableFileInput  
from .models import Cliente, DocumentoCliente, Pratiche, Nota, Lead, Consulente, SchedaConsulenza


# ===== Widget per upload multiplo =====
class MultiFileInput(ClearableFileInput):
    """Come ClearableFileInput ma consente selezione multipla."""
    allow_multiple_selected = True


# =========================
# Cliente
# =========================
class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = [
            "nome", "cognome", "email", "telefono",
            "residenza", "esperienza_finanziaria",
            "note", "stato",
            "istanza_visibilita", "documenti_inviati", "perizia_inviata",
        ]
        widgets = {
            "nome": forms.TextInput(attrs={"class": "input input-bordered w-full"}),
            "cognome": forms.TextInput(attrs={"class": "input input-bordered w-full"}),
            "email": forms.EmailInput(attrs={"class": "input input-bordered w-full"}),
            "telefono": forms.TextInput(attrs={"class": "input input-bordered w-full"}),
            "residenza": forms.Textarea(attrs={"class": "textarea textarea-bordered w-full", "rows": 1}),
            "esperienza_finanziaria": forms.Textarea(attrs={"class": "textarea textarea-bordered w-full", "rows": 1}),
            "note": forms.Textarea(attrs={"class": "textarea textarea-bordered w-full", "rows": 4}),
            "stato": forms.Select(attrs={"class": "select select-bordered w-full"}),
            "istanza_visibilita": forms.CheckboxInput(attrs={"class": "toggle toggle-primary"}),
            "documenti_inviati": forms.CheckboxInput(attrs={"class": "toggle toggle-primary"}),
            "perizia_inviata": forms.CheckboxInput(attrs={"class": "toggle toggle-primary"}),
        }



# =========================
# Documento
# =========================
class DocumentoForm(forms.ModelForm):
    class Meta:
        model = DocumentoCliente
        fields = ["categoria", "file", "descrizione"]

    # chiavi legacy da nascondere
    EXCLUDE = {"pratiche", "legali"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        field = self.fields["categoria"]
        # filtra le choices mostrate
        field.choices = [c for c in field.choices if c[0] not in self.EXCLUDE]

    def clean_categoria(self):
        v = self.cleaned_data["categoria"]
        if v in self.EXCLUDE:
            # protezione lato server in caso di manomissione del form
            raise forms.ValidationError("Categoria non valida.")
        return v


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
        fields = ["testo"]   # <-- niente 'autore_nome' e niente 'autore'
        widgets = {
            "testo": forms.Textarea(attrs={
                "class": "textarea textarea-bordered",
                "rows": 4,
                "placeholder": "Scrivi una nota...",
            }),
        }
        labels = {
            "testo": "Nota",
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
            "nome": forms.TextInput(attrs={"class": "input input-bordered w-full"}),
            "cognome": forms.TextInput(attrs={"class": "input input-bordered w-full"}),
            "telefono": forms.TextInput(attrs={"class": "input input-bordered w-full"}),
            "email": forms.EmailInput(attrs={"class": "input input-bordered w-full"}),

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

            "provenienza": forms.Select(attrs={"class": "select select-bordered w-full"}),
            "consulente": forms.Select(attrs={"class": "select select-bordered w-full"}),
            "primo_contatto": forms.DateTimeInput(
                attrs={"type": "datetime-local", "class": "input input-bordered w-full"}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

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
                "%Y-%m-%dT%H:%M",
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
        motivazione_negativa = cleaned.get("motivazione_negativa")
        if stato == "negativo" and not motivazione_negativa:
            self.add_error("motivazione_negativa", "Inserisci la motivazione per l’esito negativo.")
        return cleaned

# ========================
# SchedaConsulenza
# ========================

from django import forms
from .models import SchedaConsulenza

class SchedaConsulenzaForm(forms.ModelForm):
    class Meta:
        model = SchedaConsulenza
        fields = [
            "obiettivo",
            "occupazione",
            "esposizione_patrimoniale",   # testo libero
            "esposizione_finanziaria",    # testo libero (ATTENZIONE alla r)
            "esposizione_totale",         # il “Preventivo”
            "ha_cqs",
            "ha_equitalia",
            "note",
        ]
        labels = {
            "esposizione_patrimoniale": "Esposizione patrimoniale",
            "esposizione_finanziaria": "Esposizione finanziaria",
            "esposizione_totale": "Preventivo",
        }
        widgets = {
            "obiettivo": forms.TextInput(attrs={"class": "input input-bordered w-full"}),
            "occupazione": forms.TextInput(attrs={"class": "input input-bordered w-full"}),

            "esposizione_patrimoniale": forms.Textarea(attrs={
                "class": "textarea textarea-bordered w-full",
                "rows": 4,
                "placeholder": "Es.\nCasa: valore 30.000\nAuto: valore 5.000",
            }),
            "esposizione_finanziaria": forms.Textarea(attrs={
                "class": "textarea textarea-bordered w-full",
                "rows": 4,
                "placeholder": "Es.\nPrestito X: 12.000\nCarta Y: 2.500",
            }),

            "esposizione_totale": forms.NumberInput(attrs={"class": "input input-bordered w-full"}),
            "note": forms.Textarea(attrs={"class": "textarea textarea-bordered w-full", "rows": 4}),
        }
