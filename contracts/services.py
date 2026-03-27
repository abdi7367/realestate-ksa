from decimal import Decimal
from django.db import transaction
from django.db.models import Sum, Count
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import Contract, Payment


VAT_RATE = Decimal('0.15')


class ContractService:
    """
    All contract business logic lives here.
    Views call this — never put this logic in views or serializers.
    """

    @staticmethod
    def calculate_total_value(monthly_rent: Decimal, duration_months: int) -> Decimal:
        """Total contract value = rent × duration."""
        return monthly_rent * duration_months

    @staticmethod
    def calculate_vat(amount: Decimal) -> Decimal:
        """VAT = 15% (KSA requirement)."""
        return (amount * VAT_RATE).quantize(Decimal('0.01'))

    @staticmethod
    @transaction.atomic
    def create_contract(
        property_unit,
        tenant,
        monthly_rent: Decimal,
        start_date,
        duration_months: int,
        created_by
    ) -> 'Contract':
        """
        Create a contract with full validation.
        Wrapped in atomic() — if anything fails, nothing is saved.

        FIX: Removed the erroneous `property=property_unit.property` kwarg that
        was in the original. Contract has no direct 'property' field on the model.
        Access the property via contract.unit.property instead.
        """
        # Validate unit is available
        if property_unit.rental_status != 'vacant':
            raise ValidationError(
                f"Unit {property_unit.unit_number} is not vacant. "
                f"Current status: {property_unit.get_rental_status_display()}"
            )

        # Validate no active contract exists for this unit
        active_exists = Contract.objects.filter(
            unit=property_unit,
            status='active'
        ).exists()
        if active_exists:
            raise ValidationError(
                f"Unit {property_unit.unit_number} already has an active contract."
            )

        # Calculate financials
        total_value = ContractService.calculate_total_value(monthly_rent, duration_months)
        vat_amount = ContractService.calculate_vat(total_value)
        end_date = ContractService._calculate_end_date(start_date, duration_months)

        # Create the contract
        contract = Contract.objects.create(
            unit=property_unit,
            tenant=tenant,
            monthly_rent=monthly_rent,
            duration_months=duration_months,
            start_date=start_date,
            end_date=end_date,
            total_value=total_value,
            vat_amount=vat_amount,
            total_value_with_vat=total_value + vat_amount,
            status='active',
            created_by=created_by,
        )

        # Mark unit as occupied
        property_unit.rental_status = 'occupied'
        property_unit.save(update_fields=['rental_status'])

        return contract

    @staticmethod
    @transaction.atomic
    def terminate_contract(contract, terminated_by, reason: str = '') -> 'Contract':
        """Terminate an active contract and free the unit."""
        if contract.status != 'active':
            raise ValidationError(
                f"Cannot terminate a contract with status '{contract.status}'."
            )

        contract.status = 'terminated'
        contract.termination_date = timezone.now().date()
        contract.termination_reason = reason
        contract.save(update_fields=['status', 'termination_date', 'termination_reason'])

        # Free the unit
        contract.unit.rental_status = 'vacant'
        contract.unit.save(update_fields=['rental_status'])

        return contract

    @staticmethod
    def _calculate_end_date(start_date, duration_months: int):
        from dateutil.relativedelta import relativedelta
        return start_date + relativedelta(months=duration_months)

    @staticmethod
    def get_expiring_contracts(days_ahead: int = 30):
        """Used by Celery task for expiry alerts."""
        today = timezone.now().date()
        threshold = today + timezone.timedelta(days=days_ahead)
        return Contract.objects.filter(
            status='active',
            end_date__lte=threshold,
            end_date__gte=today,
        ).select_related('unit', 'unit__property', 'tenant')


class PaymentService:
    """All payment business logic lives here."""

    @staticmethod
    @transaction.atomic
    def record_payment(
        contract,
        amount: Decimal,
        payment_date,
        payment_method: str,
        recorded_by,
        notes: str = ''
    ) -> 'Payment':
        """
        Record a payment with full validation.
        atomic() ensures contract and payment are always in sync.

        FIX: Moved the zero-amount check BEFORE the remaining-balance check so
        validation errors are returned in the correct logical order.
        """
        if contract.status != 'active':
            raise ValidationError("Cannot add payment to a non-active contract.")

        if amount <= Decimal('0'):
            raise ValidationError("Payment amount must be greater than zero.")

        remaining = PaymentService.get_remaining_balance(contract)

        if amount > remaining:
            raise ValidationError(
                f"Payment amount ({amount}) exceeds remaining balance ({remaining}). "
                f"Maximum allowed: {remaining}"
            )

        payment = Payment.objects.create(
            contract=contract,
            amount=amount,
            payment_date=payment_date,
            payment_method=payment_method,
            status='confirmed',
            recorded_by=recorded_by,
            notes=notes,
        )

        return payment

    @staticmethod
    def get_remaining_balance(contract) -> Decimal:
        """
        Calculate remaining balance dynamically — never stored in DB.

        FIX: Original code had .aggregate_sum() which does not exist on QuerySets
        and would crash at runtime. Replaced with the correct Django ORM pattern:
        .aggregate(total=Sum('amount')).
        """
        total_paid = contract.payments.filter(
            status='confirmed'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

        return contract.total_value_with_vat - total_paid

    @staticmethod
    def get_payment_summary(contract) -> dict:
        """Full payment summary for a contract."""
        stats = contract.payments.filter(status='confirmed').aggregate(
            total_paid=Sum('amount'),
            payment_count=Count('id'),
        )
        total_paid = stats['total_paid'] or Decimal('0')
        remaining = contract.total_value_with_vat - total_paid

        return {
            'total_value': contract.total_value,
            'vat_amount': contract.vat_amount,
            'total_with_vat': contract.total_value_with_vat,
            'total_paid': total_paid,
            'remaining_balance': remaining,
            'payment_count': stats['payment_count'],
            'is_fully_paid': remaining <= Decimal('0'),
        }