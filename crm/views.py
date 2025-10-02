from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.contrib.auth.views import LoginView
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.http import require_http_methods, require_POST
from django.http import HttpResponse, JsonResponse, HttpResponseForbidden
from django.contrib import messages

from django.core.paginator import Paginator
from django.db.models import Q

import io, os, zipfile

from .models import Cliente, DocumentoCliente, Pratiche, Nota
from .forms import ClienteForm, DocumentoForm, PraticaForm, NotaForm, LeadForm, Lead
from .services import converti_lead_in_cliente


# --- Login ---
class CustomLoginView(LoginView):
    template_name = 'crm/login.html'


def home_redirect(request):
    return redirect('login')


@login_required
def dashboard(request):
    return render(request, 'crm/dashboard.html')


# --- Ruoli / permessi helper ---
def is_operatore(user):
    """
    True se l'utente è autenticato e ha un ruolo operativo (non admin).
    """
    prof = getattr(user, "profiloutente", None)
    return user.is_authenticated and (prof and prof.ruolo in ["operatore", "legale"])


def has_portal_access(user):
    """Possono usare il portale: admin, operatore, legale."""
    return hasattr(user, "profiloutente") and user.profiloutente.ruolo in ["admin", "operatore", "legale"]


def is_admin(user):
    return hasattr(user, "profiloutente") and user.profiloutente.ruolo == "admin"


# --- Clienti ---
@login_required
def clienti_tutti(request):
    qs = Cliente.objects.all().order_by("-data_creazione")

    # --- FILTRI ---
    q = request.GET.get("q", "").strip()
    stato = request.GET.get("stato", "").strip()  # active/inactive/legal
    dal = request.GET.get("dal", "").strip()
    al = request.GET.get("al", "").strip()
    has_docs = request.GET.get("has_docs", "").strip()   # "si"
    has_prat = request.GET.get("has_prat", "").strip()   # "si"

    if q:
        qs = qs.filter(
            Q(nome__icontains=q) |
            Q(cognome__icontains=q) |
            Q(email__icontains=q) |
            Q(telefono__icontains=q)
        )
    if stato in {"active", "inactive", "legal"}:
        qs = qs.filter(stato=stato)
    if dal:
        qs = qs.filter(data_creazione__date__gte=dal)
    if al:
        qs = qs.filter(data_creazione__date__lte=al)
    if has_docs == "si":
        qs = qs.filter(documenti__isnull=False).distinct()
    if has_prat == "si":
        qs = qs.filter(pratiche__isnull=False).distinct()

    # --- SORT opzionale ---
    sort = request.GET.get("sort", "")
    allowed = {"nome", "-nome", "cognome", "-cognome", "creato_il", "-creato_il"}
    if sort in allowed:
        qs = qs.order_by(sort)

    # --- PAGINAZIONE ---
    paginator = Paginator(qs, 20)
    page_obj = paginator.get_page(request.GET.get("page"))

    ctx = {
        "clienti": page_obj.object_list,
        "page_obj": page_obj,
        "q": q, "stato": stato, "dal": dal, "al": al,
        "has_docs": has_docs, "has_prat": has_prat,
    }
    return render(request, "crm/clienti_tutti.html", ctx)


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


@login_required
@user_passes_test(is_operatore)  # Solo operatori e admin
def clienti_possibili(request):
    clienti = Cliente.objects.filter(stato="possible")
    # Se hai un template dedicato, puoi renderizzarlo:
    # return render(request, "crm/clienti_possibili.html", {"clienti": clienti})
    return render(request, "crm/clienti_tutti.html", {"clienti": clienti, "page_obj": None})


