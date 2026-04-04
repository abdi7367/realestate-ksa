"""
Cash-Flow PDF Report — Professional Edition
============================================
* English UI mode  → all headings/labels in English; only *data* values that
  contain Arabic script are rendered with Arabic shaping so names like
  "محمد عبدالله الرشيدي" display correctly in an otherwise English document.
* Arabic UI mode   → full bilingual layout (Arabic headings + English structure).

Font: NotoNaskhArabic for Arabic data; built-in Helvetica for pure-Latin text
      (avoids loading a heavy Latin TTF while still supporting Arabic data).

Uses fpdf2 >= 2.7 with text-shaping (uharfbuzz) for correct Arabic rendering.
"""
from __future__ import annotations

import re
from decimal import Decimal
from pathlib import Path

from django.utils import timezone

from finance.models import Transaction
from fpdf import FPDF
from fpdf.enums import TableBordersLayout, TableCellFillMode, TableHeadingsDisplay, XPos, YPos
from fpdf.fonts import FontFace

# ---------------------------------------------------------------------------
# Font paths
# ---------------------------------------------------------------------------
_NOTO_CANDIDATES = (
    Path(__file__).resolve().parent / "fonts" / "NotoNaskhArabic-Regular.ttf",
    Path("/usr/share/fonts/truetype/noto/NotoNaskhArabic-Regular.ttf"),
    Path("/usr/share/fonts/opentype/noto/NotoNaskhArabic-Regular.ttf"),
    Path("C:/Windows/Fonts/NotoNaskhArabic-Regular.ttf"),
)

# ---------------------------------------------------------------------------
# Brand palette
# ---------------------------------------------------------------------------
_BRAND       = (13, 148, 136)      # teal-600
_BRAND_DARK  = (11, 107, 99)       # teal-700
_BRAND_LIGHT = (204, 240, 237)     # teal-100
_ACCENT      = (37, 99, 235)       # blue-600
_SUCCESS     = (22, 163, 74)       # green-600
_WARNING     = (217, 119, 6)       # amber-600
_DANGER      = (220, 38, 38)       # red-600
_NEUTRAL     = (71, 85, 105)       # slate-600
_TEXT        = (15, 23, 42)        # slate-900
_MUTED       = (100, 116, 139)     # slate-500
_BORDER      = (203, 213, 225)     # slate-300
_STRIPE_ODD  = (248, 250, 252)     # slate-50
_STRIPE_EVEN = (255, 255, 255)
_NET_FILL    = (236, 253, 245)     # green-50
_COVER_BG    = (15, 23, 42)        # slate-900

_INCOME_CAT  = dict(Transaction.INCOME_CATEGORY_CHOICES)
_EXPENSE_CAT = dict(Transaction.EXPENSE_CATEGORY_CHOICES)

_HAS_ARABIC_RE = re.compile(r"[\u0600-\u06FF\u0750-\u077F\uFB50-\uFDFF\uFE70-\uFEFF]")


class ArabicPdfFontMissing(FileNotFoundError):
    """No Arabic-capable TTF available for PDF generation."""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _has_arabic(text: str) -> bool:
    """Return True if *text* contains any Arabic/RTL characters."""
    return bool(_HAS_ARABIC_RE.search(text or ""))


def _money(d: Decimal) -> str:
    q = d.quantize(Decimal("0.01"))
    return f"{q:,.2f}"


def _dash(v) -> str:
    if v is None:
        return "—"
    s = str(v).strip()
    return s if s else "—"


def _trunc(text, max_len: int = 180) -> str:
    if text is None:
        return ""
    s = " ".join(str(text).split())
    return s if len(s) <= max_len else s[: max_len - 1] + "…"


def _property_label(prop) -> str:
    if not prop:
        return "—"
    code = getattr(prop, "property_code", None) or ""
    name = (getattr(prop, "name", "") or "").strip()
    if code and name:
        return f"{code} – {name}"
    return name or code or "—"


def _tenant_name(tenant) -> str:
    if not tenant:
        return "—"
    return (tenant.full_name or "").strip() or "—"


