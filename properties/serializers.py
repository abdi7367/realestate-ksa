from rest_framework import serializers
from accounts.models import User
from .models import Property, PropertyUnit


class PropertyManagerSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'role']


class PropertyUnitSerializer(serializers.ModelSerializer):
    class Meta:
        model = PropertyUnit
        fields = '__all__'


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

    def get_units_count(self, obj):
        return obj.units.count()

    def get_vacant_units(self, obj):
        return obj.units.filter(rental_status='vacant').count()

    def get_occupied_units(self, obj):
        return obj.units.filter(rental_status='occupied').count()