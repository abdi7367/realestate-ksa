from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PropertyViewSet, PropertyUnitViewSet

router = DefaultRouter()
router.register(r'properties', PropertyViewSet)
router.register(r'units', PropertyUnitViewSet)

urlpatterns = [
    path('', include(router.urls)),
]