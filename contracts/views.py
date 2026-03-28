from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, viewsets, status
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.decorators import action
from rest_framework.response import Response

from accounts.permissions import ContractManagementPermission, PaymentManagementPermission
from .filters import (
    ContractFilter,
    ContractSearchFilter,
    PaymentFilter,
    PaymentSearchFilter,
)
from .models import Contract, Payment, Tenant
from .serializers import ContractSerializer, PaymentSerializer, ContractSummarySerializer
from .services import ContractService, PaymentService


def _validation_error_message(exc: ValidationError) -> str:
    """Format Django ValidationError for JSON responses (Django 4+ uses .messages, not .message)."""
    if getattr(exc, 'message_dict', None):
        parts = []
        for field, msgs in exc.message_dict.items():
            parts.append(f'{field}: {"; ".join(str(m) for m in msgs)}')
        return ' '.join(parts)
    msgs = getattr(exc, 'messages', None)
    if msgs:
        return '; '.join(str(m) for m in msgs)
    return str(exc)


class ContractViewSet(viewsets.ModelViewSet):
    """
    Views are THIN — they only:
    1. Parse the request
    2. Call the service
    3. Return the response

    Zero business logic here.
    """
    queryset = Contract.objects.select_related(
        'unit', 'unit__property', 'tenant', 'created_by'
    ).prefetch_related('payments')   # Fix N+1 — Step 3
    serializer_class = ContractSerializer
    permission_classes = [ContractManagementPermission]
    filter_backends = [
        DjangoFilterBackend,
        ContractSearchFilter,
        filters.OrderingFilter,
    ]
    filterset_class = ContractFilter
    search_fields = [
        'unit__property__name',
        'unit__unit_number',
        'tenant__full_name',
        'tenant__national_id',
        'tenant__tenant_reference',
        'tenant__phone',
        'tenant__email',
    ]
    ordering_fields = [
        'start_date',
        'end_date',
        'created_at',
        'id',
        'monthly_rent',
        'status',
    ]
    ordering = ['-start_date']

    def perform_update(self, serializer):
        try:
            with transaction.atomic():
                contract = serializer.save()
                ContractService.sync_financials_from_lease_terms(contract)
        except ValidationError as e:
            raise DRFValidationError(_validation_error_message(e))

    def create(self, request, *args, **kwargs):
        serializer = ContractSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        d = serializer.validated_data
        tenant_data = d.pop('tenant_data', None)
        if not tenant_data:
            return Response(
                {
                    'success': False,
                    'error': 'tenant_data is required (full name, national ID / Iqama, etc.).',
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        tenant = Tenant.objects.create(**tenant_data)

        try:
            contract = ContractService.create_contract(
                property_unit=d['unit'],
                tenant=tenant,
                monthly_rent=d['monthly_rent'],
                start_date=d['start_date'],
                duration_months=d['duration_months'],
                created_by=request.user,
                security_deposit=d.get('security_deposit') or Decimal('0'),
                payment_schedule=d.get('payment_schedule') or 'monthly',
                security_deposit_paid=d.get('security_deposit_paid') or False,
                security_deposit_received_on=d.get('security_deposit_received_on'),
            )
        except ValidationError as e:
            return Response(
                {'success': False, 'error': _validation_error_message(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(
            {'success': True, 'data': ContractSerializer(contract).data},
            status=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=['post'])
    def terminate(self, request, pk=None):
        contract = self.get_object()
        reason = request.data.get('reason', '')

        try:
            contract = ContractService.terminate_contract(
                contract=contract,
                terminated_by=request.user,
                reason=reason,
            )
        except ValidationError as e:
            return Response(
                {'success': False, 'error': _validation_error_message(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response({'success': True, 'data': ContractSerializer(contract).data})

    @action(detail=True, methods=['get'])
    def summary(self, request, pk=None):
        contract = self.get_object()
        summary = PaymentService.get_payment_summary(contract)
        return Response({'success': True, 'data': summary})


class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.select_related(
        'contract',
        'contract__tenant',
        'contract__unit',
        'contract__unit__property',
        'recorded_by',
    )
    serializer_class = PaymentSerializer
    permission_classes = [PaymentManagementPermission]
    filter_backends = [
        DjangoFilterBackend,
        PaymentSearchFilter,
        filters.OrderingFilter,
    ]
    filterset_class = PaymentFilter
    search_fields = [
        'notes',
        'contract__tenant__full_name',
        'contract__tenant__national_id',
        'contract__tenant__tenant_reference',
        'contract__tenant__phone',
        'contract__tenant__email',
        'contract__unit__property__name',
        'contract__unit__unit_number',
    ]
    ordering_fields = ['payment_date', 'amount', 'created_at', 'id', 'due_date']
    ordering = ['-payment_date']

    def create(self, request, *args, **kwargs):
        serializer = PaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        d = serializer.validated_data

        try:
            payment = PaymentService.record_payment(
                contract=d['contract'],
                amount=d['amount'],
                payment_date=d['payment_date'],
                payment_method=d['payment_method'],
                recorded_by=request.user,
                notes=d.get('notes', ''),
                due_date=d.get('due_date'),
            )
        except ValidationError as e:
            return Response(
                {'success': False, 'error': _validation_error_message(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(
            {'success': True, 'data': PaymentSerializer(payment).data},
            status=status.HTTP_201_CREATED
        )