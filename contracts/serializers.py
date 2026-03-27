from rest_framework import serializers
from .models import Contract, Payment


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = [
            'id', 'contract', 'amount', 'payment_date',
            'payment_method', 'status', 'notes', 'created_at'
        ]
        read_only_fields = ['id', 'status', 'created_at']


class ContractSerializer(serializers.ModelSerializer):
    payments = PaymentSerializer(many=True, read_only=True)
    remaining_balance = serializers.SerializerMethodField()

    class Meta:
        model = Contract
        fields = [
            'id', 'property', 'unit', 'tenant',
            'monthly_rent', 'duration_months',
            'total_value', 'vat_amount', 'total_value_with_vat',
            'start_date', 'end_date', 'status',
            'payments', 'remaining_balance',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'total_value', 'vat_amount', 'total_value_with_vat',
            'end_date', 'status', 'created_at', 'updated_at',
        ]

    def get_remaining_balance(self, obj):
        from .services import PaymentService
        return PaymentService.get_remaining_balance(obj)


class ContractSummarySerializer(serializers.Serializer):
    """Read-only serializer for the /summary endpoint."""
    total_value = serializers.DecimalField(max_digits=12, decimal_places=2)
    vat_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_with_vat = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_paid = serializers.DecimalField(max_digits=12, decimal_places=2)
    remaining_balance = serializers.DecimalField(max_digits=12, decimal_places=2)
    payment_count = serializers.IntegerField()
    is_fully_paid = serializers.BooleanField()