from django.db import models
from properties.models import Property


class PropertyOwnership(models.Model):
    OWNERSHIP_TYPE_CHOICES = [
        ('personal', 'Personal'),
        ('third_party', 'Third Party'),
    ]

    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='ownerships')
    ownership_type = models.CharField(max_length=20, choices=OWNERSHIP_TYPE_CHOICES)
    owner_name = models.CharField(max_length=255)
    owner_id = models.CharField(max_length=50)
    owner_phone = models.CharField(max_length=20, blank=True)
    owner_email = models.EmailField(blank=True)
    ownership_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=100)
    management_fee_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    revenue_share_model = models.TextField(blank=True)
    management_agreement = models.FileField(upload_to='agreements/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.owner_name} - {self.property.name} ({self.ownership_percentage}%)'
