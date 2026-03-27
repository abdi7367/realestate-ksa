from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import Property, PropertyUnit
from .serializers import PropertySerializer, PropertyUnitSerializer


class PropertyViewSet(viewsets.ModelViewSet):
    queryset = Property.objects.all()  # needed by DRF router for basename
    serializer_class = PropertySerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['property_type', 'city']
    search_fields = ['name', 'city', 'district']

    def get_queryset(self):
        """
        FIX: prefetch_related('units') prevents N+1 queries.
        Without this, accessing property.units in the serializer
        fires a separate SQL query for EVERY property in the list.
        select_related('property_manager') fixes the manager lookup too.
        """
        return Property.objects.select_related(
            'property_manager'
        ).prefetch_related(
            'units'
        )

    @action(detail=True, methods=['get'])
    def units(self, request, pk=None):
        property_obj = self.get_object()
        # units are already prefetched — no extra query here
        units = property_obj.units.all()
        serializer = PropertyUnitSerializer(units, many=True)
        return Response(serializer.data)


class PropertyUnitViewSet(viewsets.ModelViewSet):
    queryset = PropertyUnit.objects.all()  # needed by DRF router for basename
    serializer_class = PropertyUnitSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['rental_status', 'unit_type', 'property']

    def get_queryset(self):
        return PropertyUnit.objects.select_related('property')