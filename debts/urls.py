from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DebtViewSet, DebtInstallmentViewSet

router = DefaultRouter()
router.register(r'debts', DebtViewSet)
router.register(r'installments', DebtInstallmentViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
