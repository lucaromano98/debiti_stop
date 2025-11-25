from __future__ import annotations
from datetime import datetime, date, timedelta
import io, os, zipfile
from django.utils import timezone

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.views import LoginView
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db.models import Q, Exists, OuterRef
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods, require_POST

from .services import converti_lead_in_cliente
from .services import notifica_documento_caricato as _notify_doc_raw
from .forms import ClienteForm, DocumentoForm, PraticaForm, NotaForm, LeadForm, SchedaConsulenzaForm, DocumentoClienteEditForm
from .models import (
    Cliente,
    DocumentoCliente,
    Pratiche,
    Nota,
    Lead,
    Consulente,
    Notifica,
    SchedaConsulenza
)





def notify_doc(actor, cliente, documento):
    """Chiama la funzione di servizio provando prima keyword, poi posizionale, poi senza argomenti."""
    try:
        return _notify_doc_raw(actor=actor, cliente=cliente, documento=documento)
    except TypeError:
        try:
            return _notify_doc_raw(actor, cliente, documento)
        except TypeError:
            try:
                return _notify_doc_raw()
            except Exception:
                return None




# ==============================
# Helper upload visure (multi-file)
# ==============================
def _allega_visure(request, cliente):
    files = request.FILES.getlist("visure_files")
    if not files:
        return 0

    ok = 0
    docs_ids = []
    names = []

    for f in files:
        doc = DocumentoCliente(
            cliente=cliente,
            categoria="visure",
            file=f,
            descrizione=f"Visura: {getattr(f, 'name', '')}",
        )
        try:
            doc.full_clean()
            doc.save()
            ok += 1
            docs_ids.append(doc.id)
            names.append(getattr(f, "name", "file"))
        except ValidationError as e:
            messages.error(request, f"‘{getattr(f, 'name', '?')}' non caricato: {e.messages[0] if e.messages else e}")
        except Exception as e:
            messages.error(request, f"Errore caricando ‘{getattr(f, 'name', '?')}’: {e}")

    if ok:
        # sottotitolo: primi 3 nomi file (poi "…")
        preview = ", ".join(names[:3]) + ("…" if len(names) > 3 else "")
        from .services import notifica_documento_caricato
        notifica_documento_caricato(
            actor=request.user,
            cliente=cliente,
            documento=doc,
            count=1,
            categoria_label=doc.get_categoria_display(),
            subtitle=(doc.descrizione or ""),
        )
        messages.success(request, f"Caricate {ok} visure.")
    return ok




# ==============================
# Helpers comuni
# ==============================
def _parse_date(s: str | None):
    if not s:
        return None
    s = s.strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            pass
    return None


def _get_per_page(request, default=20, cap=100):
    try:
        per = int(request.GET.get("per", default))
        return max(1, min(per, cap))
    except (TypeError, ValueError):
        return default


def _back(request, fallback_name="lead_lista"):
    return request.META.get("HTTP_REFERER") or reverse(fallback_name)


# Quick ranges per appuntamenti
def _appt_range(key: str, base: date | None = None):
    """
    Ritorna (start_date, end_date) inclusivi per filtro appuntamenti su 'appuntamento_previsto'.
    - next3: esclude OGGI → da domani a tra 3 giorni
    - next7: include OGGI → da oggi ai prossimi 7 giorni
    """
    d = base or date.today()
    if key == "today":
        return d, d
    if key == "tomorrow":
        t = d + timedelta(days=1)
        return t, t
    if key == "next3":
        start = d + timedelta(days=1)
        end = d + timedelta(days=3)
        return start, end
    if key == "next7":
        return d, d + timedelta(days=7)
    return None, None


# ==============================
# Permessi / Accesso
# ==============================
class CustomLoginView(LoginView):
    template_name = "crm/login.html"


def home_redirect(request):
    return redirect("login")


@login_required
def dashboard(request):
    return render(request, "crm/dashboard.html")


def is_operatore(user):
    prof = getattr(user, "profiloutente", None)
    return user.is_authenticated and bool(prof and prof.ruolo in ["operatore", "legale"])


def has_portal_access(user):
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    prof = getattr(user, "profiloutente", None)
    return bool(prof and prof.ruolo in ["admin", "operatore", "legale"])


def is_admin(user):
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    prof = getattr(user, "profiloutente", None)
    return bool(prof and prof.ruolo == "admin")


