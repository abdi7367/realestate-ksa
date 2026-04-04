/** Western digits 0–9 → Unicode Arabic-Indic digits (U+0660–U+0669), common in KSA UI */
const WESTERN = '0123456789'
const EASTERN = '\u0660\u0661\u0662\u0663\u0664\u0665\u0666\u0667\u0668\u0669'

/**
 * Replace Western digits in a string with Eastern Arabic numerals.
 * Leaves letters, punctuation, decimals, and minus signs unchanged.
 * @param {unknown} input
 * @returns {string}
 */
export function toEasternArabicDigits(input) {
  if (input == null) return ''
  const s = String(input)
  let out = ''
  for (let i = 0; i < s.length; i++) {
    const c = s[i]
    const idx = WESTERN.indexOf(c)
    out += idx >= 0 ? EASTERN[idx] : c
  }
  return out
}

/**
 * Parse user input that may contain Eastern digits back to Western for APIs / InputNumber.
 * @param {unknown} input
 * @returns {string}
 */
export function fromEasternArabicDigits(input) {
  if (input == null) return ''
  const s = String(input)
  let out = ''
  for (let i = 0; i < s.length; i++) {
    const c = s[i]
    const idx = EASTERN.indexOf(c)
    out += idx >= 0 ? WESTERN[idx] : c
  }
  return out
}

/** Props for Ant Design InputNumber: show Eastern Arabic digits when `isArabic` is true */
export function arabicInputNumberProps(isArabic) {
  if (!isArabic) return {}
  return {
    formatter: (val) =>
      val == null || val === '' ? '' : toEasternArabicDigits(String(val)),
    parser: (val) => {
      const raw = fromEasternArabicDigits(String(val).replace(/\s/g, ''))
      const n = Number(raw)
      return Number.isFinite(n) ? n : 0
    },
  }
}
