from django.db.models import Prefetch
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from accounts.permissions import PropertyManagementPermission
from contracts.models import Contract
from .models import Property, PropertyUnit
from .serializers import PropertySerializer, PropertyUnitSerializer


class UnitPagination(PageNumberPagination):
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 1000


class PropertyViewSet(viewsets.ModelViewSet):
    queryset = Property.objects.all()  # needed by DRF router for basename
    serializer_class = PropertySerializer
    permission_classes = [PropertyManagementPermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['property_type', 'city']
    search_fields = ['name', 'city', 'district', 'property_code', 'location']

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
    permission_classes = [PropertyManagementPermission]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['rental_status', 'unit_type', 'property']
    pagination_class = UnitPagination

    def get_queryset(self):
        active_contracts = Prefetch(
            'contracts',
            queryset=Contract.objects.filter(
                status='active',
            ).select_related('tenant'),
            to_attr='active_contract_list',
        )
        return PropertyUnit.objects.select_related('property').prefetch_related(
            active_contracts
        )