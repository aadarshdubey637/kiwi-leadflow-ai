import { api } from './axiosInstance'
import type { Admin, ApiEnvelope, LoginRequest, TokenOut } from '@/types/api'

export const authApi = {
  login: async (body: LoginRequest) => (await api.post<ApiEnvelope<TokenOut>>('/api/auth/login', body)).data.data,
  me: async () => (await api.get<ApiEnvelope<Admin>>('/api/auth/me')).data.data,
}
