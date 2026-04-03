"""
Reporting API (requirement document §5 Reporting Module).
"""
from datetime import date, timedelta
from decimal import Decimal

from django.http import HttpResponse
from django.db.models import Sum
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import ReportingPermission
from contracts.models import Contract, Payment
from contracts.services import PaymentService
from debts.models import Debt
from finance.models import Transaction
from ownership.models import PropertyOwnership
from properties.models import Property
from vouchers.models import Voucher

from reports.cashflow_pdf import (
    ArabicPdfFontMissing,
    build_cash_flow_pdf_bytes,
    cash_flow_attachment_filename,
)


def _property_filter_fields(request):
    """Resolved name for optional property_id filter (for PDFs and API consumers)."""
    pid_qp = request.query_params.get('property_id')
    if pid_qp in (None, ''):
        return {'property_id': None, 'property_code': None, 'property_name': None}
    row = (
        Property.objects.filter(pk=pid_qp)
        .values('property_code', 'name')
        .first()
    )
    if not row:
        return {'property_id': pid_qp, 'property_code': None, 'property_name': None}
    return {
        'property_id': pid_qp,
        'property_code': row.get('property_code'),
        'property_name': row.get('name'),
    }


def _parse_date_range(request):
    """Default: last 12 months when params omitted (demo-data friendly)."""
    today = date.today()
    df_raw = request.query_params.get('date_from')
    dt_raw = request.query_params.get('date_to')
    try:
        date_from = date.fromisoformat(df_raw) if df_raw else today - timedelta(days=365)
    except ValueError:
        date_from = today - timedelta(days=365)
    try:
        date_to = date.fromisoformat(dt_raw) if dt_raw else today
    except ValueError:
        date_to = today
    return date_from, date_to


def _safe_limit(request, default: int = 500, maximum: int = 2000) -> int:
    """Parse an optional ``limit`` query-param, clamping to *maximum*."""
    raw = request.query_params.get('limit', '')
    try:
        return min(int(raw), maximum) if raw else default
    except (ValueError, TypeError):
        return default


class PropertyIncomeReportView(APIView):
    """§5 Property income report — uses §3.5 income categories."""

    permission_classes = [ReportingPermission]

    def get(self, request):
        qs = Transaction.objects.filter(transaction_type='income')
        if pid := request.query_params.get('property_id'):
            qs = qs.filter(property_id=pid)
        if year := request.query_params.get('year'):
            qs = qs.filter(date__year=int(year))
        if month := request.query_params.get('month'):
            qs = qs.filter(date__month=int(month))
        by_category = list(qs.values('category').annotate(total=Sum('amount')))
        total = qs.aggregate(s=Sum('amount'))['s'] or Decimal('0')
        return Response({
            'report': 'property_income',
            'filters': {
                **_property_filter_fields(request),
                'year': request.query_params.get('year'),
                'month': request.query_params.get('month'),
            },
            'by_category': by_category,
            'total_income': str(total),
        })


class ContractReportView(APIView):
    """§5 Contract report."""

    permission_classes = [ReportingPermission]

    def get(self, request):
        qs = Contract.objects.select_related(
            'unit', 'unit__property', 'tenant',
        )
        if st := request.query_params.get('status'):
            qs = qs.filter(status=st)
        if df := request.query_params.get('date_from'):
            qs = qs.filter(start_date__gte=df)
        limit = _safe_limit(request)
        rows = []
        for c in qs[:limit]:
            tenant = c.tenant
            rows.append({
                'contract_id': c.id,
                'status': c.status,
                'tenant_name': tenant.full_name if tenant else None,
                'tenant_reference': tenant.tenant_reference if tenant else None,
                'tenant_national_id': tenant.national_id if tenant else None,
                'property_name': c.unit.property.name if c.unit_id else None,
                'unit_number': c.unit.unit_number if c.unit_id else None,
                'start_date': c.start_date,
                'end_date': c.end_date,
                'monthly_rent': str(c.monthly_rent),
                'security_deposit': str(c.security_deposit),
                'payment_schedule': c.payment_schedule,
                'total_with_vat': str(c.total_value_with_vat),
            })
        return Response({
            'report': 'contracts',
            'count': qs.count(),
            'results': rows,
        })


