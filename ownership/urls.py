from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PropertyOwnershipViewSet

router = DefaultRouter()
router.register(r'ownerships', PropertyOwnershipViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
