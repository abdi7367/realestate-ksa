from django.core.exceptions import ValidationError
from django.db import models
from properties.models import Property
from accounts.models import User


class Transaction(models.Model):
    TRANSACTION_TYPE_CHOICES = [
        ('income', 'Income'),
        ('expense', 'Expense'),
    ]
    INCOME_CATEGORY_CHOICES = [
        ('rental', 'Rental Income'),
        ('parking', 'Parking Income'),
        ('service_charge', 'Service Charge'),
        ('utility_recovery', 'Utility Recovery'),
        ('other', 'Other Income'),
    ]
    EXPENSE_CATEGORY_CHOICES = [
        ('maintenance', 'Maintenance'),
        ('utilities', 'Utilities'),
        ('security', 'Security Services'),
        ('cleaning', 'Cleaning'),
        ('government_fees', 'Government Fees'),
        ('management', 'Property Management'),
        ('other', 'Other Expense'),
    ]

    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPE_CHOICES)
    category = models.CharField(max_length=30)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    date = models.DateField()
    description = models.TextField(blank=True)
    reference = models.CharField(max_length=100, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        super().clean()
        if self.transaction_type == 'income':
            valid = {c[0] for c in self.INCOME_CATEGORY_CHOICES}
        else:
            valid = {c[0] for c in self.EXPENSE_CATEGORY_CHOICES}
        if self.category not in valid:
            raise ValidationError(
                {'category': f'Must match transaction type "{self.transaction_type}".'}
            )

    def __str__(self):
        return f'{self.transaction_type} {self.amount} - {self.property.name}'
