import { Mail, MessageCircle } from 'lucide-react'
import { Card, CardHeader } from '@/components/ui/Card'
import type { Communication } from '@/types/api'
import { cn, formatDateTime } from '@/utils/format'

const STATUS: Record<Communication['status'], { label: string; cls: string }> = {
  sent: { label: 'Sent', cls: 'bg-[#dbead9] text-[#2f6b3f]' },
  opened: { label: 'WhatsApp opened', cls: 'bg-[#dbe7f0] text-[#2f6285]' },
  failed: { label: 'Failed', cls: 'bg-[#f6dcd3] text-[#a9452d]' },
  skipped: { label: 'Skipped', cls: 'bg-[#ebe6dc] text-[#5b564b]' },
}

export function CommunicationsCard({ items }: { items: Communication[] }) {
  return (
    <Card>
      <CardHeader title="Messages" description="Emails and WhatsApp chats sent about this enquiry" />
      {items.length === 0 ? (
        <p className="p-5 text-sm text-slate-400">Nothing has been sent yet.</p>
      ) : (
        <ul className="divide-y divide-white/60">
          {items.map((c) => {
            const Icon = c.channel === 'email' ? Mail : MessageCircle
            const s = STATUS[c.status]
            return (
              <li key={c.id} className="flex gap-3 px-5 py-3.5">
                <Icon className="mt-0.5 size-4 shrink-0 text-slate-400" aria-hidden />
                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center gap-x-2 gap-y-1 text-sm">
                    <span className="font-medium text-slate-900">
                      {c.kind === 'team_notification' ? 'Team alert' : c.channel === 'email' ? 'Reply by email' : 'Reply via WhatsApp'}
                    </span>
                    <span className={cn('rounded-full px-2 py-0.5 text-xs font-medium', s.cls)}>{s.label}</span>
                    <span className="text-xs text-slate-400">{formatDateTime(c.created_at)}{c.sent_by_name && ` · by ${c.sent_by_name}`}</span>
                  </div>
                  <p className="mt-0.5 truncate text-xs text-slate-500" title={c.recipient}>To {c.recipient}</p>
                  {c.error && <p className="mt-1 text-xs text-[#a9452d]">{c.error}</p>}
                  {c.body && c.kind === 'customer_reply' && <p className="mt-1 line-clamp-2 text-xs text-slate-500">{c.body}</p>}
                </div>
              </li>
            )
          })}
        </ul>
      )}
    </Card>
  )
}