# ==============================
# Clienti – lista/filtri
# ==============================
@login_required
@user_passes_test(has_portal_access)
def clienti_tutti(request):
    qs = (
        Cliente.objects.all()
        .select_related()
        .prefetch_related("documenti", "pratiche")
    )

    # --- FILTRI ---
    q = request.GET.get("q", "").strip()
    stato = request.GET.get("stato", "").strip()           # active/inactive/legal
    dal_raw = request.GET.get("dal", "").strip()
    al_raw = request.GET.get("al", "").strip()
    has_docs = request.GET.get("has_docs", "").strip()     # "si"
    has_prat = request.GET.get("has_prat", "").strip()     # "si"

    if q:
        qs = qs.filter(
            Q(nome__icontains=q)
            | Q(cognome__icontains=q)
            | Q(email__icontains=q)
            | Q(telefono__icontains=q)
        )

    if stato in {"active", "inactive", "legal", "stragiudiziale", "instanza"}:
        qs = qs.filter(stato=stato)

    dal = _parse_date(dal_raw)
    al = _parse_date(al_raw)
    if dal:
        qs = qs.filter(data_creazione__date__gte=dal)
    if al:
        qs = qs.filter(data_creazione__date__lte=al)

    if has_docs == "si":
        sub_docs = DocumentoCliente.objects.filter(cliente=OuterRef("pk"))
        qs = qs.annotate(_has_docs=Exists(sub_docs)).filter(_has_docs=True)

    if has_prat == "si":
        sub_prat = Pratiche.objects.filter(cliente=OuterRef("pk"))
        qs = qs.annotate(_has_prat=Exists(sub_prat)).filter(_has_prat=True)

    # --- SORT ---
    sort = (request.GET.get("sort") or "").strip()

    # default: cognome A-Z
    if not sort:
        sort = "cognome"

    if sort == "cognome":
        qs = qs.order_by("cognome", "nome")
    elif sort == "-cognome":
        qs = qs.order_by("-cognome", "-nome")
    elif sort == "nome":
        qs = qs.order_by("nome", "cognome")
    elif sort == "-nome":
        qs = qs.order_by("-nome", "-cognome")
    elif sort == "data_creazione":
        qs = qs.order_by("data_creazione")
    elif sort == "-data_creazione":
        qs = qs.order_by("-data_creazione")
    else:
        # fallback di sicurezza
        sort = "cognome"
        qs = qs.order_by("cognome", "nome")

    # --- PAGINAZIONE ---
    per_page = _get_per_page(request, 20, 100)
    paginator = Paginator(qs, per_page)
    page_obj = paginator.get_page(request.GET.get("page"))

    ctx = {
        "clienti": page_obj.object_list,
        "page_obj": page_obj,
        "q": q,
        "stato": stato,
        "dal": dal_raw,
        "al": al_raw,
        "has_docs": has_docs,
        "has_prat": has_prat,
        "sort": sort,
        "per": per_page,
    }
    return render(request, "crm/clienti_tutti.html", ctx)



@login_required
@user_passes_test(has_portal_access)
def clienti_legali(request):
    clienti = Cliente.objects.filter(stato="legal").order_by("-data_creazione")
    return render(request, "crm/clienti_legali.html", {"clienti": clienti})


@login_required
@user_passes_test(has_portal_access)
def clienti_attivi(request):
    clienti = Cliente.objects.filter(stato="active").order_by("-data_creazione")
    return render(request, "crm/clienti_attivi.html", {"clienti": clienti})


@login_required
@user_passes_test(has_portal_access)
def clienti_non_attivi(request):
    clienti = Cliente.objects.filter(stato="inactive").order_by("-data_creazione")
    return render(request, "crm/clienti_non_attivi.html", {"clienti": clienti})


# ==============================
# Clienti – CRUD
# ==============================
@login_required
@user_passes_test(has_portal_access)
def cliente_nuovo(request):
    if request.method == "POST":
        form = ClienteForm(request.POST)
        if form.is_valid():
            cliente = form.save()

            if cliente.perizia_inviata and cliente.stato != "active":
                cliente.stato = "active"
                cliente.save(update_fields=["stato"])

            _allega_visure(request, cliente)

            # 🔹 se nel form hanno scritto qualcosa nel campo "note",
            #     crea una nota identica a quelle di "+ Aggiungi nota"
            if cliente.note:
                Nota.objects.create(
                    cliente=cliente,
                    testo=cliente.note,
                    # se nel modello c'è un campo autore, usa request.user
                    autore=getattr(request, "user", None),
                )

            messages.success(request, "Cliente creato.")
            return redirect("clienti_tutti")
        messages.error(request, "Controlla i campi: ci sono errori nel form.")
    else:
        form = ClienteForm()
    return render(request, "crm/cliente_form.html", {"form": form, "is_edit": False})


