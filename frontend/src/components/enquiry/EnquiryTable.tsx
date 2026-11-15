import { Link, useNavigate } from 'react-router-dom'
import { AlertTriangle, Copy, Eye } from 'lucide-react'
import { DataTable, type Column } from '@/components/ui/DataTable'
import { LeadScoreBadge, PriorityBadge, StatusBadge } from '@/components/ui/Badges'
import { useUpdateStatus } from '@/hooks/useApi'
import { ENQUIRY_STATUSES, type Enquiry, type EnquiryStatus } from '@/types/api'
import { formatDate } from '@/utils/format'

function StatusSelect({ enquiry }: { enquiry: Enquiry }) {
  const update = useUpdateStatus()
  return (
    <select
      aria-label={`Change status of ${enquiry.customer_name}`}
      value={enquiry.status}
      disabled={update.isPending}
      onClick={(e) => e.stopPropagation()}
      onChange={(e) => update.mutate({ id: enquiry.id, status: e.target.value as EnquiryStatus })}
      className="rounded-md border border-slate-300/80 bg-white/70 backdrop-blur px-2 py-1 text-xs text-slate-700 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20 disabled:opacity-50"
    >
      {ENQUIRY_STATUSES.map((s) => <option key={s}>{s}</option>)}
    </select>
  )
}

/** Full table (all plan columns) or `compact` (fewer columns, read-only status) for the dashboard. */
export function EnquiryTable({ rows, compact = false }: { rows: Enquiry[]; compact?: boolean }) {
  const navigate = useNavigate()

  const columns: Column<Enquiry>[] = [
    {
      key: 'name', header: 'Customer',
      cell: (e) => (
        <div className="min-w-[8rem]">
          <p className="font-medium text-slate-900">{e.customer_name}</p>
          {e.summary && <p className="mt-0.5 line-clamp-1 max-w-[16rem] text-xs text-slate-500" title={e.summary}>{e.summary}</p>}
          <div className="mt-0.5 flex flex-wrap gap-x-2 text-xs">
            {e.duplicate_of_id && (
              <span className="inline-flex items-center gap-1 text-amber-700" title={e.duplicate_reason ?? undefined}>
                <Copy className="size-3" aria-hidden /> Duplicate of #{e.duplicate_of_id}
              </span>
            )}
            {e.needs_manual_review && (
              <span className="inline-flex items-center gap-1 text-amber-700"><AlertTriangle className="size-3" aria-hidden /> Review</span>
            )}
          </div>
        </div>
      ),
    },
    ...(compact ? [] : [
      { key: 'email', header: 'Email', hideBelow: 'lg' as const, cell: (e: Enquiry) => <span className="text-slate-600">{e.email ?? '—'}</span> },
      { key: 'phone', header: 'Phone', hideBelow: 'lg' as const, cell: (e: Enquiry) => <span className="whitespace-nowrap text-slate-600">{e.phone ?? '—'}</span> },
    ]),
    {
      key: 'category', header: 'Service', hideBelow: 'md',
      cell: (e) => e.service_category ? <span className="text-slate-700">{e.service_category}</span> : <span className="text-xs text-slate-400">{e.ai_status === 'failed' ? 'AI failed' : 'Analysing…'}</span>,
    },
    { key: 'assignee', header: 'Assigned to', hideBelow: 'lg', cell: (e) => (e.assigned_to_name ? <span className="text-slate-700">{e.assigned_to_name}</span> : <span className="text-xs text-slate-400">Unassigned</span>) },
    { key: 'priority', header: 'Priority', cell: (e) => <PriorityBadge priority={e.priority} /> },
    { key: 'score', header: 'Lead score', hideBelow: 'md', cell: (e) => <LeadScoreBadge score={e.lead_score_total} temperature={e.lead_temperature} /> },
    { key: 'status', header: 'Status', cell: (e) => (compact ? <StatusBadge status={e.status} /> : <StatusSelect enquiry={e} />) },
    { key: 'created', header: 'Created', hideBelow: 'md', cell: (e) => <span className="whitespace-nowrap text-slate-500">{formatDate(e.created_at)}</span> },
    ...(compact ? [] : [{
      key: 'actions', header: 'Actions', className: 'text-right',
      cell: (e: Enquiry) => (
        <Link to={`/admin/enquiries/${e.id}`} onClick={(ev) => ev.stopPropagation()}
          className="inline-flex items-center gap-1 rounded-md px-2 py-1 text-xs font-medium text-brand-700 hover:bg-brand-50">
          <Eye className="size-3.5" aria-hidden /> View
        </Link>
      ),
    }]),
  ]

  return <DataTable columns={columns} rows={rows} rowKey={(e) => e.id} onRowClick={(e) => navigate(`/admin/enquiries/${e.id}`)} />
}
