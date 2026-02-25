from django.urls import path, include
from django.contrib.auth.views import LogoutView
from django.contrib.auth import views as auth_views
from . import views

from .views import (
    # auth / base
    CustomLoginView, dashboard, home_redirect,
    # clienti
    clienti_tutti, clienti_legali, clienti_attivi, clienti_non_attivi,
    cliente_nuovo, clienti_dettaglio, cliente_modifica, cliente_elimina,
    # documenti
    documento_nuovo, documento_elimina, documenti_zip_cliente,
    # pratiche
    pratica_nuova, pratica_modifica, pratica_elimina,
    # note
    nota_crea, nota_modifica, nota_elimina,
    # lead
    lead_lista, lead_nuovo, lead_modifica, lead_dettaglio,
    lead_toggle_consulenza, lead_toggle_no_risposta, lead_toggle_msg, lead_aggiorna_stato_operativo,
    # schede consulenza
    scheda_consulenza_nuova, scheda_consulenza_dettaglio,
    scheda_consulenza_modifica, scheda_consulenza_elimina, scheda_consulenza_pdf,
    # notifiche
    notifiche_segna_letto, notifiche_segna_tutte_lette, notifiche_lista,
)

from rest_framework.routers import DefaultRouter
from crm.api.views import ClienteViewSet, LeadViewSet
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

router = DefaultRouter()
router.register(r"clienti", ClienteViewSet, basename="api-clienti")
router.register(r"leads", LeadViewSet, basename="api-leads")

urlpatterns = [
    # root / auth / dashboard
    path("", home_redirect, name="home"),
    path("login/", CustomLoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("dashboard/", dashboard, name="dashboard"),

    # reset password
    path("password-reset/",
         auth_views.PasswordResetView.as_view(template_name="crm/password_reset_form.html"),
         name="password_reset"),
    path("password-reset/done/",
         auth_views.PasswordResetDoneView.as_view(template_name="crm/password_reset_done.html"),
         name="password_reset_done"),
    path("reset/<uidb64>/<token>/",
         auth_views.PasswordResetConfirmView.as_view(template_name="crm/password_reset_confirm.html"),
         name="password_reset_confirm"),
    path("reset/done/",
         auth_views.PasswordResetCompleteView.as_view(template_name="crm/password_reset_complete.html"),
         name="password_reset_complete"),

    # Clienti
    path("clienti/", clienti_tutti, name="clienti_tutti"),
    path("clienti/legali/", clienti_legali, name="clienti_legali"),
    path("clienti/attivi/", clienti_attivi, name="clienti_attivi"),
    path("clienti/non_attivi/", clienti_non_attivi, name="clienti_non_attivi"),
    path("clienti/nuovo/", cliente_nuovo, name="cliente_nuovo"),
    path("clienti/<int:cliente_id>/", clienti_dettaglio, name="cliente_dettaglio"),
    path("clienti/<int:cliente_id>/modifica/", cliente_modifica, name="cliente_modifica"),
    path("clienti/<int:cliente_id>/elimina/", cliente_elimina, name="cliente_elimina"),

    # Documenti
    path("clienti/<int:cliente_id>/documenti/nuovo/", documento_nuovo, name="documento_nuovo"),
    path("documenti/<int:doc_id>/elimina/", documento_elimina, name="documento_elimina"),
    path("clienti/<int:cliente_id>/documenti/zip/", documenti_zip_cliente, name="documenti_zip_cliente"),
    path("documenti/<int:documento_id>/modifica/", views.documento_modifica, name="documento_modifica"),

    # Pratiche
    path("clienti/<int:cliente_id>/pratiche/nuova/", pratica_nuova, name="pratica_nuova"),
    path("pratiche/<int:pratica_id>/modifica/", pratica_modifica, name="pratica_modifica"),
    path("pratiche/<int:pratica_id>/elimina/", pratica_elimina, name="pratica_elimina"),

    # Note
    path("clienti/<int:cliente_id>/note/nuova/", nota_crea, name="nota_crea"),
    path("note/<int:nota_id>/modifica/", nota_modifica, name="nota_modifica"),
    path("note/<int:nota_id>/elimina/", nota_elimina, name="nota_elimina"),

    # Lead
    path("leads/", lead_lista, name="lead_lista"),
    path("leads/nuovo/", lead_nuovo, name="lead_nuovo"),
    path("leads/<int:lead_id>/modifica/", lead_modifica, name="lead_modifica"),
    path("leads/<int:lead_id>/", lead_dettaglio, name="lead_dettaglio"),
    path("leads/<int:lead_id>/toggle-consulenza/", lead_toggle_consulenza, name="lead_toggle_consulenza"),
    path("leads/<int:lead_id>/toggle-no-risposta/", lead_toggle_no_risposta, name="lead_toggle_no_risposta"),
    path("leads/<int:lead_id>/toggle-msg/", lead_toggle_msg, name="lead_toggle_msg"),
    path("leads/<int:lead_id>/stato-operativo/", lead_aggiorna_stato_operativo, name="lead_aggiorna_stato_operativo"),

    # Schede di consulenza
    # — crea per CLIENTE (nome che il tuo template già usa)
    path("clienti/<int:cliente_id>/consulenza/nuova/", scheda_consulenza_nuova, name="scheda_consulenza_nuova"),
    # — crea per LEAD
    path("leads/<int:lead_id>/consulenza/nuova/", scheda_consulenza_nuova, name="scheda_consulenza_nuova_lead"),
    # — dettaglio / edit / delete (un solo set con 'scheda_id'), pdf
    path("consulenze/<int:scheda_id>/", scheda_consulenza_dettaglio, name="scheda_consulenza_dettaglio"),
    path("consulenze/<int:scheda_id>/modifica/", scheda_consulenza_modifica, name="scheda_consulenza_modifica"),
    path("consulenze/<int:scheda_id>/elimina/", scheda_consulenza_elimina, name="scheda_consulenza_elimina"),
    path("schede-consulenza/<int:scheda_id>/pdf/", scheda_consulenza_pdf, name="scheda_consulenza_pdf"),

    

    # Notifiche
    path("notifiche/<int:notifica_id>/letto/", notifiche_segna_letto, name="notifiche_segna_letto"),
    path("notifiche/letto/tutte/", notifiche_segna_tutte_lette, name="notifiche_segna_tutte_lette"),
    path("notifiche/", notifiche_lista, name="notifiche_lista"),

    # API / JWT
    path("api/", include(router.urls)),
    path("api/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
]
