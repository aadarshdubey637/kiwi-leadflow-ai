import { api } from './axiosInstance'
import type { ApiEnvelope, Capabilities } from '@/types/api'

export const systemApi = {
  capabilities: async () => (await api.get<ApiEnvelope<Capabilities>>('/api/system/capabilities')).data.data,
}
