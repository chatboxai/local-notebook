import { computed, watch } from 'vue'
import { createI18n } from 'vue-i18n'
import {
  DEFAULT_LOCALE,
  STORAGE_KEY,
  detectBrowserLocale,
  localeConfig,
  normalizeLocale,
  type Locale,
} from './config'
import en from './locales/en'
import zhCN from './locales/zh-CN'

export { localeConfig, type Locale } from './config'

const messages = {
  'zh-CN': zhCN,
  en,
} as const

function getInitialLocale(): Locale {
  if (typeof window === 'undefined') return DEFAULT_LOCALE

  const stored = normalizeLocale(window.localStorage.getItem(STORAGE_KEY))
  if (stored) return stored

  return detectBrowserLocale(window.navigator.language)
}

export const i18n = createI18n({
  legacy: false,
  globalInjection: true,
  locale: getInitialLocale(),
  fallbackLocale: DEFAULT_LOCALE,
  messages,
  missingWarn: false,
  fallbackWarn: false,
})

const composer = i18n.global

export const locale = computed<Locale>({
  get() {
    return normalizeLocale(composer.locale.value) || DEFAULT_LOCALE
  },
  set(nextLocale) {
    setLocale(nextLocale)
  },
})

export const isEnglish = computed(() => locale.value === 'en')

export function setLocale(nextLocale: Locale | string) {
  const normalized = normalizeLocale(nextLocale) || DEFAULT_LOCALE
  composer.locale.value = normalized

  if (typeof document !== 'undefined') {
    document.documentElement.lang = localeConfig[normalized].htmlLang
  }

  if (typeof window !== 'undefined') {
    window.localStorage.setItem(STORAGE_KEY, normalized)
  }
}

export function getModelOutputLanguage(targetLocale: Locale = locale.value): string {
  return localeConfig[targetLocale].modelOutputLanguage
}

export function t(key: string, named?: Record<string, unknown>): string {
  return named ? composer.t(key, named) : composer.t(key)
}

watch(
  () => composer.locale.value,
  (nextLocale) => {
    const normalized = normalizeLocale(nextLocale) || DEFAULT_LOCALE
    if (typeof document !== 'undefined') {
      document.documentElement.lang = localeConfig[normalized].htmlLang
    }
    if (typeof window !== 'undefined') {
      window.localStorage.setItem(STORAGE_KEY, normalized)
    }
  },
  { immediate: true },
)