def _tx_category_label(t) -> str:
    m = _INCOME_CAT if t.transaction_type == "income" else _EXPENSE_CAT
    return m.get(t.category, t.category.replace("_", " ").title())


def resolve_noto_naskh_path() -> Path:
    for fp in _NOTO_CANDIDATES:
        try:
            if fp.exists() and fp.stat().st_size > 1_000:
                return fp
        except OSError:
            continue
    raise ArabicPdfFontMissing(
        "Arabic PDF font not found. Add reports/fonts/NotoNaskhArabic-Regular.ttf "
        "or install Noto Naskh Arabic on the server."
    )


def cash_flow_attachment_filename(date_from, date_to, pid, pf: dict) -> str:
    base = f"cash-flow_{date_from.isoformat()}_to_{date_to.isoformat()}"
    if pid:
        raw = pf.get("property_code") or pf.get("property_name") or f"property-{pid}"
        slug = re.sub(r"[^a-zA-Z0-9]+", "-", str(raw)).strip("-").lower()
        base = f"{base}_{slug}"
    return f"{base}.pdf"


# ---------------------------------------------------------------------------
# PDF document class
# ---------------------------------------------------------------------------

class CashFlowPdf(FPDF):
    """
    Professional cash-flow PDF with:
    - Branded cover page
    - Running header/footer on inner pages
    - Mixed Arabic data / English labels
    """

    # Fonts registered once per instance
    _arabic_font = "NotoNaskh"

    def __init__(
        self,
        *,
        report_title: str,
        period_line: str,
        scope_line: str,
        generated_line: str,
        is_arabic_ui: bool = False,
        font_path: Path,
    ):
        super().__init__(orientation="portrait", unit="mm", format="A4")
        self._report_title = report_title
        self._period_line = period_line
        self._scope_line = scope_line
        self._generated_line = generated_line
        self._is_ar = is_arabic_ui
        self._font_path = font_path

        self.set_margins(18, 18, 18)
        self.set_auto_page_break(auto=True, margin=20)

        # Register Arabic font
        self.add_font(self._arabic_font, "", str(font_path))
        # Try to enable text shaping for correct Arabic glyph ordering
        try:
            self.set_text_shaping(use_shaping_engine=True)
        except Exception as exc:
            raise ArabicPdfFontMissing(
                "PDF text shaping failed — install uharfbuzz: pip install uharfbuzz"
            ) from exc

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _set_arabic(self, size: float = 9):
        self.set_font(self._arabic_font, size=size)

    def _set_latin(self, size: float = 9, bold: bool = False):
        style = "B" if bold else ""
        self.set_font("Helvetica", style=style, size=size)

    def _smart_font(self, text: str, size: float = 9, bold: bool = False):
        """Choose font based on whether text contains Arabic."""
        if _has_arabic(text):
            self._set_arabic(size)
        else:
            self._set_latin(size, bold)

    def _h_rule(self, color=None, thickness: float = 0.4):
        c = color or _BORDER
        self.set_draw_color(*c)
        self.set_line_width(thickness)
        self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
        self.set_draw_color(0, 0, 0)
        self.set_line_width(0.2)

    def _colored_rect(self, x, y, w, h, color):
        self.set_fill_color(*color)
        self.rect(x, y, w, h, "F")

    # ------------------------------------------------------------------
    # Header / Footer
    # ------------------------------------------------------------------

    def header(self):
        if self.page_no() == 1:
            return
        # Thin brand-color top bar
        self._colored_rect(0, 0, self.w, 6, _BRAND)
        # Title in bar
        self._set_latin(7)
        self.set_text_color(255, 255, 255)
        self.set_xy(self.l_margin, 0.8)
        self.cell(0, 5, self._report_title, align="L")
        self.set_xy(-60, 0.8)
        self.cell(55, 5, self._period_line, align="R")
        self.set_text_color(*_TEXT)
        self.set_y(10)

    def footer(self):
        self.set_y(-14)
        self._set_latin(7.5)
        self.set_text_color(*_MUTED)
        total = self.pages  # works in fpdf2
        self.cell(
            0, 5,
            f"{self._generated_line}   ·   Page {self.page_no()} of {{nb}}",
            align="C",
        )
        self.set_text_color(*_TEXT)

    # ------------------------------------------------------------------
    # Cover page
    # ------------------------------------------------------------------

    def draw_cover(
        self,
        *,
        title_en: str,
        title_ar: str | None,
        period_line: str,
        scope_line: str,
        date_from,
        date_to,
        summary: dict,
    ):
        """Full-bleed cover page with summary KPIs."""
        # Dark background
        self._colored_rect(0, 0, self.w, 80, _COVER_BG)
        # Brand accent bar at very top
        self._colored_rect(0, 0, self.w, 3, _BRAND)

        # Main title
        self.set_xy(self.l_margin, 14)
        self._set_latin(22, bold=True)
        self.set_text_color(255, 255, 255)
        self.cell(0, 10, title_en, align="L", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        # Arabic subtitle (if UI is Arabic)
        if title_ar and self._is_ar:
            self._set_arabic(14)
            self.cell(0, 8, title_ar, align="L", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        # Period & scope on cover
        self._set_latin(9)
        self.set_text_color(180, 210, 200)
        self.set_x(self.l_margin)
        self.cell(0, 6, period_line, align="L", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self._set_latin(8)
        self.set_text_color(140, 170, 160)
        self.cell(0, 5, scope_line, align="L", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        # KPI cards below the dark block
        self.set_y(88)
        self.set_text_color(*_TEXT)

        kpis = [
            ("Operating Income", _money(summary["income"]) + " SAR", _SUCCESS),
            ("Operating Expense", _money(summary["expense"]) + " SAR", _DANGER),
            ("Net Operating", _money(summary["net"]) + " SAR",
             _SUCCESS if summary["net"] >= 0 else _DANGER),
            ("Voucher Disbursements", _money(summary["disbursements"]) + " SAR", _WARNING),
            ("Rent Collected", _money(summary["collections"]) + " SAR", _ACCENT),
        ]

        card_w = (self.epw - 4 * 4) / 5  # 5 cards with 4mm gaps
        x0 = self.l_margin
        y0 = self.get_y()
        card_h = 28

        for i, (label, value, color) in enumerate(kpis):
            cx = x0 + i * (card_w + 4)
            # Card background
            self.set_fill_color(248, 250, 252)
            self.rect(cx, y0, card_w, card_h, "FD")
            # Top accent stripe
            self._colored_rect(cx, y0, card_w, 3, color)
            # Label
            self._set_latin(6.5)
            self.set_text_color(*_MUTED)
            self.set_xy(cx + 2, y0 + 5)
            self.cell(card_w - 4, 4, label, align="L")
            # Value
            self._set_latin(8.5, bold=True)
            self.set_text_color(*color)
            self.set_xy(cx + 2, y0 + 10)
            self.multi_cell(card_w - 4, 5, value, align="L")

        self.set_y(y0 + card_h + 6)
        self.set_text_color(*_TEXT)

        # Divider + description
        self._h_rule(_BORDER)
        self.ln(3)
        self._set_latin(8)
        self.set_text_color(*_MUTED)
        self.multi_cell(
            0,
            4.5,
            "This report consolidates ledger transactions, approved payment vouchers, "
            "and tenant rent collections for the selected period. Figures are in Saudi Riyals (SAR). "
            "VAT at 15% is included in contract totals. "
            "Note: if rent is recorded as both a Payment and a ledger Transaction, figures may overlap.",
            align="L",
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        self.ln(2)

    # ------------------------------------------------------------------
    # Section heading
    # ------------------------------------------------------------------

    def section_heading(self, number: str, title_en: str, title_ar: str | None = None):
        self.ln(3)
        # Left accent bar
        bar_x = self.l_margin - 5
        bar_y = self.get_y()
        self._colored_rect(bar_x, bar_y, 3, 8, _BRAND)

        self.set_x(self.l_margin)
        self._set_latin(11, bold=True)
        self.set_text_color(*_BRAND_DARK)
        heading_text = f"{number}  {title_en}"
        if title_ar and self._is_ar:
            heading_text += f"  /  {title_ar}"
        self.cell(0, 8, heading_text, align="L", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self._h_rule(_BRAND_LIGHT, thickness=0.6)
        self.ln(1.5)
        self.set_text_color(*_TEXT)

    # ------------------------------------------------------------------
    # Summary table
    # ------------------------------------------------------------------

    def draw_summary_table(self, *, income, expense, net, disbursements, collections,
                           tx_count, v_count, p_count):
        rows = [
            ("Operating Income (Ledger Transactions)", _money(income) + " SAR", _SUCCESS),
            ("Operating Expense (Ledger Transactions)", _money(expense) + " SAR", _DANGER),
            ("Net Operating  (Income − Expense)", _money(net) + " SAR",
             _SUCCESS if net >= 0 else _DANGER),
            ("Approved Voucher Disbursements", _money(disbursements) + " SAR", _WARNING),
            ("Tenant Rent Collected (Confirmed Payments)", _money(collections) + " SAR", _ACCENT),
            ("Transaction Records", str(tx_count), _NEUTRAL),
            ("Voucher Records (Approved)", str(v_count), _NEUTRAL),
            ("Payment Records", str(p_count), _NEUTRAL),
        ]

        col_w = [self.epw * 0.72, self.epw * 0.28]

        # Header row
        self._colored_rect(self.l_margin, self.get_y(), self.epw, 7, _BRAND)
        self._set_latin(8, bold=True)
        self.set_text_color(255, 255, 255)
        self.set_x(self.l_margin)
        self.cell(col_w[0], 7, "  Metric", align="L")
        self.cell(col_w[1], 7, "Amount / Count  ", align="R",
                  new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_text_color(*_TEXT)

        for i, (label, value, color) in enumerate(rows):
            fill = _STRIPE_ODD if i % 2 == 0 else _STRIPE_EVEN
            if "Net" in label:
                fill = _NET_FILL
            self.set_fill_color(*fill)
            row_y = self.get_y()
            row_h = 7

            # background
            self.rect(self.l_margin, row_y, self.epw, row_h, "F")

            self._set_latin(8.5)
            self.set_text_color(*_TEXT)
            self.set_x(self.l_margin)
            self.cell(col_w[0], row_h, f"  {label}", align="L")

            self._set_latin(8.5, bold=True)
            self.set_text_color(*color)
            self.cell(col_w[1], row_h, f"{value}  ", align="R",
                      new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        self.set_text_color(*_TEXT)
        # outer border
        self.set_draw_color(*_BORDER)
        self.set_line_width(0.3)
        table_h = 7 + len(rows) * 7
        self.rect(self.l_margin, self.get_y() - table_h, self.epw, table_h)
        self.set_draw_color(0, 0, 0)
        self.set_line_width(0.2)
        self.ln(4)


# ---------------------------------------------------------------------------
# Smart cell renderer (handles Arabic data in English doc)
# ---------------------------------------------------------------------------

def _write_smart_cell(
    pdf: CashFlowPdf,
    width: float,
    height: float,
    text: str,
    align: str = "L",
    size: float = 7.5,
    bold: bool = False,
    color=None,
):
    """Render cell choosing Arabic or Latin font based on content."""
    if color:
        pdf.set_text_color(*color)
    if _has_arabic(text):
        pdf._set_arabic(size)
    else:
        pdf._set_latin(size, bold)
    pdf.cell(width, height, text, align=align)
    if color:
        pdf.set_text_color(*_TEXT)


# ---------------------------------------------------------------------------
# Table builders
# ---------------------------------------------------------------------------

_HEAD_STYLE = FontFace(
    size_pt=8,
    emphasis="",
    color=(255, 255, 255),
    fill_color=_BRAND,
)


def _draw_transactions_table(pdf: CashFlowPdf, tx_rows: list):
    """Section 2 – Ledger transactions."""
    if not tx_rows:
        pdf._set_latin(8)
        pdf.set_text_color(*_MUTED)
        pdf.cell(0, 7, "  No transaction records in the selected period.", align="L",
                 new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_text_color(*_TEXT)
        return

    # Column widths: Date | Type | Category | Amount | Property | Description | Ref
    cw = [22, 18, 28, 24, 48, 0, 24]   # 0 = fill remaining
    cw[5] = pdf.epw - sum(cw) + cw[5]
    row_h = 6

    # Header
    headers = ["Date", "Type", "Category", "Amount (SAR)", "Property", "Description", "Ref"]
    _draw_header_row(pdf, cw, headers, row_h)

    for i, t in enumerate(tx_rows):
        fill = _STRIPE_ODD if i % 2 == 0 else _STRIPE_EVEN
        pdf.set_fill_color(*fill)
        row_y = pdf.get_y()
        pdf.rect(pdf.l_margin, row_y, pdf.epw, row_h, "F")

        is_income = t.transaction_type == "income"
        type_color = _SUCCESS if is_income else _DANGER

        pdf.set_x(pdf.l_margin)
        _write_smart_cell(pdf, cw[0], row_h, str(t.date), "L", 7.5)
        _write_smart_cell(pdf, cw[1], row_h,
                          "Income" if is_income else "Expense", "L", 7.5, color=type_color)
        _write_smart_cell(pdf, cw[2], row_h, _tx_category_label(t), "L", 7.5)
        _write_smart_cell(pdf, cw[3], row_h, _money(t.amount), "R", 7.5,
                          bold=True, color=type_color)
        _write_smart_cell(pdf, cw[4], row_h, _property_label(t.property), "L", 7.5)

        # Description – may contain Arabic
        desc = _trunc(t.description, 60) or "—"
        _write_smart_cell(pdf, cw[5], row_h, desc, "L", 7)
        _write_smart_cell(pdf, cw[6], row_h, _dash(t.reference), "L", 7)
        pdf.ln(row_h)

    _draw_border(pdf, len(tx_rows) + 1, row_h)
    pdf.ln(3)


def _draw_vouchers_table(pdf: CashFlowPdf, v_rows: list):
    """Section 3 – Approved vouchers."""
    if not v_rows:
        pdf._set_latin(8)
        pdf.set_text_color(*_MUTED)
        pdf.cell(0, 7, "  No approved vouchers in the selected period.", align="L",
                 new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_text_color(*_TEXT)
        return

    # Date | Voucher# | Payee | Method | Amount | Property | Description
    cw = [20, 28, 38, 22, 24, 40, 0]
    cw[6] = pdf.epw - sum(cw) + cw[6]
    row_h = 6

    headers = ["Date", "Voucher No.", "Payee", "Method", "Amount (SAR)", "Property", "Description"]
    _draw_header_row(pdf, cw, headers, row_h)

    for i, v in enumerate(v_rows):
        fill = _STRIPE_ODD if i % 2 == 0 else _STRIPE_EVEN
        pdf.set_fill_color(*fill)
        row_y = pdf.get_y()
        pdf.rect(pdf.l_margin, row_y, pdf.epw, row_h, "F")
        pdf.set_x(pdf.l_margin)

        _write_smart_cell(pdf, cw[0], row_h, str(v.date), "L", 7.5)
        _write_smart_cell(pdf, cw[1], row_h, v.voucher_number or "—", "L", 7.5)
        _write_smart_cell(pdf, cw[2], row_h, _dash(v.payee_name), "L", 7.5)
        _write_smart_cell(pdf, cw[3], row_h, v.get_payment_method_display(), "L", 7.5)
        _write_smart_cell(pdf, cw[4], row_h, _money(v.amount), "R", 7.5,
                          bold=True, color=_WARNING)
        _write_smart_cell(pdf, cw[5], row_h, _property_label(v.property), "L", 7.5)
        desc = _trunc(v.description, 60) or "—"
        _write_smart_cell(pdf, cw[6], row_h, desc, "L", 7)
        pdf.ln(row_h)

    _draw_border(pdf, len(v_rows) + 1, row_h)
    pdf.ln(3)


def _draw_payments_table(pdf: CashFlowPdf, p_rows: list):
    """Section 4 – Tenant rent payments."""
    if not p_rows:
        pdf._set_latin(8)
        pdf.set_text_color(*_MUTED)
        pdf.cell(0, 7, "  No tenant payment records in the selected period.", align="L",
                 new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_text_color(*_TEXT)
        return

    # Paid Date | Due Date | Amount | Method | Tenant | Tenant Ref | Unit | Property | Contract | Notes
    cw = [18, 16, 24, 18, 38, 18, 14, 40, 14, 0]
    cw[9] = pdf.epw - sum(cw) + cw[9]
    row_h = 6

    headers = ["Paid", "Due", "Amount (SAR)", "Method", "Tenant", "Ref", "Unit", "Property", "Ctr#", "Notes"]
    _draw_header_row(pdf, cw, headers, row_h)

    for i, p in enumerate(p_rows):
        fill = _STRIPE_ODD if i % 2 == 0 else _STRIPE_EVEN
        pdf.set_fill_color(*fill)
        row_y = pdf.get_y()
        pdf.rect(pdf.l_margin, row_y, pdf.epw, row_h, "F")
        pdf.set_x(pdf.l_margin)

        c = p.contract
        tenant = c.tenant if c else None
        unit = c.unit if c else None
        prop = unit.property if (unit and unit.property_id) else None

        is_late = bool(p.due_date and p.payment_date and p.payment_date > p.due_date)
        amt_color = _DANGER if is_late else _SUCCESS

        _write_smart_cell(pdf, cw[0], row_h, str(p.payment_date), "L", 7.5)
        _write_smart_cell(pdf, cw[1], row_h, str(p.due_date) if p.due_date else "—", "L", 7.5)
        _write_smart_cell(pdf, cw[2], row_h, _money(p.amount), "R", 7.5,
                          bold=True, color=amt_color)
        _write_smart_cell(pdf, cw[3], row_h, p.get_payment_method_display(), "L", 7.5)
        _write_smart_cell(pdf, cw[4], row_h, _tenant_name(tenant), "L", 7.5)
        tref = (tenant.tenant_reference or "—") if tenant else "—"
        _write_smart_cell(pdf, cw[5], row_h, tref, "L", 7.5)
        unit_no = (unit.unit_number or "—") if unit else "—"
        _write_smart_cell(pdf, cw[6], row_h, unit_no, "C", 7.5)
        _write_smart_cell(pdf, cw[7], row_h, _property_label(prop), "L", 7.5)
        _write_smart_cell(pdf, cw[8], row_h, str(c.id) if c else "—", "C", 7.5)
        notes = _trunc(p.notes, 40) or ("⚠ Late" if is_late else "—")
        if is_late:
            pdf.set_text_color(*_DANGER)
        _write_smart_cell(pdf, cw[9], row_h, notes, "L", 7)
        pdf.set_text_color(*_TEXT)
        pdf.ln(row_h)

    _draw_border(pdf, len(p_rows) + 1, row_h)
    pdf.ln(3)


def _draw_header_row(pdf: CashFlowPdf, cw: list, headers: list, row_h: float):
    """Draw a branded header row."""
    pdf._colored_rect(pdf.l_margin, pdf.get_y(), pdf.epw, row_h, _BRAND)
    pdf.set_text_color(255, 255, 255)
    pdf._set_latin(7.5, bold=True)
    pdf.set_x(pdf.l_margin)
    for w, h in zip(cw, headers):
        pdf.cell(w, row_h, f" {h}", align="L")
    pdf.ln(row_h)
    pdf.set_text_color(*_TEXT)


def _draw_border(pdf: CashFlowPdf, num_rows: int, row_h: float):
    """Draw outer border around table."""
    total_h = num_rows * row_h
    pdf.set_draw_color(*_BORDER)
    pdf.set_line_width(0.3)
    pdf.rect(pdf.l_margin, pdf.get_y() - total_h, pdf.epw, total_h)
    pdf.set_draw_color(0, 0, 0)
    pdf.set_line_width(0.2)


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

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
    ui_lang: str = "en",
    company=None,
    report_id: str | None = None,
    generated_by: str | None = None,
    filters: list[str] | None = None,
) -> bytes:
    # New master report template (used for all reports)
    from reports.pdf_master import CompanyInfo, MasterReportPdf

    font_path = str(resolve_noto_naskh_path())
    net_profit = income - expense

    if company is None:
        company = CompanyInfo(
            name="Real Estate KSA",
            address_line="Riyadh, Saudi Arabia",
            contact_line="+966 XX XXX XXXX | info@example.com",
            vat_number="VAT-XXXXXXXXX",
            logo_path=None,
        )

    if not report_id:
        report_id = f"RPT-CF-{timezone.now().strftime('%Y%m%d-%H%M')}"

    if not generated_by:
        generated_by = "System"

    if filters is None:
        prop_name = (pf.get("property_name") or "").strip()
        filters = [
            f"Property: {prop_name or ('ID ' + str(pid) if pid else 'All')}",
            f"Date: {date_from.isoformat()} – {date_to.isoformat()}",
        ]

    pdf = MasterReportPdf(
        font_path=font_path,
        company=company,
        report_title="Cash Flow Report",
        report_id=report_id,
        generated_by=generated_by,
        filters=filters,
    )
    pdf.add_page()

    # KPI cards (boxed)
    pdf.draw_kpi_cards(
        [
            ("Total Income", f"{_money(income)} SAR", (22, 163, 74)),
            ("Total Expenses", f"{_money(expense)} SAR", (220, 38, 38)),
            ("Net Profit", f"{_money(net_profit)} SAR", (13, 148, 136)),
        ]
    )

    # Main tables
    tx_headers = ["Date", "Type", "Category", "Amount (SAR)", "Property", "Reference"]
    tx_rows_out = [
        [
            str(t.date),
            "Income" if t.transaction_type == "income" else "Expense",
            _tx_category_label(t),
            _money(t.amount),
            (getattr(t.property, "name", "") or "—") if t.property_id else "—",
            _dash(t.reference),
        ]
        for t in tx_rows
    ]
    if not tx_rows_out:
        tx_rows_out = [["—", "—", "—", "—", "—", "No records"]]
    pdf.draw_table(
        headers=tx_headers,
        rows=tx_rows_out,
        col_widths=[22, 18, 28, 26, 52, 30],
        right_align_cols={3},
        title=f"Ledger Transactions ({len(tx_rows)} records)",
    )

    v_headers = ["Date", "Voucher No.", "Payee", "Method", "Amount (SAR)", "Property", "Description"]
    v_rows_out = [
        [
            str(v.date),
            v.voucher_number or "—",
            _dash(v.payee_name),
            v.get_payment_method_display(),
            _money(v.amount),
            (getattr(v.property, "name", "") or "—") if v.property_id else "—",
            _trunc(v.description, 80) or "—",
        ]
        for v in v_rows
    ]
    if not v_rows_out:
        v_rows_out = [["—", "—", "—", "—", "—", "—", "No records"]]
    pdf.draw_table(
        headers=v_headers,
        rows=v_rows_out,
        col_widths=[18, 24, 34, 20, 24, 44, 0],
        right_align_cols={4},
        title=f"Approved Vouchers ({len(v_rows)} records)",
    )

    p_headers = ["Paid", "Due", "Amount (SAR)", "Method", "Tenant", "Unit", "Property", "Contract", "Notes"]
    p_rows_out = []
    for p in p_rows:
        c = p.contract
        tenant = c.tenant if c else None
        unit = c.unit if c else None
        prop = unit.property if (unit and unit.property_id) else None
        p_rows_out.append(
            [
                str(p.payment_date),
                str(p.due_date) if p.due_date else "—",
                _money(p.amount),
                p.get_payment_method_display(),
                _tenant_name(tenant),
                (unit.unit_number or "—") if unit else "—",
                (getattr(prop, "name", "") or "—") if prop else "—",
                str(c.id) if c else "—",
                _trunc(p.notes, 60) or "—",
            ]
        )
    if not p_rows_out:
        p_rows_out = [["—", "—", "—", "—", "—", "—", "—", "—", "No records"]]
    pdf.draw_table(
        headers=p_headers,
        rows=p_rows_out,
        col_widths=[16, 16, 22, 20, 36, 14, 40, 16, 0],
        right_align_cols={2},
        title=f"Tenant Payments ({len(p_rows)} records)",
    )

    return bytes(pdf.output())