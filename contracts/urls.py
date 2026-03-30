from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ContractViewSet, PaymentViewSet, TenantViewSet

router = DefaultRouter()
router.register(r'contracts', ContractViewSet)
router.register(r'payments', PaymentViewSet)
router.register(r'tenants', TenantViewSet)

urlpatterns = [
    path('', include(router.urls)),
]