import { toEasternArabicDigits } from './arabicNumerals'

/**
 * Display a value with the Saudi Riyal label from i18n (e.g. "SAR" / "ر.س").
 * @param {unknown} value
 * @param {string} currencyLabel - t('common.currencySAR')
 * @param {boolean} [easternArabicDigits] - use ٠١٢… when true (Arabic locale)
 */
export function sarDisplay(value, currencyLabel, easternArabicDigits = false) {
  if (value === undefined || value === null || value === '') return '—'
  const s = `${String(value)} ${currencyLabel}`
  return easternArabicDigits ? toEasternArabicDigits(s) : s
}

export function isNumericCellValue(v) {
  if (v === null || v === undefined || v === '') return false
  if (typeof v === 'number') return Number.isFinite(v)
  const s = String(v).trim()
  if (s === '' || s === '—') return false
  return /^-?\d+(\.\d+)?$/.test(s)
}

/** Heuristic for generic report tables: column keys that represent money in SAR */
export function isReportMoneyColumnKey(key) {
  if (!key || typeof key !== 'string') return false
  const k = key.toLowerCase()
  if (
    /date|time|_at$|phone|email|status|reference|description|notes|name$|code$|method|schedule|category|tenant|property|unit|owner|creditor|payee|district|city|location|address|iban|bank/.test(
      k,
    )
  ) {
    return false
  }
  if (/(^|_)(id|ids)(_|$)/.test(k)) return false
  if (
    /percentage|percent|_pct|rate$|year$|month$|day$|count$|number$|floor|size|total_units|vacant|occupied/.test(
      k,
    )
  ) {
    return false
  }
  if (
    /amount|balance|rent|paid|remaining|income|expense|profit|vat|cost|fee|price|due|deposit|instal|install|outstanding|collected|received|collection|disbursement|net_|total/.test(
      k,
    )
  ) {
    return true
  }
  return false
}
