import { api } from './client'

const PATHS = {
  property_income: '/api/reports/property-income/',
  property_income_pdf: '/api/reports/property-income/pdf/',
  contracts: '/api/reports/contracts/',
  tenant_payments: '/api/reports/tenant-payments/',
  outstanding_balances: '/api/reports/outstanding-balances/',
  debt_repayment: '/api/reports/debt-repayment/',
  property_profitability: '/api/reports/property-profitability/',
  vouchers: '/api/reports/vouchers/',
  cash_flow: '/api/reports/cash-flow/',
  cash_flow_pdf: '/api/reports/cash-flow/pdf/',
  income_statement: '/api/reports/income-statement/',
  expenses: '/api/reports/expenses/',
  ownership: '/api/reports/ownership/',
}

function omitEmpty(params) {
  const out = {}
  for (const [k, v] of Object.entries(params)) {
    if (v === '' || v === null || v === undefined) continue
    out[k] = v
  }
  return out
}

/**
 * @param {keyof PATHS} reportId
 * @param {Record<string, string|number|undefined>} params query params (snake_case as backend expects)
 */
export async function fetchReport(reportId, params = {}) {
  const path = PATHS[reportId]
  if (!path) {
    throw new Error(`Unknown report: ${reportId}`)
  }
  const { data } = await api.get(path, { params: omitEmpty(params) })
  return data
}

export async function downloadCashFlowPdf(params = {}) {
  const res = await api.get(PATHS.cash_flow_pdf, {
    params: omitEmpty(params),
    responseType: 'blob',
  })
  const blob = res.data
  if (!(blob instanceof Blob) || blob.size === 0) {
    throw new Error('Empty PDF response')
  }
  const head = new Uint8Array(await blob.slice(0, 5).arrayBuffer())
  const sig = String.fromCharCode(...head)
  if (!sig.startsWith('%PDF')) {
    const text = await blob.text()
    throw new Error(
      (text && text.slice(0, 400)) || 'Server did not return a PDF file',
    )
  }
  return blob
}

export async function downloadPropertyIncomePdf(params = {}) {
  const res = await api.get(PATHS.property_income_pdf, {
    params: omitEmpty(params),
    responseType: 'blob',
  })
  const blob = res.data
  if (!(blob instanceof Blob) || blob.size === 0) {
    throw new Error('Empty PDF response')
  }
  const head = new Uint8Array(await blob.slice(0, 5).arrayBuffer())
  const sig = String.fromCharCode(...head)
  if (!sig.startsWith('%PDF')) {
    const text = await blob.text()
    throw new Error(
      (text && text.slice(0, 400)) || 'Server did not return a PDF file',
    )
  }
  return blob
}

export const REPORT_OPTIONS = [
  { value: 'property_income', label: 'Property income (by category)' },
  { value: 'contracts', label: 'Contracts' },
  { value: 'tenant_payments', label: 'Tenant payments' },
  { value: 'outstanding_balances', label: 'Outstanding balances' },
  { value: 'debt_repayment', label: 'Debt repayment' },
  { value: 'property_profitability', label: 'Property profitability' },
  { value: 'vouchers', label: 'Vouchers' },
  { value: 'cash_flow', label: 'Cash flow' },
  { value: 'income_statement', label: 'Income statement' },
  { value: 'expenses', label: 'Expenses' },
  { value: 'ownership', label: 'Ownership (by owner)' },
]
