import { useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { Card, CardHeader } from '@/components/ui/Card'
import { DataTable, type Column } from '@/components/ui/DataTable'
import { EmptyState, ErrorMessage, LoadingSpinner } from '@/components/ui/States'
import { Pagination } from '@/components/ui/Pagination'
import { WorkflowTimeline } from '@/components/enquiry/WorkflowTimeline'
import { useEnquiries, useWorkflowLogs, useWorkflowTimeline } from '@/hooks/useApi'
import type { WorkflowLog } from '@/types/api'
import { cn, formatDateTime, formatSeconds } from '@/utils/format'
import { stepLabel } from '@/utils/workflow'

const STATUS_CLS: Record<WorkflowLog['execution_status'], string> = {
  success: 'bg-emerald-50 text-emerald-700 ring-emerald-600/20',
  failed: 'bg-red-50 text-red-700 ring-red-600/20',
  skipped: 'bg-slate-100 text-slate-600 ring-slate-500/20',
  started: 'bg-brand-50 text-brand-700 ring-brand-600/20',
}
const STATUSES = ['success', 'failed', 'skipped', 'started'] as const

export default function WorkflowPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const enquiryId = id && Number.isInteger(Number(id)) ? Number(id) : null

  const options = useEnquiries({ page: 1, page_size: 100 })
  const timeline = useWorkflowTimeline(enquiryId)
  const [page, setPage] = useState(1)
  const [status, setStatus] = useState<WorkflowLog['execution_status'] | ''>('')
  const logs = useWorkflowLogs({ page, page_size: 15, status: status || undefined })

  const columns: Column<WorkflowLog>[] = [
    { key: 'time', header: 'Time', cell: (l) => <span className="whitespace-nowrap text-slate-500">{formatDateTime(l.created_at)}</span> },
    { key: 'enq', header: 'Enquiry', cell: (l) => <span className="font-medium text-slate-900">#{l.enquiry_id}</span> },
    { key: 'step', header: 'Step', cell: (l) => stepLabel(l.workflow_step) },
    { key: 'status', header: 'Status', cell: (l) => <span className={cn('rounded-full px-2 py-0.5 text-xs font-medium ring-1 ring-inset', STATUS_CLS[l.execution_status])}>{l.execution_status}</span> },
    { key: 'dur', header: 'Duration', hideBelow: 'md', cell: (l) => <span className="text-slate-500">{formatSeconds(l.execution_time)}</span> },
    { key: 'msg', header: 'Details', hideBelow: 'lg', cell: (l) => <span className="line-clamp-1 max-w-xs text-xs text-slate-500" title={l.message ?? undefined}>{l.message ?? '—'}</span> },
  ]

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader
          title="Enquiry processing timeline"
          description="Every step the automated workflow ran for one enquiry"
          action={
            <select aria-label="Choose an enquiry" value={enquiryId ?? ''} onChange={(e) => navigate(e.target.value ? `/admin/workflows/${e.target.value}` : '/admin/workflows')}
              className="max-w-[14rem] rounded-lg border border-slate-300/80 bg-white/70 backdrop-blur px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20">
              <option value="">Select an enquiry…</option>
              {enquiryId !== null && !options.data?.data.some((e) => e.id === enquiryId) && <option value={enquiryId}>#{enquiryId}</option>}
              {options.data?.data.map((e) => <option key={e.id} value={e.id}>#{e.id} · {e.customer_name}</option>)}
            </select>
          }
        />
        <div className="p-5">
          {enquiryId === null ? (
            <EmptyState title="Choose an enquiry" description="Pick an enquiry above (or click a row below) to see its step-by-step execution history." />
          ) : timeline.isLoading ? <LoadingSpinner /> : timeline.error ? <ErrorMessage error={timeline.error} onRetry={() => timeline.refetch()} /> :
            timeline.data && timeline.data.length ? <WorkflowTimeline logs={timeline.data} /> : <EmptyState title="No workflow history for this enquiry" />}
        </div>
      </Card>

      <Card>
        <CardHeader
          title="All workflow executions" description="Latest step records across every enquiry"
          action={
            <select aria-label="Filter by status" value={status} onChange={(e) => { setStatus(e.target.value as typeof status); setPage(1) }}
              className="rounded-lg border border-slate-300/80 bg-white/70 backdrop-blur px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20">
              <option value="">Status: All</option>
              {STATUSES.map((s) => <option key={s}>{s}</option>)}
            </select>
          }
        />
        {logs.isLoading ? <LoadingSpinner /> : logs.error ? <ErrorMessage error={logs.error} onRetry={() => logs.refetch()} /> :
          logs.data && logs.data.data.length === 0 ? <EmptyState title="No workflow records yet" description="Records appear as soon as an enquiry is submitted." /> :
          logs.data && (
            <>
              <DataTable columns={columns} rows={logs.data.data} rowKey={(l) => l.id} onRowClick={(l) => { navigate(`/admin/workflows/${l.enquiry_id}`); window.scrollTo({ top: 0, behavior: 'smooth' }) }} />
              <Pagination meta={logs.data.meta} onPage={setPage} />
            </>
          )}
      </Card>
    </div>
  )
}
