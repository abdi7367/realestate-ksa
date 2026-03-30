import i18n from 'i18next'
import { initReactI18next } from 'react-i18next'
import en from './locales/en.json'
import ar from './locales/ar.json'

const STORAGE_KEY = 'realestate_locale'

function getStoredLng() {
  try {
    return localStorage.getItem(STORAGE_KEY)
  } catch {
    return null
  }
}

const initialLng = getStoredLng() || 'en'

i18n.use(initReactI18next).init({
  resources: {
    en: { translation: en },
    ar: { translation: ar },
  },
  lng: initialLng,
  fallbackLng: 'en',
  interpolation: { escapeValue: false },
})

function applyDocumentDirection(lng) {
  if (typeof document === 'undefined') return
  const rtl = lng === 'ar'
  document.documentElement.dir = rtl ? 'rtl' : 'ltr'
  document.documentElement.lang = lng
  document.title = i18n.t('brand')
  try {
    localStorage.setItem(STORAGE_KEY, lng)
  } catch {
    /* ignore */
  }
}

applyDocumentDirection(i18n.language)

i18n.on('languageChanged', applyDocumentDirection)

export default i18n
