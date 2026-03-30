from django.urls import path

from .views import (
    CashFlowReportView,
    CashFlowReportPdfView,
    ContractReportView,
    DebtRepaymentReportView,
    ExpenseReportView,
    IncomeStatementReportView,
    OutstandingBalancesReportView,
    OwnershipReportView,
    PropertyIncomeReportView,
    PropertyProfitabilityReportView,
    TenantPaymentReportView,
    VoucherReportView,
)

urlpatterns = [
    path('reports/property-income/', PropertyIncomeReportView.as_view()),
    path('reports/contracts/', ContractReportView.as_view()),
    path('reports/tenant-payments/', TenantPaymentReportView.as_view()),
    path('reports/outstanding-balances/', OutstandingBalancesReportView.as_view()),
    path('reports/debt-repayment/', DebtRepaymentReportView.as_view()),
    path('reports/property-profitability/', PropertyProfitabilityReportView.as_view()),
    path('reports/vouchers/', VoucherReportView.as_view()),
    path('reports/cash-flow/', CashFlowReportView.as_view()),
    path('reports/cash-flow/pdf/', CashFlowReportPdfView.as_view()),
    path('reports/income-statement/', IncomeStatementReportView.as_view()),
    path('reports/expenses/', ExpenseReportView.as_view()),
    path('reports/ownership/', OwnershipReportView.as_view()),
]
