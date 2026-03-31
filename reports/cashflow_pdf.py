"""
Cash-flow PDF using fpdf2 + uharfbuzz for Arabic shaping and Unicode bidi.

Logical-order text from the database only — shaping/bidi are handled by fpdf2.
"""
from __future__ import annotations

from decimal import Decimal
from pathlib import Path

from django.utils import timezone

from finance.models import Transaction
from fpdf import FPDF
from fpdf.enums import TableBordersLayout, TableCellFillMode, TableHeadingsDisplay, XPos, YPos
from fpdf.fonts import FontFace

_NOTO_CANDIDATES = (
    Path(__file__).resolve().parent / 'fonts' / 'NotoNaskhArabic-Regular.ttf',
    Path('/usr/share/fonts/truetype/noto/NotoNaskhArabic-Regular.ttf'),
    Path('/usr/share/fonts/opentype/noto/NotoNaskhArabic-Regular.ttf'),
    Path('C:/Windows/Fonts/NotoNaskhArabic-Regular.ttf'),
)

# Brand (tailwind teal-600 / emerald accent)
_TEAL = (13, 148, 136)
_TEAL_DARK = (15, 118, 110)
_MUTED = (75, 85, 99)
_STRIPE = (248, 250, 249)
_NET_ROW = (236, 253, 245)

_INCOME_CAT = dict(Transaction.INCOME_CATEGORY_CHOICES)
_EXPENSE_CAT = dict(Transaction.EXPENSE_CATEGORY_CHOICES)


class ArabicPdfFontMissing(FileNotFoundError):
    """No Arabic-capable TTF available for PDF generation."""


class CashFlowPdf(FPDF):
    """Consistent header/footer and generation stamp."""

    def __init__(self, *, report_title: str, period_line: str, scope_line: str, generated_line: str):
        super().__init__(orientation='portrait', unit='mm', format='A4')
        self._report_title = report_title
        self._period_line = period_line
        self._scope_line = scope_line
        self._generated_line = generated_line
        self.set_margins(18, 18, 18)
        self.set_auto_page_break(auto=True, margin=16)

    def header(self) -> None:
        if self.page_no() == 1:
            return
        self.set_fill_color(*_TEAL)
        self.rect(0, 0, self.w, 7, 'F')
        self.set_font('NotoNaskh', size=7)
        self.set_text_color(255, 255, 255)
        self.set_xy(self.l_margin, 2)
        self.cell(0, 4, text=f'{self._report_title}  ·  {self._period_line}', align='L')
        self.set_text_color(0, 0, 0)

    def footer(self) -> None:
        self.set_y(-14)
        self.set_font('NotoNaskh', size=7)
        self.set_text_color(*_MUTED)
        self.cell(
            0,
            5,
            text=f'{self._generated_line}  ·  Page {self.page_no()}/{{nb}}',
            align='C',
        )
        self.set_text_color(0, 0, 0)


def resolve_noto_naskh_path() -> Path:
    for fp in _NOTO_CANDIDATES:
        try:
            if fp.exists() and fp.stat().st_size > 1000:
                return fp
        except OSError:
            continue
    raise ArabicPdfFontMissing(
        'Arabic PDF font not found. Add reports/fonts/NotoNaskhArabic-Regular.ttf '
        '(Noto Naskh Arabic) or install that font on the server.'
    )


def _dash(v) -> str:
    if v is None:
        return '—'
    s = str(v).strip()
    return s if s else '—'


def _trunc(text, max_len: int = 240) -> str:
    if text is None:
        return ''
    s = ' '.join(str(text).split())
    if len(s) <= max_len:
        return s
    return s[: max_len - 1] + '…'


def _money(d: Decimal) -> str:
    q = d.quantize(Decimal('0.01'))
    return f'{q:,.2f}'


def _property_cell(prop) -> str:
    if not prop:
        return '—'
    code = getattr(prop, 'property_code', None) or ''
    na = (getattr(prop, 'name', '') or '').strip()
    if code and na:
        return f'{code} — {na}'
    if code:
        return code
    return na if na else '—'


def _tenant_block(tenant) -> str:
    if not tenant:
        return '—'
    ref = tenant.tenant_reference or '—'
    nid = (tenant.national_id or '').strip() if tenant.national_id else '—'
    name = (tenant.full_name or '').strip() or '—'
    lines = [name, f'Ref: {ref}   Nat. ID: {nid}']
    if tenant.email:
        lines.append(f'Email: {tenant.email}')
    if tenant.phone:
        lines.append(f'Phone: {tenant.phone}')
    return '\n'.join(lines)