@login_required
@user_passes_test(has_portal_access)
def clienti_possibili(request):
    clienti = Cliente.objects.filter(stato="istanza").order_by("-data_creazione")
    return render(request, "crm/clienti_tutti.html", {"clienti": clienti, "page_obj": None})


@login_required
@user_passes_test(has_portal_access)
def clienti_dettaglio(request, cliente_id):
    cliente = get_object_or_404(Cliente, pk=cliente_id)
    is_admin_user = is_admin(request.user)

    # Categorie da mostrare (ordine tab)
    CATS = [
        (DocumentoCliente.Categoria.ANAGRAFICI,      "Anagrafici"),
        (DocumentoCliente.Categoria.SCHED_CON,       "Scheda Consulenza"),
        (DocumentoCliente.Categoria.PREVENTIVI,      "Preventivi"),
        (DocumentoCliente.Categoria.MANDATO,         "Mandato"),
        (DocumentoCliente.Categoria.CONTRATTI,       "Privato Admin"),
        (DocumentoCliente.Categoria.VISURE,          "Visure"),
        (DocumentoCliente.Categoria.PROVVEDIMENTI,   "Provvedimenti"),
        (DocumentoCliente.Categoria.DECR_INGIUNTIVO, "Decreto Ingiuntivo"),
        (DocumentoCliente.Categoria.PRECETTO,        "Precetto"),
        (DocumentoCliente.Categoria.PIGNORAMENTO,    "Pignoramento"),
        (DocumentoCliente.Categoria.RICHI_ISTANZA,   "Richiesta Istanza"),
        (DocumentoCliente.Categoria.RISC_ISTANZA,    "Riscontro Istanza"),
        (DocumentoCliente.Categoria.RECLAMO,         "Reclamo"),
        (DocumentoCliente.Categoria.OPPOSIZIONE,     "Opposizione"),
        (DocumentoCliente.Categoria.PROP_TRANSATTIVA,"Proposta transattiva"),
        (DocumentoCliente.Categoria.ALTRO,           "Altro"),
    ]

    # solo gli admin possono vedere Privato Admin
    if not is_admin_user:
        CATS = [
            (code, label)
            for (code, label) in CATS
            if code != DocumentoCliente.Categoria.CONTRATTI
        ]

    # 🔎 testo di ricerca
    doc_query = (request.GET.get("q") or "").strip()
    q_norm = doc_query.lower().replace(" ", "") if doc_query else ""

    # prendo tutti i documenti del cliente (senza ordine, lo gestiamo noi)
    all_docs_qs = cliente.documenti.all()
    all_docs = list(all_docs_qs)

    # funzione per avere un nome "umano" con cui ordinare
    def _normalized_filename(doc):
        path = doc.file.name or ""
        base = os.path.basename(path)          # es: 1763_ci-mario-rossi.jpg
        name, ext = os.path.splitext(base)     # es: 1763_ci-mario-rossi , .jpg
        parts = name.split("_", 1)
        if len(parts) == 2 and parts[0].isdigit():
            name = parts[1]                    # es: ci-mario-rossi
        name = name.replace("-", " ")          # es: ci mario rossi
        return f"{name}{ext}".lower()

    # helper per capire se è un’immagine (per l’anteprima)
    def _is_image(doc):
        fname = (doc.file.name or "").lower()
        return fname.endswith((".png", ".jpg", ".jpeg", ".gif", ".webp"))

    # filtro in PYTHON così possiamo gestire spazi / trattini / maiuscole
    if q_norm:
        filtered = []
        for d in all_docs:
            # descrizione (quello che scrive l'utente)
            desc = (d.descrizione or "").lower()

            # nome file "umano" (simile al pretty_filename del template)
            path = d.file.name or ""
            base = os.path.basename(path)
            name, ext = os.path.splitext(base)
            parts = name.split("_", 1)
            if len(parts) == 2 and parts[0].isdigit():
                name = parts[1]
            name = name.replace("-", " ")
            filename_text = f"{name}{ext}".lower()

            # normalizzo togliendo spazi per la ricerca
            haystack = (desc + " " + filename_text).replace(" ", "")
            if q_norm in haystack:
                filtered.append(d)

        all_docs = filtered

    # 🔤 ordino alfabeticamente per nome "umano"
    all_docs.sort(key=_normalized_filename)

    # Raggruppo per categoria (usando solo i doc filtrati)
    docs_by_cat = {code: [] for code, _ in CATS}
    for d in all_docs:
        # info extra per il template (anteprima)
        d.is_image = _is_image(d)
        d.extension = os.path.splitext(d.file.name or "")[1].lower()

        if d.categoria in docs_by_cat:
            docs_by_cat[d.categoria].append(d)

    # tab attiva dalla querystring, es. ?tab=contratti
    active_tab = request.GET.get("tab")
    valid_codes = {code for code, _ in CATS}
    if active_tab not in valid_codes:
        active_tab = CATS[0][0]

    pratiche = cliente.pratiche.all().order_by("-data_creazione")
    schede_consulenza = SchedaConsulenza.objects.filter(cliente=cliente).order_by("-created_at")
    note = cliente.note_entries.all().order_by("-creata_il")
    nota_form = NotaForm()

    return render(
        request,
        "crm/cliente_dettaglio.html",
        {
            "cliente": cliente,
            "categories": CATS,
            "docs_by_cat": docs_by_cat,
            "pratiche": pratiche,
            "schede_consulenza": schede_consulenza,
            "note": note,
            "nota_form": nota_form,
            "active_tab": active_tab,
            "doc_query": doc_query,
        },
    )

