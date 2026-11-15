import { useState } from 'react'
import { CalendarClock, HelpCircle, Mail, MessageCircle, RotateCcw, Save } from 'lucide-react'
import { toast } from 'sonner'
import { Button } from '@/components/ui/Button'
import { Card, CardHeader } from '@/components/ui/Card'
import { ConfirmationModal } from '@/components/ui/ConfirmationModal'
import { useCapabilities, useSendEmail, useUpdateResponse, useWhatsApp } from '@/hooks/useApi'
import type { AiResponse, FollowUp } from '@/types/api'
import { formatDateTime } from '@/utils/format'
import { AiTag } from './AIAnalysisCard'

interface Props {
  enquiryId: number
  response: AiResponse | null
  followups: FollowUp[]
  contact: { email: string | null; phone: string | null }
}

export function ResponseCard({ enquiryId, response, followups, contact }: Props) {
  const save = useUpdateResponse()
  const sendEmail = useSendEmail()
  const whatsapp = useWhatsApp()
  const caps = useCapabilities()
  const saved = response?.final_response ?? ''
  const [text, setText] = useState(saved)
  const [confirmEmail, setConfirmEmail] = useState(false)

  if (!response) {
    return (
      <Card>
        <CardHeader title="Suggested customer response" action={<AiTag />} />
        <p className="p-5 text-sm text-slate-400">No response has been generated yet.</p>
      </Card>
    )
  }

  const dirty = text.trim() !== saved.trim()
  const edited = response.edited_response != null
  const canEmail = !!contact.email && !!caps.data?.email_enabled
  const emailHint = !contact.email ? 'This enquiry has no email address' : caps.data && !caps.data.email_enabled ? 'Email is not configured on the server (SMTP settings)' : 'Send this reply by email'

  // WhatsApp: open the tab synchronously on click (so popup blockers allow it), then point it at the prepared link.
  const openWhatsApp = () => {
    const tab = window.open('', '_blank')
    whatsapp.mutate({ id: enquiryId, text: text.trim() }, {
      onSuccess: ({ link }) => {
        if (tab) { tab.opener = null; tab.location.href = link } else { toast.message('Popup blocked', { description: 'Allow popups to open WhatsApp.' }) }
      },
      onError: () => tab?.close(),
    })
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader
          title="Suggested customer response"
          description={edited ? 'Showing your edited version. The original AI draft is preserved.' : 'Review and edit, then send it by email or WhatsApp.'}
          action={<AiTag />}
        />
        <div className="space-y-3 p-5">
          <textarea
            value={text} onChange={(e) => setText(e.target.value)} rows={10} maxLength={3000} aria-label="Customer response"
            className="w-full resize-y rounded-lg border border-slate-300/80 bg-white/70 p-3 text-sm leading-relaxed text-slate-800 backdrop-blur focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20"
          />
          <div className="flex flex-wrap items-center justify-between gap-3">
            <span className="text-xs text-slate-400">{text.length}/3000{dirty && ' · unsaved changes (they will still be sent)'}</span>
            <div className="flex flex-wrap gap-2">
              <Button variant="secondary" icon={<RotateCcw className="size-4" />}
                disabled={text === response.generated_response || save.isPending} onClick={() => setText(response.generated_response)}>
                Use AI original
              </Button>
              <Button icon={<Save className="size-4" />} loading={save.isPending} disabled={!dirty || !text.trim()}
                onClick={() => save.mutate({ id: enquiryId, text })}>
                Save response
              </Button>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-2 border-t border-white/60 pt-4">
            <span className="mr-1 text-xs font-medium uppercase tracking-wide text-slate-400">Send to customer</span>
            <Button variant="secondary" icon={<Mail className="size-4" />} disabled={!canEmail || !text.trim()} title={emailHint}
              onClick={() => setConfirmEmail(true)}>
              Email
            </Button>
            <Button variant="secondary" icon={<MessageCircle className="size-4" />} loading={whatsapp.isPending}
              disabled={!contact.phone || !text.trim()} title={contact.phone ? 'Open WhatsApp with this reply ready to send' : 'This enquiry has no phone number'}
              onClick={openWhatsApp}>
              WhatsApp
            </Button>
            {!canEmail && contact.email && caps.data && <span className="text-xs text-slate-400">Email is not set up on this server.</span>}
          </div>
        </div>
      </Card>

      <div className="grid gap-6 md:grid-cols-2">
        <Card>
          <CardHeader title="Follow-up questions" description="Questions asked in the draft" />
          <ul className="space-y-2 p-5">
            {response.followup_questions.length ? response.followup_questions.map((q) => (
              <li key={q} className="flex gap-2 text-sm text-slate-700"><HelpCircle className="mt-0.5 size-4 shrink-0 text-brand-500" aria-hidden />{q}</li>
            )) : <li className="text-sm text-slate-400">None</li>}
          </ul>
        </Card>
        <Card>
          <CardHeader title="Suggested next steps" description="AI-assisted follow-up actions" />
          <ul className="space-y-3 p-5">
            {followups.length ? followups.map((f) => (
              <li key={f.id} className="text-sm text-slate-700">
                <p>{f.suggested_action}</p>
                {f.suggested_date && (
                  <p className="mt-0.5 flex items-center gap-1 text-xs text-slate-400"><CalendarClock className="size-3" aria-hidden />Suggested by {formatDateTime(f.suggested_date)} · {f.status}</p>
                )}
              </li>
            )) : <li className="text-sm text-slate-400">No follow-ups suggested (the enquiry may be closed or converted).</li>}
          </ul>
        </Card>
      </div>

      <ConfirmationModal
        open={confirmEmail} title="Email this reply?"
        message={`This will be sent to ${contact.email ?? ''} exactly as written above${dirty ? ' (including your unsaved edits)' : ''}.`}
        confirmLabel="Send email" loading={sendEmail.isPending}
        onCancel={() => setConfirmEmail(false)}
        onConfirm={() => sendEmail.mutate({ id: enquiryId, body: text.trim() }, { onSettled: () => setConfirmEmail(false) })}
      />
    </div>
  )
}
