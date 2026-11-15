import { api } from './axiosInstance'
import type { AIUsageStats, ApiEnvelope, PerformanceStats } from '@/types/api'

export const monitoringApi = {
  aiUsage: async () => (await api.get<ApiEnvelope<AIUsageStats>>('/api/monitoring/ai-usage')).data.data,
  performance: async () => (await api.get<ApiEnvelope<PerformanceStats>>('/api/monitoring/performance')).data.data,
}
