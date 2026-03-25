from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import Voucher
from .serializers import VoucherSerializer


class VoucherViewSet(viewsets.ModelViewSet):
    queryset = Voucher.objects.all()
    serializer_class = VoucherSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['property', 'approval_status', 'payment_method']
    search_fields = ['voucher_number', 'payee_name', 'description']

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        voucher = self.get_object()
        role = request.user.role
        transitions = {
            'draft': ('accountant', 'pending_accountant'),
            'pending_accountant': ('accountant', 'pending_finance'),
            'pending_finance': ('property_manager', 'pending_admin'),
            'pending_admin': ('admin', 'approved'),
        }
        current = voucher.approval_status
        if current in transitions:
            required_role, next_status = transitions[current]
            if role == required_role or role == 'admin':
                voucher.approval_status = next_status
                voucher.approved_by = request.user
                voucher.save()
                return Response({'status': next_status})
        return Response({'error': 'Not authorized or invalid transition'}, status=403)
