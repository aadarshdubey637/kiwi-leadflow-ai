import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { LoadingSpinner } from '@/components/ui/States'
import { useAuth } from './AuthContext'

/** Client-side gate for a better UX. Real authorization is enforced by the backend on every API call. */
export function ProtectedRoute() {
  const { status } = useAuth()
  const location = useLocation()
  if (status === 'loading') return <div className="flex h-full items-center justify-center"><LoadingSpinner label="Checking session…" /></div>
  if (status === 'anonymous') return <Navigate to="/admin/login" replace state={{ from: location.pathname + location.search }} />
  return <Outlet />
}