@login_required
@user_passes_test(has_portal_access)
@require_http_methods(["GET", "POST"])
def documento_modifica(request, documento_id):
    documento = get_object_or_404(DocumentoCliente, pk=documento_id)
    cliente = documento.cliente

    # tab corrente (categoria) per tornare alla stessa tab dopo il salvataggio
    current_tab = request.GET.get("tab") or request.POST.get("tab") or documento.categoria

    if request.method == "POST":
        form = DocumentoClienteEditForm(request.POST, instance=documento)
        if form.is_valid():
            form.save()
            messages.success(request, "Documento aggiornato correttamente.")
            url = reverse("cliente_dettaglio", args=[cliente.id])
            return redirect(f"{url}?tab={current_tab}")
        else:
            messages.error(request, "Controlla i campi: ci sono errori nel form.")
    else:
        form = DocumentoClienteEditForm(instance=documento)

    return render(
        request,
        "crm/documento_form.html",
        {
            "form": form,
            "documento": documento,
            "cliente": cliente,
            "active_tab": current_tab,
        },
    )


@login_required
@user_passes_test(has_portal_access)
@require_http_methods(["GET", "POST"])
@login_required
@user_passes_test(has_portal_access)
@require_http_methods(["GET", "POST"])
def cliente_modifica(request, cliente_id):
    cliente = get_object_or_404(Cliente, pk=cliente_id)
    old_note = cliente.note  # 🔹 salviamo la nota prima delle modifiche

    if request.method == "POST":
        form = ClienteForm(request.POST, instance=cliente)
        if form.is_valid():
            cliente = form.save()

            if cliente.perizia_inviata and cliente.stato != "active":
                cliente.stato = "active"
                cliente.save(update_fields=["stato"])

            _allega_visure(request, cliente)

            # 🔹 se la nota non è vuota ed è cambiata rispetto a prima
            if cliente.note and cliente.note != old_note:
                # proviamo a trovare una nota esistente con il vecchio testo
                nota_esistente = None
                if old_note:
                    nota_esistente = (
                        cliente.note_entries
                        .filter(testo=old_note)
                        .order_by("-creata_il")
                        .first()
                    )

                if nota_esistente:
                    # aggiorniamo quella esistente
                    nota_esistente.testo = cliente.note
                    nota_esistente.autore = getattr(request, "user", None)
                    # se vuoi aggiornare anche la data:
                    # nota_esistente.creata_il = timezone.now()
                    nota_esistente.save()
                else:
                    # altrimenti ne creiamo una nuova
                    Nota.objects.create(
                        cliente=cliente,
                        testo=cliente.note,
                        autore=getattr(request, "user", None),
                    )

            messages.success(request, "Cliente aggiornato.")
            return redirect("cliente_dettaglio", cliente_id=cliente.id)

        messages.error(request, "Controlla i campi: ci sono errori nel form.")
    else:
        form = ClienteForm(instance=cliente)

    return render(
        request,
        "crm/cliente_form.html",
        {"form": form, "is_edit": True, "cliente": cliente},
    )



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
    return render(request, "crm/cliente_elimina.html", {"cliente": cliente})


