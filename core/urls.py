from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('properties.urls')),
    path('api/', include('contracts.urls')),
    path('api/', include('debts.urls')),
    path('api/', include('finance.urls')),
    path('api/', include('vouchers.urls')),
    path('api/', include('ownership.urls')),
    path('api/', include('reports.urls')),
    path('api/auth/', include('accounts.urls')),
]

