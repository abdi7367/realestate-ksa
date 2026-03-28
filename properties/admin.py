from django.contrib import admin
from .models import Property, PropertyUnit


class PropertyUnitInline(admin.TabularInline):
    model = PropertyUnit
    extra = 1


@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = (
        'owner_reference',
        'property_code',
        'name',
        'owner_full_name',
        'property_type',
        'city',
        'location',
        'num_units',
        'property_manager',
    )
    list_filter = ('property_type', 'city')
    search_fields = (
        'name',
        'city',
        'district',
        'owner_reference',
        'owner_full_name',
        'owner_national_id',
    )
    inlines = [PropertyUnitInline]


@admin.register(PropertyUnit)
class PropertyUnitAdmin(admin.ModelAdmin):
    list_display = ('unit_number', 'property', 'unit_type', 'rental_status', 'monthly_rent')
    list_filter = ('rental_status', 'unit_type')