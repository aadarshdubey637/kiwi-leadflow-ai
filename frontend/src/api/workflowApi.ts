import { api } from './axiosInstance'
import type { ApiEnvelope, Paginated, WorkflowLog } from '@/types/api'

export interface WorkflowFilters {
  page?: number
  page_size?: number
  status?: WorkflowLog['execution_status']
  step?: string
}

export const workflowApi = {
  timeline: async (enquiryId: number) =>
    (await api.get<ApiEnvelope<WorkflowLog[]>>(`/api/workflows/${enquiryId}`)).data.data,
  list: async (filters: WorkflowFilters) =>
    (await api.get<Paginated<WorkflowLog>>('/api/workflows', {
      params: Object.fromEntries(Object.entries(filters).filter(([, v]) => v !== undefined && v !== '')),
    })).data,
}
