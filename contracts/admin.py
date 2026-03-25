from django.contrib import admin
from .models import Contract, Payment


class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 1


@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
    list_display = ('contract_number', 'tenant_name', 'unit', 'rent_amount', 'status', 'start_date', 'end_date')
    list_filter = ('status', 'payment_schedule')
    search_fields = ('contract_number', 'tenant_name', 'tenant_id')
    inlines = [PaymentInline]


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('contract', 'amount', 'due_date', 'paid_date', 'status')
    list_filter = ('status',)
    search_fields = ('contract__contract_number', 'contract__tenant_name')