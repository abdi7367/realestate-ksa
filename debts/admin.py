from django.contrib import admin
from .models import Debt, DebtInstallment


class DebtInstallmentInline(admin.TabularInline):
    model = DebtInstallment
    extra = 1


@admin.register(Debt)
class DebtAdmin(admin.ModelAdmin):
    list_display = ('creditor_name', 'property', 'debt_type', 'total_amount', 'start_date')
    list_filter = ('debt_type',)
    search_fields = ('creditor_name', 'property__name')
    inlines = [DebtInstallmentInline]


@admin.register(DebtInstallment)
class DebtInstallmentAdmin(admin.ModelAdmin):
    list_display = ('debt', 'amount', 'due_date', 'paid_date', 'status')
    list_filter = ('status',)