class TenantPaymentReportView(APIView):
    """§5 Tenant payment report."""

    permission_classes = [ReportingPermission]

    def get(self, request):
        qs = Payment.objects.filter(status='confirmed').select_related(
            'contract',
            'contract__tenant',
            'contract__unit',
            'contract__unit__property',
        )
        if tid := request.query_params.get('tenant_id'):
            qs = qs.filter(contract__tenant_id=tid)
        if pid := request.query_params.get('property_id'):
            qs = qs.filter(contract__unit__property_id=pid)
        limit = _safe_limit(request)
        rows = []
        for p in qs.order_by('-payment_date')[:limit]:
            c = p.contract
            t = c.tenant
            rows.append({
                'payment_id': p.id,
                'payment_date': p.payment_date,
                'due_date': p.due_date,
                'amount': str(p.amount),
                'is_late': bool(
                    p.due_date and p.payment_date and p.payment_date > p.due_date
                ),
                'tenant_name': t.full_name if t else None,
                'tenant_reference': t.tenant_reference if t else None,
                'tenant_national_id': t.national_id if t else None,
                'contract_id': c.id,
                'property_name': c.unit.property.name if c.unit_id else None,
            })
        return Response({
            'report': 'tenant_payments',
            'count': qs.count(),
            'results': rows,
        })


class OutstandingBalancesReportView(APIView):
    """§5 Outstanding balances (active contracts with remaining rent/VAT balance)."""

    permission_classes = [ReportingPermission]

    def get(self, request):
        contracts = Contract.objects.filter(status='active').select_related(
            'tenant', 'unit', 'unit__property',
        ).prefetch_related('payments')
        rows = []
        for c in contracts:
            remaining = PaymentService.get_remaining_balance(c)
            if remaining > Decimal('0'):
                t = c.tenant
                rows.append({
                    'contract_id': c.id,
                    'tenant_name': t.full_name if t else None,
                    'tenant_reference': t.tenant_reference if t else None,
                    'tenant_national_id': t.national_id if t else None,
                    'property_name': c.unit.property.name if c.unit_id else None,
                    'unit_number': c.unit.unit_number if c.unit_id else None,
                    'remaining_balance': str(remaining),
                    'total_contract_with_vat': str(c.total_value_with_vat),
                })
        return Response({
            'report': 'outstanding_balances',
            'count': len(rows),
            'results': rows,
        })


class DebtRepaymentReportView(APIView):
    """§5 Debt repayment report."""

    permission_classes = [ReportingPermission]

    def get(self, request):
        qs = Debt.objects.select_related('property').prefetch_related('installments')
        if pid := request.query_params.get('property_id'):
            qs = qs.filter(property_id=pid)
        rows = []
        for d in qs:
            rows.append({
                'debt_id': d.id,
                'property_name': d.property.name,
                'creditor_name': d.creditor_name,
                'total_amount': str(d.total_amount),
                'paid_amount': str(d.paid_amount()),
                'remaining_balance': str(d.remaining_balance()),
                'installment_count': d.installments.count(),
            })
        return Response({
            'report': 'debt_repayment',
            'count': len(rows),
            'results': rows,
        })


class PropertyProfitabilityReportView(APIView):
    """§5 Property profitability (income − expenses)."""

    permission_classes = [ReportingPermission]

    def get(self, request):
        pid = request.query_params.get('property_id')
        qs = Transaction.objects.all()
        if pid:
            qs = qs.filter(property_id=pid)
        if year := request.query_params.get('year'):
            qs = qs.filter(date__year=int(year))
        income = qs.filter(transaction_type='income').aggregate(
            t=Sum('amount')
        )['t'] or Decimal('0')
        expense = qs.filter(transaction_type='expense').aggregate(
            t=Sum('amount')
        )['t'] or Decimal('0')
        profit = income - expense
        prop_name = None
        if pid:
            prop_name = Property.objects.filter(pk=pid).values_list('name', flat=True).first()
        return Response({
            'report': 'property_profitability',
            'property_id': pid,
            'property_name': prop_name,
            'year': request.query_params.get('year'),
            'total_income': str(income),
            'total_expense': str(expense),
            'profit': str(profit),
        })


