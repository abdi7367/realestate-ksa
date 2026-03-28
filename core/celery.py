import os

from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

app = Celery('core')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

app.conf.beat_schedule = {
    'check-expiring-contracts-daily': {
        'task': 'contracts.tasks.check_expiring_contracts',
        'schedule': crontab(hour=6, minute=0),
    },
    'mark-overdue-debt-installments-daily': {
        'task': 'debts.tasks.mark_overdue_debt_installments',
        'schedule': crontab(hour=6, minute=15),
    },
}
