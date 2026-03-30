"""
Reporting API (requirement document §5 Reporting Module).
"""
from datetime import date, timedelta
from decimal import Decimal
from functools import lru_cache
from io import BytesIO
from pathlib import Path

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

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

try:
    import arabic_reshaper
except ImportError:  # pragma: no cover
    arabic_reshaper = None
try:
    from bidi.algorithm import get_display
except ImportError:  # pragma: no cover
    get_display = None


def _pdf_latin_only(value):
    """
    ReportLab’s built-in fonts render Arabic poorly. For printable PDFs we keep
    Latin digits / punctuation and drop Arabic script (UI and JSON still show full names).
    """
    if value is None:
        return ''
    s = str(value)
    out = []
    for ch in s:
        o = ord(ch)
        if ch in '\n\r\t':
            out.append(' ')
        elif 0x0600 <= o <= 0x06FF or 0x0750 <= o <= 0x077F or 0x08A0 <= o <= 0x08FF:
            continue
        else:
            out.append(ch)
    cleaned = ' '.join(''.join(out).split())
    return cleaned if cleaned else '—'


def _property_cell_pdf(property_obj):
    if not property_obj:
        return '—'
    code = getattr(property_obj, 'property_code', None) or ''
    name_l = _pdf_latin_only(getattr(property_obj, 'name', '') or '')
    if code and name_l != '—':
        return f'{code} — {name_l}'
    if code:
        return code
    return name_l


@lru_cache(maxsize=1)
def _cashflow_detail_font():
    """
    Return (reportlab_font_name, path_to_ttf) for Arabic-capable text in PDF tables.
    The path is used with arabic-reshaper's TTF configuration.
    """
    candidates = (
        Path(__file__).resolve().parent / 'fonts' / 'NotoNaskhArabic-Regular.ttf',
        Path('C:/Windows/Fonts/arial.ttf'),
        Path('C:/Windows/Fonts/tahoma.ttf'),
    )
    for idx, fp in enumerate(candidates):
        try:
            if fp.exists() and fp.stat().st_size > 1000:
                font_name = f'CashFlowDetail{idx}'
                pdfmetrics.registerFont(TTFont(font_name, str(fp)))
                return font_name, str(fp)
        except Exception:
            continue
    return None, None


@lru_cache(maxsize=4)
def _arabic_reshaper_for_path(ttf_path: str):
    if not arabic_reshaper or not ttf_path:
        return arabic_reshaper.default_reshaper if arabic_reshaper else None
    try:
        cfg = arabic_reshaper.config_for_true_type_font(ttf_path)
        return arabic_reshaper.ArabicReshaper(configuration=cfg)
    except Exception:
        return arabic_reshaper.default_reshaper


def _pdf_shaped_text(text, ttf_path):
    """
    ReportLab draws LTR glyph-by-glyph. For Arabic we must reshape + bidi-reorder
    so joining and direction match what readers expect.
    """
    if text is None:
        return ''
    s = str(text)
    if not s or not ttf_path or not arabic_reshaper or not get_display:
        return s
    try:
        reshaper = _arabic_reshaper_for_path(ttf_path)
        if not reshaper:
            reshaper = arabic_reshaper.default_reshaper
        parts = []
        for line in s.split('\n'):
            stripped = line.strip()
            if not stripped:
                parts.append('')
                continue
            parts.append(get_display(reshaper.reshape(stripped)))
        return '\n'.join(parts)
    except Exception:
        return s


def _pdf_trunc_plain(text, max_len=240):
    if text is None:
        return ''
    s = ' '.join(str(text).split())
    if len(s) <= max_len:
        return s
    return s[: max_len - 1] + '…'


def _pdf_name_field(value, detail_font, ttf_path):
    if value is None:
        return ''
    s = str(value).strip()
    if not s:
        return ''
    if detail_font and ttf_path:
        return _pdf_shaped_text(s, ttf_path)
    if detail_font:
        return s
    return _pdf_latin_only(value)


def _property_cell_pdf_rich(property_obj, detail_font, ttf_path):
    if not property_obj:
        return '—'
    if not detail_font:
        return _property_cell_pdf(property_obj)
    code = getattr(property_obj, 'property_code', None) or ''
    raw_name = (getattr(property_obj, 'name', '') or '').strip()
    if code and raw_name:
        line = f'{code} — {raw_name}'
    elif code:
        line = code
    else:
        line = raw_name
    if not line:
        return '—'
    if ttf_path:
        return _pdf_shaped_text(line, ttf_path)
    return line


