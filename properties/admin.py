from django.contrib import admin
from .models import Property, PropertyUnit


class PropertyUnitInline(admin.TabularInline):
    model = PropertyUnit
    extra = 1


@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = ('name', 'property_type', 'city', 'num_units', 'property_manager')
    list_filter = ('property_type', 'city')
    search_fields = ('name', 'city', 'district')
    inlines = [PropertyUnitInline]


@admin.register(PropertyUnit)
class PropertyUnitAdmin(admin.ModelAdmin):
    list_display = ('unit_number', 'property', 'unit_type', 'rental_status', 'monthly_rent')
    list_filter = ('rental_status', 'unit_type')