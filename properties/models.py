from django.db import models
from accounts.models import User


class Property(models.Model):
    PROPERTY_TYPE_CHOICES = [
        ('residential', 'Residential'),
        ('commercial', 'Commercial'),
        ('industrial', 'Industrial'),
        ('land', 'Land'),
    ]

    name = models.CharField(max_length=255)
    property_type = models.CharField(max_length=20, choices=PROPERTY_TYPE_CHOICES)
    city = models.CharField(max_length=100)
    district = models.CharField(max_length=100)
    size_sqm = models.DecimalField(max_digits=10, decimal_places=2)
    num_units = models.IntegerField(default=1)
    ownership_status = models.CharField(max_length=100, blank=True)
    property_manager = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='managed_properties'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - {self.city}"

    class Meta:
        verbose_name_plural = "Properties"


class PropertyUnit(models.Model):
    UNIT_TYPE_CHOICES = [
        ('apartment', 'Apartment'),
        ('office', 'Office'),
        ('shop', 'Shop'),
        ('villa', 'Villa'),
    ]

    RENTAL_STATUS_CHOICES = [
        ('vacant', 'Vacant'),
        ('occupied', 'Occupied'),
        ('maintenance', 'Under Maintenance'),
        ('reserved', 'Reserved'),
    ]

    property = models.ForeignKey(
        Property,
        on_delete=models.CASCADE,
        related_name='units'
    )
    unit_number = models.CharField(max_length=20)
    floor = models.IntegerField(default=1)
    size_sqm = models.DecimalField(max_digits=8, decimal_places=2)
    unit_type = models.CharField(max_length=20, choices=UNIT_TYPE_CHOICES)
    rental_status = models.CharField(
        max_length=20,
        choices=RENTAL_STATUS_CHOICES,
        default='vacant'
    )
    monthly_rent = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"Unit {self.unit_number} - {self.property.name}"