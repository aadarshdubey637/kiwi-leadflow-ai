export const formatDate = (iso: string) =>
  new Date(iso.endsWith('Z') || /[+-]\d\d:?\d\d$/.test(iso) ? iso : iso + 'Z').toLocaleDateString(undefined, {
    day: 'numeric', month: 'short', year: 'numeric',
  })

/** Backend timestamps are UTC; SQLite returns them without a zone suffix, so treat them as UTC explicitly. */
export const formatDateTime = (iso: string) =>
  new Date(iso.endsWith('Z') || /[+-]\d\d:?\d\d$/.test(iso) ? iso : iso + 'Z').toLocaleString(undefined, {
    day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit',
  })

export const formatNumber = (n: number) => new Intl.NumberFormat().format(n)

export const formatMoney = (amount: number, currency?: string | null) => {
  try {
    return new Intl.NumberFormat(undefined, currency ? { style: 'currency', currency, maximumFractionDigits: 0 } : { maximumFractionDigits: 0 }).format(amount)
  } catch {
    return `${formatNumber(amount)} ${currency ?? ''}`.trim()
  }
}

export const formatSeconds = (s: number | null | undefined) =>
  s == null ? '—' : s < 1 ? `${Math.round(s * 1000)} ms` : `${s.toFixed(s < 10 ? 2 : 1)} s`

export const cn = (...parts: (string | false | null | undefined)[]) => parts.filter(Boolean).join(' ')
