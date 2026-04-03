"""
Enterprise Master PDF Report Engine (KSA Ready)

Features:
- Header (2-column layout)
- KPI Cards
- VAT + Currency formatting (SAR)
- Page-safe tables with header repeat
- Footer with audit info
- Watermark (optional)
- Ready for Arabic (Unicode font required)
"""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, Sequence, List

from django.utils import timezone
from fpdf import FPDF
from fpdf.enums import XPos, YPos


# -----------------------------
# Helpers
# -----------------------------
def fmt_money(amount: float, currency: str = "SAR") -> str:
    return f"{amount:,.2f} {currency}"


def vat_split(amount: float, vat_rate: float = 0.15):
    vat = amount * vat_rate
    total = amount + vat
    return amount, vat, total


# -----------------------------
# Data Models
# -----------------------------
@dataclass(frozen=True)
class CompanyInfo:
    name: str
    address_line: str
    contact_line: str
    vat_number: str
    logo_path: str | None = None


# -----------------------------
# Main PDF Class
# -----------------------------
class EnterpriseReportPDF(FPDF):
    BRAND = (13, 148, 136)
    TEXT = (15, 23, 42)
    MUTED = (100, 116, 139)
    BORDER = (203, 213, 225)
    STRIPE_ODD = (248, 250, 252)
    STRIPE_EVEN = (255, 255, 255)

    def __init__(
        self,
        *,
        font_path: str,
        company: CompanyInfo,
        report_title: str,
        report_id: str,
        generated_by: str,
        filters: Sequence[str],
    ):
        super().__init__()
        self.set_margins(14, 14, 14)
        self.set_auto_page_break(auto=True, margin=18)
        self.alias_nb_pages()

        self.company = company
        self.report_title = report_title
        self.report_id = report_id
        self.generated_by = generated_by
        self.filters = filters

        self.font_family = "custom"
        self.add_font(self.font_family, "", font_path)
        self.set_font(self.font_family, size=10)
        self.set_text_shaping(use_shaping_engine=True)

        self.generated_on = timezone.now() if timezone else datetime.utcnow()

    # -----------------------------
    # HEADER
    # -----------------------------
    def header(self):
        self.set_y(10)

        # LEFT (Company Info)
        left_x = self.l_margin
        self.set_xy(left_x, 10)

        if self.company.logo_path and Path(self.company.logo_path).exists():
            self.image(self.company.logo_path, x=left_x, y=10, w=18)
            self.set_x(left_x + 22)

        self.set_font(self.font_family, size=12)
        self.set_text_color(*self.TEXT)
        self.cell(90, 6, self.company.name, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        self.set_font(self.font_family, size=9)
        self.set_text_color(*self.MUTED)
        self.multi_cell(
            90,
            4,
            f"{self.company.address_line}\n{self.company.contact_line}\nVAT: {self.company.vat_number}",
        )

        # RIGHT (Report Meta)
        self.set_xy(self.w - self.r_margin - 70, 10)
        self.set_font(self.font_family, size=9)
        self.set_text_color(*self.TEXT)

        self.multi_cell(
            70,
            5,
            f"{self.report_title}\n"
            f"Report ID: {self.report_id}\n"
            f"Date: {self.generated_on.strftime('%d %b %Y')}\n"
            f"By: {self.generated_by}",
            align="R",
        )

        # Divider
        self.ln(2)
        self.set_draw_color(*self.BORDER)
        self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())

        # Filters
        self.ln(2)
        self.set_font(self.font_family, size=8)
        self.set_text_color(*self.MUTED)
        for f in self.filters:
            self.cell(0, 4, f, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        self.ln(3)

    # -----------------------------
    # FOOTER
    # -----------------------------
    def footer(self):
        self.set_y(-18)
        self.set_draw_color(*self.BORDER)
        self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())

        self.ln(2)
        self.set_font(self.font_family, size=8)

        self.cell(0, 5, "Approved By: ____________________", align="L")
        self.cell(0, 5, f"Page {self.page_no()}/{{nb}}", align="R")

        self.ln(4)
        self.set_text_color(*self.MUTED)
        self.cell(0, 4, "System Generated Report (No Signature Required)")

    # -----------------------------
    # KPI CARDS
    # -----------------------------
    def kpi_cards(self, cards: List[tuple[str, str]]):
        gap = 4
        card_w = (self.epw - gap * 2) / 3
        y = self.get_y()

        for i, (label, value) in enumerate(cards[:3]):
            x = self.l_margin + i * (card_w + gap)

            self.set_draw_color(*self.BORDER)
            self.rect(x, y, card_w, 18)

            self.set_xy(x + 2, y + 3)
            self.set_font(self.font_family, size=8)
            self.set_text_color(*self.MUTED)
            self.cell(card_w, 4, label)

            self.set_xy(x + 2, y + 9)
            self.set_font(self.font_family, size=14)
            self.set_text_color(*self.TEXT)
            self.cell(card_w, 6, value)

        self.ln(22)

    # -----------------------------
    # TABLE (ENTERPRISE SAFE)
    # -----------------------------
    def table(
        self,
        headers: Sequence[str],
        rows: Iterable[Sequence[str]],
        col_widths: Sequence[float],
        right_align: set[int] = None,
    ):
        right_align = right_align or set()

        def draw_header():
            self.set_fill_color(*self.BRAND)
            self.set_text_color(255, 255, 255)
            self.set_font(self.font_family, size=9)

            for w, h in zip(col_widths, headers):
                self.cell(w, 6, h, fill=True)
            self.ln()

        draw_header()

        self.set_text_color(*self.TEXT)
        self.set_font(self.font_family, size=9)

        for i, row in enumerate(rows):
            if self.get_y() > self.page_break_trigger - 10:
                self.add_page()
                draw_header()

            fill = self.STRIPE_ODD if i % 2 == 0 else self.STRIPE_EVEN
            self.set_fill_color(*fill)

            for j, (w, cell) in enumerate(zip(col_widths, row)):
                align = "R" if j in right_align else "L"
                self.cell(w, 6, str(cell), align=align, fill=True)

            self.ln()

    # -----------------------------
    # WATERMARK
    # -----------------------------
    def watermark(self, text="CONFIDENTIAL"):
        self.set_text_color(230, 230, 230)
        self.set_font(self.font_family, size=40)
        self.rotate(45, x=60, y=190)
        self.text(60, 190, text)
        self.rotate(0)


