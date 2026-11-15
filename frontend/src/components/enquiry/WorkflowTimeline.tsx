import { useMemo, useState } from 'react'
import { CheckCircle2, Circle, MinusCircle, XCircle } from 'lucide-react'
import type { WorkflowLog } from '@/types/api'
import { cn, formatDateTime, formatSeconds } from '@/utils/format'
import { stepLabel } from '@/utils/workflow'

/** A retry appends a new "workflow_started" — split the flat log list into separate runs. */
function splitRuns(logs: WorkflowLog[]): WorkflowLog[][] {
  const runs: WorkflowLog[][] = []
  let current: WorkflowLog[] = []
  for (const l of logs) {
    if (l.workflow_step === 'workflow_started' && current.some((x) => x.workflow_step === 'workflow_started')) {
      runs.push(current)
      current = []
    }
    current.push(l)
  }
  if (current.length) runs.push(current)
  return runs
}

const ICON = {
  success: { icon: CheckCircle2, cls: 'text-emerald-500' },
  failed: { icon: XCircle, cls: 'text-red-500' },
  skipped: { icon: MinusCircle, cls: 'text-slate-400' },
  started: { icon: Circle, cls: 'text-brand-500' },
}

export function WorkflowTimeline({ logs }: { logs: WorkflowLog[] }) {
  const runs = useMemo(() => splitRuns(logs), [logs])
  const [selected, setSelected] = useState(runs.length - 1)
  const [seenRuns, setSeenRuns] = useState(runs.length)
  if (runs.length !== seenRuns) { // a retry added a run: jump to the newest one
    setSeenRuns(runs.length)
    setSelected(runs.length - 1)
  }
  const run = runs[Math.min(selected, runs.length - 1)] ?? []

  return (
    <div>
      {runs.length > 1 && (
        <div className="mb-4 flex flex-wrap gap-2" role="tablist" aria-label="Processing attempts">
          {runs.map((r, i) => {
            const failed = r.some((l) => l.execution_status === 'failed')
            return (
              <button key={i} role="tab" aria-selected={i === selected} onClick={() => setSelected(i)}
                className={cn('rounded-full px-3 py-1 text-xs font-medium ring-1 ring-inset transition-colors',
                  i === selected ? 'bg-slate-900 text-white ring-slate-900' : 'bg-white text-slate-600 ring-slate-300 hover:bg-slate-50')}>
                Attempt {i + 1}{failed ? ' · failed' : ''}
              </button>
            )
          })}
        </div>
      )}

      <ol className="relative">
        {run.map((l, i) => {
          const { icon: Icon, cls } = ICON[l.execution_status]
          const failed = l.execution_status === 'failed'
          return (
            <li key={l.id} className="relative flex gap-4 pb-6 last:pb-0">
              {i < run.length - 1 && <span className="absolute left-[11px] top-6 h-full w-px bg-slate-200" aria-hidden />}
              <Icon className={cn('relative z-10 size-6 shrink-0 rounded-full bg-white', cls)} aria-hidden />
              <div className="min-w-0 flex-1 -mt-0.5">
                <div className="flex flex-wrap items-baseline justify-between gap-x-4">
                  <p className={cn('text-sm font-medium', failed ? 'text-red-700' : 'text-slate-900')}>{stepLabel(l.workflow_step)}</p>
                  <p className="text-xs text-slate-400">
                    {formatDateTime(l.created_at)}{l.execution_time != null && <> · {formatSeconds(l.execution_time)}</>}
                  </p>
                </div>
                {l.message && (
                  <p className={cn('mt-0.5 break-words text-xs', failed ? 'rounded-md bg-red-50 p-2 text-red-700' : 'text-slate-500')}>{l.message}</p>
                )}
              </div>
            </li>
          )
        })}
      </ol>
    </div>
  )
}
