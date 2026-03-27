from django.db import models
from django.db.models import Sum   # FIX: was missing — models.Sum does not exist
from properties.models import Property


class Debt(models.Model):
    DEBT_TYPE_CHOICES = [
        ('bank_loan', 'Bank Loan'),
        ('construction', 'Construction Loan'),
        ('maintenance', 'Maintenance Debt'),
        ('contractor', 'Contractor Payment'),
        ('supplier', 'Supplier Payment'),
        ('other', 'Other'),
    ]

    property = models.ForeignKey(
        Property,
        on_delete=models.CASCADE,
        related_name='debts'
    )
    debt_type = models.CharField(max_length=30, choices=DEBT_TYPE_CHOICES)
    creditor_name = models.CharField(max_length=255)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def paid_amount(self):
        """
        FIX: Original used models.Sum('amount') which does not exist.
        django.db.models.Sum must be imported separately (done at the top of this file).
        """
        return self.installments.filter(status='paid').aggregate(
            total=Sum('amount')
        )['total'] or 0

    def remaining_balance(self):
        return self.total_amount - self.paid_amount()

    def __str__(self):
        return f'{self.creditor_name} - {self.total_amount}'


class DebtInstallment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('overdue', 'Overdue'),
    ]

    debt = models.ForeignKey(
        Debt,
        on_delete=models.CASCADE,
        related_name='installments'
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    due_date = models.DateField()
    paid_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    notes = models.TextField(blank=True)

    def __str__(self):
        return f'Installment {self.amount} due {self.due_date}'