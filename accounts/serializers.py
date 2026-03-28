from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

User = get_user_model()


class UserListSerializer(serializers.ModelSerializer):
    display_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'display_name', 'national_id', 'role']

    def get_display_name(self, obj):
        full = (obj.get_full_name() or '').strip()
        return full or obj.username


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['username'] = user.username
        token['role'] = user.role
        token['email'] = user.email
        token['national_id'] = user.national_id or ''
        return token