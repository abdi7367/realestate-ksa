import { useCallback, useMemo } from 'react'
import { useTranslation } from 'react-i18next'
import { toEasternArabicDigits } from '../utils/arabicNumerals'

/**
 * When UI language is Arabic, format strings that contain digits using Eastern Arabic numerals (٠١٢…).
 */
export function useLocalizedDigits() {
  const { i18n } = useTranslation()
  const isArabic = useMemo(
    () => Boolean(i18n.language?.startsWith('ar')),
    [i18n.language],
  )

  const localizeDigits = useCallback(
    (value) => {
      if (value == null || value === '') return value
      return isArabic ? toEasternArabicDigits(String(value)) : String(value)
    },
    [isArabic],
  )

  return { isArabic, localizeDigits, toEasternArabicDigits }
}