# ==============================
# Documenti
# ==============================
@login_required
@user_passes_test(has_portal_access)
@require_http_methods(["GET", "POST"])
def documento_nuovo(request, cliente_id):
    cliente = get_object_or_404(Cliente, pk=cliente_id)

    # categoria proposta dalla tab (es. ?categoria=visure)
    categoria_param = request.GET.get("categoria")
    initial = {}

    # verifico che sia una categoria valida
    valid_codes = {code for code, _ in DocumentoCliente.Categoria.choices}
    if categoria_param in valid_codes:
        initial["categoria"] = categoria_param

    if request.method == "POST":
        files = request.FILES.getlist("file")  # <- nome del field del form

        # passa anche request.FILES così il form vede almeno un file
        form = DocumentoForm(request.POST, request.FILES if files else None)

        if not files:
            # niente file selezionati
            form.add_error("file", "Seleziona almeno un file.")

        if form.is_valid() and files:
            categoria = form.cleaned_data["categoria"]
            descr_input = (form.cleaned_data.get("descrizione") or "").strip()

            created = 0
            for f in files:
                doc = DocumentoCliente(
                    cliente=cliente,
                    categoria=categoria,
                    descrizione=descr_input,  # <- solo la descrizione scritta dall'utente
                    file=f,
                )
                doc.full_clean()
                doc.save()
                try:
                    notify_doc(actor=request.user, cliente=cliente, documento=doc)
                except Exception:
                    pass
                created += 1

            messages.success(request, f"Caricati {created} documento/i.")

            # dopo l'upload torno al cliente sulla stessa tab della categoria
            url = reverse("cliente_dettaglio", kwargs={"cliente_id": cliente.id})
            return redirect(f"{url}?tab={categoria}")

        # form non valido → torna al template con gli errori
        return render(request, "crm/documento_form.html", {"form": form, "cliente": cliente})

    # GET → mostra il form, con categoria precompilata se arrivata da ?categoria=
    form = DocumentoForm(initial=initial)
    return render(request, "crm/documento_form.html", {"form": form, "cliente": cliente})







@login_required
@user_passes_test(has_portal_access)
@require_http_methods(["GET", "POST"])
def documento_elimina(request, doc_id):
    doc = get_object_or_404(DocumentoCliente, id=doc_id)
    cliente_id = doc.cliente.id

    # tab corrente: prima provo a leggerla dalla query (?tab=...),
    # se non c'è uso la categoria del documento
    tab = request.GET.get("tab") or doc.categoria

    if request.method == "POST":
        doc.delete()
        messages.success(request, "Documento eliminato.")

        # redirect alla pagina cliente mantenendo la stessa tab
        from django.urls import reverse  # se non è già importato in cima al file

        url = reverse("cliente_dettaglio", kwargs={"cliente_id": cliente_id})
        return redirect(f"{url}?tab={tab}")

    # in GET mostro la pagina di conferma, passando anche "tab"
    return render(
        request,
        "crm/documento_conferma_elimina.html",
        {"doc": doc, "tab": tab},
    )



@login_required
@user_passes_test(has_portal_access)
def documenti_zip_cliente(request, cliente_id):
    cliente = get_object_or_404(Cliente, pk=cliente_id)
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for d in cliente.documenti.all():
            if not getattr(d, "file", None):
                continue
            arcname = f"{d.categoria}/{os.path.basename(d.file.name)}"
            try:
                d.file.open("rb")
                zf.writestr(arcname, d.file.read())
            except Exception:
                pass
            finally:
                try:
                    d.file.close()
                except Exception:
                    pass
    buffer.seek(0)
    filename = f"documenti_cliente_{cliente.id}.zip"
    resp = HttpResponse(buffer.getvalue(), content_type="application/zip")
    resp["Content-Disposition"] = f'attachment; filename="{filename}"'
    return resp


# ==============================
# Pratiche
# ==============================
@login_required
@user_passes_test(has_portal_access)
@require_http_methods(["GET", "POST"])
def pratica_nuova(request, cliente_id):
    cliente = get_object_or_404(Cliente, id=cliente_id)
    if request.method == "POST":
        form = PraticaForm(request.POST)
        if form.is_valid():
            p = form.save(commit=False)
            p.cliente = cliente
            p.save()
            messages.success(request, "Pratica creata.")
            return redirect("cliente_dettaglio", cliente_id=cliente.id)
        messages.error(request, "Controlla i campi: ci sono errori nel form.")
    else:
        form = PraticaForm()
    return render(request, "crm/pratica_form.html", {"form": form, "cliente": cliente})


@login_required
@user_passes_test(has_portal_access)
@require_http_methods(["GET", "POST"])
def pratica_modifica(request, pratica_id):
    pratica = get_object_or_404(Pratiche, id=pratica_id)
    if request.method == "POST":
        form = PraticaForm(request.POST, instance=pratica)
        if form.is_valid():
            form.save()
            messages.success(request, "Pratica aggiornata.")
            return redirect("cliente_dettaglio", cliente_id=pratica.cliente.id)
        messages.error(request, "Controlla i campi: ci sono errori nel form.")
    else:
        form = PraticaForm(instance=pratica)
    return render(
        request,
        "crm/pratica_form.html",
        {"form": form, "cliente": pratica.cliente, "is_edit": True},
    )


