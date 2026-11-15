import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom'
import { AlertCircle, ArrowLeft, Eye, EyeOff } from 'lucide-react'
import { errorMessage } from '@/api/axiosInstance'
import { useAuth } from '@/auth/AuthContext'
import { Backdrop } from '@/components/ui/Backdrop'
import { Button } from '@/components/ui/Button'
import { LogoMark } from '@/components/ui/Logo'

// The backend authenticates with a USERNAME (not an email): POST /api/auth/login {username, password}.
const schema = z.object({
  username: z.string().trim().min(1, 'Please enter your username').max(50, 'Username is too long'),
  password: z.string().min(1, 'Please enter your password').max(200, 'Password is too long'),
})
type FormValues = z.infer<typeof schema>

export default function LoginPage() {
  const { status, login } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const from = (location.state as { from?: string } | null)?.from ?? '/admin'
  const [serverError, setServerError] = useState<string | null>(null)
  const [showPassword, setShowPassword] = useState(false)

  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm<FormValues>({ resolver: zodResolver(schema) })

  if (status === 'authenticated') return <Navigate to={from} replace />

  const onSubmit = async (values: FormValues) => {
    setServerError(null)
    try {
      await login(values.username, values.password)
      navigate(from, { replace: true })
    } catch (e) {
      setServerError(errorMessage(e))
    }
  }

  const input = (invalid: boolean) =>
    `mt-1.5 w-full rounded-lg border bg-white/75 px-3.5 py-2.5 text-sm text-slate-900 placeholder:text-slate-400 backdrop-blur focus:outline-none focus:ring-2 ${
      invalid ? 'border-red-400 focus:ring-red-500/20' : 'border-slate-300/80 focus:border-brand-500 focus:ring-brand-500/20'
    }`

  return (
    <div className="grid min-h-screen lg:grid-cols-5">
      <Backdrop />

      {/* left: deep teal panel */}
      <div className="relative hidden flex-col justify-between overflow-hidden bg-[#14302e] p-12 text-[#e9f0ed] lg:col-span-2 lg:flex">
        <div aria-hidden className="absolute -bottom-24 -left-24 size-80 rounded-full bg-[#1d7069]/50" />
        <div aria-hidden className="absolute -right-16 top-1/3 size-56 rounded-full bg-[#d9962b]/15" />
        <Link to="/" className="relative flex items-center gap-3">
          <LogoMark className="size-10" />
          <span className="leading-tight">
            <span className="block text-lg font-semibold text-[#f4efe7]">LeadFlow</span>
            <span className="block text-xs text-[#8fa9a3]">Kiwi Connect Digital</span>
          </span>
        </Link>
        <div className="relative">
          <h2 className="font-serif text-4xl leading-tight text-[#f4efe7]">Welcome back.</h2>
          <p className="mt-4 max-w-sm leading-relaxed text-[#b4c7c2]">
            See what came in, how each lead was scored, and which ones need a reply first.
          </p>
        </div>
        <p className="relative text-xs text-[#6f8c86]">Admin console · authorised staff only</p>
      </div>

      {/* right: form */}
      <div className="relative flex items-center justify-center p-6 lg:col-span-3">
        <Link to="/" className="absolute left-6 top-6 inline-flex items-center gap-1.5 text-sm text-slate-600 hover:text-slate-900">
          <ArrowLeft className="size-4" aria-hidden /> Back to website
        </Link>
        <form onSubmit={handleSubmit(onSubmit)} noValidate className="glass-strong w-full max-w-sm rounded-3xl p-8">
          <div className="mb-6 flex items-center gap-3 lg:hidden">
            <LogoMark className="size-9" />
            <span className="text-lg font-semibold">LeadFlow</span>
          </div>
          <h1 className="font-serif text-3xl text-slate-900">Sign in</h1>
          <p className="mt-1 text-sm text-slate-500">Use your administrator account.</p>

          {serverError && (
            <div role="alert" className="mt-6 flex items-start gap-2 rounded-lg border border-red-200 bg-red-50/80 p-3 text-sm text-red-800">
              <AlertCircle className="mt-0.5 size-4 shrink-0" aria-hidden /> {serverError}
            </div>
          )}

          <div className="mt-6">
            <label htmlFor="username" className="text-sm font-medium text-slate-700">Username</label>
            <input id="username" autoComplete="username" autoFocus placeholder="admin" aria-invalid={!!errors.username}
              className={input(!!errors.username)} {...register('username')} />
            {errors.username && <p className="mt-1 text-xs text-red-700">{errors.username.message}</p>}
          </div>

          <div className="mt-4">
            <label htmlFor="password" className="text-sm font-medium text-slate-700">Password</label>
            <div className="relative">
              <input id="password" type={showPassword ? 'text' : 'password'} autoComplete="current-password" placeholder="••••••••"
                aria-invalid={!!errors.password} className={input(!!errors.password) + ' pr-10'} {...register('password')} />
              <button type="button" onClick={() => setShowPassword((s) => !s)} aria-label={showPassword ? 'Hide password' : 'Show password'}
                className="absolute right-2.5 top-1/2 mt-0.5 -translate-y-1/2 text-slate-400 hover:text-slate-600">
                {showPassword ? <EyeOff className="size-4" /> : <Eye className="size-4" />}
              </button>
            </div>
            {errors.password && <p className="mt-1 text-xs text-red-700">{errors.password.message}</p>}
          </div>

          <Button type="submit" className="mt-7 w-full py-2.5" loading={isSubmitting}>Sign in</Button>
        </form>
      </div>
    </div>
  )
}
