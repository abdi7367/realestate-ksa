import logging

from celery import shared_task

from contracts.services import ContractService

logger = logging.getLogger(__name__)


@shared_task
def check_expiring_contracts(days_ahead: int = 30):
    """
    Daily alert hook: log active contracts ending within ``days_ahead`` days.
    Wire email or push by extending logging handlers or calling notify services.
    """
    contracts = list(ContractService.get_expiring_contracts(days_ahead=days_ahead))
    for c in contracts:
        prop_name = c.unit.property.name if c.unit_id else None
        unit_no = c.unit.unit_number if c.unit_id else None
        tenant_label = None
        if c.tenant_id:
            t = c.tenant
            tenant_label = t.full_name if t else None
        logger.info(
            'Contract expiry alert: id=%s end_date=%s property=%s unit=%s tenant=%s',
            c.id,
            c.end_date,
            prop_name,
            unit_no,
            tenant_label,
        )
    return {'count': len(contracts), 'contract_ids': [c.id for c in contracts]}
