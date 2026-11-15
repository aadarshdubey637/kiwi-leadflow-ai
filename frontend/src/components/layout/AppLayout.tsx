import { Suspense, useState } from 'react'
import { Outlet, useLocation } from 'react-router-dom'
import { useAuth } from '@/auth/AuthContext'
import { Backdrop } from '@/components/ui/Backdrop'
import { LoadingSpinner } from '@/components/ui/States'
import { Header } from './Header'
import { Sidebar } from './Sidebar'

export function AppLayout() {
  const [drawer, setDrawer] = useState(false)
  const { logout } = useAuth()
  const { pathname } = useLocation()

  return (
    <div className="min-h-screen">
      <Backdrop />
      <Sidebar open={drawer} onClose={() => setDrawer(false)} onLogout={logout} />
      <div className="lg:pl-72">
        <Header onMenu={() => setDrawer(true)} />
        <main className="mx-auto max-w-7xl p-4 pb-10 sm:p-6">
          {/* keyed by route: loading state and the entrance animation reset on every navigation */}
          <Suspense key={pathname} fallback={<LoadingSpinner />}>
            <div key={pathname} className="animate-fade-up">
              <Outlet />
            </div>
          </Suspense>
        </main>
      </div>
    </div>
  )
}