# --- Dettaglio Cliente ---
@login_required
def clienti_dettaglio(request, cliente_id):
    cliente = get_object_or_404(Cliente, pk=cliente_id)
    docs_anag = cliente.documenti.filter(categoria="anagrafici").order_by("-caricato_il")
    docs_prat = cliente.documenti.filter(categoria="pratiche").order_by("-caricato_il")
    docs_leg = cliente.documenti.filter(categoria="legali").order_by("-caricato_il")
    pratiche = cliente.pratiche.all().order_by("-data_creazione")
    note = cliente.note_entries.all().order_by("-creata_il")  # usa related_name note_entries
    nota_form = NotaForm()
    return render(request, "crm/cliente_dettaglio.html", {
        "cliente": cliente,
        "docs_anag": docs_anag,
        "docs_prat": docs_prat,
        "docs_leg": docs_leg,
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


# --- Elimina Cliente (GET=conferma, POST=elimina) ---
@login_required
@user_passes_test(has_portal_access)
@require_http_methods(["GET", "POST"])
def cliente_elimina(request, cliente_id):
    cliente = get_object_or_404(Cliente, pk=cliente_id)

    if request.method == "POST":
        if not is_admin(request.user):
            return HttpResponseForbidden("Solo gli admin possono eliminare clienti.")
        cliente.delete()
        messages.success(request, "Cliente eliminato con successo.")
        return redirect("clienti_tutti")

    # GET → pagina di conferma
    return render(request, "crm/cliente_elimina.html", {"cliente": cliente})


# --- Documenti ---
@login_required
@require_http_methods(["GET", "POST"])
def documento_nuovo(request, cliente_id):
    cliente = get_object_or_404(Cliente, pk=cliente_id)
    if request.method == "POST":
        form = DocumentoForm(request.POST, request.FILES)
        if form.is_valid():
            doc = form.save(commit=False)
            doc.cliente = cliente
            doc.save()
            messages.success(request, "Documento caricato correttamente.")
            return redirect("cliente_dettaglio", cliente_id=cliente.id)
        else:
            # log semplice lato server
            print("⚠️ DocumentoForm errors:", form.errors.as_data())
            messages.error(request, "Controlla i campi: ci sono errori nel form.")
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


@login_required
def documenti_zip_cliente(request, cliente_id):
    cliente = get_object_or_404(Cliente, pk=cliente_id)
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for d in cliente.documenti.all():
            if not d.file:
                continue
            arcname = f"{d.categoria}/{os.path.basename(d.file.name)}"
            try:
                zf.writestr(arcname, d.file.read())
            except Exception:
                # file non leggibile: ignora
                pass
    buffer.seek(0)
    filename = f"documenti_cliente_{cliente.id}.zip"
    resp = HttpResponse(buffer.getvalue(), content_type="application/zip")
    resp["Content-Disposition"] = f'attachment; filename="{filename}"'
    return resp


# --- Pratiche ---
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
    return render(
        request,
        "crm/pratica_form.html",
        {"form": form, "cliente": pratica.cliente, "is_edit": True},
    )


@login_required
@require_http_methods(["GET", "POST"])
def pratica_elimina(request, pratica_id):
    pratica = get_object_or_404(Pratiche, id=pratica_id)
    cliente_id = pratica.cliente.id
    if request.method == "POST":
        pratica.delete()
        return redirect("cliente_dettaglio", cliente_id=cliente_id)
    return render(request, "crm/pratica_conferma_elimina.html", {"pratica": pratica})


# --- Note ---
@login_required
@require_http_methods(["POST"])
def nota_crea(request, cliente_id):
    cliente = get_object_or_404(Cliente, pk=cliente_id)
    form = NotaForm(request.POST)
    if form.is_valid():
        nota = form.save(commit=False)
        nota.cliente = cliente
        nota.save()
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


# --- LEAD ---
@login_required
def lead_lista(request):
    qs = Lead.objects.filter(is_archiviato=False).order_by("-creato_il")

    # Filtri
    q = request.GET.get("q", "").strip()
    stato = request.GET.get("stato", "").strip()
    dal = request.GET.get("dal", "").strip()
    al = request.GET.get("al", "").strip()

    # Nuovi filtri
    only_no_risposta = request.GET.get("no_risposta", "") == "1"
    only_msg_inviato = request.GET.get("msg_inviato", "") == "1"
    only_acquisizione = request.GET.get("in_acquisizione", "") == "1"
    da_richiamare_da = request.GET.get("richiamo_da", "").strip()
    da_richiamare_a = request.GET.get("richiamo_a", "").strip()

    if q:
        qs = qs.filter(
            Q(nome__icontains=q) |
            Q(cognome__icontains=q) |
            Q(email__icontains=q) |
            Q(telefono__icontains=q)
        )
    if stato in {"in_corso", "negativo", "positivo"}:
        qs = qs.filter(stato=stato)
    if dal:
        qs = qs.filter(creato_il__date__gte=dal)
    if al:
        qs = qs.filter(creato_il__date__lte=al)

    if only_no_risposta:
        qs = qs.filter(no_risposta=True)
    if only_msg_inviato:
        qs = qs.filter(messaggio_inviato=True)
    if only_acquisizione:
        qs = qs.filter(in_acquisizione=True)
    if da_richiamare_da:
        qs = qs.filter(richiamare_il__date__gte=da_richiamare_da)
    if da_richiamare_a:
        qs = qs.filter(richiamare_il__date__lte=da_richiamare_a)

    # Sort opzionale
    sort = request.GET.get("sort", "")
    allowed = {"nome", "-nome", "cognome", "-cognome", "creato_il", "-creato_il", "richiamare_il", "-richiamare_il"}
    if sort in allowed:
        qs = qs.order_by(sort)

    ha_negativi = qs.filter(stato="negativo").exists()

    # Paginazione
    paginator = Paginator(qs, 20)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(request, "crm/lead_lista.html", {
        "leads": page_obj.object_list,
        "page_obj": page_obj,
        "q": q, "stato": stato, "dal": dal, "al": al,
        "no_risposta": "1" if only_no_risposta else "",
        "msg_inviato": "1" if only_msg_inviato else "",
        "in_acquisizione": "1" if only_acquisizione else "",
        "richiamo_da": da_richiamare_da,
        "richiamo_a": da_richiamare_a,
        "sort": sort,
        "ha_negativi": ha_negativi,
    })


@login_required
@require_http_methods(["GET", "POST"])
def lead_nuovo(request):
    if request.method == "POST":
        form = LeadForm(request.POST)
        if form.is_valid():
            lead = form.save()
            if lead.stato == "positivo":
                cliente = converti_lead_in_cliente(lead, request.user)
                messages.success(request, f"Lead convertito → Cliente: {cliente.nome} {cliente.cognome}.")
                return redirect("clienti_tutti")
            messages.success(request, "Lead salvato correttamente.")
            return redirect("lead_lista")
    else:
        form = LeadForm()
    return render(request, "crm/lead_form.html", {"form": form})


@login_required
@require_http_methods(["GET", "POST"])
def lead_modifica(request, lead_id):
    lead = get_object_or_404(Lead, pk=lead_id, is_archiviato=False)
    if request.method == "POST":
        form = LeadForm(request.POST, instance=lead)
        if form.is_valid():
            lead = form.save()
            if lead.stato == "positivo":
                cliente = converti_lead_in_cliente(lead, request.user)
                messages.success(request, f"Lead convertito → Cliente: {cliente.nome} {cliente.cognome}.")
                return redirect("clienti_tutti")
            messages.success(request, "Lead aggiornato correttamente.")
            return redirect("lead_lista")
    else:
        form = LeadForm(instance=lead)
    return render(request, "crm/lead_form.html", {"form": form, "lead": lead, "is_edit": True})


# --- Toggle consulenza, no_risposta, messaggio_inviato ---
def _back(request):
    return request.META.get("HTTP_REFERER") or reverse("lead_lista")


@login_required
@require_POST
def lead_toggle_msg(request, lead_id):
    lead = get_object_or_404(Lead, pk=lead_id)
    lead.messaggio_inviato = not lead.messaggio_inviato
    lead.save(update_fields=["messaggio_inviato"])
    return redirect(_back(request))


@login_required
@require_POST
def lead_toggle_no_risposta(request, lead_id):
    lead = get_object_or_404(Lead, pk=lead_id)
    lead.no_risposta = not lead.no_risposta
    if not lead.no_risposta:
        lead.messaggio_inviato = False
        lead.save(update_fields=["no_risposta", "messaggio_inviato"])
    else:
        lead.save(update_fields=["no_risposta"])
    return redirect(_back(request))


@login_required
@require_POST
def lead_toggle_consulenza(request, lead_id):
    lead = get_object_or_404(Lead, pk=lead_id)
    lead.consulenza_effettuata = not lead.consulenza_effettuata
    lead.save(update_fields=["consulenza_effettuata"])
    return redirect(_back(request))
