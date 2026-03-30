from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Sum
from django_filters.rest_framework import DjangoFilterBackend

from accounts.permissions import FinanceTransactionPermission
from .models import Transaction
from .serializers import TransactionSerializer
from .filters import TransactionFilter


class TransactionViewSet(viewsets.ModelViewSet):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer
    permission_classes = [FinanceTransactionPermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_class = TransactionFilter
    search_fields = ['description', 'reference']

    @action(detail=False, methods=['get'])
    def summary(self, request):
        property_id = request.query_params.get('property_id')
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')
        qs = self.get_queryset()
        if property_id:
            qs = qs.filter(property_id=property_id)
        if date_from:
            qs = qs.filter(date__gte=date_from)
        if date_to:
            qs = qs.filter(date__lte=date_to)
        income = qs.filter(transaction_type='income').aggregate(total=Sum('amount'))['total'] or 0
        expense = qs.filter(transaction_type='expense').aggregate(total=Sum('amount'))['total'] or 0
        return Response({'income': income, 'expense': expense, 'profit': income - expense})
