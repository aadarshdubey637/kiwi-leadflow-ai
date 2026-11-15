import { api } from './axiosInstance'
import type { ApiEnvelope, FollowUpFilters, FollowUpItem, FollowUpStatus, FollowUpSummary, Paginated } from '@/types/api'

export const followupApi = {
  list: async (filters: FollowUpFilters) =>
    (await api.get<Paginated<FollowUpItem>>('/api/followups', {
      params: Object.fromEntries(Object.entries(filters).filter(([, v]) => v !== undefined && v !== '' && v !== false)),
    })).data,
  summary: async () => (await api.get<ApiEnvelope<FollowUpSummary>>('/api/followups/summary')).data.data,
  update: async (id: number, status: FollowUpStatus) =>
    (await api.put<ApiEnvelope<FollowUpSummary>>(`/api/followups/${id}`, { status })).data.data,
}
