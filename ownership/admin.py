from django.contrib import admin
from .models import PropertyOwnership


@admin.register(PropertyOwnership)
class PropertyOwnershipAdmin(admin.ModelAdmin):
    list_display = ('owner_name', 'property', 'ownership_type', 'ownership_percentage', 'management_fee_percentage')
    list_filter = ('ownership_type',)
    search_fields = ('owner_name', 'owner_id', 'property__name')