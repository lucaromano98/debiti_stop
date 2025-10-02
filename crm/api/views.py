from rest_framework import viewsets, filters, permissions, status
from rest_framework.response import Response
from crm.models import Cliente, Lead
from .serializers import ClienteSerializer, LeadSerializer


class IsOperatore(permissions.BasePermission):
    def has_permission(self, request, view):
        u = request.user
        return u.is_authenticated and (
            hasattr(u, "profiloutente") and u.profiloutente.ruolo in ["operatore", "admin"]
        )


class ClienteViewSet(viewsets.ModelViewSet):
    queryset = Cliente.objects.all()
    serializer_class = ClienteSerializer
    permission_classes = [permissions.IsAuthenticated]

    def destroy(self, request, *args, **kwargs):
        prof = getattr(request.user, "profiloutente", None)
        if not prof or prof.ruolo != "admin":
            return Response(
                {"detail": "Solo gli admin possono eliminare clienti."},
                status=status.HTTP_403_FORBIDDEN,
            )
        return super().destroy(request, *args, **kwargs)


class LeadViewSet(viewsets.ModelViewSet):
    queryset = Lead.objects.filter(is_archiviato=False).order_by("-creato_il")
    serializer_class = LeadSerializer
    permission_classes = [IsOperatore]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["nome", "cognome", "email", "telefono"]
    ordering_fields = ["nome", "cognome", "creato_il", "stato"]
