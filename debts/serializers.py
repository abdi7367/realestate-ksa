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
        return float(obj.paid_amount())

    def get_remaining_balance(self, obj):
        return float(obj.remaining_balance())
