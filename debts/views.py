from rest_framework import viewsets
from django_filters.rest_framework import DjangoFilterBackend

from accounts.permissions import DebtManagementPermission
from .models import Debt, DebtInstallment
from .serializers import DebtSerializer, DebtInstallmentSerializer


class DebtViewSet(viewsets.ModelViewSet):
    queryset = Debt.objects.all()
    serializer_class = DebtSerializer
    permission_classes = [DebtManagementPermission]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['property', 'debt_type']


class DebtInstallmentViewSet(viewsets.ModelViewSet):
    queryset = DebtInstallment.objects.all()
    serializer_class = DebtInstallmentSerializer
    permission_classes = [DebtManagementPermission]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['debt', 'status']
