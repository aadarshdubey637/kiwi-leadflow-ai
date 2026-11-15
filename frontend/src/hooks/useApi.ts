import { keepPreviousData, useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { analyticsApi } from '@/api/analyticsApi'
import { errorMessage } from '@/api/axiosInstance'
import { dashboardApi } from '@/api/dashboardApi'
import { enquiryApi } from '@/api/enquiryApi'
import { followupApi } from '@/api/followupApi'
import { monitoringApi } from '@/api/monitoringApi'
import { systemApi } from '@/api/systemApi'
import { teamApi } from '@/api/teamApi'
import { workflowApi, type WorkflowFilters } from '@/api/workflowApi'
import type {
  Enquiry, EnquiryCreate, EnquiryFilters, EnquiryStatus, FollowUpFilters, FollowUpStatus, TeamMemberCreate, TrendPeriod,
} from '@/types/api'

const POLL_MS = 3000
const isAiActive = (e?: Pick<Enquiry, 'ai_status'>) => e?.ai_status === 'pending' || e?.ai_status === 'processing'

// ---------- dashboard / analytics ----------
export const useStats = () => useQuery({ queryKey: ['stats'], queryFn: dashboardApi.stats })
export const useCategories = () => useQuery({ queryKey: ['categories'], queryFn: dashboardApi.categories })
export const usePriorities = () => useQuery({ queryKey: ['priorities'], queryFn: dashboardApi.priorities })
export const useLeadDistribution = () => useQuery({ queryKey: ['leads'], queryFn: analyticsApi.leads })
export const useConversion = () => useQuery({ queryKey: ['conversion'], queryFn: analyticsApi.conversion })
export const useFunnel = () => useQuery({ queryKey: ['funnel'], queryFn: analyticsApi.funnel })
export const usePipeline = () => useQuery({ queryKey: ['pipeline'], queryFn: analyticsApi.pipeline })
export const useTrends = (period: TrendPeriod, days: number) =>
  useQuery({ queryKey: ['trends', period, days], queryFn: () => analyticsApi.trends(period, days), placeholderData: keepPreviousData })

// ---------- monitoring ----------
export const useAiUsage = () => useQuery({ queryKey: ['ai-usage'], queryFn: monitoringApi.aiUsage })
export const usePerformance = () => useQuery({ queryKey: ['performance'], queryFn: monitoringApi.performance })

// ---------- enquiries ----------
export const useEnquiries = (filters: EnquiryFilters) =>
  useQuery({
    queryKey: ['enquiries', filters],
    queryFn: () => enquiryApi.list(filters),
    placeholderData: keepPreviousData,
    // keep refreshing while any visible row is still being analysed by the AI
    refetchInterval: (q) => (q.state.data?.data.some(isAiActive) ? POLL_MS : false),
  })

export const useEnquiry = (id: number) =>
  useQuery({
    queryKey: ['enquiry', id],
    queryFn: () => enquiryApi.get(id),
    refetchInterval: (q) => (isAiActive(q.state.data) ? POLL_MS : false),
  })

export const useWorkflowTimeline = (id: number | null) =>
  useQuery({
    queryKey: ['workflow', id],
    queryFn: () => workflowApi.timeline(id as number),
    enabled: id !== null,
    refetchInterval: (q) => {
      const last = q.state.data?.at(-1)?.workflow_step
      return last && !['workflow_completed', 'workflow_failed'].includes(last) ? POLL_MS : false
    },
  })

export const useWorkflowLogs = (filters: WorkflowFilters) =>
  useQuery({ queryKey: ['workflow-logs', filters], queryFn: () => workflowApi.list(filters), placeholderData: keepPreviousData })

/** Everything derived from enquiries must refresh after any change to them. */
function useInvalidateAll() {
  const qc = useQueryClient()
  return () => {
    for (const key of ['enquiries', 'enquiry', 'stats', 'categories', 'priorities', 'leads', 'conversion', 'funnel', 'pipeline', 'trends', 'workflow', 'workflow-logs', 'ai-usage', 'performance', 'team', 'followups', 'followup-summary']) {
      qc.invalidateQueries({ queryKey: [key] })
    }
  }
}

export function useCreateEnquiry() {
  const invalidate = useInvalidateAll()
  return useMutation({
    mutationFn: (body: EnquiryCreate) => enquiryApi.create(body),
    onSuccess: invalidate,
    onError: (e) => toast.error(errorMessage(e)),
  })
}

/** Customer-site submission: public endpoint, no admin data to invalidate. */
export function usePublicCreateEnquiry() {
  return useMutation({
    mutationFn: (body: EnquiryCreate) => enquiryApi.createPublic(body),
    onError: (e) => toast.error(errorMessage(e)),
  })
}

export function useUpdateStatus() {
  const invalidate = useInvalidateAll()
  return useMutation({
    mutationFn: ({ id, status }: { id: number; status: EnquiryStatus }) => enquiryApi.updateStatus(id, status),
    onSuccess: (e) => { invalidate(); toast.success(`Status updated to ${e.status}`) },
    onError: (e) => toast.error(errorMessage(e)),
  })
}

export function useReanalyze() {
  const invalidate = useInvalidateAll()
  return useMutation({
    mutationFn: (id: number) => enquiryApi.reanalyze(id),
    onSuccess: () => { invalidate(); toast.success('AI analysis restarted') },
    onError: (e) => toast.error(errorMessage(e)),
  })
}

export function useUpdateResponse() {
  const invalidate = useInvalidateAll()
  return useMutation({
    mutationFn: ({ id, text }: { id: number; text: string }) => enquiryApi.updateResponse(id, text),
    onSuccess: () => { invalidate(); toast.success('Response saved') },
    onError: (e) => toast.error(errorMessage(e)),
  })
}

// ---------- team ----------
export const useTeam = () => useQuery({ queryKey: ['team'], queryFn: teamApi.list, staleTime: 30_000 })

export function useCreateMember() {
  const invalidate = useInvalidateAll()
  return useMutation({
    mutationFn: (body: TeamMemberCreate) => teamApi.create(body),
    onSuccess: (m) => { invalidate(); toast.success(`${m.username} added to the team`) },
    onError: (e) => toast.error(errorMessage(e)),
  })
}

export function useUpdateMember() {
  const invalidate = useInvalidateAll()
  return useMutation({
    mutationFn: ({ id, ...body }: { id: number; is_active?: boolean; role?: 'admin' | 'agent' }) => teamApi.update(id, body),
    onSuccess: (m) => { invalidate(); toast.success(m.is_active ? `${m.username} is active` : `${m.username} paused: no new assignments`) },
    onError: (e) => toast.error(errorMessage(e)),
  })
}

export function useAssign() {
  const invalidate = useInvalidateAll()
  return useMutation({
    mutationFn: ({ id, assigneeId }: { id: number; assigneeId: number | null }) => enquiryApi.assign(id, assigneeId),
    onSuccess: (e) => { invalidate(); toast.success(e.assigned_to_name ? `Assigned to ${e.assigned_to_name}` : 'Enquiry unassigned') },
    onError: (e) => toast.error(errorMessage(e)),
  })
}

export function useAutoAssign() {
  const invalidate = useInvalidateAll()
  return useMutation({
    mutationFn: (id: number) => enquiryApi.autoAssign(id),
    onSuccess: (e) => { invalidate(); toast.success(e.assigned_to_name ? `Auto-assigned to ${e.assigned_to_name}` : 'No active team member available') },
    onError: (e) => toast.error(errorMessage(e)),
  })
}

// ---------- follow-up reminders ----------
export const useFollowups = (filters: FollowUpFilters) =>
  useQuery({ queryKey: ['followups', filters], queryFn: () => followupApi.list(filters), placeholderData: keepPreviousData })
export const useFollowupSummary = () => useQuery({ queryKey: ['followup-summary'], queryFn: followupApi.summary, refetchInterval: 60_000 })

export function useUpdateFollowup() {
  const invalidate = useInvalidateAll()
  return useMutation({
    mutationFn: ({ id, status }: { id: number; status: FollowUpStatus }) => followupApi.update(id, status),
    onSuccess: (_s, v) => { invalidate(); toast.success(v.status === 'Done' ? 'Marked as done' : v.status === 'Dismissed' ? 'Dismissed' : 'Reopened') },
    onError: (e) => toast.error(errorMessage(e)),
  })
}

// ---------- messaging ----------
export const useCapabilities = () => useQuery({ queryKey: ['capabilities'], queryFn: systemApi.capabilities, staleTime: 5 * 60_000 })

export function useSendEmail() {
  const invalidate = useInvalidateAll()
  return useMutation({
    mutationFn: ({ id, body }: { id: number; body?: string }) => enquiryApi.sendEmail(id, { body }),
    onSuccess: (c) => { invalidate(); toast.success(`Email sent to ${c.recipient}`) },
    onError: (e) => { invalidate(); toast.error(errorMessage(e)) }, // a failed attempt is logged too, so refresh the history
  })
}

export function useWhatsApp() {
  const invalidate = useInvalidateAll()
  return useMutation({
    mutationFn: ({ id, text }: { id: number; text?: string }) => enquiryApi.whatsapp(id, text),
    onSuccess: () => invalidate(),
    onError: (e) => toast.error(errorMessage(e)),
  })
}
