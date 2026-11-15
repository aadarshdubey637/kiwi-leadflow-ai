import { api } from './axiosInstance'
import type { ApiEnvelope, CountItem, DashboardStats } from '@/types/api'

export const dashboardApi = {
  stats: async () => (await api.get<ApiEnvelope<DashboardStats>>('/api/dashboard/stats')).data.data,
  categories: async () => (await api.get<ApiEnvelope<CountItem[]>>('/api/dashboard/categories')).data.data,
  priorities: async () => (await api.get<ApiEnvelope<CountItem[]>>('/api/dashboard/priorities')).data.data,
}
