from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

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

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

