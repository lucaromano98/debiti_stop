from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ClienteViewSet, LeadViewSet  # importa le tue viewset

router = DefaultRouter()
router.register(r"clienti", ClienteViewSet, basename="clienti")
router.register(r"leads", LeadViewSet, basename="leads")

urlpatterns = [
    path("", include(router.urls)),
]
