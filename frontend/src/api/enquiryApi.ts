import { api, publicApi } from './axiosInstance'
import type {
  AiResponse, ApiEnvelope, Communication, Enquiry, EnquiryCreate, EnquiryDetail, EnquiryFilters, EnquiryStatus, Paginated, WhatsAppResult,
} from '@/types/api'

/** Drop empty filter values so they are not sent as `?search=`. */
const clean = <T extends object>(params: T) =>
  Object.fromEntries(Object.entries(params).filter(([, v]) => v !== undefined && v !== '' && v !== null))

export const enquiryApi = {
  list: async (filters: EnquiryFilters) =>
    (await api.get<Paginated<Enquiry>>('/api/enquiries', { params: clean(filters) })).data,
  get: async (id: number) => (await api.get<ApiEnvelope<EnquiryDetail>>(`/api/enquiries/${id}`)).data.data,
  create: async (body: EnquiryCreate) => (await api.post<ApiEnvelope<Enquiry>>('/api/enquiries', body)).data.data,
  /** Public endpoint used by the customer site (no login). Only the id is shown back to the customer. */
  createPublic: async (body: EnquiryCreate) =>
    (await publicApi.post<ApiEnvelope<Enquiry>>('/api/enquiries', body)).data.data,
  updateStatus: async (id: number, status: EnquiryStatus) =>
    (await api.put<ApiEnvelope<Enquiry>>(`/api/enquiries/${id}/status`, { status })).data.data,
  reanalyze: async (id: number) => (await api.post<ApiEnvelope<Enquiry>>(`/api/enquiries/${id}/reanalyze`)).data.data,
  updateResponse: async (id: number, edited_response: string) =>
    (await api.put<ApiEnvelope<AiResponse>>(`/api/enquiries/${id}/response`, { edited_response })).data.data,
  /** The export endpoint is protected, so it is fetched with the auth header and saved as a Blob. */
  exportFile: async (format: 'csv' | 'xlsx', filters: Omit<EnquiryFilters, 'page' | 'page_size'>) =>
    (await api.get<Blob>('/api/enquiries/export', { params: { ...clean(filters), format }, responseType: 'blob' })).data,
  assign: async (id: number, assignee_id: number | null) =>
    (await api.put<ApiEnvelope<Enquiry>>(`/api/enquiries/${id}/assignee`, { assignee_id })).data.data,
  autoAssign: async (id: number) => (await api.post<ApiEnvelope<Enquiry>>(`/api/enquiries/${id}/auto-assign`)).data.data,
  sendEmail: async (id: number, body: { subject?: string; body?: string } = {}) =>
    (await api.post<ApiEnvelope<Communication>>(`/api/enquiries/${id}/send-email`, body)).data.data,
  whatsapp: async (id: number, text?: string) =>
    (await api.post<ApiEnvelope<WhatsAppResult>>(`/api/enquiries/${id}/whatsapp`, { text })).data.data,
}
