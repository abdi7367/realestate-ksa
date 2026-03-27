from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.core.exceptions import ValidationError

from .models import Contract, Payment
from .serializers import ContractSerializer, PaymentSerializer, ContractSummarySerializer
from .services import ContractService, PaymentService


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
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        serializer = ContractSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        d = serializer.validated_data

        try:
            contract = ContractService.create_contract(
                property_unit=d['unit'],
                tenant=d['tenant'],
                monthly_rent=d['monthly_rent'],
                start_date=d['start_date'],
                duration_months=d['duration_months'],
                created_by=request.user,
            )
        except ValidationError as e:
            return Response(
                {'success': False, 'error': str(e.message)},
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
                {'success': False, 'error': str(e.message)},
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
        'contract', 'recorded_by'
    )   # Fix N+1 — Step 3
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]

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
            )
        except ValidationError as e:
            return Response(
                {'success': False, 'error': str(e.message)},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(
            {'success': True, 'data': PaymentSerializer(payment).data},
            status=status.HTTP_201_CREATED
        )