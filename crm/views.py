from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.views import LoginView
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.http import require_http_methods
from .models import Cliente, DocumentoCliente, Pratiche, Nota
from .forms import ClienteForm, DocumentoForm, PraticaForm, NotaForm

# --- Login ---
class CustomLoginView(LoginView):
    template_name = 'crm/login.html'

def home_redirect(request):
    return redirect('login')

@login_required
def dashboard(request):
    return render(request, 'crm/dashboard.html')


# --- Utility: controlla se è operatore o admin ---
def is_operatore(user):
    return hasattr(user, "profiloutente") and user.profiloutente.ruolo in ["operatore", "admin"]


# --- Clienti ---
@login_required
@user_passes_test(is_operatore)
def clienti_tutti(request):
    clienti = Cliente.objects.all()
    return render(request, "crm/clienti_tutti.html", {"clienti": clienti})

@login_required
@user_passes_test(is_operatore)
def clienti_legali(request):
    clienti = Cliente.objects.filter(stato="legal")
    return render(request, "crm/clienti_legali.html", {"clienti": clienti})

@login_required
@user_passes_test(is_operatore)
def clienti_attivi(request):
    clienti = Cliente.objects.filter(stato="active")
    return render(request, "crm/clienti_attivi.html", {"clienti": clienti})

@login_required
@user_passes_test(is_operatore)
def clienti_non_attivi(request):
    clienti = Cliente.objects.filter(stato="inactive")
    return render(request, "crm/clienti_non_attivi.html", {"clienti": clienti})


# --- Aggiungi nuovo cliente ---
@login_required
@user_passes_test(is_operatore)
def cliente_nuovo(request):
    if request.method == "POST":
        form = ClienteForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("clienti_tutti")
    else:
        form = ClienteForm()
    return render(request, "crm/cliente_form.html", {"form": form})

# --- Dettaglio Cliente ---

@login_required
def clienti_dettaglio(request, cliente_id):
    cliente = get_object_or_404(Cliente, pk=cliente_id)
    documenti = cliente.documenti.all().order_by("-caricato_il")
    pratiche = cliente.pratiche.all().order_by("-data_creazione")
    note = cliente.note_entries.all().order_by("-creata_il")  # <--- usa note_entries
    nota_form = NotaForm()
    return render(request, "crm/cliente_dettaglio.html", {
        "cliente": cliente,
        "documenti": documenti,
        "pratiche": pratiche,
        "note": note,
        "nota_form": nota_form,
    })



# --- Modifica Cliente ---

@require_http_methods(["GET", "POST"])
def cliente_modifica(request, cliente_id):
    cliente = get_object_or_404(Cliente, pk=cliente_id)

    if request.method == "POST":
        form = ClienteForm(request.POST, instance=cliente)
        if form.is_valid():
            form.save()
            return redirect("cliente_dettaglio", cliente_id=cliente.id)
    else:
        form = ClienteForm(instance=cliente)

    return render(request, "crm/cliente_form.html", {
        "form": form,
        "is_edit": True,
        "cliente": cliente,
    })

# --- Elimina Cliente ---

@login_required
@require_http_methods(["GET", "POST"])
def cliente_elimina(request, cliente_id):
    cliente = get_object_or_404(Cliente, id=cliente_id)
    if request.method == "POST":
        cliente.delete()
        return redirect("clienti_tutti")
    return render(request, "crm/cliente_conferma_elimina.html", {"cliente": cliente})

@login_required
@require_http_methods(["GET", "POST"])
def documento_nuovo(request, cliente_id):
    cliente = get_object_or_404(Cliente, id=cliente_id)
    if request.method == "POST":
        form = DocumentoForm(request.POST, request.FILES)
        if form.is_valid():
            doc = form.save(commit=False)
            doc.cliente = cliente
            doc.save()
            return redirect("cliente_dettaglio", cliente_id=cliente.id)
    else:
        form = DocumentoForm()
    return render(request, "crm/documento_form.html", {"form": form, "cliente": cliente})

@login_required
@require_http_methods(["GET", "POST"])
def documento_elimina(request, doc_id):
    doc = get_object_or_404(DocumentoCliente, id=doc_id)
    cliente_id = doc.cliente.id
    if request.method == "POST":
        doc.delete()
        return redirect("cliente_dettaglio", cliente_id=cliente_id)
    return render(request, "crm/documento_conferma_elimina.html", {"doc": doc})

# --- Pratiche 
@login_required
@require_http_methods(["GET", "POST"])
def pratica_nuova(request, cliente_id):
    cliente = get_object_or_404(Cliente, id=cliente_id)
    if request.method == "POST":
        form = PraticaForm(request.POST)
        if form.is_valid():
            p = form.save(commit=False)
            p.cliente = cliente
            p.save()
            return redirect("cliente_dettaglio", cliente_id=cliente.id)
    else:
        form = PraticaForm()
    return render(request, "crm/pratica_form.html", {"form": form, "cliente": cliente})

@login_required
@require_http_methods(["GET", "POST"])
def pratica_modifica(request, pratica_id):
    pratica = get_object_or_404(Pratiche, id=pratica_id)
    if request.method == "POST":
        form = PraticaForm(request.POST, instance=pratica)
        if form.is_valid():
            form.save()
            return redirect("cliente_dettaglio", cliente_id=pratica.cliente.id)
    else:
        form = PraticaForm(instance=pratica)
    return render(request, "crm/pratica_form.html", {"form": form, "cliente": pratica.cliente, "is_edit": True})

@login_required
@require_http_methods(["GET", "POST"])
def pratica_elimina(request, pratica_id):
    pratica = get_object_or_404(Pratiche, id=pratica_id)
    cliente_id = pratica.cliente.id
    if request.method == "POST":
        pratica.delete()
        return redirect("cliente_dettaglio", cliente_id=cliente_id)
    return render(request, "crm/pratica_conferma_elimina.html", {"pratica": pratica})


#--- Note 

@login_required
@require_http_methods(["POST"])
def nota_crea(request, cliente_id):
    cliente = get_object_or_404(Cliente, pk=cliente_id)
    form = NotaForm(request.POST)
    if form.is_valid():
        nota = form.save(commit=False)   # <-- istanza della Nota
        nota.cliente = cliente           # <-- collega al cliente
        nota.save()                      # <-- salva
    # anche se il form non è valido, torniamo al dettaglio (poi puoi mostrare errori)
    return redirect("cliente_dettaglio", cliente_id=cliente.id)


@login_required
@require_http_methods(["GET", "POST"])
def nota_modifica(request, nota_id):
    nota = get_object_or_404(Nota, pk=nota_id)
    cliente = nota.cliente
    if request.method == "POST":
        form = NotaForm(request.POST, instance=nota)
        if form.is_valid():
            form.save()
            return redirect("cliente_dettaglio", cliente_id=cliente.id)
    else:
        form = NotaForm(instance=nota)
    # pagina semplice (non modale) per modificare
    return render(request, "crm/nota_form.html", {
        "form": form,
        "cliente": cliente,
        "nota": nota,
        "is_edit": True,
    })


@login_required
@require_http_methods(["GET", "POST"])
def nota_elimina(request, nota_id):
    nota = get_object_or_404(Nota, pk=nota_id)
    cliente_id = nota.cliente.id
    if request.method == "POST":
        nota.delete()
        return redirect("cliente_dettaglio", cliente_id=cliente_id)
    return render(request, "crm/nota_conferma_elimina.html", {"nota": nota})