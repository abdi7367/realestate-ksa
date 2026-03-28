from decimal import Decimal
from django.db import models
from django.conf import settings
from simple_history.models import HistoricalRecords


class Tenant(models.Model):
    """
    Office-held tenant record (not a login user). Linked from Contract via FK.
    """

    tenant_reference = models.CharField(
        max_length=32,
        unique=True,
        editable=False,
        blank=True,
        help_text='Display ID e.g. T-000042',
    )
    full_name = models.CharField(max_length=255)
    national_id = models.CharField(
        max_length=50,
        db_index=True,
        help_text='National ID or Iqama number',
    )
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    nationality = models.CharField(max_length=100, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        ref = self.tenant_reference or f'#{self.pk}'
        return f'{ref} — {self.full_name}'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if not self.tenant_reference:
            ref = f'T-{self.pk:06d}'
            Tenant.objects.filter(pk=self.pk).update(tenant_reference=ref)
            self.tenant_reference = ref


class Contract(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('terminated', 'Terminated'),
    ]

    PAYMENT_SCHEDULE_CHOICES = [
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('semi_annual', 'Semi-annual'),
        ('annual', 'Annual'),
        ('lump_sum', 'Lump sum'),
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
        'Tenant',
        on_delete=models.PROTECT,
        related_name='contracts',
        null=True,
        blank=True,
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
    security_deposit = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text='§3.2 Security Deposit',
    )
    security_deposit_paid = models.BooleanField(
        default=False,
        help_text='Whether the security deposit amount has been collected.',
    )
    security_deposit_received_on = models.DateField(
        null=True,
        blank=True,
        help_text='Date deposit was received (optional).',
    )
    payment_schedule = models.CharField(
        max_length=20,
        choices=PAYMENT_SCHEDULE_CHOICES,
        default='monthly',
        help_text='§3.2 Payment Schedule',
    )

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
    due_date = models.DateField(
        null=True,
        blank=True,
        help_text='Expected due date for this installment (§3.2 late payments).',
    )
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