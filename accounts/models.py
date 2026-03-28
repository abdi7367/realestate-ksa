from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('property_manager', 'Property Manager'),
        ('accountant', 'Accountant'),
        # FIX: Added finance_manager role to match the requirements document.
        # The approval workflow in vouchers requires: Accountant → Finance Manager → Admin.
        # The original code mapped this step to 'property_manager' which was wrong.
        ('finance_manager', 'Finance Manager'),
    ]

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='accountant'
    )
    phone = models.CharField(max_length=20, blank=True)
    national_id = models.CharField(
        max_length=50,
        blank=True,
        db_index=True,
        help_text='Tenant / user national ID or Iqama (§3.2 Tenant ID).',
    )

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

    @property
    def is_admin(self):
        return self.role == 'admin'

    @property
    def is_property_manager(self):
        return self.role == 'property_manager'

    @property
    def is_accountant(self):
        return self.role == 'accountant'

    @property
    def is_finance_manager(self):
        return self.role == 'finance_manager'