@login_required
@user_passes_test(has_portal_access)
@require_http_methods(["GET", "POST"])
def pratica_elimina(request, pratica_id):
    pratica = get_object_or_404(Pratiche, id=pratica_id)
    cliente_id = pratica.cliente.id
    if request.method == "POST":
        pratica.delete()
        messages.success(request, "Pratica eliminata.")
        return redirect("cliente_dettaglio", cliente_id=cliente_id)
    return render(request, "crm/pratica_conferma_elimina.html", {"pratica": pratica})


# ==============================
# Note
# ==============================


@login_required
@user_passes_test(has_portal_access)
@require_POST
def nota_crea(request, cliente_id):
    cliente = get_object_or_404(Cliente, pk=cliente_id)
    form = NotaForm(request.POST)
    if form.is_valid():
        nota = form.save(commit=False)
        nota.cliente = cliente
        # imposta autore (fullname se presente, altrimenti username)
        nota.autore = (getattr(request.user, "get_full_name", lambda: "")() or "").strip() or request.user.username
        nota.save()
        messages.success(request, "Nota aggiunta.")
    else:
        messages.error(request, "Impossibile salvare la nota.")
    return redirect("cliente_dettaglio", cliente_id=cliente.id)

@login_required
@user_passes_test(has_portal_access)
@require_http_methods(["GET", "POST"])
def nota_modifica(request, nota_id):
    nota = get_object_or_404(Nota, pk=nota_id)
    cliente = nota.cliente
    if request.method == "POST":
        form = NotaForm(request.POST, instance=nota)
        if form.is_valid():
            form.save()
            messages.success(request, "Nota aggiornata.")
            return redirect("cliente_dettaglio", cliente_id=cliente.id)
        messages.error(request, "Controlla i campi: ci sono errori nel form.")
    else:
        form = NotaForm(instance=nota)
    return render(request, "crm/nota_form.html", {
        "form": form,
        "cliente": cliente,
        "nota": nota,
        "is_edit": True,
    })


@login_required
@user_passes_test(has_portal_access)
@require_http_methods(["GET", "POST"])
def nota_elimina(request, nota_id):
    nota = get_object_or_404(Nota, pk=nota_id)
    cliente_id = nota.cliente.id
    if request.method == "POST":
        nota.delete()
        messages.success(request, "Nota eliminata.")
        return redirect("cliente_dettaglio", cliente_id=cliente_id)
    return render(request, "crm/nota_conferma_elimina.html", {"nota": nota})


