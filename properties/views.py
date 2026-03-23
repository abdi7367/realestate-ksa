from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import Property, PropertyUnit
from .serializers import PropertySerializer, PropertyUnitSerializer


class PropertyViewSet(viewsets.ModelViewSet):
    queryset = Property.objects.all()
    serializer_class = PropertySerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['property_type', 'city']
    search_fields = ['name', 'city', 'district']

    @action(detail=True, methods=['get'])
    def units(self, request, pk=None):
        property = self.get_object()
        units = property.units.all()
        serializer = PropertyUnitSerializer(units, many=True)
        return Response(serializer.data)


class PropertyUnitViewSet(viewsets.ModelViewSet):
    queryset = PropertyUnit.objects.all()
    serializer_class = PropertyUnitSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['rental_status', 'unit_type', 'property']