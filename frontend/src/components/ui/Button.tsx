import type { ButtonHTMLAttributes, ReactNode } from 'react'
import { Loader2 } from 'lucide-react'
import { cn } from '@/utils/format'

type Variant = 'primary' | 'secondary' | 'danger' | 'ghost'
const styles: Record<Variant, string> = {
  primary: 'bg-brand-600 text-white shadow-sm shadow-brand-900/20 hover:bg-brand-700 disabled:bg-brand-600/50',
  secondary: 'bg-white/70 text-slate-700 ring-1 ring-inset ring-slate-300/80 backdrop-blur hover:bg-white disabled:text-slate-400',
  danger: 'bg-clay text-white shadow-sm hover:bg-[#a9452d] disabled:opacity-50',
  ghost: 'text-slate-600 hover:bg-white/60 disabled:text-slate-400',
}

interface Props extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant
  loading?: boolean
  icon?: ReactNode
}

export function Button({ variant = 'primary', loading, icon, children, className, disabled, ...rest }: Props) {
  return (
    <button
      {...rest}
      disabled={disabled || loading}
      className={cn(
        'inline-flex items-center justify-center gap-2 rounded-lg px-4 py-2 text-sm font-medium transition-colors duration-150 disabled:cursor-not-allowed',
        styles[variant],
        className,
      )}
    >
      {loading ? <Loader2 className="size-4 animate-spin" aria-hidden /> : icon}
      {children}
    </button>
  )
}

/** Same look as Button, for react-router <Link>s. */
export const primaryLinkClass =
  'inline-flex items-center justify-center gap-2 rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white shadow-sm shadow-brand-900/20 transition-colors hover:bg-brand-700'
export const secondaryLinkClass =
  'inline-flex items-center justify-center gap-2 rounded-lg bg-white/70 px-4 py-2 text-sm font-medium text-slate-700 ring-1 ring-inset ring-slate-300/80 backdrop-blur transition-colors hover:bg-white'
