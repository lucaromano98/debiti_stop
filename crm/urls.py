from django.urls import path
from django.contrib.auth.views import LogoutView
from .views import CustomLoginView, dashboard, home_redirect, clienti_tutti, clienti_legali, clienti_attivi, clienti_non_attivi, cliente_nuovo, clienti_dettaglio, cliente_modifica, cliente_elimina, documento_nuovo, documento_elimina, pratica_nuova, pratica_modifica, pratica_elimina
from .views import nota_crea, nota_modifica, nota_elimina

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
    path("clienti/<int:cliente_id>/", clienti_dettaglio, name="cliente_dettaglio"),
    path("clienti/<int:cliente_id>/modifica/", cliente_modifica, name="cliente_modifica"),
    path("clienti/<int:cliente_id>/elimina/", cliente_elimina, name="cliente_elimina"),
    path("clienti/<int:cliente_id>/documenti/nuovo/", documento_nuovo, name="documento_nuovo"),
    path("documenti/<int:doc_id>/elimina/", documento_elimina, name="documento_elimina"),
     path("clienti/<int:cliente_id>/pratiche/nuova/", pratica_nuova, name="pratica_nuova"),
    path("pratiche/<int:pratica_id>/modifica/", pratica_modifica, name="pratica_modifica"),
    path("pratiche/<int:pratica_id>/elimina/", pratica_elimina, name="pratica_elimina"),

    #Note
    path("clienti/<int:cliente_id>/note/nuova/", nota_crea, name="nota_crea"),
    path("note/<int:nota_id>/modifica/", nota_modifica, name="nota_modifica"),
    path("note/<int:nota_id>/elimina/", nota_elimina, name="nota_elimina"),
]
