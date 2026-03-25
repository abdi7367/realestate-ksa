from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Sum
from django_filters.rest_framework import DjangoFilterBackend
from .models import Transaction
from .serializers import TransactionSerializer


class TransactionViewSet(viewsets.ModelViewSet):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['property', 'transaction_type', 'category']
    search_fields = ['description', 'reference']

    @action(detail=False, methods=['get'])
    def summary(self, request):
        property_id = request.query_params.get('property_id')
        qs = self.get_queryset()
        if property_id:
            qs = qs.filter(property_id=property_id)
        income = qs.filter(transaction_type='income').aggregate(total=Sum('amount'))['total'] or 0
        expense = qs.filter(transaction_type='expense').aggregate(total=Sum('amount'))['total'] or 0
        return Response({'income': income, 'expense': expense, 'profit': income - expense})
