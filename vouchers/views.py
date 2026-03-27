from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import Voucher
from .serializers import VoucherSerializer


class VoucherViewSet(viewsets.ModelViewSet):
    queryset = Voucher.objects.select_related(
        'property', 'created_by', 'approved_by'
    )
    serializer_class = VoucherSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['property', 'approval_status', 'payment_method']
    search_fields = ['voucher_number', 'payee_name', 'description']

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """
        Advance a voucher through the approval chain.

        FIX: Corrected role mapping to match the requirements document.
        Requirements specify: Accountant → Finance Manager → Administrator.
        Original code had 'pending_finance' mapped to 'property_manager' which
        is wrong — it must be 'finance_manager'.

        Transition table:
          draft              → (accountant submits)    → pending_accountant
          pending_accountant → (accountant approves)   → pending_finance
          pending_finance    → (finance_manager)        → pending_admin
          pending_admin      → (admin approves)         → approved
        """
        voucher = self.get_object()
        role = request.user.role

        # Maps current_status → (required_role, next_status)
        transitions = {
            'draft':               ('accountant',      'pending_accountant'),
            'pending_accountant':  ('accountant',      'pending_finance'),
            'pending_finance':     ('finance_manager', 'pending_admin'),
            'pending_admin':       ('admin',           'approved'),
        }

        current = voucher.approval_status

        if current not in transitions:
            return Response(
                {'error': f"Cannot advance voucher from status '{current}'."},
                status=status.HTTP_400_BAD_REQUEST
            )

        required_role, next_status = transitions[current]

        # Admin can always advance at any step
        if role == required_role or role == 'admin':
            voucher.approval_status = next_status
            voucher.approved_by = request.user
            voucher.save(update_fields=['approval_status', 'approved_by', 'updated_at'])
            return Response({
                'success': True,
                'status': next_status,
                'voucher_id': voucher.id,
            })

        return Response(
            {'error': f"Role '{role}' is not authorized to approve at this stage. "
                      f"Required role: '{required_role}'."},
            status=status.HTTP_403_FORBIDDEN
        )

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """
        Reject a voucher at any stage.

        FIX: Added this missing action. The requirements include 'rejected' as a
        valid approval_status but the original code had no way to set it.
        Accountants, finance managers, and admins can reject.
        """
        voucher = self.get_object()
        role = request.user.role

        if voucher.approval_status in ('approved', 'rejected'):
            return Response(
                {'error': f"Cannot reject a voucher that is already '{voucher.approval_status}'."},
                status=status.HTTP_400_BAD_REQUEST
            )

        authorized_roles = ('accountant', 'finance_manager', 'admin')
        if role not in authorized_roles:
            return Response(
                {'error': 'Not authorized to reject vouchers.'},
                status=status.HTTP_403_FORBIDDEN
            )

        reason = request.data.get('reason', '')
        voucher.approval_status = 'rejected'
        voucher.approved_by = request.user
        # Store rejection reason in description if provided
        if reason:
            voucher.description = f"{voucher.description}\n\n[Rejection reason: {reason}]"
        voucher.save(update_fields=['approval_status', 'approved_by', 'description', 'updated_at'])

        return Response({
            'success': True,
            'status': 'rejected',
            'voucher_id': voucher.id,
        })