from rest_framework import serializers
from accounts.models import User
from .models import Property, PropertyUnit


class PropertyManagerSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'role']


class PropertyUnitSerializer(serializers.ModelSerializer):
    active_tenant = serializers.SerializerMethodField(read_only=True)
    property_name = serializers.CharField(source='property.name', read_only=True)
    property_city = serializers.CharField(source='property.city', read_only=True)

    class Meta:
        model = PropertyUnit
        fields = '__all__'

    def get_active_tenant(self, obj):
        """§3.1 tenant information on unit via active rental contract."""
        cached = getattr(obj, 'active_contract_list', None)
        if cached is None:
            from contracts.models import Contract as ContractModel

            contract = (
                ContractModel.objects.filter(unit=obj, status='active')
                .select_related('tenant')
                .first()
            )
        else:
            contract = cached[0] if cached else None
        if not contract or not contract.tenant:
            return None
        tenant = contract.tenant
        return {
            'id': tenant.id,
            'tenant_reference': tenant.tenant_reference,
            'name': (tenant.full_name or '').strip() or None,
            'national_id': tenant.national_id or None,
        }


class PropertySerializer(serializers.ModelSerializer):
    units = PropertyUnitSerializer(many=True, read_only=True)
    units_count = serializers.SerializerMethodField()
    vacant_units = serializers.SerializerMethodField()
    occupied_units = serializers.SerializerMethodField()
    property_manager = PropertyManagerSerializer(read_only=True)
    property_manager_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        source='property_manager',
        write_only=True,
        required=False
    )

    class Meta:
        model = Property
        fields = '__all__'
        read_only_fields = ('owner_reference', 'created_at', 'updated_at')

    def validate(self, attrs):
        request = self.context.get('request')
        if request and request.method == 'POST':
            required_owner = (
                'owner_full_name',
                'owner_national_id',
                'owner_phone',
                'owner_email',
                'owner_bank_iban',
            )
            errors = {}
            data = {**attrs}
            for key in required_owner:
                val = data.get(key)
                if val is None or (isinstance(val, str) and not val.strip()):
                    errors[key] = 'Required for the registered property owner.'
            if errors:
                raise serializers.ValidationError(errors)
        return attrs

    def get_units_count(self, obj):
        return len(obj.units.all())

    def get_vacant_units(self, obj):
        return sum(1 for u in obj.units.all() if u.rental_status == 'vacant')

    def get_occupied_units(self, obj):
        return sum(1 for u in obj.units.all() if u.rental_status == 'occupied')