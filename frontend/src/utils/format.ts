
import { locale, localeConfig, type Locale } from '../i18n'

type RelativeFallback = 'date' | 'month'

interface RelativeTimeOptions {
  maxRelativeDays?: number
  fallback?: RelativeFallback
  targetLocale?: Locale
}

function getIntlLocale(targetLocale: Locale = locale.value): string {
  return localeConfig[targetLocale].htmlLang
}

function formatRelativeValue(value: number, unit: Intl.RelativeTimeFormatUnit, targetLocale: Locale): string {
  return new Intl.RelativeTimeFormat(getIntlLocale(targetLocale), { numeric: 'always' }).format(value, unit)
}


export function escapeHtml(text: string): string {
  const div = document.createElement('div')
  div.textContent = text
  return div.innerHTML
}


export function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}


export function formatDate(dateStr: string, targetLocale: Locale = locale.value): string {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleDateString(getIntlLocale(targetLocale), {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit'
  })
}


export function formatRelativeTime(dateStr: string, options: RelativeTimeOptions = {}): string {
  if (!dateStr) return ''
  const targetLocale = options.targetLocale || locale.value
  const maxRelativeDays = options.maxRelativeDays ?? 7
  const fallback = options.fallback || 'date'
  const date = new Date(dateStr)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMs / 3600000)
  const diffDays = Math.floor(diffMs / 86400000)

  if (diffMins < 1) return localeConfig[targetLocale].relativeNow
  if (diffMins < 60) return formatRelativeValue(-diffMins, 'minute', targetLocale)
  if (diffHours < 24) return formatRelativeValue(-diffHours, 'hour', targetLocale)
  if (diffDays < maxRelativeDays) return formatRelativeValue(-diffDays, 'day', targetLocale)
  if (fallback === 'month') return formatRelativeValue(-Math.max(1, Math.floor(diffDays / 30)), 'month', targetLocale)
  return formatDate(dateStr, targetLocale)
}


export function formatMessageTimestamp(dateStr: string, targetLocale: Locale = locale.value): string {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  const now = new Date()

  const isToday = date.getFullYear() === now.getFullYear() &&
                  date.getMonth() === now.getMonth() &&
                  date.getDate() === now.getDate()

  if (isToday) {
    return date.toLocaleTimeString(getIntlLocale(targetLocale), {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false,
    })
  }

  const monthDay = date.toLocaleDateString(getIntlLocale(targetLocale), {
    month: '2-digit',
    day: '2-digit',
  })
  const weekday = date.toLocaleDateString(getIntlLocale(targetLocale), {
    weekday: 'short',
  })
  return `${monthDay} ${weekday}`
}


export function truncateText(text: string, maxLength: number): string {
  if (!text || text.length <= maxLength) return text
  return text.slice(0, maxLength) + '...'
}
