import { AlertTriangle, Copy } from 'lucide-react'
import { Link } from 'react-router-dom'
import { Card, CardHeader } from '@/components/ui/Card'
import { PriorityBadge } from '@/components/ui/Badges'
import type { EnquiryDetail, Temperature } from '@/types/api'
import { AiTag } from './AIAnalysisCard'

const RING: Record<Temperature, string> = { Hot: '#ef4444', Warm: '#f97316', Cold: '#3b82f6' }

function ScoreRing({ score, temperature }: { score: number; temperature: Temperature }) {
  const r = 42
  const c = 2 * Math.PI * r
  return (
    <div className="relative size-28 shrink-0">
      <svg viewBox="0 0 100 100" className="size-full -rotate-90" role="img" aria-label={`Lead score ${score} out of 100, ${temperature}`}>
        <circle cx="50" cy="50" r={r} fill="none" stroke="#f1f5f9" strokeWidth="9" />
        <circle cx="50" cy="50" r={r} fill="none" stroke={RING[temperature]} strokeWidth="9" strokeLinecap="round"
          strokeDasharray={c} strokeDashoffset={c * (1 - score / 100)} />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-2xl font-semibold text-slate-900">{score}</span>
        <span className="text-[10px] font-medium uppercase tracking-wide" style={{ color: RING[temperature] }}>{temperature}</span>
      </div>
    </div>
  )
}

function Bar({ label, value, max }: { label: string; value: number; max: number }) {
  return (
    <div>
      <div className="flex justify-between text-xs"><span className="text-slate-600">{label}</span><span className="font-medium text-slate-800">{value}/{max}</span></div>
      <div className="mt-1 h-1.5 overflow-hidden rounded-full bg-slate-100">
        <div className="h-full rounded-full bg-brand-500" style={{ width: `${(value / max) * 100}%` }} />
      </div>
    </div>
  )
}

export function LeadIntelligenceCard({ enquiry }: { enquiry: EnquiryDetail }) {
  const s = enquiry.lead_score
  return (
    <Card>
      <CardHeader title="Lead intelligence" description="Computed by backend rules from the AI's extracted facts" action={<AiTag />} />
      <div className="space-y-5 p-5">
        {enquiry.duplicate_of_id && (
          <div role="alert" className="flex items-start gap-2 rounded-lg border border-amber-300 bg-amber-50 p-3 text-sm text-amber-900">
            <Copy className="mt-0.5 size-4 shrink-0" aria-hidden />
            <p>
              <span className="font-medium">Possible duplicate</span> of{' '}
              <Link to={`/admin/enquiries/${enquiry.duplicate_of_id}`} className="font-medium underline">enquiry #{enquiry.duplicate_of_id}</Link>
              {enquiry.duplicate_reason && <> — {enquiry.duplicate_reason}</>}. Flagged for your review; nothing was merged or deleted.
            </p>
          </div>
        )}
        {enquiry.needs_manual_review && (
          <div role="alert" className="flex items-start gap-2 rounded-lg border border-amber-300 bg-amber-50 p-3 text-sm text-amber-900">
            <AlertTriangle className="mt-0.5 size-4 shrink-0" aria-hidden />
            <p><span className="font-medium">Manual review recommended.</span> The AI was unsure of the category, or the message looked unusual.</p>
          </div>
        )}

        {s ? (
          <div className="flex flex-col items-center gap-5 sm:flex-row">
            <ScoreRing score={s.total_score} temperature={s.lead_temperature} />
            <div className="w-full space-y-2.5">
              <Bar label="Budget" value={s.budget_score} max={25} />
              <Bar label="Requirement clarity" value={s.requirement_clarity_score} max={20} />
              <Bar label="Urgency" value={s.urgency_score} max={25} />
              <Bar label="Service relevance" value={s.service_relevance_score} max={20} />
              <Bar label="Engagement" value={s.engagement_score} max={10} />
            </div>
          </div>
        ) : <p className="text-sm text-slate-400">No lead score yet.</p>}

        {s?.scoring_explanation && <p className="rounded-lg bg-slate-50 p-3 text-xs leading-relaxed text-slate-600">{s.scoring_explanation}</p>}

        <div className="border-t border-slate-100 pt-4">
          <div className="flex items-center gap-2">
            <span className="text-xs font-medium uppercase tracking-wide text-slate-400">Priority</span>
            <PriorityBadge priority={enquiry.priority} />
          </div>
          <p className="mt-2 text-sm text-slate-600">{enquiry.priority_reason ?? 'Priority has not been assigned yet.'}</p>
        </div>
      </div>
    </Card>
  )
}
