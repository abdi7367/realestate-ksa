from django.contrib.auth import get_user_model
from rest_framework.filters import SearchFilter
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView

from .permissions import UserListPermission
from .serializers import CustomTokenObtainPairSerializer, UserListSerializer

User = get_user_model()


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


class UserListView(ListAPIView):
    """Compact user list for staff pickers where a User FK is required."""

    serializer_class = UserListSerializer
    permission_classes = [IsAuthenticated, UserListPermission]
    filter_backends = [SearchFilter]
    search_fields = ['username', 'first_name', 'last_name', 'national_id']
    queryset = User.objects.all().order_by('username')
    pagination_class = None