# ==============================
# Lead – lista/filtri/CRUD
# ==============================
@login_required
@user_passes_test(has_portal_access)
def lead_lista(request):
    qs = Lead.objects.filter(is_archiviato=False).select_related("consulente")

    # --- Filtri esistenti ---
    q = request.GET.get("q", "").strip()
    stato = request.GET.get("stato", "").strip()
    dal_raw = request.GET.get("dal", "").strip()
    al_raw = request.GET.get("al", "").strip()

    only_no_risposta = request.GET.get("no_risposta", "") == "1"
    only_msg_inviato = request.GET.get("msg_inviato", "") == "1"
    only_acquisizione = request.GET.get("in_acquisizione", "") == "1"
    richiamo_da_raw = request.GET.get("richiamo_da", "").strip()
    richiamo_a_raw = request.GET.get("richiamo_a", "").strip()

    # --- NUOVI FILTRI ---
    provenienza = request.GET.get("provenienza", "").strip()   # 'tiktok' | 'meta' | 'google' | 'passaparola'
    consulente_id = request.GET.get("consulente", "").strip()  # id numerico

    if q:
        qs = qs.filter(
            Q(nome__icontains=q) |
            Q(cognome__icontains=q) |
            Q(email__icontains=q) |
            Q(telefono__icontains=q)
        )
    if stato in {"in_corso", "negativo", "positivo"}:
        qs = qs.filter(stato=stato)

    dal = _parse_date(dal_raw)
    al = _parse_date(al_raw)
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

    richiamo_da = _parse_date(richiamo_da_raw)
    richiamo_a = _parse_date(richiamo_a_raw)
    if richiamo_da:
        qs = qs.filter(richiamare_il__date__gte=richiamo_da)
    if richiamo_a:
        qs = qs.filter(richiamare_il__date__lte=richiamo_a)

    # Quick filter appuntamenti
    appt = request.GET.get("appt", "").strip()
    start, end = _appt_range(appt)
    if start and end:
        qs = qs.filter(
            appuntamento_previsto__date__gte=start,
            appuntamento_previsto__date__lte=end
        )

    # Applica nuovi filtri
    if provenienza in dict(Lead.Provenienza.choices):
        qs = qs.filter(provenienza=provenienza)
    if consulente_id.isdigit():
        qs = qs.filter(consulente_id=int(consulente_id))

    # --- SORT ---
    sort_raw = request.GET.get("sort", "").strip()
    sort_map = {
        "nome": "nome", "-nome": "-nome",
        "cognome": "cognome", "-cognome": "-cognome",
        "creato_il": "creato_il", "-creato_il": "-creato_il",
        "appuntamento_previsto": "appuntamento_previsto", "-appuntamento_previsto": "-appuntamento_previsto",
        "richiamare_il": "richiamare_il", "-richiamare_il": "-richiamare_il",
        "primo_contatto": "primo_contatto", "-primo_contatto": "-primo_contatto",
        "provenienza": "provenienza", "-provenienza": "-provenienza",
        "consulente": "consulente__nome", "-consulente": "-consulente__nome",
    }
    sort = sort_map.get(sort_raw, "-creato_il")
    qs = qs.order_by(sort)

    ha_negativi = qs.filter(stato="negativo").exists()

    # --- Paginazione ---
    per_page = _get_per_page(request, 20, 100)
    paginator = Paginator(qs, per_page)
    page_obj = paginator.get_page(request.GET.get("page"))

    consulenti = Consulente.objects.filter(is_active=True).order_by("nome")

    return render(request, "crm/lead_lista.html", {
        "leads": page_obj.object_list,
        "page_obj": page_obj,
        "q": q, "stato": stato, "dal": dal_raw, "al": al_raw,
        "no_risposta": "1" if only_no_risposta else "",
        "msg_inviato": "1" if only_msg_inviato else "",
        "in_acquisizione": "1" if only_acquisizione else "",
        "richiamo_da": richiamo_da_raw, "richiamo_a": richiamo_a_raw,
        "sort": sort_raw, "ha_negativi": ha_negativi, "per": per_page,
        "provenienza": provenienza,
        "consulente_sel": consulente_id,
        "consulenti": consulenti,
        "PROVENIENZA_CHOICES": Lead.Provenienza.choices,
        "appt": appt,
    })


@login_required
@user_passes_test(has_portal_access)
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
        messages.error(request, "Controlla i campi: ci sono errori nel form.")
    else:
        form = LeadForm()
    return render(request, "crm/lead_form.html", {"form": form})


@login_required
@user_passes_test(has_portal_access)
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
        messages.error(request, "Controlla i campi: ci sono errori nel form.")
    else:
        form = LeadForm(instance=lead)
    return render(request, "crm/lead_form.html", {"form": form, "lead": lead, "is_edit": True})

# Scheda Lead

@login_required
@user_passes_test(has_portal_access)
def lead_dettaglio(request, lead_id):
    lead = get_object_or_404(Lead, pk=lead_id, is_archiviato=False)
    schede = SchedaConsulenza.objects.filter(lead=lead).order_by("-created_at")
    return render(request, "crm/lead_dettaglio.html", {
        "lead": lead,
        "schede_consulenza": schede,
    })


@login_required
@user_passes_test(has_portal_access)
@require_http_methods(["GET", "POST"])
def scheda_consulenza_nuova(request, *, cliente_id=None, lead_id=None):
    cliente = get_object_or_404(Cliente, pk=cliente_id) if cliente_id else None
    lead = get_object_or_404(Lead, pk=lead_id) if lead_id else None

    if request.method == "POST":
        form = SchedaConsulenzaForm(request.POST)
        if form.is_valid():
            s = form.save(commit=False)
            # lega in modo sicuro per id (evita qualsiasi mismatch di FK/istanze)
            s.cliente_id = cliente_id or None
            s.lead_id = lead_id or None
            s.compilata_da = request.user
            s.save()
            messages.success(request, "Scheda di consulenza salvata.")
            if cliente_id:
                return redirect("cliente_dettaglio", cliente_id=cliente_id)
            if lead_id:
                return redirect("lead_dettaglio", lead_id=lead_id)
            return redirect("dashboard")
        messages.error(request, "Controlla i campi: ci sono errori nel form.")
    else:
        form = SchedaConsulenzaForm()

    return render(
        request,
        "crm/scheda_consulenza_form.html",
        {"form": form, "cliente": cliente, "lead": lead}
    )

