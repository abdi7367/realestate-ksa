from rest_framework import viewsets
from django_filters.rest_framework import DjangoFilterBackend

from accounts.permissions import OwnershipManagementPermission
from .models import PropertyOwnership
from .serializers import PropertyOwnershipSerializer


class PropertyOwnershipViewSet(viewsets.ModelViewSet):
    queryset = PropertyOwnership.objects.all()
    serializer_class = PropertyOwnershipSerializer
    permission_classes = [OwnershipManagementPermission]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['property', 'ownership_type']