def _tx_category_label(t) -> str:
    m = _INCOME_CAT if t.transaction_type == 'income' else _EXPENSE_CAT
    return m.get(t.category, t.category)


def cash_flow_attachment_filename(date_from, date_to, pid, pf: dict) -> str:
    filename = f'cash-flow_{date_from.isoformat()}_to_{date_to.isoformat()}'
    if pid:
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
    return f'{filename}.pdf'


_HEAD_WHITE_ON_TEAL = FontFace(
    size_pt=8,
    emphasis='',
    color=(255, 255, 255),
    fill_color=_TEAL,
)


def _draw_cover(
    pdf: CashFlowPdf,
    *,
    cover_title_en: str,
    cover_title_ar: str | None,
    period_line: str,
    scope_line: str,
) -> None:
    pdf.set_fill_color(*_TEAL)
    pdf.rect(0, 0, pdf.w, 30, 'F')
    pdf.set_xy(pdf.l_margin, 8)
    pdf.set_font('NotoNaskh', size=17)
    pdf.set_text_color(255, 255, 255)
    pdf.multi_cell(0, text=cover_title_en, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    if cover_title_ar:
        pdf.set_font('NotoNaskh', size=11)
        pdf.multi_cell(0, text=cover_title_ar, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font('NotoNaskh', size=9)
    pdf.multi_cell(
        0,
        text=period_line,
        new_x=XPos.LMARGIN,
        new_y=YPos.NEXT,
    )
    pdf.set_font('NotoNaskh', size=9)
    pdf.multi_cell(
        0,
        text=scope_line,
        new_x=XPos.LMARGIN,
        new_y=YPos.NEXT,
    )
    pdf.set_text_color(0, 0, 0)
    pdf.set_xy(pdf.l_margin, 36)


def _section_heading(pdf: CashFlowPdf, title: str) -> None:
    pdf.ln(2.5)
    pdf.set_font('NotoNaskh', size=12)
    pdf.set_text_color(*_TEAL_DARK)
    pdf.multi_cell(0, text=title, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_text_color(0, 0, 0)
    pdf.set_draw_color(180, 180, 180)
    pdf.set_line_width(0.25)
    pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
    pdf.ln(1.2)


def _s(v) -> str:
    if v is None:
        return ''
    return str(v)


def build_cash_flow_pdf_bytes(
    *,
    date_from,
    date_to,
    pid,
    pf: dict,
    income: Decimal,
    expense: Decimal,
    disbursements: Decimal,
    collections: Decimal,
    tx_rows: list,
    v_rows: list,
    p_rows: list,
    ui_lang: str = 'en',
) -> bytes:
    font_path = resolve_noto_naskh_path()
    net_tx = income - expense
    is_ar = str(ui_lang or 'en').lower().startswith('ar')
    tr = (lambda en, ar: ar if is_ar else en)

    report_title = tr('Cash flow report', 'تقرير التدفق النقدي')
    period_line = tr(
        f'Reporting period: {date_from.isoformat()} → {date_to.isoformat()}',
        f'فترة التقرير: {date_from.isoformat()} → {date_to.isoformat()}',
    )
    if pf.get('property_id'):
        code = pf.get('property_code') or ''
        name = (pf.get('property_name') or '').strip()
        pid_v = pf['property_id']
        if code and name:
            scope = tr(
                f'Scope: {code} — {name} (ID {pid_v})',
                f'نطاق التقرير: {code} — {name} (معرّف {pid_v})',
            )
        elif code:
            scope = tr(f'Scope: {code} (ID {pid_v})', f'نطاق التقرير: {code} (معرّف {pid_v})')
        elif name:
            scope = tr(f'Scope: {name} (ID {pid_v})', f'نطاق التقرير: {name} (معرّف {pid_v})')
        else:
            scope = tr(f'Scope: Property ID {pid_v}', f'نطاق التقرير: معرّف العقار {pid_v}')
    else:
        scope = tr('Scope: All properties', 'نطاق التقرير: جميع العقارات')

    now = timezone.now()
    generated_line = tr(
        f'Generated: {now.strftime("%Y-%m-%d %H:%M")}',
        f'أُنشئ في: {now.strftime("%Y-%m-%d %H:%M")}',
    )

    pdf = CashFlowPdf(
        report_title=report_title,
        period_line=period_line,
        scope_line=scope,
        generated_line=generated_line,
    )
    pdf.add_font('NotoNaskh', '', str(font_path))
    pdf.set_font('NotoNaskh', size=10)
    try:
        pdf.set_text_shaping(use_shaping_engine=True)
    except Exception as exc:  # pragma: no cover
        raise ArabicPdfFontMissing(
            'PDF text shaping failed. Install HarfBuzz bindings: pip install uharfbuzz'
        ) from exc

    pdf.add_page()
    _draw_cover(
        pdf,
        cover_title_en='Cash flow report',
        cover_title_ar='تقرير التدفق النقدي' if is_ar else None,
        period_line=period_line,
        scope_line=scope,
    )

    _section_heading(pdf, tr('1. Summary (SAR)', '١. الملخص (ر.س)'))

    with pdf.table(
        width=pdf.epw,
        col_widths=(2, 1),
        text_align=('LEFT', 'RIGHT'),
        line_height=6.5,
        repeat_headings=TableHeadingsDisplay.NONE,
        headings_style=_HEAD_WHITE_ON_TEAL,
        borders_layout=TableBordersLayout.ALL,
        cell_fill_mode=TableCellFillMode.EVEN_ROWS,
        cell_fill_color=_STRIPE,
        padding=(1.5, 2, 1.5, 2),
    ) as table:
        table.row(
            (
                tr('Metric', 'البند'),
                tr('Amount (SAR)', 'المبلغ (ر.س)'),
            )
        )
        table.row(
            (
                tr('Operating income (ledger)', 'إيرادات تشغيلية (قيود)'),
                _money(income),
            )
        )
        table.row(
            (
                tr('Operating expense (ledger)', 'مصروفات تشغيلية (قيود)'),
                _money(expense),
            )
        )
        table.row(
            (
                tr('Net operating (income − expense)', 'صافي التشغيل (الإيرادات - المصروفات)'),
                _money(net_tx),
            ),
            style=FontFace(fill_color=_NET_ROW),
        )
        table.row(
            (
                tr('Paid on approved vouchers', 'مدفوعات السندات المعتمدة'),
                _money(disbursements),
            )
        )
        table.row(
            (
                tr('Tenant rent collected (confirmed payments)', 'إيجار محصّل (مدفوعات مؤكدة)'),
                _money(collections),
            )
        )
        table.row(
            (
                tr('Records shown (transactions / vouchers / payments)', 'عدد السجلات (قيود / سندات / مدفوعات)'),
                f'{len(tx_rows)} / {len(v_rows)} / {len(p_rows)}',
            )
        )

    pdf.set_font('NotoNaskh', size=7.5)
    pdf.set_text_color(*_MUTED)
    pdf.ln(1)
    pdf.multi_cell(
        0,
        text=(
            tr(
                'Important: if the same rent is entered as both tenant payment and ledger income, '
                'totals can overlap. Treat each stream separately.',
                'مهم: إذا سُجّل نفس الإيجار كمدفوع مستأجر وكإيراد دفتر، قد تتداخل المجاميع. '
                'تعامل مع كل مسار بشكل منفصل.',
            )
        ),
        new_x=XPos.LMARGIN,
        new_y=YPos.NEXT,
    )
    pdf.set_text_color(0, 0, 0)

    _section_heading(
        pdf,
        tr('2. Ledger transactions (max 500)', '٢. حركات الدفتر المحاسبي (حتى ٥٠٠ سطر)'),
    )
    pdf.set_font('NotoNaskh', size=7.5)

    with pdf.table(
        width=pdf.epw,
        col_widths=(22, 20, 30, 22, 52, 28),
        line_height=5,
        repeat_headings=TableHeadingsDisplay.ON_TOP_OF_EVERY_PAGE,
        v_align='TOP',
        headings_style=_HEAD_WHITE_ON_TEAL,
        borders_layout=TableBordersLayout.ALL,
        cell_fill_mode=TableCellFillMode.EVEN_ROWS,
        cell_fill_color=_STRIPE,
        padding=(1, 1.5, 1, 1.5),
    ) as table:
        table.row(
            (
                tr('Date', 'التاريخ'),
                tr('Type', 'النوع'),
                tr('Category', 'الفئة'),
                tr('Amount', 'المبلغ'),
                tr('Property', 'العقار'),
                tr('Reference', 'المرجع'),
            )
        )
        if not tx_rows:
            table.row((tr('No transaction records', 'لا توجد قيود'), '', '', '', '', ''))
        else:
            for t in tx_rows:
                prop = _property_cell(t.property) if t.property_id else '—'
                ref = _dash(t.reference)
                r = table.row()
                r.cell(_s(t.date), align='L')
                r.cell(_s(t.get_transaction_type_display()), align='L')
                r.cell(_tx_category_label(t), align='R')
                r.cell(_money(t.amount), align='R')
                r.cell(prop, align='R')
                r.cell(ref, align='R')

    _section_heading(
        pdf,
        tr('3. Approved vouchers (max 500)', '٣. السندات المعتمدة (حتى ٥٠٠ سطر)'),
    )
    pdf.set_font('NotoNaskh', size=7.5)

    with pdf.table(
        width=pdf.epw,
        col_widths=(16, 18, 28, 22, 38, 20, 32),
        line_height=5,
        repeat_headings=TableHeadingsDisplay.ON_TOP_OF_EVERY_PAGE,
        v_align='TOP',
        headings_style=_HEAD_WHITE_ON_TEAL,
        borders_layout=TableBordersLayout.ALL,
        cell_fill_mode=TableCellFillMode.EVEN_ROWS,
        cell_fill_color=_STRIPE,
        padding=(1, 1.5, 1, 1.5),
    ) as table:
        table.row(
            (
                tr('Date', 'التاريخ'),
                tr('Voucher', 'السند'),
                tr('Payee', 'المستفيد'),
                tr('Method', 'طريقة الدفع'),
                tr('Description', 'الوصف'),
                tr('Amount', 'المبلغ'),
                tr('Property', 'العقار'),
            )
        )
        if not v_rows:
            table.row((tr('No approved voucher records', 'لا توجد سندات معتمدة'), '', '', '', '', '', ''))
        else:
            for v in v_rows:
                desc = _trunc(v.description, 200) or '—'
                pay_m = v.get_payment_method_display()
                prop = _property_cell(v.property) if v.property_id else '—'
                r = table.row()
                r.cell(_s(v.date), align='L')
                r.cell(_s(v.voucher_number), align='L')
                r.cell(_dash(v.payee_name), align='R')
                r.cell(_s(pay_m), align='R')
                r.cell(desc, align='R')
                r.cell(_money(v.amount), align='R')
                r.cell(prop, align='R')

    _section_heading(
        pdf,
        tr('4. Tenant payments (max 500)', '٤. مدفوعات المستأجرين (حتى ٥٠٠ سطر)'),
    )
    pdf.set_font('NotoNaskh', size=7.5)

    with pdf.table(
        width=pdf.epw,
        col_widths=(15, 14, 16, 18, 40, 12, 26, 12, 25),
        line_height=5,
        repeat_headings=TableHeadingsDisplay.ON_TOP_OF_EVERY_PAGE,
        v_align='TOP',
        headings_style=_HEAD_WHITE_ON_TEAL,
        borders_layout=TableBordersLayout.ALL,
        cell_fill_mode=TableCellFillMode.EVEN_ROWS,
        cell_fill_color=_STRIPE,
        padding=(1, 1.5, 1, 1.5),
    ) as table:
        table.row(
            (
                tr('Paid', 'تاريخ الدفع'),
                tr('Due', 'الاستحقاق'),
                tr('Amount', 'المبلغ'),
                tr('Method', 'الطريقة'),
                tr('Tenant', 'المستأجر'),
                tr('Unit', 'الوحدة'),
                tr('Property', 'العقار'),
                tr('Contract', 'العقد'),
                tr('Notes', 'ملاحظات'),
            )
        )
        if not p_rows:
            table.row((tr('No tenant payment records', 'لا توجد مدفوعات مستأجرين'), '', '', '', '', '', '', '', ''))
        else:
            for p in p_rows:
                c = p.contract
                tenant = c.tenant if c else None
                unit = c.unit if c else None
                prop = unit.property if unit and unit.property_id else None
                notes = _trunc(p.notes, 140) or '—'
                p_prop = _property_cell(prop) if prop else '—'
                r = table.row()
                r.cell(_s(p.payment_date), align='L')
                r.cell(_s(p.due_date or '—'), align='L')
                r.cell(_money(p.amount), align='R')
                r.cell(_s(p.get_payment_method_display()), align='R')
                r.cell(_tenant_block(tenant), align='R')
                r.cell(unit.unit_number if unit else '—', align='R')
                r.cell(p_prop, align='R')
                r.cell(_s(c.id) if c else '—', align='R')
                r.cell(notes, align='R')

    return bytes(pdf.output())
