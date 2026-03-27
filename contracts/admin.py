from django.contrib import admin
from .models import Contract, Payment


class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 1


@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'tenant',
        'unit',
        'monthly_rent',
        'status',
        'start_date',
        'end_date'
    )

    list_filter = ('status', 'start_date', 'end_date')

    search_fields = (
        'id',
        'tenant__username',   # adjust if custom user model
        'unit__unit_number'   # adjust based on your PropertyUnit model
    )

    inlines = [PaymentInline]


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        'contract',
        'amount',
        'payment_date',
        'payment_method',
        'status'
    )

    list_filter = ('status', 'payment_method', 'payment_date')

    search_fields = (
        'contract__id',
        'contract__tenant__username'
    )