import django_filters
from rest_framework import filters

from .models import Contract, Payment


class ContractFilter(django_filters.FilterSet):
    """GET /api/contracts/?status=active&payment_schedule=monthly&..."""

    class Meta:
        model = Contract
        fields = ['status', 'payment_schedule', 'unit', 'tenant']


class PaymentFilter(django_filters.FilterSet):
    """GET /api/payments/ — use contract or contract_number (same field)."""

    amount_min = django_filters.NumberFilter(field_name='amount', lookup_expr='gte')
    amount_max = django_filters.NumberFilter(field_name='amount', lookup_expr='lte')
    payment_date_from = django_filters.DateFilter(
        field_name='payment_date', lookup_expr='gte'
    )
    payment_date_to = django_filters.DateFilter(
        field_name='payment_date', lookup_expr='lte'
    )
    contract_number = django_filters.NumberFilter(
        field_name='contract',
        lookup_expr='exact',
        help_text='Same as contract id / “contract number” in the UI.',
    )

    class Meta:
        model = Payment
        fields = ['contract', 'status', 'payment_method', 'amount']


class ContractSearchFilter(filters.SearchFilter):
    """
    ?search= matches property / unit / tenant fields.
    If the term is all digits, results also include that contract id (pk).
    """

    def filter_queryset(self, request, queryset, view):
        term = request.query_params.get(self.search_param, '').strip()
        if not term:
            return queryset
        qs_text = super().filter_queryset(request, queryset, view)
        if term.isdigit():
            qs_id = queryset.filter(pk=int(term))
            return (qs_text | qs_id).distinct()
        return qs_text


class PaymentSearchFilter(filters.SearchFilter):
    """
    ?search= matches notes and related contract tenant/property/unit.
    If the term is all digits, results also include payments for that contract id.
    """

    def filter_queryset(self, request, queryset, view):
        term = request.query_params.get(self.search_param, '').strip()
        if not term:
            return queryset
        qs_text = super().filter_queryset(request, queryset, view)
        if term.isdigit():
            qs_id = queryset.filter(contract_id=int(term))
            return (qs_text | qs_id).distinct()
        return qs_text
