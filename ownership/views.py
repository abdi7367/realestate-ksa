from rest_framework import viewsets
from django_filters.rest_framework import DjangoFilterBackend
from .models import PropertyOwnership
from .serializers import PropertyOwnershipSerializer


class PropertyOwnershipViewSet(viewsets.ModelViewSet):
    queryset = PropertyOwnership.objects.all()
    serializer_class = PropertyOwnershipSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['property', 'ownership_type']
