import { useState } from 'react'
import { Link } from 'react-router-dom'
import { AlarmClock, CalendarClock, CheckCheck, CheckCircle2, ListTodo, RotateCcw, X } from 'lucide-react'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { LeadScoreBadge, PriorityBadge } from '@/components/ui/Badges'
import { Pagination } from '@/components/ui/Pagination'
import { EmptyState, ErrorMessage, LoadingSpinner } from '@/components/ui/States'
import { StatCard } from '@/components/ui/StatCard'
import { useFollowups, useFollowupSummary, useTeam, useUpdateFollowup } from '@/hooks/useApi'
import type { FollowUpFilters, FollowUpItem } from '@/types/api'
import { cn, formatDateTime } from '@/utils/format'

type Tab = 'overdue' | 'pending' | 'done' | 'dismissed'
const TABS: { key: Tab; label: string }[] = [
  { key: 'overdue', label: 'Overdue' },
  { key: 'pending', label: 'All pending' },
  { key: 'done', label: 'Done' },
  { key: 'dismissed', label: 'Dismissed' },
]

const dueLabel = (f: FollowUpItem) => {
  if (!f.suggested_date) return 'No date'
  return formatDateTime(f.suggested_date)
}

export default function FollowUpsPage() {
  const [tab, setTab] = useState<Tab>('pending')
  const [page, setPage] = useState(1)
  const [assignee, setAssignee] = useState<string>('') // '' = everyone, 'none' = unassigned, else member id
  const summary = useFollowupSummary()
  const team = useTeam()
  const update = useUpdateFollowup()

  const filters: FollowUpFilters = {
    page, page_size: 12,
    status: tab === 'done' ? 'Done' : tab === 'dismissed' ? 'Dismissed' : 'Pending',
    overdue: tab === 'overdue',
    assignee_id: assignee && assignee !== 'none' ? Number(assignee) : undefined,
    unassigned: assignee === 'none',
  }
  const list = useFollowups(filters)

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard delay={0} label="Overdue" value={summary.data?.overdue ?? '—'} icon={AlarmClock} tone="red" hint="Past their suggested date" />
        <StatCard delay={60} label="Due today" value={summary.data?.due_today ?? '—'} icon={CalendarClock} tone="amber" />
        <StatCard delay={120} label="Pending" value={summary.data?.pending ?? '—'} icon={ListTodo} tone="sky" />
        <StatCard delay={180} label="Done" value={summary.data?.done ?? '—'} icon={CheckCheck} tone="emerald" />
      </div>

      <Card>
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-white/60 p-4">
          <div className="flex rounded-lg bg-slate-200/60 p-0.5" role="tablist" aria-label="Follow-up filter">
            {TABS.map((t) => (
              <button key={t.key} role="tab" aria-selected={tab === t.key} onClick={() => { setTab(t.key); setPage(1) }}
                className={cn('rounded-md px-3 py-1.5 text-xs font-medium transition-colors', tab === t.key ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-500 hover:text-slate-700')}>
                {t.label}
                {t.key === 'overdue' && !!summary.data?.overdue && <span className="ml-1.5 rounded-full bg-clay px-1.5 py-0.5 text-[10px] font-semibold text-white">{summary.data.overdue}</span>}
              </button>
            ))}
          </div>
          <select aria-label="Filter by team member" value={assignee} onChange={(e) => { setAssignee(e.target.value); setPage(1) }}
            className="rounded-lg border border-slate-300/80 bg-white/70 px-3 py-2 text-sm backdrop-blur focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20">
            <option value="">Everyone</option>
            <option value="none">Unassigned</option>
            {team.data?.map((m) => <option key={m.id} value={m.id}>{m.username}</option>)}
          </select>
        </div>

        {list.isLoading ? <LoadingSpinner /> : list.error ? <ErrorMessage error={list.error} onRetry={() => list.refetch()} /> :
          list.data && list.data.data.length === 0 ? (
            <EmptyState
              title={tab === 'overdue' ? 'Nothing is overdue' : tab === 'pending' ? 'No pending follow-ups' : 'Nothing here yet'}
              description={tab === 'overdue' ? 'Every suggested follow-up is still within its date. Nice work.' : 'Follow-up suggestions appear here after an enquiry has been analysed.'}
            />
          ) : list.data && (
            <>
              <ul className="divide-y divide-white/60">
                {list.data.data.map((f) => (
                  <li key={f.id} className="flex flex-col gap-3 px-5 py-4 sm:flex-row sm:items-center sm:justify-between">
                    <div className="min-w-0">
                      <p className="text-sm font-medium text-slate-900">{f.suggested_action}</p>
                      <div className="mt-1.5 flex flex-wrap items-center gap-x-3 gap-y-1.5 text-xs text-slate-500">
                        <Link to={`/admin/enquiries/${f.enquiry_id}`} className="font-medium text-brand-700 hover:underline">#{f.enquiry_id} · {f.customer_name}</Link>
                        <PriorityBadge priority={f.enquiry_priority} />
                        <LeadScoreBadge score={null} temperature={f.lead_temperature} />
                        <span>{f.assigned_to_name ? `Assigned to ${f.assigned_to_name}` : 'Unassigned'}</span>
                        <span className={cn('inline-flex items-center gap-1', f.is_overdue && 'font-semibold text-clay')}>
                          <CalendarClock className="size-3.5" aria-hidden /> {f.is_overdue ? 'Overdue · ' : 'Due '}{dueLabel(f)}
                        </span>
                      </div>
                    </div>
                    <div className="flex shrink-0 gap-2">
                      {f.status === 'Pending' ? (
                        <>
                          <Button variant="secondary" icon={<CheckCircle2 className="size-4" />} disabled={update.isPending} onClick={() => update.mutate({ id: f.id, status: 'Done' })}>Done</Button>
                          <Button variant="ghost" icon={<X className="size-4" />} disabled={update.isPending} onClick={() => update.mutate({ id: f.id, status: 'Dismissed' })}>Dismiss</Button>
                        </>
                      ) : (
                        <Button variant="secondary" icon={<RotateCcw className="size-4" />} disabled={update.isPending} onClick={() => update.mutate({ id: f.id, status: 'Pending' })}>Reopen</Button>
                      )}
                    </div>
                  </li>
                ))}
              </ul>
              <Pagination meta={list.data.meta} onPage={setPage} />
            </>
          )}
      </Card>
    </div>
  )
}
