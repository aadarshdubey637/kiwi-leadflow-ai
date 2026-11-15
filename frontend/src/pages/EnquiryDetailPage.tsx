import { useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { ArrowLeft, GitBranch, Loader2, Mail, Phone, RefreshCw, XCircle } from 'lucide-react'
import { AIAnalysisCard } from '@/components/enquiry/AIAnalysisCard'
import { LeadIntelligenceCard } from '@/components/enquiry/LeadIntelligenceCard'
import { CommunicationsCard } from '@/components/enquiry/CommunicationsCard'
import { ResponseCard } from '@/components/enquiry/ResponseCard'
import { AiStatusBadge, StatusBadge } from '@/components/ui/Badges'
import { Button } from '@/components/ui/Button'
import { Card, CardHeader } from '@/components/ui/Card'
import { ConfirmationModal } from '@/components/ui/ConfirmationModal'
import { ErrorMessage, LoadingSpinner } from '@/components/ui/States'
import { useAssign, useEnquiry, useReanalyze, useTeam, useUpdateStatus } from '@/hooks/useApi'
import { ApiError } from '@/api/axiosInstance'
import { ENQUIRY_STATUSES, type EnquiryStatus } from '@/types/api'
import { formatDateTime } from '@/utils/format'

export default function EnquiryDetailPage() {
  const { id: idParam } = useParams()
  const id = Number(idParam)
  const navigate = useNavigate()
  const { data: e, isLoading, error, refetch } = useEnquiry(id)
  const updateStatus = useUpdateStatus()
  const reanalyze = useReanalyze()
  const assign = useAssign()
  const team = useTeam()
  const [confirmReanalyze, setConfirmReanalyze] = useState(false)

  if (!Number.isInteger(id) || id < 1) return <Card><ErrorMessage error={new ApiError('This enquiry link is not valid.', 404, 'not_found')} /></Card>
  if (isLoading) return <LoadingSpinner />
  if (error || !e) return (
    <div className="space-y-4">
      <Link to="/admin/enquiries" className="inline-flex items-center gap-1 text-sm text-slate-500 hover:text-slate-800"><ArrowLeft className="size-4" /> Back to enquiries</Link>
      <Card><ErrorMessage error={error} onRetry={error instanceof ApiError && error.status === 404 ? undefined : () => refetch()} /></Card>
    </div>
  )

  const analysing = e.ai_status === 'pending' || e.ai_status === 'processing'

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <button onClick={() => (window.history.length > 1 ? navigate(-1) : navigate('/admin/enquiries'))} className="inline-flex items-center gap-1 text-sm text-slate-500 hover:text-slate-800">
          <ArrowLeft className="size-4" /> Back
        </button>
        <div className="flex flex-wrap items-center gap-2">
          <Link to={`/admin/workflows/${e.id}`} className="inline-flex items-center gap-2 rounded-lg border border-slate-300/80 bg-white/70 backdrop-blur px-3.5 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50">
            <GitBranch className="size-4" /> Workflow history
          </Link>
          <Button variant="secondary" icon={<RefreshCw className="size-4" />} disabled={analysing} onClick={() => setConfirmReanalyze(true)}>Re-analyse</Button>
        </div>
      </div>

      {/* Header: identity + the two admin controls (status) */}
      <Card className="p-5">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <h2 className="text-xl font-semibold tracking-tight text-slate-900">{e.customer_name}</h2>
              <span className="text-sm text-slate-400">#{e.id}</span>
              <StatusBadge status={e.status} />
              <AiStatusBadge status={e.ai_status} />
            </div>
            <div className="mt-2 flex flex-wrap gap-x-5 gap-y-1 text-sm text-slate-600">
              {e.email && <span className="flex items-center gap-1.5"><Mail className="size-4 text-slate-400" aria-hidden />{e.email}</span>}
              {e.phone && <span className="flex items-center gap-1.5"><Phone className="size-4 text-slate-400" aria-hidden />{e.phone}</span>}
              <span className="text-slate-400">Submitted {formatDateTime(e.created_at)} · via {e.source}</span>
            </div>
          </div>
          <div className="flex flex-col gap-3 sm:flex-row">
          <div>
            <label htmlFor="assignee" className="text-xs font-medium uppercase tracking-wide text-slate-400">Assigned to</label>
            <select id="assignee" value={e.assigned_to_id ?? ''} disabled={assign.isPending}
              onChange={(ev) => assign.mutate({ id: e.id, assigneeId: ev.target.value ? Number(ev.target.value) : null })}
              className="mt-1 block w-full rounded-lg border border-slate-300/80 bg-white/70 px-3 py-2 text-sm backdrop-blur focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20 sm:w-44">
              <option value="">Unassigned</option>
              {team.data?.map((m) => <option key={m.id} value={m.id} disabled={!m.is_active && m.id !== e.assigned_to_id}>{m.username}{m.is_active ? '' : ' (paused)'}</option>)}
            </select>
          </div>
          <div>
            <label htmlFor="status" className="text-xs font-medium uppercase tracking-wide text-slate-400">Update status</label>
            <select id="status" value={e.status} disabled={updateStatus.isPending}
              onChange={(ev) => updateStatus.mutate({ id: e.id, status: ev.target.value as EnquiryStatus })}
              className="mt-1 block w-full rounded-lg border border-slate-300/80 bg-white/70 backdrop-blur px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20 sm:w-44">
              {ENQUIRY_STATUSES.map((s) => <option key={s}>{s}</option>)}
            </select>
          </div>
          </div>
        </div>
      </Card>

      {analysing && (
        <div role="status" className="flex items-center gap-2 rounded-lg border border-brand-100 bg-brand-50 p-3 text-sm text-brand-800">
          <Loader2 className="size-4 animate-spin" aria-hidden /> AI is analysing this enquiry. Results will appear here automatically.
        </div>
      )}
      {e.ai_status === 'failed' && (
        <div role="alert" className="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-800">
          <span className="flex items-center gap-2"><XCircle className="size-4" aria-hidden /> AI analysis failed. The original enquiry is intact — check the workflow history for the reason, then retry.</span>
          <Button variant="secondary" loading={reanalyze.isPending} onClick={() => reanalyze.mutate(e.id)}>Retry analysis</Button>
        </div>
      )}

      <div className="grid gap-6 xl:grid-cols-5">
        <div className="space-y-6 xl:col-span-3">
          {/* ORIGINAL customer data — kept visually separate from everything AI-generated */}
          <Card>
            <CardHeader title="Original customer message" description="Exactly as submitted — never modified" />
            <p dir="auto" className="whitespace-pre-wrap break-words p-5 text-sm leading-relaxed text-slate-800">{e.message}</p>
          </Card>
          {e.analysis ? <AIAnalysisCard analysis={e.analysis} /> : !analysing && (
            <Card><p className="p-5 text-sm text-slate-400">No AI analysis available yet.</p></Card>
          )}
        </div>
        <div className="xl:col-span-2">
          <LeadIntelligenceCard enquiry={e} />
        </div>
      </div>

      <ResponseCard key={e.response?.updated_at ?? 'none'} enquiryId={e.id} response={e.response} followups={e.followups} contact={{ email: e.email, phone: e.phone }} />

      <CommunicationsCard items={e.communications} />

      <ConfirmationModal
        open={confirmReanalyze} title="Re-analyse this enquiry?"
        message="The AI will process the original message again and refresh the analysis, score, priority and suggested response. Your edited response, if any, is kept."
        confirmLabel="Re-analyse" loading={reanalyze.isPending}
        onCancel={() => setConfirmReanalyze(false)}
        onConfirm={() => reanalyze.mutate(e.id, { onSettled: () => setConfirmReanalyze(false) })}
      />
    </div>
  )
}
