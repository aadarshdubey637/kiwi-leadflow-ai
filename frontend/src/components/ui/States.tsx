import type { ReactNode } from 'react'
import { AlertCircle, Inbox, Loader2 } from 'lucide-react'
import { Button } from './Button'
import { errorMessage } from '@/api/axiosInstance'

export function LoadingSpinner({ label = 'Loading…' }: { label?: string }) {
  return (
    <div role="status" className="flex items-center justify-center gap-2 py-12 text-sm text-slate-500">
      <Loader2 className="size-5 animate-spin text-brand-600" aria-hidden /> {label}
    </div>
  )
}

export function ErrorMessage({ error, onRetry }: { error: unknown; onRetry?: () => void }) {
  return (
    <div role="alert" className="flex flex-col items-center gap-3 px-4 py-10 text-center">
      <AlertCircle className="size-8 text-red-500" aria-hidden />
      <p className="max-w-sm text-sm text-slate-600">{errorMessage(error)}</p>
      {onRetry && (
        <Button variant="secondary" onClick={onRetry}>
          Try again
        </Button>
      )}
    </div>
  )
}

export function EmptyState({ title, description, action }: { title: string; description?: string; action?: ReactNode }) {
  return (
    <div className="flex flex-col items-center gap-2 px-4 py-12 text-center">
      <div className="flex size-12 items-center justify-center rounded-full bg-slate-100">
        <Inbox className="size-6 text-slate-400" aria-hidden />
      </div>
      <p className="text-sm font-medium text-slate-700">{title}</p>
      {description && <p className="max-w-sm text-xs text-slate-500">{description}</p>}
      {action}
    </div>
  )
}

/** Unified loading / error / empty handling for any query-backed block. */
export function QueryState({
  isLoading, error, onRetry, isEmpty, empty, children,
}: {
  isLoading: boolean
  error: unknown
  onRetry?: () => void
  isEmpty?: boolean
  empty?: ReactNode
  children: ReactNode
}) {
  if (isLoading) return <LoadingSpinner />
  if (error) return <ErrorMessage error={error} onRetry={onRetry} />
  if (isEmpty) return <>{empty}</>
  return <>{children}</>
}

/** For data the backend does not (yet) provide — shown honestly instead of inventing numbers. */
export function NotAvailable({ title, reason }: { title: string; reason: string }) {
  return (
    <div className="flex flex-col items-center gap-1 px-4 py-10 text-center">
      <p className="text-sm font-medium text-slate-600">{title}</p>
      <p className="max-w-sm text-xs text-slate-500">{reason}</p>
    </div>
  )
}