# ==============================
# Lead toggles (POST only)
# ==============================
@login_required
@user_passes_test(has_portal_access)
@require_POST
def lead_toggle_msg(request, lead_id):
    lead = get_object_or_404(Lead, pk=lead_id)
    lead.messaggio_inviato = not lead.messaggio_inviato
    lead.save(update_fields=["messaggio_inviato"])
    return redirect(_back(request))


@login_required
@user_passes_test(has_portal_access)
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
@user_passes_test(has_portal_access)
@require_POST
def lead_toggle_consulenza(request, lead_id):
    lead = get_object_or_404(Lead, pk=lead_id)
    lead.consulenza_effettuata = not lead.consulenza_effettuata
    lead.save(update_fields=["consulenza_effettuata"])
    return redirect(_back(request))

# NOTIFICHE

def _go_back(request, fallback="dashboard"):
    # torna alla pagina precedente o a una fallback url name
    return redirect(request.POST.get("next") or request.META.get("HTTP_REFERER") or fallback)


@require_POST
@login_required
def notifiche_segna_letto(request, notifica_id):
    Notifica.objects.filter(pk=notifica_id).update(is_read=True)
    messages.success(request, "Notifica segnata come letta.")
    return _go_back(request)

@require_POST
@login_required
def notifiche_segna_tutte_lette(request):
    Notifica.objects.filter(is_read=False).update(is_read=True)
    messages.success(request, "Tutte le notifiche segnate come lette.")
    return _go_back(request)


@login_required
def notifiche_lista(request):
    """
    Pagina semplice con tutte le notifiche (opzionale).
    """
    qs = Notifica.objects.select_related("cliente", "actor").order_by("-created_at")
    return render(request, "crm/notifiche_lista.html", {"notifiche": qs})

# ==============================
# Schede di consulenza
# ==============================
# --- Schede consulenza: dettaglio / modifica / elimina ---

@login_required
@user_passes_test(has_portal_access)
def scheda_consulenza_dettaglio(request, scheda_id: int):
    scheda = get_object_or_404(SchedaConsulenza, pk=scheda_id)
    # Passo lo stesso oggetto con più chiavi per compatibilità con il tuo template
    return render(
        request,
        "crm/scheda_consulenza_dettaglio.html",  # <-- usa il tuo template esistente
        {"scheda": scheda, "object": scheda, "s": scheda}
    )

@login_required
@user_passes_test(has_portal_access)
@require_http_methods(["GET", "POST"])
def scheda_consulenza_modifica(request, scheda_id: int):
    scheda = get_object_or_404(SchedaConsulenza, pk=scheda_id)
    if request.method == "POST":
        form = SchedaConsulenzaForm(request.POST, instance=scheda)
        if form.is_valid():
            form.save()
            messages.success(request, "Scheda di consulenza aggiornata.")
            # torna alla pagina del cliente/lead se presente
            if scheda.cliente_id:
                return redirect("cliente_dettaglio", cliente_id=scheda.cliente_id)
            if scheda.lead_id:
                return redirect("lead_dettaglio", lead_id=scheda.lead_id)
            return redirect("dashboard")
        messages.error(request, "Controlla i campi: ci sono errori nel form.")
    else:
        form = SchedaConsulenzaForm(instance=scheda)
    return render(request, "crm/scheda_consulenza_form.html", {"form": form, "scheda": scheda, "is_edit": True})

@login_required
@user_passes_test(has_portal_access)
@require_http_methods(["GET", "POST"])
def scheda_consulenza_elimina(request, scheda_id: int):
    scheda = get_object_or_404(SchedaConsulenza, pk=scheda_id)
    # Solo admin può eliminare
    if not (request.user.is_superuser or getattr(getattr(request.user, "profiloutente", None), "ruolo", "") == "admin"):
        return HttpResponseForbidden("Solo gli admin possono eliminare le schede.")
    if request.method == "POST":
        dst = "dashboard"
        if scheda.cliente_id:
            dst = ("cliente_dettaglio", {"cliente_id": scheda.cliente_id})
        elif scheda.lead_id:
            dst = ("lead_dettaglio", {"lead_id": scheda.lead_id})
        scheda.delete()
        messages.success(request, "Scheda di consulenza eliminata.")
        if isinstance(dst, tuple):
            name, kwargs = dst
            return redirect(name, **kwargs)
        return redirect(dst)
    return render(request, "crm/scheda_consulenza_conferma_elimina.html", {"scheda": scheda})