class VoucherReportView(APIView):
    """§5 Voucher report."""

    permission_classes = [ReportingPermission]

    def get(self, request):
        qs = Voucher.objects.select_related('property', 'created_by').all()
        if st := request.query_params.get('approval_status'):
            qs = qs.filter(approval_status=st)
        if pid := request.query_params.get('property_id'):
            qs = qs.filter(property_id=pid)
        limit = _safe_limit(request)
        rows = []
        for v in qs.order_by('-date')[:limit]:
            rows.append({
                'voucher_id': v.id,
                'voucher_number': v.voucher_number,
                'date': v.date,
                'amount': str(v.amount),
                'payee_name': v.payee_name,
                'approval_status': v.approval_status,
                'property_name': v.property.name,
            })
        return Response({
            'report': 'vouchers',
            'count': qs.count(),
            'results': rows,
        })


class CashFlowReportView(APIView):
    """§3.6 Cash flow — transactions plus voucher disbursements and rent collections (see note)."""

    permission_classes = [ReportingPermission]

    def get(self, request):
        date_from, date_to = _parse_date_range(request)
        tq = Transaction.objects.filter(date__gte=date_from, date__lte=date_to)
        if pid := request.query_params.get('property_id'):
            tq = tq.filter(property_id=pid)
        income = tq.filter(transaction_type='income').aggregate(t=Sum('amount'))['t'] or Decimal('0')
        expense = tq.filter(transaction_type='expense').aggregate(t=Sum('amount'))['t'] or Decimal('0')
        vq = Voucher.objects.filter(
            date__gte=date_from,
            date__lte=date_to,
            approval_status='approved',
        )
        if pid:
            vq = vq.filter(property_id=pid)
        disbursements = vq.aggregate(t=Sum('amount'))['t'] or Decimal('0')
        pq = Payment.objects.filter(
            status='confirmed',
            payment_date__gte=date_from,
            payment_date__lte=date_to,
        ).select_related('contract__unit')
        if pid:
            pq = pq.filter(contract__unit__property_id=pid)
        collections = pq.aggregate(t=Sum('amount'))['t'] or Decimal('0')
        return Response({
            'report': 'cash_flow',
            'date_from': date_from.isoformat(),
            'date_to': date_to.isoformat(),
            'filters': {**_property_filter_fields(request)},
            'operating_income_from_transactions': str(income),
            'operating_expense_from_transactions': str(expense),
            'net_operating_transactions': str(income - expense),
            'approved_disbursements': str(disbursements),
            'tenant_payment_collections': str(collections),
            'note': (
                'Avoid double-counting: if rent is both recorded as Payment and '
                'as a rental income Transaction, totals overlap.'
            ),
        })


class CashFlowReportPdfView(APIView):
    """
    Printable, downloadable PDF for cash flow.
    Same filters as CashFlowReportView: property_id, date_from, date_to.
    """

    permission_classes = [ReportingPermission]

    def get(self, request):
        date_from, date_to = _parse_date_range(request)
        pid = request.query_params.get('property_id')
        ui_lang = (request.query_params.get('lang') or '').strip().lower()
        if not ui_lang:
            al = (request.headers.get('Accept-Language') or '').lower()
            ui_lang = 'ar' if al.startswith('ar') else 'en'

        tq = Transaction.objects.filter(date__gte=date_from, date__lte=date_to)
        if pid:
            tq = tq.filter(property_id=pid)

        vq = Voucher.objects.filter(
            date__gte=date_from,
            date__lte=date_to,
            approval_status='approved',
        )
        if pid:
            vq = vq.filter(property_id=pid)

        pq = Payment.objects.filter(
            status='confirmed',
            payment_date__gte=date_from,
            payment_date__lte=date_to,
        ).select_related('contract__unit__property', 'contract__tenant')
        if pid:
            pq = pq.filter(contract__unit__property_id=pid)

        income = tq.filter(transaction_type='income').aggregate(t=Sum('amount'))['t'] or Decimal('0')
        expense = tq.filter(transaction_type='expense').aggregate(t=Sum('amount'))['t'] or Decimal('0')
        disbursements = vq.aggregate(t=Sum('amount'))['t'] or Decimal('0')
        collections = pq.aggregate(t=Sum('amount'))['t'] or Decimal('0')

        pf = _property_filter_fields(request)
        tx_rows = list(tq.select_related('property').order_by('date', 'id')[:500])
        v_rows = list(vq.select_related('property').order_by('date', 'id')[:500])
        p_rows = list(pq.order_by('payment_date', 'id')[:500])

        try:
            pdf = build_cash_flow_pdf_bytes(
                date_from=date_from,
                date_to=date_to,
                pid=pid,
                pf=pf,
                income=income,
                expense=expense,
                disbursements=disbursements,
                collections=collections,
                tx_rows=tx_rows,
                v_rows=v_rows,
                p_rows=p_rows,
                ui_lang=ui_lang,
            )
        except ArabicPdfFontMissing as exc:
            return Response({'detail': str(exc)}, status=500)

        filename = cash_flow_attachment_filename(date_from, date_to, pid, pf)
        resp = HttpResponse(pdf, content_type='application/pdf')
        resp['Content-Disposition'] = f'attachment; filename="{filename}"'
        return resp


