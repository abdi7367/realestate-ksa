from django.contrib import admin
from .models import Transaction


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('property', 'transaction_type', 'category', 'amount', 'date', 'created_by')
    list_filter = ('transaction_type', 'category')
    search_fields = ('description', 'reference', 'property__name')
    date_hierarchy = 'date'