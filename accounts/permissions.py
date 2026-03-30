"""
Role-based access aligned with requirement document §4 (User Roles).
Superusers always pass.
"""
from rest_framework.permissions import BasePermission, SAFE_METHODS


def user_role(user):
    return getattr(user, 'role', None) if user.is_authenticated else None


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True
        return user_role(request.user) == 'admin'


class PropertyManagementPermission(BasePermission):
    """§3.1 + §4: Admin & Property Manager manage properties; others read."""

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True
        r = user_role(request.user)
        if request.method in SAFE_METHODS:
            return r in (
                'admin',
                'property_manager',
                'accountant',
                'finance_manager',
            )
        return r in ('admin', 'property_manager')


class ContractManagementPermission(BasePermission):
    """§3.2 + §4: Admin & Property Manager manage contracts; finance roles read."""

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True
        r = user_role(request.user)
        if request.method in SAFE_METHODS:
            return r in (
                'admin',
                'property_manager',
                'accountant',
                'finance_manager',
            )
        return r in ('admin', 'property_manager')


class PaymentManagementPermission(BasePermission):
    """§4 Accountant: manage payments; Property Manager may also record collections."""

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True
        r = user_role(request.user)
        if request.method in SAFE_METHODS:
            return r in (
                'admin',
                'property_manager',
                'accountant',
                'finance_manager',
            )
        return r in ('admin', 'accountant', 'property_manager')


class FinanceTransactionPermission(BasePermission):
    """§3.5 + §4: Accountant & PM record income/expense; finance staff read."""

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True
        r = user_role(request.user)
        if request.method in SAFE_METHODS:
            return r in (
                'admin',
                'property_manager',
                'accountant',
                'finance_manager',
            )
        return r in ('admin', 'property_manager', 'accountant')


class DebtManagementPermission(BasePermission):
    """§3.3: operational debt tracking — write for admin/accountant/PM; read wider."""

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True
        r = user_role(request.user)
        if request.method in SAFE_METHODS:
            return r in (
                'admin',
                'property_manager',
                'accountant',
                'finance_manager',
            )
        return r in ('admin', 'property_manager', 'accountant')


class OwnershipManagementPermission(BasePermission):
    """§3.4: ownership records — Admin & Property Manager write."""

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True
        r = user_role(request.user)
        if request.method in SAFE_METHODS:
            return r in (
                'admin',
                'property_manager',
                'accountant',
                'finance_manager',
            )
        return r in ('admin', 'property_manager')


class VoucherManagementPermission(BasePermission):
    """§3.6: Accountant issues vouchers; finance chain reads."""

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True
        r = user_role(request.user)
        if request.method in SAFE_METHODS:
            return r in (
                'admin',
                'property_manager',
                'accountant',
                'finance_manager',
            )
        return r in ('admin', 'accountant')


class UserListPermission(BasePermission):
    """List users for admin pickers (e.g. property manager assignment)."""

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True
        return user_role(request.user) in ('admin', 'property_manager')


class ReportingPermission(BasePermission):
    """§5 Reporting — staff with read access to operational/financial data."""

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True
        return user_role(request.user) in (
            'admin',
            'property_manager',
            'accountant',
            'finance_manager',
        )