class IncomeStatementReportView(APIView):
    """§3.6 Income side — rental and other income categories for a period."""

    permission_classes = [ReportingPermission]

    def get(self, request):
        date_from, date_to = _parse_date_range(request)
        qs = Transaction.objects.filter(
            transaction_type='income',
            date__gte=date_from,
            date__lte=date_to,
        )
        if pid := request.query_params.get('property_id'):
            qs = qs.filter(property_id=pid)
        by_category = list(qs.values('category').annotate(total=Sum('amount')))
        total = qs.aggregate(s=Sum('amount'))['s'] or Decimal('0')
        return Response({
            'report': 'income_statement',
            'date_from': date_from.isoformat(),
            'date_to': date_to.isoformat(),
            'filters': {**_property_filter_fields(request)},
            'by_category': by_category,
            'total_income': str(total),
        })


class ExpenseReportView(APIView):
    """§3.6 Expense report by category for a period."""

    permission_classes = [ReportingPermission]

    def get(self, request):
        date_from, date_to = _parse_date_range(request)
        qs = Transaction.objects.filter(
            transaction_type='expense',
            date__gte=date_from,
            date__lte=date_to,
        )
        if pid := request.query_params.get('property_id'):
            qs = qs.filter(property_id=pid)
        by_category = list(qs.values('category').annotate(total=Sum('amount')))
        total = qs.aggregate(s=Sum('amount'))['s'] or Decimal('0')
        return Response({
            'report': 'expenses',
            'date_from': date_from.isoformat(),
            'date_to': date_to.isoformat(),
            'filters': {**_property_filter_fields(request)},
            'by_category': by_category,
            'total_expense': str(total),
        })


class OwnershipReportView(APIView):
    """§3.4 Owner-wise properties and management / revenue-sharing metadata."""

    permission_classes = [ReportingPermission]

    def get(self, request):
        qs = PropertyOwnership.objects.select_related('property').order_by(
            'owner_name', 'property__name'
        )
        if pid := request.query_params.get('property_id'):
            qs = qs.filter(property_id=pid)
        if ot := request.query_params.get('ownership_type'):
            qs = qs.filter(ownership_type=ot)

        owners = {}
        for o in qs:
            key = (o.owner_id, o.owner_name)
            if key not in owners:
                owners[key] = {
                    'owner_id': o.owner_id,
                    'owner_name': o.owner_name,
                    'contact': {
                        'phone': o.owner_phone or None,
                        'email': o.owner_email or None,
                    },
                    'ownership_type': o.ownership_type,
                    'properties': [],
                }
            owners[key]['properties'].append({
                'property_id': o.property_id,
                'property_name': o.property.name,
                'property_city': o.property.city,
                'ownership_percentage': str(o.ownership_percentage),
                'management_fee_percentage': str(o.management_fee_percentage),
                'revenue_share_model': o.revenue_share_model or None,
                'has_management_agreement': bool(o.management_agreement),
            })

        return Response({
            'report': 'ownership',
            'count': qs.count(),
            'owners': list(owners.values()),
        })
