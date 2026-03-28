from rest_framework import serializers
from .models import Debt, DebtInstallment


class DebtInstallmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = DebtInstallment
        fields = '__all__'


class DebtSerializer(serializers.ModelSerializer):
    installments = DebtInstallmentSerializer(many=True, read_only=True)
    paid_amount = serializers.SerializerMethodField()
    remaining_balance = serializers.SerializerMethodField()

    class Meta:
        model = Debt
        fields = '__all__'

    def get_paid_amount(self, obj):
        """Keep money as decimal string for JSON (§3.3 remaining balance)."""
        val = obj.paid_amount()
        return str(val) if val is not None else '0.00'

    def get_remaining_balance(self, obj):
        val = obj.remaining_balance()
        return str(val)