class MasterReportPdf(EnterpriseReportPDF):
    """
    Backward-compatible adapter for existing report builders.
    Keeps old method names/signatures used across cashflow/property income generators.
    """

    def draw_kpi_cards(self, cards):
        normalized = [(label, value) for (label, value, *_) in cards]
        self.kpi_cards(normalized)

    def draw_table(
        self,
        *,
        headers: Sequence[str],
        rows: Iterable[Sequence[str]],
        col_widths: Sequence[float],
        right_align_cols: set[int] | None = None,
        row_height: float = 6,  # kept for compatibility
        title: str | None = None,
    ):
        _ = row_height
        if title:
            self.set_font(self.font_family, size=10)
            self.set_text_color(*self.TEXT)
            self.cell(0, 6, title, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            self.ln(1)
        self.table(headers=headers, rows=rows, col_widths=col_widths, right_align=right_align_cols or set())
        self.ln(4)


# -----------------------------
# SAMPLE USAGE (IMPORTANT)
# -----------------------------
def generate_sample_report():
    company = CompanyInfo(
        name="ABC Real Estate",
        address_line="Riyadh, Saudi Arabia",
        contact_line="+966 500000000",
        vat_number="123456789",
    )

    pdf = EnterpriseReportPDF(
        font_path="DejaVuSans.ttf",
        company=company,
        report_title="Property Income Report",
        report_id="RPT-KSA-2026-001",
        generated_by="Admin",
        filters=["Property: All", "Date: Jan - Mar 2026"],
    )

    pdf.add_page()

    # KPI
    pdf.kpi_cards([
        ("Total Income", fmt_money(120000)),
        ("VAT", fmt_money(18000)),
        ("Net", fmt_money(138000)),
    ])

    # Table
    rows = []
    for i in range(20):
        base = 1000 + i * 50
        excl, vat, total = vat_split(base)
        rows.append([
            f"Tenant {i}",
            fmt_money(excl),
            fmt_money(vat),
            fmt_money(total),
        ])

    pdf.table(
        headers=["Tenant", "Amount", "VAT", "Total"],
        rows=rows,
        col_widths=[50, 40, 40, 40],
        right_align={1, 2, 3},
    )

    pdf.output("report.pdf")