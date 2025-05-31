import { formatDistanceToNow, format, parseISO } from 'date-fns'

export function formatDate(date: string | Date, pattern = 'MMM d, yyyy') {
  const dateObj = typeof date === 'string' ? parseISO(date) : date
  return format(dateObj, pattern)
}

export function formatRelativeTime(date: string | Date) {
  const dateObj = typeof date === 'string' ? parseISO(date) : date
  return formatDistanceToNow(dateObj, { addSuffix: true })
}

export function formatNumber(num: number) {
  if (num >= 1000000) {
    return (num / 1000000).toFixed(1) + 'M'
  }
  if (num >= 1000) {
    return (num / 1000).toFixed(1) + 'K'
  }
  return num.toString()
}

export function formatPercentage(value: number, decimals = 1) {
  return `${(value * 100).toFixed(decimals)}%`
}

export function truncateText(text: string, maxLength: number) {
  if (text.length <= maxLength) return text
  return text.substring(0, maxLength).trim() + '...'
}

export function capitalizeFirst(str: string) {
  return str.charAt(0).toUpperCase() + str.slice(1)
}

export function formatEngagementRate(rate: number) {
  return `${(rate * 100).toFixed(1)}%`
}

export function formatScore(score: number, max = 100) {
  return `${Math.round(score)}/${max}`
}
