import { cn } from '@/utils/format'

/** Simple custom mark: leads narrowing through a funnel, with one that gets through (the terracotta dot). */
export function LogoMark({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 40 40" className={cn('size-9', className)} role="img" aria-label="LeadFlow">
      <rect width="40" height="40" rx="11" fill="#175a55" />
      <rect x="9" y="11" width="22" height="4" rx="2" fill="#f4efe7" />
      <rect x="12.5" y="18" width="15" height="4" rx="2" fill="#f4efe7" opacity="0.8" />
      <rect x="16" y="25" width="8" height="4" rx="2" fill="#f4efe7" opacity="0.6" />
      <circle cx="30.5" cy="29.5" r="3.2" fill="#e0724f" />
    </svg>
  )
}