def _tenant_detail_block(tenant, detail_font, ttf_path):
    """Multiline cell: tenant name + reference + national id (+ phone if Latin)."""
    if not tenant:
        return '—'
    ref = tenant.tenant_reference or '—'
    email = _pdf_latin_only(tenant.email) if tenant.email else ''
    phone = _pdf_latin_only(tenant.phone) if tenant.phone else ''
    if not detail_font:
        name = _pdf_latin_only(tenant.full_name)
        nid = _pdf_latin_only(tenant.national_id) if tenant.national_id else '—'
        lines = [name, f'Ref: {ref}   Nat. ID: {nid}']
        if email:
            lines.append(f'Email: {email}')
        if phone:
            lines.append(f'Phone: {phone}')
        return '\n'.join(lines)
    name_raw = (tenant.full_name or '').strip()
    nid_raw = (tenant.national_id or '').strip() if tenant.national_id else '—'
    lines = [name_raw, f'Ref: {ref}   Nat. ID: {nid_raw}']
    if email:
        lines.append(f'Email: {email}')
    if phone:
        lines.append(f'Phone: {phone}')
    block = '\n'.join(lines)
    if ttf_path:
        return _pdf_shaped_text(block, ttf_path)
    return block


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
    if df_raw:
        date_from = date.fromisoformat(df_raw)
    else:
        date_from = today - timedelta(days=365)
    if dt_raw:
        date_to = date.fromisoformat(dt_raw)
    else:
        date_to = today
    return date_from, date_to


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
        limit = min(int(request.query_params.get('limit', 500)), 2000)
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
        limit = min(int(request.query_params.get('limit', 500)), 2000)
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
        limit = min(int(request.query_params.get('limit', 500)), 2000)
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

        buf = BytesIO()
        doc = SimpleDocTemplate(
            buf,
            pagesize=A4,
            leftMargin=18 * mm,
            rightMargin=18 * mm,
            topMargin=16 * mm,
            bottomMargin=16 * mm,
            title='Cash Flow Report',
        )

        styles = getSampleStyleSheet()
        story = []
        detail_font, ttf_path = _cashflow_detail_font()

        story.append(Paragraph('Cash Flow Report', styles['Title']))
        subtitle = f'Period: {date_from.isoformat()} → {date_to.isoformat()}'
        story.append(Paragraph(subtitle, styles['Normal']))
        pf = _property_filter_fields(request)
        if pf['property_id']:
            code = pf.get('property_code') or ''
            raw_name = (pf.get('property_name') or '').strip()
            name_l = _pdf_latin_only(pf.get('property_name'))
            name_disp = raw_name if detail_font else (name_l if name_l != '—' else '')
            if code and name_disp:
                line = f'Property: {code} — {name_disp} (ID {pf["property_id"]})'
            elif code:
                line = f'Property: {code} (ID {pf["property_id"]})'
            elif name_disp:
                line = f'Property: {name_disp} (ID {pf["property_id"]})'
            else:
                line = f'Property ID: {pf["property_id"]}'
            if detail_font:
                line_out = _pdf_shaped_text(line, ttf_path) if ttf_path else line
                story.append(
                    Paragraph(
                        line_out,
                        ParagraphStyle(
                            'PdfPropFilter',
                            parent=styles['Normal'],
                            fontName=detail_font,
                            fontSize=10,
                            leading=12,
                        ),
                    )
                )
            else:
                story.append(Paragraph(line, styles['Normal']))
        story.append(Spacer(1, 8 * mm))

        totals_tbl = Table(
            [
                ['Metric', 'Amount (SAR)'],
                ['Operating income (Transactions)', str(income)],
                ['Operating expense (Transactions)', str(expense)],
                ['Net operating (Tx income − expense)', str(income - expense)],
                ['Approved disbursements (Vouchers)', str(disbursements)],
                ['Tenant collections (Payments)', str(collections)],
            ],
            colWidths=[110 * mm, 60 * mm],
            hAlign='LEFT',
        )
        totals_tbl.setStyle(
            TableStyle(
                [
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0d9488')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('GRID', (0, 0), (-1, -1), 0.25, colors.grey),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.whitesmoke, colors.lightgrey]),
                    ('ALIGN', (1, 1), (1, -1), 'RIGHT'),
                ]
            )
        )
        story.append(Paragraph('Summary', styles['Heading2']))
        story.append(totals_tbl)
        story.append(Spacer(1, 6 * mm))
        story.append(
            Paragraph(
                'Note: avoid double-counting if rent is recorded as both Payments and income Transactions.',
                styles['Italic'],
            )
        )
        story.append(Spacer(1, 8 * mm))

        # Detailed: Transactions
        tx_rows = list(tq.select_related('property').order_by('date', 'id')[:500])
        story.append(Paragraph(f'Transactions ({len(tx_rows)} shown, max 500)', styles['Heading2']))
        tx_table_data = [['Date', 'Type', 'Category', 'Amount', 'Property', 'Reference']]
        for t in tx_rows:
            tx_table_data.append(
                [
                    str(t.date),
                    t.transaction_type,
                    t.category,
                    str(t.amount),
                    _property_cell_pdf_rich(t.property, detail_font, ttf_path) if t.property_id else '—',
                    _pdf_name_field(t.reference, detail_font, ttf_path) if t.reference else '',
                ]
            )
        tx_tbl = Table(tx_table_data, repeatRows=1, colWidths=[22*mm, 18*mm, 28*mm, 22*mm, 55*mm, 25*mm])
        tx_tbl.setStyle(
            TableStyle(
                [
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#111827')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    (
                        'FONTNAME',
                        (0, 1),
                        (-1, -1),
                        detail_font or 'Helvetica',
                    ),
                    ('GRID', (0, 0), (-1, -1), 0.25, colors.grey),
                    ('ALIGN', (3, 1), (3, -1), 'RIGHT'),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('FONTSIZE', (0, 0), (-1, -1), 8),
                ]
            )
        )
        story.append(tx_tbl)
        story.append(Spacer(1, 8 * mm))

        # Detailed: Approved vouchers
        v_rows = list(vq.select_related('property').order_by('date', 'id')[:500])
        story.append(Paragraph(f'Approved Vouchers ({len(v_rows)} shown, max 500)', styles['Heading2']))
        v_table_data = [
            [
                'Date',
                'Voucher #',
                'Payee',
                'Pay method',
                'Description',
                'Amount',
                'Property',
            ],
        ]
        for v in v_rows:
            desc = _pdf_trunc_plain(v.description, 220)
            if detail_font and ttf_path and desc:
                desc = _pdf_shaped_text(desc, ttf_path)
            v_table_data.append(
                [
                    str(v.date),
                    v.voucher_number,
                    _pdf_name_field(v.payee_name, detail_font, ttf_path),
                    v.get_payment_method_display(),
                    desc,
                    str(v.amount),
                    _property_cell_pdf_rich(v.property, detail_font, ttf_path) if v.property_id else '—',
                ]
            )
        v_tbl = Table(
            v_table_data,
            repeatRows=1,
            colWidths=[16 * mm, 20 * mm, 28 * mm, 20 * mm, 42 * mm, 18 * mm, 30 * mm],
        )
        v_tbl.setStyle(
            TableStyle(
                [
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#111827')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    (
                        'FONTNAME',
                        (0, 1),
                        (-1, -1),
                        detail_font or 'Helvetica',
                    ),
                    ('GRID', (0, 0), (-1, -1), 0.25, colors.grey),
                    ('ALIGN', (5, 1), (5, -1), 'RIGHT'),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('FONTSIZE', (0, 0), (-1, -1), 7),
                ]
            )
        )
        story.append(v_tbl)
        story.append(Spacer(1, 8 * mm))

        # Detailed: Tenant payments
        p_rows = list(pq.order_by('payment_date', 'id')[:500])
        story.append(Paragraph(f'Tenant Collections (Payments) ({len(p_rows)} shown, max 500)', styles['Heading2']))
        p_table_data = [
            [
                'Payment date',
                'Due date',
                'Amount',
                'Method',
                'Tenant details',
                'Unit',
                'Property',
                'Contract',
                'Notes',
            ],
        ]
        for p in p_rows:
            c = p.contract
            tenant = c.tenant if c else None
            unit = c.unit if c else None
            prop = unit.property if unit and unit.property_id else None
            p_table_data.append(
                [
                    str(p.payment_date),
                    str(p.due_date or '—'),
                    str(p.amount),
                    p.get_payment_method_display(),
                    _tenant_detail_block(tenant, detail_font, ttf_path),
                    unit.unit_number if unit else '—',
                    _property_cell_pdf_rich(prop, detail_font, ttf_path) if prop else '—',
                    str(c.id) if c else '',
                    (
                        _pdf_shaped_text(_pdf_trunc_plain(p.notes, 160), ttf_path)
                        if (p.notes and detail_font and ttf_path)
                        else (_pdf_trunc_plain(p.notes, 160) if p.notes else '')
                    ),
                ]
            )
        # Total width ~174mm (A4 minus 18mm side margins each)
        p_tbl = Table(
            p_table_data,
            repeatRows=1,
            colWidths=[
                16 * mm,
                15 * mm,
                15 * mm,
                16 * mm,
                42 * mm,
                11 * mm,
                24 * mm,
                11 * mm,
                24 * mm,
            ],
        )
        p_tbl.setStyle(
            TableStyle(
                [
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#111827')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    (
                        'FONTNAME',
                        (0, 1),
                        (-1, -1),
                        detail_font or 'Helvetica',
                    ),
                    ('GRID', (0, 0), (-1, -1), 0.25, colors.grey),
                    ('ALIGN', (2, 1), (2, -1), 'RIGHT'),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('FONTSIZE', (0, 0), (-1, -1), 7),
                ]
            )
        )
        story.append(p_tbl)

        doc.build(story)
        pdf = buf.getvalue()
        buf.close()

        filename = f'cash-flow_{date_from.isoformat()}_to_{date_to.isoformat()}'
        if pid:
            pf = _property_filter_fields(request)
            slug_parts = []
            if pf.get('property_code'):
                slug_parts.append(
                    ''.join(
                        ch.lower() if ch.isalnum() else '-'
                        for ch in str(pf['property_code'])
                    ).strip('-')
                )
            if pf.get('property_name'):
                slug_parts.append(
                    ''.join(
                        ch.lower() if ch.isalnum() else '-'
                        for ch in pf['property_name']
                    ).strip('-')
                )
            slug = '-'.join(p for p in slug_parts if p)
            while '--' in slug:
                slug = slug.replace('--', '-')
            if slug:
                filename = f'{filename}_{slug}'
            else:
                filename = f'{filename}_property-{pid}'
        filename = f'{filename}.pdf'

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
