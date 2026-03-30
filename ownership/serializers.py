from rest_framework import serializers
from .models import PropertyOwnership


class PropertyOwnershipSerializer(serializers.ModelSerializer):
    class Meta:
        model = PropertyOwnership
        fields = '__all__'
