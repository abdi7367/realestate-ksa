from datetime import timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional
from django.db import transaction
from django.db.models import Sum, Count
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import Contract, Payment, Tenant


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
        tenant: Tenant,
        monthly_rent: Decimal,
        start_date,
        duration_months: int,
        created_by,
        security_deposit: Decimal = Decimal('0'),
        payment_schedule: str = 'monthly',
        security_deposit_paid: bool = False,
        security_deposit_received_on=None,
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
            security_deposit=security_deposit,
            security_deposit_paid=security_deposit_paid,
            security_deposit_received_on=security_deposit_received_on,
            payment_schedule=payment_schedule,
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
        threshold = today + timedelta(days=days_ahead)
        return Contract.objects.filter(
            status='active',
            end_date__lte=threshold,
            end_date__gte=today,
        ).select_related('unit', 'unit__property', 'tenant')

    @staticmethod
    @transaction.atomic
    def sync_financials_from_lease_terms(contract: 'Contract') -> 'Contract':
        """
        Recompute total_value, VAT, total_with_vat, and end_date from
        monthly_rent, duration_months, and start_date.

        Call after PATCH changes those fields so stored totals stay in sync.
        Payment schedule does not change totals — only rent × lease length does.
        """
        if contract.status != 'active':
            raise ValidationError('Only active contracts can have totals recalculated.')

        total_value = ContractService.calculate_total_value(
            contract.monthly_rent,
            contract.duration_months,
        )
        vat_amount = ContractService.calculate_vat(total_value)
        total_with_vat = total_value + vat_amount

        total_paid = contract.payments.filter(status='confirmed').aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0')

        if total_paid > total_with_vat:
            raise ValidationError(
                f'New total with VAT ({total_with_vat}) cannot be less than confirmed '
                f'payments already recorded ({total_paid}).'
            )

        contract.total_value = total_value
        contract.vat_amount = vat_amount
        contract.total_value_with_vat = total_with_vat
        contract.end_date = ContractService._calculate_end_date(
            contract.start_date,
            contract.duration_months,
        )
        contract.save(
            update_fields=[
                'total_value',
                'vat_amount',
                'total_value_with_vat',
                'end_date',
                'updated_at',
            ]
        )
        return contract


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
        notes: str = '',
        due_date=None,
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
            due_date=due_date,
            payment_method=payment_method,
            status='confirmed',
            recorded_by=recorded_by,
            notes=notes,
        )

        return payment

    @staticmethod
    def scheduled_installment_count(duration_months: int, payment_schedule: str) -> int:
        """
        Number of rent installments over the lease from duration + schedule.
        Uses ceiling of months per period so e.g. 12 months quarterly → 4 payments.
        """
        d = max(1, int(duration_months))
        if payment_schedule == 'monthly':
            return d
        if payment_schedule == 'quarterly':
            return max(1, (d + 2) // 3)
        if payment_schedule == 'semi_annual':
            return max(1, (d + 5) // 6)
        if payment_schedule == 'annual':
            return max(1, (d + 11) // 12)
        if payment_schedule == 'lump_sum':
            return 1
        return d

    @staticmethod
    def get_installment_guidance(contract, remaining: Optional[Decimal] = None) -> dict:
        """
        Even split of remaining VAT-inclusive balance across installments still due.

        Each *confirmed* Payment row counts as one installment for this hint so
        after paying 58650 once on a 2-installment semi-annual lease, the next
        suggestion is the full remaining balance (÷1).
        """
        rem = (
            remaining
            if remaining is not None
            else PaymentService.get_remaining_balance(contract)
        )
        n_total = PaymentService.scheduled_installment_count(
            contract.duration_months,
            contract.payment_schedule,
        )
        paid_count = contract.payments.filter(status='confirmed').count()

        if rem <= Decimal('0'):
            return {
                'payment_schedule': contract.payment_schedule,
                'installments_planned': n_total,
                'installments_recorded': paid_count,
                'installments_remaining': 0,
                'suggested_next_amount': Decimal('0'),
                'remaining_balance': rem,
            }

        periods_left = n_total - paid_count
        if periods_left < 1:
            periods_left = 1

        suggested = (rem / Decimal(periods_left)).quantize(
            Decimal('0.01'), rounding=ROUND_HALF_UP
        )

        return {
            'payment_schedule': contract.payment_schedule,
            'installments_planned': n_total,
            'installments_recorded': paid_count,
            'installments_remaining': periods_left,
            'suggested_next_amount': suggested,
            'remaining_balance': rem,
        }

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

        guidance = PaymentService.get_installment_guidance(contract, remaining=remaining)

        return {
            'total_value': contract.total_value,
            'vat_amount': contract.vat_amount,
            'total_with_vat': contract.total_value_with_vat,
            'total_paid': total_paid,
            'remaining_balance': remaining,
            'payment_count': stats['payment_count'],
            'is_fully_paid': remaining <= Decimal('0'),
            'installment_guidance': guidance,
        }