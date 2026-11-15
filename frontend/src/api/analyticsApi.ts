import { api } from './axiosInstance'
import type {
  ApiEnvelope, ConversionStats, FunnelStage, LeadDistribution, PipelineValue, TrendPeriod, TrendPoint,
} from '@/types/api'

export const analyticsApi = {
  leads: async () => (await api.get<ApiEnvelope<LeadDistribution>>('/api/analytics/leads')).data.data,
  conversion: async () => (await api.get<ApiEnvelope<ConversionStats>>('/api/analytics/conversion')).data.data,
  funnel: async () => (await api.get<ApiEnvelope<FunnelStage[]>>('/api/analytics/funnel')).data.data,
  pipeline: async () => (await api.get<ApiEnvelope<PipelineValue>>('/api/analytics/pipeline')).data.data,
  trends: async (period: TrendPeriod, days: number) =>
    (await api.get<ApiEnvelope<TrendPoint[]>>('/api/analytics/trends', { params: { period, days } })).data.data,
}
