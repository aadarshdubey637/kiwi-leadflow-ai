import { useState } from 'react'
import { Link } from 'react-router-dom'
import { CheckCircle2, Loader2, XCircle } from 'lucide-react'
import { toast } from 'sonner'
import { ApiError } from '@/api/axiosInstance'
import { EnquiryForm } from '@/components/enquiry/EnquiryForm'
import { AIAnalysisCard } from '@/components/enquiry/AIAnalysisCard'
import { AiStatusBadge, LeadScoreBadge, PriorityBadge } from '@/components/ui/Badges'
import { Button } from '@/components/ui/Button'
import { Card, CardHeader } from '@/components/ui/Card'
import { useCreateEnquiry, useEnquiry, useReanalyze } from '@/hooks/useApi'
import type { EnquiryCreate } from '@/types/api'

/** Shows the freshly created enquiry and live-updates (polling) until the backend's AI workflow finishes. */
function Result({ id, onAnother }: { id: number; onAnother: () => void }) {
  const { data: enquiry } = useEnquiry(id)
  const reanalyze = useReanalyze()
  const status = enquiry?.ai_status ?? 'pending'

  return (
    <div className="space-y-6">
      <Card>
        <div className="flex flex-col gap-4 p-5 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-start gap-3">
            <CheckCircle2 className="mt-0.5 size-6 text-emerald-500" aria-hidden />
            <div>
              <p className="font-semibold text-slate-900">Enquiry #{id} saved</p>
              <p className="text-sm text-slate-500">The original message is stored. AI analysis runs automatically in the background.</p>
            </div>
          </div>
          <div className="flex gap-2">
            <Button variant="secondary" onClick={onAnother}>Add another</Button>
            <Link to={`/admin/enquiries/${id}`} className="inline-flex items-center rounded-lg bg-brand-600 px-3.5 py-2 text-sm font-medium text-white hover:bg-brand-700">View full details</Link>
          </div>
        </div>
      </Card>

      <Card>
        <CardHeader title="AI processing" action={<AiStatusBadge status={status} />} />
        <div className="p-5">
          {(status === 'pending' || status === 'processing') && (
            <p className="flex items-center gap-2 text-sm text-slate-600"><Loader2 className="size-4 animate-spin text-brand-600" aria-hidden /> Analysing the enquiry — this page updates automatically.</p>
          )}
          {status === 'failed' && (
            <div className="space-y-3">
              <p className="flex items-center gap-2 text-sm text-red-700"><XCircle className="size-4" aria-hidden /> AI analysis could not be completed. The enquiry is safe and can be retried.</p>
              <Button variant="secondary" loading={reanalyze.isPending} onClick={() => reanalyze.mutate(id)}>Retry analysis</Button>
            </div>
          )}
          {status === 'completed' && enquiry && (
            <div className="flex flex-wrap items-center gap-x-6 gap-y-2 text-sm text-slate-700">
              <span>Category: <strong>{enquiry.service_category}</strong></span>
              <span className="flex items-center gap-2">Priority: <PriorityBadge priority={enquiry.priority} /></span>
              <span className="flex items-center gap-2">Lead: <LeadScoreBadge score={enquiry.lead_score_total} temperature={enquiry.lead_temperature} /></span>
            </div>
          )}
        </div>
      </Card>

      {status === 'completed' && enquiry?.analysis && <AIAnalysisCard analysis={enquiry.analysis} />}
    </div>
  )
}

export default function AddEnquiryPage() {
  const create = useCreateEnquiry()
  const [createdId, setCreatedId] = useState<number | null>(null)
  const [formKey, setFormKey] = useState(0) // remount the form to clear it

  const submit = async (values: EnquiryCreate) => {
    try {
      const enquiry = await create.mutateAsync(values)
      setCreatedId(enquiry.id)
      toast.success(`Enquiry #${enquiry.id} submitted`)
    } catch {
      /* the mutation's onError already showed a toast */
    }
  }

  if (createdId !== null) return <div className="mx-auto max-w-3xl"><Result id={createdId} onAnother={() => { setCreatedId(null); setFormKey((k) => k + 1); create.reset() }} /></div>

  return (
    <div className="mx-auto max-w-3xl">
      <Card>
        <CardHeader title="New enquiry" description="Enter the customer's details. The AI will classify, score and draft a reply automatically." />
        <div className="p-5">
          <EnquiryForm
            key={formKey}
            onSubmit={submit}
            submitting={create.isPending}
            serverFieldErrors={create.error instanceof ApiError ? create.error.fieldErrors : undefined}
          />
        </div>
      </Card>
    </div>
  )
}
