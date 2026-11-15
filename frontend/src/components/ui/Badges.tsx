import { AlertTriangle, CheckCircle2, Clock, Loader2, XCircle } from 'lucide-react'
import type { AiStatus, EnquiryStatus, Priority, Temperature } from '@/types/api'
import { cn } from '@/utils/format'

const base = 'inline-flex items-center gap-1 whitespace-nowrap rounded-full px-2 py-0.5 text-xs font-medium ring-1 ring-inset'

const STATUS: Record<EnquiryStatus, string> = {
  New: 'bg-sky-50 text-sky-700 ring-sky-600/20',
  'In Progress': 'bg-amber-50 text-amber-700 ring-amber-600/20',
  Converted: 'bg-emerald-50 text-emerald-700 ring-emerald-600/20',
  Closed: 'bg-slate-100 text-slate-600 ring-slate-500/20',
}
const PRIORITY: Record<Priority, string> = {
  High: 'bg-red-50 text-red-700 ring-red-600/20',
  Medium: 'bg-amber-50 text-amber-700 ring-amber-600/20',
  Low: 'bg-slate-100 text-slate-600 ring-slate-500/20',
}
const TEMP: Record<Temperature, string> = {
  Hot: 'bg-red-50 text-red-700 ring-red-600/20',
  Warm: 'bg-orange-50 text-orange-700 ring-orange-600/20',
  Cold: 'bg-blue-50 text-blue-700 ring-blue-600/20',
}
const SENTIMENT: Record<string, string> = {
  Positive: 'bg-emerald-50 text-emerald-700 ring-emerald-600/20',
  Neutral: 'bg-slate-100 text-slate-600 ring-slate-500/20',
  Negative: 'bg-red-50 text-red-700 ring-red-600/20',
}

const Dash = () => <span className="text-xs text-slate-400">—</span>

export const StatusBadge = ({ status }: { status: EnquiryStatus }) => (
  <span className={cn(base, STATUS[status])}>{status}</span>
)

export const PriorityBadge = ({ priority }: { priority: Priority | null }) =>
  priority ? <span className={cn(base, PRIORITY[priority])}>{priority}</span> : <Dash />

/** Temperature + numeric score together, e.g. "Hot · 87". */
export const LeadScoreBadge = ({ score, temperature }: { score: number | null; temperature: Temperature | null }) =>
  temperature ? (
    <span className={cn(base, TEMP[temperature])}>
      {temperature}
      {score != null && <span className="opacity-70">· {score}</span>}
    </span>
  ) : (
    <Dash />
  )

export const SentimentBadge = ({ sentiment }: { sentiment: string | null }) =>
  sentiment ? <span className={cn(base, SENTIMENT[sentiment] ?? SENTIMENT.Neutral)}>{sentiment}</span> : <Dash />

const AI: Record<AiStatus, { label: string; cls: string; icon: typeof Clock }> = {
  pending: { label: 'AI pending', cls: 'bg-slate-100 text-slate-600 ring-slate-500/20', icon: Clock },
  processing: { label: 'Analysing…', cls: 'bg-brand-50 text-brand-700 ring-brand-600/20', icon: Loader2 },
  completed: { label: 'Analysed', cls: 'bg-emerald-50 text-emerald-700 ring-emerald-600/20', icon: CheckCircle2 },
  failed: { label: 'AI failed', cls: 'bg-red-50 text-red-700 ring-red-600/20', icon: XCircle },
}
export const AiStatusBadge = ({ status }: { status: AiStatus }) => {
  const { label, cls, icon: Icon } = AI[status]
  return (
    <span className={cn(base, cls)}>
      <Icon className={cn('size-3', status === 'processing' && 'animate-spin')} aria-hidden />
      {label}
    </span>
  )
}

export const ReviewBadge = () => (
  <span className={cn(base, 'bg-amber-50 text-amber-800 ring-amber-600/20')}>
    <AlertTriangle className="size-3" aria-hidden /> Needs review
  </span>
)
