from django.urls import path, include
from django.contrib.auth.views import LogoutView
from django.contrib.auth import views as auth_views
from .views import CustomLoginView, notifiche_segna_letto,notifiche_segna_tutte_lette,notifiche_lista ,lead_toggle_no_risposta, lead_toggle_consulenza, lead_toggle_msg,lead_modifica,lead_lista, lead_nuovo, documenti_zip_cliente, dashboard, home_redirect, clienti_tutti, clienti_legali, clienti_attivi, clienti_non_attivi, cliente_nuovo, clienti_dettaglio, cliente_modifica, cliente_elimina, documento_nuovo, documento_elimina, pratica_nuova, pratica_modifica, pratica_elimina
from .views import nota_crea, nota_modifica, nota_elimina, lead_dettaglio, scheda_consulenza_nuova
from rest_framework.routers import DefaultRouter
from crm.api.views import ClienteViewSet, LeadViewSet
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView


router = DefaultRouter()
router.register(r"clienti", ClienteViewSet, basename="api-clienti")
router.register(r"leads", LeadViewSet, basename="api-leads")

urlpatterns = [
    path('', home_redirect, name='home'),  # root → login
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('dashboard/', dashboard, name='dashboard'),

    # Reset password (4 step classici)
    path('password-reset/', 
         auth_views.PasswordResetView.as_view(template_name='crm/password_reset_form.html'),
         name='password_reset'),
    path('password-reset/done/', 
         auth_views.PasswordResetDoneView.as_view(template_name='crm/password_reset_done.html'),
         name='password_reset_done'),
    path('reset/<uidb64>/<token>/', 
         auth_views.PasswordResetConfirmView.as_view(template_name='crm/password_reset_confirm.html'),
         name='password_reset_confirm'),
    path('reset/done/', 
         auth_views.PasswordResetCompleteView.as_view(template_name='crm/password_reset_complete.html'),
         name='password_reset_complete'),

    # Clienti
    path('clienti/', clienti_tutti, name='clienti_tutti'),
    path('clienti/legali/', clienti_legali, name='clienti_legali'),
    path('clienti/attivi/', clienti_attivi, name='clienti_attivi'),
    path('clienti/non_attivi/', clienti_non_attivi, name='clienti_non_attivi'),
    path('clienti/nuovo/', cliente_nuovo, name='cliente_nuovo'),
    path("clienti/<int:cliente_id>/", clienti_dettaglio, name="cliente_dettaglio"),
    path("clienti/<int:cliente_id>/modifica/", cliente_modifica, name="cliente_modifica"),
    path("clienti/<int:cliente_id>/elimina/", cliente_elimina, name="cliente_elimina"),
    #Scheda consulenza cliente
    path("clienti/<int:cliente_id>/schede/nuova/", scheda_consulenza_nuova, {"cliente_id": None}, name="scheda_consulenza_nuova_cliente"),
    path("clienti/<int:cliente_id>/scheda-consulenza/nuova/", scheda_consulenza_nuova, name="scheda_consulenza_nuova_cliente"),

    #Leads  
    path("leads/", lead_lista, name="lead_lista"),
    path("leads/nuovo/", lead_nuovo, name="lead_nuovo"),
    path("leads/<int:lead_id>/modifica/", lead_modifica, name="lead_modifica"),
    path("leads/<int:lead_id>/", lead_dettaglio, name="lead_dettaglio"),
    #scheda consulenza lead     
    path("leads/<int:lead_id>/scheda-consulenza/nuova/", scheda_consulenza_nuova, name="scheda_consulenza_nuova_lead"),

   
    # Documenti
    path("clienti/<int:cliente_id>/documenti/nuovo/", documento_nuovo, name="documento_nuovo"),
    path("documenti/<int:doc_id>/elimina/", documento_elimina, name="documento_elimina"),
    path("clienti/<int:cliente_id>/documenti/zip/", documenti_zip_cliente, name="documenti_zip_cliente"),

    # Pratiche
    path("clienti/<int:cliente_id>/pratiche/nuova/", pratica_nuova, name="pratica_nuova"),
    path("pratiche/<int:pratica_id>/modifica/", pratica_modifica, name="pratica_modifica"),
    path("pratiche/<int:pratica_id>/elimina/", pratica_elimina, name="pratica_elimina"),

    # Note
    path("clienti/<int:cliente_id>/note/nuova/", nota_crea, name="nota_crea"),
    path("note/<int:nota_id>/modifica/", nota_modifica, name="nota_modifica"),
    path("note/<int:nota_id>/elimina/", nota_elimina, name="nota_elimina"),

    # API Token (JWT)
    path("api/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/", include(router.urls)),  # API routes   

    # consulenza e messaggi
    path("leads/<int:lead_id>/toggle-consulenza/", lead_toggle_consulenza, name="lead_toggle_consulenza"),
    path("leads/<int:lead_id>/toggle-no-risposta/", lead_toggle_no_risposta, name="lead_toggle_no_risposta"),
    path("leads/<int:lead_id>/toggle-msg/", lead_toggle_msg, name="lead_toggle_msg"),

     # notifiche
     path("notifiche/<int:notifica_id>/letto/", notifiche_segna_letto, name="notifiche_segna_letto"),
     path("notifiche/letto/tutte/", notifiche_segna_tutte_lette, name="notifiche_segna_tutte_lette"),
     path("notifiche/", notifiche_lista, name="notifiche_lista"),
    
     path("clienti/<int:cliente_id>/consulenza/nuova/",
          scheda_consulenza_nuova, name="scheda_consulenza_nuova_per_cliente"),
     path("leads/<int:lead_id>/consulenza/nuova/",
           scheda_consulenza_nuova, name="scheda_consulenza_nuova_per_lead"),

]
