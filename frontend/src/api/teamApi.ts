import { api } from './axiosInstance'
import type { ApiEnvelope, TeamMember, TeamMemberCreate } from '@/types/api'

export const teamApi = {
  list: async () => (await api.get<ApiEnvelope<TeamMember[]>>('/api/team')).data.data,
  create: async (body: TeamMemberCreate) => (await api.post<ApiEnvelope<TeamMember>>('/api/team', body)).data.data,
  update: async (id: number, body: { is_active?: boolean; role?: 'admin' | 'agent' }) =>
    (await api.put<ApiEnvelope<TeamMember>>(`/api/team/${id}`, body)).data.data,
}
