import type { ReactNode } from 'react'
import { AlertCircle } from 'lucide-react'
import { Card, CardHeader } from '@/components/ui/Card'
import { PriorityBadge, SentimentBadge } from '@/components/ui/Badges'
import type { Analysis } from '@/types/api'
import { formatMoney } from '@/utils/format'

export function AiTag() {
  return (
    <span aria-label="AI generated" className="inline-flex shrink-0 items-center gap-1.5 whitespace-nowrap rounded-md bg-[#f6e6c4] px-2 py-0.5 text-xs font-medium text-[#8f6410]">
      <span aria-hidden className="rounded bg-[#8f6410] px-1 text-[10px] font-bold leading-4 text-[#fbf1da]">AI</span>
      <span aria-hidden>generated</span>
    </span>
  )
}

function Item({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div>
      <dt className="text-xs font-medium uppercase tracking-wide text-slate-400">{label}</dt>
      <dd className="mt-1 text-sm text-slate-800">{children}</dd>
    </div>
  )
}
const None = () => <span className="text-slate-400">Not stated</span>

export function AIAnalysisCard({ analysis }: { analysis: Analysis }) {
  const conf = analysis.confidence_score
  return (
    <Card>
      <CardHeader title="AI analysis" description="Extracted from the customer's message" action={<AiTag />} />
      <div className="space-y-5 p-5">
        {analysis.summary && <p className="rounded-lg bg-slate-50 p-3 text-sm text-slate-700">{analysis.summary}</p>}

        <dl className="grid gap-x-6 gap-y-4 sm:grid-cols-2">
          <Item label="Service category">{analysis.service_category}</Item>
          <Item label="Customer intent">{analysis.customer_intent ?? <None />}</Item>
          <Item label="Budget">{analysis.budget != null ? formatMoney(analysis.budget, analysis.currency) : <None />}</Item>
          <Item label="Location">{analysis.customer_location ?? <None />}</Item>
          <Item label="Timeline">{analysis.project_timeline ?? <None />}</Item>
          <Item label="Urgency">{analysis.urgency ? <PriorityBadge priority={analysis.urgency} /> : <None />}</Item>
          <Item label="Sentiment"><SentimentBadge sentiment={analysis.sentiment} /></Item>
          <Item label="Language">{analysis.detected_language ?? <None />}</Item>
        </dl>

        <div>
          <p className="text-xs font-medium uppercase tracking-wide text-slate-400">Extracted requirements</p>
          {analysis.project_requirements.length ? (
            <ul className="mt-2 flex flex-wrap gap-2">
              {analysis.project_requirements.map((r) => (
                <li key={r} className="rounded-md bg-brand-50 px-2.5 py-1 text-xs font-medium text-brand-800">{r}</li>
              ))}
            </ul>
          ) : <p className="mt-1 text-sm text-slate-400">No specific requirements extracted</p>}
        </div>

        <div>
          <p className="flex items-center gap-1.5 text-xs font-medium uppercase tracking-wide text-amber-600">
            <AlertCircle className="size-3.5" aria-hidden /> Missing information
          </p>
          {analysis.missing_information.length ? (
            <ul className="mt-2 flex flex-wrap gap-2">
              {analysis.missing_information.map((m) => (
                <li key={m} className="rounded-md bg-amber-50 px-2.5 py-1 text-xs font-medium text-amber-800 ring-1 ring-inset ring-amber-600/20">{m}</li>
              ))}
            </ul>
          ) : <p className="mt-1 text-sm text-slate-400">Nothing missing</p>}
        </div>

        {conf != null && (
          <div>
            <div className="flex items-center justify-between text-xs">
              <span className="font-medium uppercase tracking-wide text-slate-400">AI confidence</span>
              <span className="font-medium text-slate-700">{Math.round(conf * 100)}%</span>
            </div>
            <div className="mt-1.5 h-1.5 overflow-hidden rounded-full bg-slate-100" role="progressbar" aria-valuenow={Math.round(conf * 100)} aria-valuemin={0} aria-valuemax={100} aria-label="AI confidence">
              <div className="h-full rounded-full bg-brand-500" style={{ width: `${conf * 100}%` }} />
            </div>
            <p className="mt-1 text-xs text-slate-400">The model's own estimate of reliability — an indicator, not a calibrated probability.</p>
          </div>
        )}
      </div>
    </Card>
  )
}
