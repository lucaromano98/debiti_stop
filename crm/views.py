from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.views import LoginView
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import Cliente
from .forms import ClienteForm, DocumentoForm

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
