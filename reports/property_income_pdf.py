from __future__ import annotations

from decimal import Decimal
from typing import List, Dict

from django.utils import timezone
from fpdf.enums import XPos, YPos

from finance.models import Transaction
from reports.pdf_master import CompanyInfo, MasterReportPdf
from reports.cashflow_pdf import resolve_noto_naskh_path


_INCOME_LABELS = dict(Transaction.INCOME_CATEGORY_CHOICES)


def fmt_money(val) -> str:
    return f"{Decimal(str(val or '0')):,.2f} SAR"


def property_income_attachment_filename(period_key: str, pid: str | None) -> str:
    base = f"property-income_{period_key}"
    if pid:
        base = f"{base}_property-{pid}"
    return f"{base}.pdf"


def build_property_income_pdf_bytes(
    *,
    report_id: str,
    generated_by: str,
    company: CompanyInfo,
    filters: List[str],
    total_rental_income: Decimal,
    total_other_income: Decimal,
    total_income: Decimal,
    rows: List[Dict],
    by_category: List[Dict],
    monthly_trend: List[Dict],
    period_label: str,
) -> bytes:

    pdf = MasterReportPdf(
        font_path=str(resolve_noto_naskh_path()),
        company=company,
        report_title="Property Income Report",
        report_id=report_id,
        generated_by=generated_by,
        filters=filters,
    )

    pdf.add_page()

    # =========================================================
    # 🧾 REPORT DESCRIPTION
    # =========================================================
    pdf.set_font(pdf.font_family, size=10)
    pdf.set_text_color(0, 0, 0)

    pdf.multi_cell(
        0,
        6,
        "This report provides a comprehensive overview of income generated from properties "
        "during the selected reporting period. It includes rental income, additional income "
        "streams, category-wise breakdown, and monthly performance trends. "
        "All amounts are presented in Saudi Riyal (SAR) and include applicable VAT where relevant.",
    )
    pdf.ln(4)

    # =========================================================
    # 📅 REPORT CONTEXT
    # =========================================================
    pdf.set_font(pdf.font_family, size=9)
    pdf.set_text_color(*pdf.MUTED)

    pdf.multi_cell(
        0,
        5,
        f"Reporting Period: {period_label}\n"
        f"Generated On: {timezone.now().strftime('%Y-%m-%d %H:%M')}\n"
        f"Currency: SAR\n"
        f"VAT Rate: 15%",
    )
    pdf.ln(4)

    # =========================================================
    # 📊 SUMMARY KPIs
    # =========================================================
    pdf.set_font(pdf.font_family, size=11)
    pdf.set_text_color(*pdf.TEXT)
    pdf.cell(0, 6, "Summary Overview", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(2)

    pdf.draw_kpi_cards(
        [
            ("Total Rental Income", fmt_money(total_rental_income), (22, 163, 74)),
            ("Other Income", fmt_money(total_other_income), (217, 119, 6)),
            ("Total Income", fmt_money(total_income), (13, 148, 136)),
        ]
    )

    pdf.ln(4)

    # =========================================================
    # 🔹 SECTION SEPARATOR
    # =========================================================
    pdf.set_draw_color(*pdf.BORDER)
    pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
    pdf.ln(4)

    # =========================================================
    # 📋 1. DETAILED BREAKDOWN
    # =========================================================
    pdf.set_font(pdf.font_family, size=11)
    pdf.cell(0, 6, "1. Detailed Income Breakdown", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(2)

    pdf.set_font(pdf.font_family, size=9)
    pdf.multi_cell(
        0,
        5,
        "This section lists all income transactions including tenant, unit, "
        "income type, and respective amounts.",
    )
    pdf.ln(2)

    headers = [
        "Transaction Date",
        "Unit",
        "Tenant",
        "Income Type",
        "Amount (SAR)",
    ]

    detail_rows = []
    total_calc = Decimal("0")

    for r in rows:
        amt = Decimal(str(r.get("amount") or "0"))
        total_calc += amt

        detail_rows.append(
            [
                str(r.get("date") or "—"),
                str(r.get("unit") or "—"),
                str(r.get("tenant") or "—"),
                str(r.get("income_type") or "—"),
                f"{amt:,.2f}",
            ]
        )

    # TOTAL ROW
    detail_rows.append(["TOTAL", "", "", "", f"{total_calc:,.2f}"])

    pdf.draw_table(
        headers=headers,
        rows=detail_rows,
        col_widths=[28, 25, 45, 45, 0],
        right_align_cols={4},
    )

    pdf.ln(4)

    # =========================================================
    # 🔹 SEPARATOR
    # =========================================================
    pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
    pdf.ln(4)

    # =========================================================
    # 📊 2. INCOME BY CATEGORY
    # =========================================================
    pdf.set_font(pdf.font_family, size=11)
    pdf.cell(0, 6, "2. Income by Category", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(2)

    pdf.set_font(pdf.font_family, size=9)
    pdf.multi_cell(
        0,
        5,
        "This section summarizes income grouped by category such as rental income, "
        "parking fees, and service charges.",
    )
    pdf.ln(2)

    totals_by_key = {
        str(c.get("category")): Decimal(str(c.get("total") or "0"))
        for c in by_category
    }

    category_rows = []
    total_cat = Decimal("0")

    for key, val in totals_by_key.items():
        label = _INCOME_LABELS.get(key, key.replace("_", " ").title())
        total_cat += val
        category_rows.append([label, f"{val:,.2f}"])

    category_rows.append(["TOTAL", f"{total_cat:,.2f}"])

    pdf.draw_table(
        headers=["Income Category", "Amount (SAR)"],
        rows=category_rows,
        col_widths=[130, 0],
        right_align_cols={1},
    )

    pdf.ln(4)

    # =========================================================
    # 📈 3. MONTHLY TREND
    # =========================================================
    pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
    pdf.ln(4)

    pdf.set_font(pdf.font_family, size=11)
    pdf.cell(0, 6, "3. Monthly Income Trend", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(2)

    pdf.set_font(pdf.font_family, size=9)
    pdf.multi_cell(
        0,
        5,
        "This section shows how income has evolved over time on a monthly basis.",
    )
    pdf.ln(2)

    trend_rows = []
    total_trend = Decimal("0")

    for m in monthly_trend:
        amt = Decimal(str(m.get("total") or "0"))
        total_trend += amt

        month_label = m.get("month").strftime("%Y-%m") if m.get("month") else "—"

        trend_rows.append([month_label, f"{amt:,.2f}"])

    trend_rows.append(["TOTAL", f"{total_trend:,.2f}"])

    pdf.draw_table(
        headers=["Month", "Income (SAR)"],
        rows=trend_rows,
        col_widths=[70, 0],
        right_align_cols={1},
    )

    # =========================================================
    # 🏁 FINAL OUTPUT
    # =========================================================
    return bytes(pdf.output())