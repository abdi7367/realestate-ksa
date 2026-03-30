from django.contrib import admin
from .models import Voucher


@admin.register(Voucher)
class VoucherAdmin(admin.ModelAdmin):
    list_display = ('voucher_number', 'payee_name', 'property', 'amount', 'payment_method', 'approval_status', 'date')
    list_filter = ('approval_status', 'payment_method')
    search_fields = ('voucher_number', 'payee_name', 'description')
    date_hierarchy = 'date'
    readonly_fields = ('created_at', 'updated_at')