import { Link, NavLink, useLocation } from 'react-router-dom'
import {
  BarChart3, CalendarCheck, Gauge, Globe, History, Inbox, LayoutGrid, LogOut, Plus, Target, UsersRound, X,
} from 'lucide-react'
import { LogoMark } from '@/components/ui/Logo'
import { useFollowupSummary } from '@/hooks/useApi'
import { cn } from '@/utils/format'

const NAV = [
  { to: '/admin', label: 'Overview', icon: LayoutGrid, match: (p: string) => p === '/admin' || p === '/admin/' },
  { to: '/admin/enquiries', label: 'Enquiries', icon: Inbox, match: (p: string) => p.startsWith('/admin/enquiries') && p !== '/admin/enquiries/new' },
  { to: '/admin/enquiries/new', label: 'Add Enquiry', icon: Plus, match: (p: string) => p === '/admin/enquiries/new' },
  { to: '/admin/followups', label: 'Follow-ups', icon: CalendarCheck, match: (p: string) => p.startsWith('/admin/followups'), badge: true },
  { to: '/admin/team', label: 'Team', icon: UsersRound, match: (p: string) => p.startsWith('/admin/team'), badge: false },
  { to: '/admin/intelligence', label: 'AI Intelligence', icon: Target, match: (p: string) => p.startsWith('/admin/intelligence') },
  { to: '/admin/workflows', label: 'Workflow History', icon: History, match: (p: string) => p.startsWith('/admin/workflows') },
  { to: '/admin/analytics', label: 'Analytics', icon: BarChart3, match: (p: string) => p.startsWith('/admin/analytics') },
  { to: '/admin/monitoring', label: 'AI Monitoring', icon: Gauge, match: (p: string) => p.startsWith('/admin/monitoring') },
]

interface Props {
  open: boolean // mobile drawer state
  onClose: () => void
  onLogout: () => void
}

export function Sidebar({ open, onClose, onLogout }: Props) {
  const { pathname } = useLocation()
  const overdue = useFollowupSummary().data?.overdue ?? 0

  const content = (
    <div className="flex h-full flex-col bg-[#14302e]/95 text-[#c9d6d2] ring-1 ring-white/10 backdrop-blur-xl">
      <div className="flex h-16 shrink-0 items-center justify-between px-5">
        <Link to="/admin" className="flex items-center gap-3">
          <LogoMark className="size-9" />
          <div className="leading-tight">
            <span className="block text-[15px] font-semibold tracking-tight text-[#f4efe7]">LeadFlow</span>
            <span className="block text-[11px] text-[#8fa9a3]">Kiwi Connect Digital</span>
          </div>
        </Link>
        <button className="rounded p-1 text-[#8fa9a3] hover:text-white lg:hidden" onClick={onClose} aria-label="Close menu">
          <X className="size-5" />
        </button>
      </div>

      <nav className="flex-1 space-y-0.5 overflow-y-auto px-3 py-3" aria-label="Main navigation">
        {NAV.map(({ to, label, icon: Icon, match, ...rest }) => {
          const active = match(pathname)
          return (
            <NavLink
              key={to}
              to={to}
              onClick={onClose}
              aria-current={active ? 'page' : undefined}
              className={cn(
                'flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors',
                active ? 'bg-white/10 text-white' : 'text-[#9db4ae] hover:bg-white/5 hover:text-white',
              )}
            >
              <Icon className={cn('size-[18px]', active && 'text-[#e0a56a]')} aria-hidden />
              {label}
              {'badge' in rest && rest.badge && overdue > 0 ? (
                <span className="ml-auto rounded-full bg-clay px-1.5 py-0.5 text-[10px] font-semibold leading-none text-white" aria-label={`${overdue} overdue`}>{overdue}</span>
              ) : (
                active && <span aria-hidden className="ml-auto size-1.5 rounded-full bg-[#e0a56a]" />
              )}
            </NavLink>
          )
        })}
      </nav>

      <div className="space-y-0.5 border-t border-white/10 p-3">
        <Link to="/" className="flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium text-[#9db4ae] transition-colors hover:bg-white/5 hover:text-white">
          <Globe className="size-[18px]" aria-hidden /> Customer site
        </Link>
        <button
          onClick={onLogout}
          className="flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium text-[#9db4ae] transition-colors hover:bg-white/5 hover:text-[#f0a58f]"
        >
          <LogOut className="size-[18px]" aria-hidden /> Logout
        </button>
      </div>
    </div>
  )

  return (
    <>
      {/* Desktop: floating panel */}
      <aside className="fixed bottom-4 left-4 top-4 z-30 hidden w-64 overflow-hidden rounded-2xl shadow-xl shadow-[#14302e]/20 lg:block">{content}</aside>
      {/* Mobile: slide-in drawer */}
      <div className={cn('fixed inset-0 z-40 lg:hidden', open ? 'visible' : 'invisible')} aria-hidden={!open}>
        <div className={cn('absolute inset-0 bg-[#14302e]/40 backdrop-blur-sm transition-opacity', open ? 'opacity-100' : 'opacity-0')} onClick={onClose} />
        <aside className={cn('absolute inset-y-3 left-3 w-64 overflow-hidden rounded-2xl transition-transform duration-300', open ? 'translate-x-0' : '-translate-x-[110%]')}>
          {content}
        </aside>
      </div>
    </>
  )
}
