export const STORAGE_KEY = 'local-notebook-locale'

export const localeConfig = {
  'zh-CN': {
    htmlLang: 'zh-CN',
    modelOutputLanguage: 'Chinese',
    relativeNow: '刚刚',
    matchesBrowserLanguage: (language: string) => language.startsWith('zh'),
  },
  en: {
    htmlLang: 'en',
    modelOutputLanguage: 'English',
    relativeNow: 'Just now',
    matchesBrowserLanguage: () => true,
  },
} as const

export type Locale = keyof typeof localeConfig

export const DEFAULT_LOCALE: Locale = 'zh-CN'
export const supportedLocales = Object.keys(localeConfig) as Locale[]

export function normalizeLocale(value: string | null | undefined): Locale | null {
  if (!value) return null
  if (value === 'zh') return 'zh-CN'
  return supportedLocales.includes(value as Locale) ? value as Locale : null
}

export function detectBrowserLocale(browserLanguage: string): Locale {
  const normalized = browserLanguage.toLowerCase()
  return supportedLocales.find((item) => localeConfig[item].matchesBrowserLanguage(normalized)) || 'en'
}
