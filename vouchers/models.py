from django.db import models
from properties.models import Property
from accounts.models import User


class Voucher(models.Model):
    PAYMENT_METHOD_CHOICES = [
        ('cash', 'Cash'),
        ('bank_transfer', 'Bank Transfer'),
        ('cheque', 'Cheque'),
        ('online', 'Online Payment'),
    ]
    APPROVAL_STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('pending_accountant', 'Pending Accountant'),
        ('pending_finance', 'Pending Finance Manager'),
        ('pending_admin', 'Pending Administrator'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    voucher_number = models.CharField(max_length=50, unique=True)
    date = models.DateField()
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payee_name = models.CharField(max_length=255)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    description = models.TextField()
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='vouchers')
    approval_status = models.CharField(max_length=30, choices=APPROVAL_STATUS_CHOICES, default='draft')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True,
                                    blank=True, related_name='created_vouchers')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True,
                                     blank=True, related_name='approved_vouchers')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Voucher {self.voucher_number} - {self.amount}'
