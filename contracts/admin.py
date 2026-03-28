from decimal import Decimal

from django.contrib import admin, messages
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils.html import format_html

from .models import Contract, Payment, Tenant
from .services import ContractService


def _validation_error_message(exc: ValidationError) -> str:
    if getattr(exc, 'message_dict', None):
        parts = []
        for field, msgs in exc.message_dict.items():
            parts.append(f'{field}: {"; ".join(str(m) for m in msgs)}')
        return ' '.join(parts)
    msgs = getattr(exc, 'messages', None)
    if msgs:
        return '; '.join(str(m) for m in msgs)
    return str(exc)


class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0


@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'tenant',
        'unit',
        'monthly_rent',
        'duration_months',
        'security_deposit_display',
        'payment_schedule',
        'status',
        'start_date',
        'end_date',
    )

    list_filter = ('status', 'payment_schedule', 'security_deposit_paid', 'start_date', 'end_date')

    search_fields = (
        'id',
        'tenant__full_name',
        'tenant__national_id',
        'tenant__tenant_reference',
        'unit__unit_number',
    )

    readonly_fields = (
        'total_value',
        'vat_amount',
        'total_value_with_vat',
        'end_date',
        'created_at',
        'updated_at',
    )

    inlines = [PaymentInline]

    def security_deposit_display(self, obj):
        if not obj.security_deposit or obj.security_deposit == Decimal('0'):
            return '—'
        paid = getattr(obj, 'security_deposit_paid', False)
        label = format_html(
            '<span style="color:{}">{}</span>',
            '#0a0' if paid else '#a60',
            'Paid' if paid else 'Not paid',
        )
        return format_html('{} SAR · {}', obj.security_deposit, label)

    security_deposit_display.short_description = 'Deposit'

    def save_model(self, request, obj, form, change):
        """
        Keep rent×duration+VAT in line when staff edit the contract in admin.
        API PATCH already runs sync; admin bypassed it before, which caused
        duration=12 with totals still based on 6 months.
        """
        if obj.start_date and obj.duration_months:
            obj.end_date = ContractService._calculate_end_date(
                obj.start_date,
                obj.duration_months,
            )
        if obj.total_value is None:
            obj.total_value = Decimal('0')
        if obj.vat_amount is None:
            obj.vat_amount = Decimal('0')
        if obj.total_value_with_vat is None:
            obj.total_value_with_vat = Decimal('0')
        try:
            with transaction.atomic():
                super().save_model(request, obj, form, change)
                if obj.status == 'active':
                    ContractService.sync_financials_from_lease_terms(obj)
        except ValidationError as e:
            self.message_user(request, _validation_error_message(e), level=messages.ERROR)
            raise


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        'contract',
        'amount',
        'due_date',
        'payment_date',
        'payment_method',
        'status',
    )

    list_filter = ('status', 'payment_method', 'payment_date')

    search_fields = (
        'contract__id',
        'contract__tenant__full_name',
        'contract__tenant__national_id',
    )


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = (
        'tenant_reference',
        'full_name',
        'national_id',
        'phone',
        'email',
        'created_at',
    )
    search_fields = ('tenant_reference', 'full_name', 'national_id', 'phone', 'email')
    readonly_fields = ('tenant_reference', 'created_at')
