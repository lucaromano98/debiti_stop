from django.shortcuts import render
from django.contrib.auth.views import LoginView
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
# Create your views here.

# Login 
class CustomLoginView(LoginView):
    template_name = 'crm/login.html'

def home_redirect(request):
    return redirect('login')

@login_required
def dashboard(request):
    return render(request, 'crm/dashboard.html')

def clienti_tutti(request):
    return render(request, 'crm/dashboard.html')

def clienti_legali(request):
    return render(request, 'crm/dasboard.html')

def clienti_attivi(request):
    return render(request, 'crm/dasboard.html')

def clienti_non_attivi(request):
    return render(request, 'crm/dasboard.html')

def cliente_nuovo(request):
    return render(request, 'crm/dasboard.html')