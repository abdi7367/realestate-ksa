from celery import shared_task
from django.utils import timezone

from debts.models import DebtInstallment


@shared_task
def mark_overdue_debt_installments():
    """Mark pending installments past due_date as overdue (§3.3 reminders / status)."""
    today = timezone.now().date()
    updated = DebtInstallment.objects.filter(
        status='pending',
        due_date__lt=today,
    ).update(status='overdue')
    return {'marked_overdue': updated}
