from decimal import Decimal
from django.db import models
from django.conf import settings
from simple_history.models import HistoricalRecords


class Contract(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('terminated', 'Terminated'),
    ]

    # Relations
    unit = models.ForeignKey(
        'properties.PropertyUnit',
        on_delete=models.PROTECT,
        related_name='contracts',
        null=True,
        blank=True
    )
    tenant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='tenant_contracts',
        null=True,
        blank=True
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_contracts'
    )

    # Financial fields — always Decimal, never Float
    monthly_rent = models.DecimalField(max_digits=10, decimal_places=2)
    duration_months = models.IntegerField(default=12)

    total_value = models.DecimalField(max_digits=12, decimal_places=2)
    vat_amount = models.DecimalField(max_digits=10, decimal_places=2)
    total_value_with_vat = models.DecimalField(max_digits=12, decimal_places=2)

    # Dates
    start_date = models.DateField()
    end_date = models.DateField()
    termination_date = models.DateField(null=True, blank=True)
    termination_reason = models.TextField(blank=True)

    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Audit log
    history = HistoricalRecords()

    class Meta:
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['unit']),
            models.Index(fields=['end_date']),
        ]

    def __str__(self):
        return f"Contract #{self.pk} — {self.unit} ({self.status})"

    @property
    def property(self):
        """Convenience accessor — navigate to property via the unit FK."""
        if self.unit:
            return self.unit.property
        return None


class Payment(models.Model):
    STATUS_CHOICES = [
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
    ]

    METHOD_CHOICES = [
        ('bank_transfer', 'Bank Transfer'),
        ('cash', 'Cash'),
        ('cheque', 'Cheque'),
        ('online', 'Online'),
    ]

    contract = models.ForeignKey(
        Contract,
        on_delete=models.PROTECT,
        related_name='payments'
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateField()
    payment_method = models.CharField(max_length=20, choices=METHOD_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='confirmed')
    notes = models.TextField(blank=True)
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='recorded_payments'
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)

    # Audit log
    history = HistoricalRecords()

    class Meta:
        indexes = [
            models.Index(fields=['contract']),
            models.Index(fields=['payment_date']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"Payment #{self.pk} — {self.amount} SAR ({self.contract})"