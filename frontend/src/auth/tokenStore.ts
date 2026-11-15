// The JWT lives in sessionStorage: it is cleared when the tab/browser closes and is not shared across tabs.
// (localStorage would survive restarts, which is convenient but leaves a long-lived token on disk.)
// The backend remains the real authority — it validates every request's token.
const KEY = 'leadflow.token'

export const tokenStore = {
  get: (): string | null => sessionStorage.getItem(KEY),
  set: (token: string) => sessionStorage.setItem(KEY, token),
  clear: () => sessionStorage.removeItem(KEY),
}

export const AUTH_EXPIRED_EVENT = 'leadflow:auth-expired'
