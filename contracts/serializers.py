from rest_framework import serializers
from .models import Contract, Payment


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = '__all__'


class ContractSerializer(serializers.ModelSerializer):
    payments = PaymentSerializer(many=True, read_only=True)
    total_contract_value = serializers.SerializerMethodField()
    paid_amount = serializers.SerializerMethodField()
    remaining_balance = serializers.SerializerMethodField()

    class Meta:
        model = Contract
        fields = '__all__'

    def get_total_contract_value(self, obj):
        return obj.total_contract_value()

    def get_paid_amount(self, obj):
        return float(obj.paid_amount())

    def get_remaining_balance(self, obj):
        return float(obj.remaining_balance())
