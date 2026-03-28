from rest_framework import serializers
from .models import Contract, Payment, Tenant


class TenantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tenant
        fields = [
            'id',
            'tenant_reference',
            'full_name',
            'national_id',
            'phone',
            'email',
            'nationality',
            'date_of_birth',
        ]
        read_only_fields = ['id', 'tenant_reference']


class TenantCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tenant
        fields = [
            'full_name',
            'national_id',
            'phone',
            'email',
            'nationality',
            'date_of_birth',
        ]


class PaymentSerializer(serializers.ModelSerializer):
    is_late = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Payment
        fields = [
            'id', 'contract', 'amount', 'payment_date', 'due_date',
            'payment_method', 'status', 'notes', 'created_at', 'is_late',
        ]
        read_only_fields = ['id', 'status', 'created_at', 'is_late']

    def get_is_late(self, obj):
        """§3.2 late payments when settlement is after the agreed due date."""
        if obj.due_date and obj.payment_date and obj.payment_date > obj.due_date:
            return True
        return False


class ContractSerializer(serializers.ModelSerializer):
    payments = PaymentSerializer(many=True, read_only=True)
    remaining_balance = serializers.SerializerMethodField()
    installment_guidance = serializers.SerializerMethodField()

    # Read-only convenience fields derived from the unit FK
    property_name = serializers.SerializerMethodField()
    unit_number = serializers.SerializerMethodField()
    tenant = TenantSerializer(read_only=True)
    tenant_data = TenantCreateSerializer(write_only=True, required=False)
    tenant_name = serializers.SerializerMethodField(read_only=True)
    tenant_national_id = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Contract
        fields = [
            'id',
            # FIX: Removed 'property' — Contract has no direct property field.
            # Use property_name (read-only) for display, and navigate via unit.property.
            'unit',
            'property_name',
            'unit_number',
            'tenant',
            'tenant_data',
            'tenant_name',
            'tenant_national_id',
            'monthly_rent', 'duration_months',
            'security_deposit',
            'security_deposit_paid', 'security_deposit_received_on',
            'payment_schedule',
            'total_value', 'vat_amount', 'total_value_with_vat',
            'start_date', 'end_date', 'status',
            'payments', 'remaining_balance', 'installment_guidance',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'total_value', 'vat_amount', 'total_value_with_vat',
            'end_date', 'status', 'created_at', 'updated_at',
            'property_name', 'unit_number', 'tenant', 'tenant_name', 'tenant_national_id',
        ]

    def get_remaining_balance(self, obj):
        from .services import PaymentService
        return PaymentService.get_remaining_balance(obj)

    def get_installment_guidance(self, obj):
        from .services import PaymentService

        g = PaymentService.get_installment_guidance(obj)
        return {
            **g,
            'suggested_next_amount': str(g['suggested_next_amount']),
            'remaining_balance': str(g['remaining_balance']),
        }

    def get_property_name(self, obj):
        if obj.unit and obj.unit.property:
            return obj.unit.property.name
        return None

    def get_unit_number(self, obj):
        if obj.unit:
            return obj.unit.unit_number
        return None

    def get_tenant_name(self, obj):
        if not obj.tenant:
            return None
        return (obj.tenant.full_name or '').strip() or None

    def get_tenant_national_id(self, obj):
        if not obj.tenant:
            return None
        return obj.tenant.national_id or None

    def update(self, instance, validated_data):
        validated_data.pop('tenant_data', None)
        return super().update(instance, validated_data)


class ContractSummarySerializer(serializers.Serializer):
    """Read-only serializer for the /summary endpoint."""
    total_value = serializers.DecimalField(max_digits=12, decimal_places=2)
    vat_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_with_vat = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_paid = serializers.DecimalField(max_digits=12, decimal_places=2)
    remaining_balance = serializers.DecimalField(max_digits=12, decimal_places=2)
    payment_count = serializers.IntegerField()
    is_fully_paid = serializers.BooleanField()