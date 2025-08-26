from django.urls import path
from django.contrib.auth.views import LogoutView
from .views import CustomLoginView, dashboard, home_redirect, clienti_tutti, clienti_legali, clienti_attivi, clienti_non_attivi, cliente_nuovo

urlpatterns = [
    path('', home_redirect, name='home'),  # root → login
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('dashboard/', dashboard, name='dashboard'),

    # Clienti
    path('clienti/', clienti_tutti, name='clienti_tutti'),
    path('clienti/legali/', clienti_legali, name='clienti_legali'),
    path('clienti/attivi/', clienti_attivi, name='clienti_attivi'),
    path('clienti/non_attivi/', clienti_non_attivi, name='clienti_non_attivi'),
    path('clienti/nuovo/', cliente_nuovo, name='cliente_nuovo'),
]
