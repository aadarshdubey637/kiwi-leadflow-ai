import axios, { AxiosError } from 'axios'
import { AUTH_EXPIRED_EVENT, tokenStore } from '@/auth/tokenStore'

export const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL as string | undefined)?.replace(/\/$/, '') ?? 'http://127.0.0.1:8000'

/** A user-presentable error. `message` is always safe to show; raw technical details never reach the UI. */
export class ApiError extends Error {
  status: number
  code: string
  fieldErrors: Record<string, string>
  constructor(message: string, status: number, code: string, fieldErrors: Record<string, string> = {}) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.code = code
    this.fieldErrors = fieldErrors
  }
}

interface BackendError {
  success: false
  error: { code: string; message: string; details?: { field: string; message: string }[] | null }
}

function toApiError(err: unknown): ApiError {
  if (!axios.isAxiosError(err)) return new ApiError('Something unexpected happened. Please try again.', 0, 'unknown')
  const e = err as AxiosError<BackendError>

  if (!e.response) {
    if (e.code === 'ECONNABORTED') return new ApiError('The server took too long to respond. Please try again.', 0, 'timeout')
    return new ApiError('Cannot reach the server. Check your connection and that the backend is running.', 0, 'network')
  }

  const { status, data } = e.response
  const body = data?.error
  const fieldErrors: Record<string, string> = {}
  body?.details?.forEach((d) => {
    if (d.field && !fieldErrors[d.field]) fieldErrors[d.field] = d.message
  })

  // The backend's own messages are written for humans (e.g. "Invalid username or password"), so we show them
  // for client errors. Server errors get a generic message instead of internals.
  if (status === 401) return new ApiError(body?.message && body.code === 'invalid_credentials' ? body.message : 'Your session has expired. Please sign in again.', 401, body?.code ?? 'unauthorized')
  if (status === 422) {
    const first = Object.values(fieldErrors)[0]
    return new ApiError(first ? `Please check your input: ${first}` : 'Please check the information you entered.', 422, 'validation_error', fieldErrors)
  }
  if (status === 403) return new ApiError('You do not have permission to do that.', 403, 'forbidden')
  if (status === 409 && body?.message) return new ApiError(body.message, 409, body.code ?? 'conflict')
  if (status === 429) return new ApiError('Too many requests. Please wait a moment and try again.', 429, 'rate_limited')
  if (status === 502) return new ApiError('The AI service is unavailable right now. The enquiry is saved and can be retried.', 502, body?.code ?? 'ai_failed')
  if (status >= 500) return new ApiError('The server ran into a problem. Please try again shortly.', status, 'server_error')
  return new ApiError(body?.message ?? 'The request could not be completed.', status, body?.code ?? 'error')
}

export const api = axios.create({ baseURL: API_BASE_URL, timeout: 30_000 })

api.interceptors.request.use((config) => {
  const token = tokenStore.get()
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

api.interceptors.response.use(
  (r) => r,
  (err) => {
    const apiErr = toApiError(err)
    // An expired/invalid token on a protected call -> drop it and tell the app to go to /login.
    // (Failed *login* attempts also return 401 but have code invalid_credentials and must not trigger this.)
    if (apiErr.status === 401 && apiErr.code !== 'invalid_credentials' && tokenStore.get()) {
      tokenStore.clear()
      window.dispatchEvent(new Event(AUTH_EXPIRED_EVENT))
    }
    return Promise.reject(apiErr)
  },
)

/** Client for the public customer site: same error mapping, never attaches an admin token. */
export const publicApi = axios.create({ baseURL: API_BASE_URL, timeout: 30_000 })
publicApi.interceptors.response.use((r) => r, (err) => Promise.reject(toApiError(err)))

export const errorMessage = (e: unknown): string =>
  e instanceof ApiError ? e.message : 'Something unexpected happened. Please try again.'
