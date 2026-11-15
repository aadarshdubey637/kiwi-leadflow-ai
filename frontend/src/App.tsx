import { lazy } from 'react'
import { Navigate, Route, Routes } from 'react-router-dom'
import { ProtectedRoute } from '@/auth/ProtectedRoute'
import { AppLayout } from '@/components/layout/AppLayout'
import LoginPage from '@/pages/LoginPage'

// Pages are code-split so the heavy chart library only loads when a chart page is opened.
const LandingPage = lazy(() => import('@/pages/LandingPage'))
const OverviewPage = lazy(() => import('@/pages/OverviewPage'))
const EnquiriesPage = lazy(() => import('@/pages/EnquiriesPage'))
const AddEnquiryPage = lazy(() => import('@/pages/AddEnquiryPage'))
const EnquiryDetailPage = lazy(() => import('@/pages/EnquiryDetailPage'))
const IntelligencePage = lazy(() => import('@/pages/IntelligencePage'))
const WorkflowPage = lazy(() => import('@/pages/WorkflowPage'))
const AnalyticsPage = lazy(() => import('@/pages/AnalyticsPage'))
const MonitoringPage = lazy(() => import('@/pages/MonitoringPage'))
const FollowUpsPage = lazy(() => import('@/pages/FollowUpsPage'))
const TeamPage = lazy(() => import('@/pages/TeamPage'))

/**
 * Two panels:
 *   /          public customer site (submit an enquiry — no login)
 *   /admin/*   admin console (JWT-protected)
 */
export default function App() {
  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route path="/login" element={<Navigate to="/admin/login" replace />} />
      <Route path="/admin/login" element={<LoginPage />} />
      <Route path="/admin" element={<ProtectedRoute />}>
        <Route element={<AppLayout />}>
          <Route index element={<OverviewPage />} />
          <Route path="enquiries" element={<EnquiriesPage />} />
          <Route path="enquiries/new" element={<AddEnquiryPage />} />
          <Route path="enquiries/:id" element={<EnquiryDetailPage />} />
          <Route path="intelligence" element={<IntelligencePage />} />
          <Route path="followups" element={<FollowUpsPage />} />
          <Route path="team" element={<TeamPage />} />
          <Route path="workflows" element={<WorkflowPage />} />
          <Route path="workflows/:id" element={<WorkflowPage />} />
          <Route path="analytics" element={<AnalyticsPage />} />
          <Route path="monitoring" element={<MonitoringPage />} />
        </Route>
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
