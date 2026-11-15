// Types mirror the backend's Pydantic schemas exactly (backend/app/schemas/*). Do not invent fields here.

export interface ApiEnvelope<T> {
  success: true
  data: T
}
export interface PageMeta {
  page: number
  page_size: number
  total: number
  total_pages: number
}
export interface Paginated<T> {
  success: true
  data: T[]
  meta: PageMeta
}

export const ENQUIRY_STATUSES = ['New', 'In Progress', 'Converted', 'Closed'] as const
export type EnquiryStatus = (typeof ENQUIRY_STATUSES)[number]

export const PRIORITIES = ['Low', 'Medium', 'High'] as const
export type Priority = (typeof PRIORITIES)[number]

export const TEMPERATURES = ['Hot', 'Warm', 'Cold'] as const
export type Temperature = (typeof TEMPERATURES)[number]

export type AiStatus = 'pending' | 'processing' | 'completed' | 'failed'

export const SERVICE_CATEGORIES = [
  'Website Development',
  'Mobile Application Development',
  'AI Software Development',
  'Digital Marketing',
  'E-commerce Development',
  'Custom Software Development',
  'Other Services',
] as const
export type ServiceCategory = (typeof SERVICE_CATEGORIES)[number]

// ---------- auth ----------
export interface LoginRequest {
  username: string
  password: string
}
export interface TokenOut {
  access_token: string
  token_type: string
  expires_in: number
}
export interface Admin {
  id: number
  username: string
  email: string
  role: string
  created_at: string
}

// ---------- enquiries ----------
export interface EnquiryCreate {
  customer_name: string
  phone?: string | null
  email?: string | null
  message: string
  source?: string
}

export interface Enquiry {
  id: number
  customer_name: string
  phone: string | null
  email: string | null
  message: string
  source: string
  status: EnquiryStatus
  ai_status: AiStatus
  priority: Priority | null
  priority_reason: string | null
  needs_manual_review: boolean
  duplicate_of_id: number | null
  duplicate_reason: string | null
  assigned_to_id: number | null
  assigned_to_name: string | null
  summary: string | null
  service_category: ServiceCategory | null
  lead_score_total: number | null
  lead_temperature: Temperature | null
  created_at: string
  updated_at: string
}

export interface Analysis {
  service_category: ServiceCategory
  customer_location: string | null
  budget: number | null
  currency: string | null
  urgency: Priority | null
  project_timeline: string | null
  project_requirements: string[]
  missing_information: string[]
  summary: string | null
  customer_intent: string | null
  sentiment: 'Positive' | 'Neutral' | 'Negative' | null
  detected_language: string | null
  confidence_score: number | null
  created_at: string
}

export interface LeadScore {
  total_score: number
  budget_score: number
  requirement_clarity_score: number
  urgency_score: number
  service_relevance_score: number
  engagement_score: number
  lead_temperature: Temperature
  scoring_explanation: string | null
  created_at: string
}

export interface AiResponse {
  generated_response: string
  edited_response: string | null
  final_response: string
  followup_questions: string[]
  created_at: string
  updated_at: string
}

export interface FollowUp {
  id: number
  suggested_action: string
  suggested_date: string | null
  status: string
  created_at: string
}

export interface EnquiryDetail extends Enquiry {
  analysis: Analysis | null
  lead_score: LeadScore | null
  response: AiResponse | null
  followups: FollowUp[]
  communications: Communication[]
}

export interface EnquiryFilters {
  page?: number
  page_size?: number
  search?: string
  status?: EnquiryStatus
  priority?: Priority
  category?: ServiceCategory
  temperature?: Temperature
  ai_status?: AiStatus
  date_from?: string
  date_to?: string
  assignee_id?: number
  unassigned?: boolean
}

// ---------- dashboard / analytics ----------
export interface DashboardStats {
  total_enquiries: number
  new_enquiries: number
  high_priority_enquiries: number
  in_progress_enquiries: number
  converted_enquiries: number
  closed_enquiries: number
  needs_manual_review: number
  ai_failed: number
}
export interface CountItem {
  label: string
  count: number
  percentage: number
}
export interface LeadDistribution {
  hot: number
  warm: number
  cold: number
  unscored: number
  average_score: number | null
  score_buckets: CountItem[]
}
export interface ConversionStats {
  total_enquiries: number
  converted: number
  closed: number
  open: number
  conversion_rate: number
  by_temperature: { temperature: Temperature; enquiries: number; converted: number; conversion_rate: number }[]
}
export interface FunnelStage {
  stage: string
  count: number
  percentage_of_total: number
}
export interface TrendPoint {
  period: string
  count: number
}
export type TrendPeriod = 'daily' | 'weekly' | 'monthly'
export interface PipelineValue {
  note: string
  by_currency: { currency: string; enquiries: number; estimated_pipeline_value: number }[]
  open_enquiries_without_budget: number
}

// ---------- workflow / monitoring ----------
export interface WorkflowLog {
  id: number
  enquiry_id: number
  workflow_step: string
  execution_status: 'started' | 'success' | 'failed' | 'skipped'
  message: string | null
  execution_time: number | null
  created_at: string
}
export interface ProviderUsage {
  provider: string
  model_name: string
  requests: number
  successful: number
  failed: number
  input_tokens: number
  output_tokens: number
  estimated_cost_usd: number
  average_response_time: number
}
export interface AIUsageStats {
  total_requests: number
  successful_requests: number
  failed_requests: number
  retry_count: number
  input_tokens: number
  output_tokens: number
  estimated_cost_usd: number
  average_response_time: number
  cost_note: string
  by_provider: ProviderUsage[]
}
export interface PerformanceStats {
  ai_success_rate: number
  average_latency_seconds: number
  p95_latency_seconds: number
  workflows_completed: number
  workflows_failed: number
  workflow_success_rate: number
  average_workflow_seconds: number
  latency_by_provider: { provider: string; requests: number; average: number; p95: number }[]
}

// ---------- team, communications, reminders, capabilities ----------
export interface TeamMember {
  id: number
  username: string
  email: string
  role: 'admin' | 'agent'
  is_active: boolean
  open_enquiries: number
  total_assigned: number
  created_at: string
}
export interface TeamMemberCreate {
  username: string
  email: string
  password: string
  role: 'admin' | 'agent'
}
export interface Communication {
  id: number
  channel: 'email' | 'whatsapp'
  kind: 'customer_reply' | 'team_notification'
  recipient: string
  subject: string | null
  body: string | null
  status: 'sent' | 'failed' | 'opened' | 'skipped'
  error: string | null
  sent_by_name: string | null
  created_at: string
}
export interface WhatsAppResult {
  link: string
  communication: Communication
}
export interface Capabilities {
  email_enabled: boolean
  whatsapp_enabled: boolean
  default_country_code: string
}
export type FollowUpStatus = 'Pending' | 'Done' | 'Dismissed'
export interface FollowUpItem {
  id: number
  enquiry_id: number
  customer_name: string
  enquiry_priority: Priority | null
  lead_temperature: Temperature | null
  assigned_to_name: string | null
  suggested_action: string
  suggested_date: string | null
  status: FollowUpStatus
  is_overdue: boolean
  created_at: string
}
export interface FollowUpSummary {
  pending: number
  overdue: number
  due_today: number
  done: number
}
export interface FollowUpFilters {
  page?: number
  page_size?: number
  status?: FollowUpStatus
  overdue?: boolean
  assignee_id?: number
  unassigned?: boolean
}
