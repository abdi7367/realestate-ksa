from django.db import models
from accounts.models import User
from properties.models import PropertyUnit


class Contract(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('terminated', 'Terminated'),
        ('pending', 'Pending'),
    ]
    PAYMENT_SCHEDULE_CHOICES = [
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('semi_annual', 'Semi-Annual'),
        ('annual', 'Annual'),
    ]

    contract_number = models.CharField(max_length=50, unique=True)
    unit = models.ForeignKey(PropertyUnit, on_delete=models.CASCADE, related_name='contracts')
    tenant_name = models.CharField(max_length=255)
    tenant_id = models.CharField(max_length=50)
    tenant_phone = models.CharField(max_length=20, blank=True)
    tenant_email = models.EmailField(blank=True)
    start_date = models.DateField()
    end_date = models.DateField()
    rent_amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_schedule = models.CharField(max_length=20, choices=PAYMENT_SCHEDULE_CHOICES, default='monthly')
    security_deposit = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def total_contract_value(self):
        from datetime import date
        months = ((self.end_date.year - self.start_date.year) * 12 +
                  self.end_date.month - self.start_date.month)
        return self.rent_amount * months

    def paid_amount(self):
        return self.payments.filter(status='paid').aggregate(
            total=models.Sum('amount'))['total'] or 0

    def remaining_balance(self):
        return self.total_contract_value() - self.paid_amount()

    def __str__(self):
        return f'Contract {self.contract_number} - {self.tenant_name}'


class Payment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('overdue', 'Overdue'),
        ('partial', 'Partial'),
    ]

    contract = models.ForeignKey(Contract, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    due_date = models.DateField()
    paid_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Payment {self.amount} for {self.contract.contract_number}'
