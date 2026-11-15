import { Menu } from 'lucide-react'
import { useLocation } from 'react-router-dom'
import { useAuth } from '@/auth/AuthContext'

const TITLES: [string, string, string][] = [
  ['/admin/enquiries/new', 'Add Enquiry', 'Record an enquiry on behalf of a customer'],
  ['/admin/enquiries', 'Enquiries', 'Search, filter and manage every lead'],
  ['/admin/followups', 'Follow-ups', 'Reminders for what to do next, most urgent first'],
  ['/admin/team', 'Team', 'Who is handling what'],
  ['/admin/intelligence', 'AI Intelligence', 'Lead quality and priorities at a glance'],
  ['/admin/workflows', 'Workflow History', 'Every automated step, with timings'],
  ['/admin/analytics', 'Analytics & Reports', 'Trends, conversion and pipeline'],
  ['/admin/monitoring', 'AI Monitoring', 'Usage, speed, tokens and cost'],
]

const greeting = () => {
  const h = new Date().getHours()
  return h < 12 ? 'Good morning' : h < 18 ? 'Good afternoon' : 'Good evening'
}

export function Header({ onMenu }: { onMenu: () => void }) {
  const { pathname } = useLocation()
  const { admin } = useAuth()
  const match = TITLES.find(([p]) => pathname === p || pathname.startsWith(p + '/'))
  const title = match?.[1] ?? 'Overview'
  const subtitle = match?.[2] ?? `${greeting()}${admin ? `, ${admin.username}` : ''}. Here's where your pipeline stands.`

  return (
    <header className="glass sticky top-4 z-20 mx-4 mt-4 flex h-16 items-center justify-between rounded-2xl px-4 sm:mx-6 sm:px-5">
      <div className="flex min-w-0 items-center gap-3">
        <button className="rounded-lg p-2 text-slate-600 hover:bg-white/70 lg:hidden" onClick={onMenu} aria-label="Open menu">
          <Menu className="size-5" />
        </button>
        <div className="min-w-0">
          <h1 className="truncate text-lg font-semibold tracking-tight text-slate-900">{title}</h1>
          <p className="hidden truncate text-xs text-slate-500 sm:block">{subtitle}</p>
        </div>
      </div>
      {admin && (
        <div className="flex items-center gap-3">
          <div className="hidden text-right sm:block">
            <p className="text-sm font-medium text-slate-900">{admin.username}</p>
            <p className="text-xs capitalize text-slate-500">{admin.role}</p>
          </div>
          <div className="flex size-10 items-center justify-center rounded-full bg-[#e8d9c0] text-sm font-semibold uppercase text-[#6b4f1d] ring-2 ring-white" aria-hidden>
            {admin.username.slice(0, 2)}
          </div>
        </div>
      )}
    </header>
  )
}
