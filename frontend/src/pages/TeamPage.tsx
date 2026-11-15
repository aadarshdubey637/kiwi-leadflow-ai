import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Pause, Play, ShieldCheck, UserPlus } from 'lucide-react'
import { useAuth } from '@/auth/AuthContext'
import { Button } from '@/components/ui/Button'
import { Card, CardHeader } from '@/components/ui/Card'
import { ErrorMessage, LoadingSpinner } from '@/components/ui/States'
import { useCreateMember, useTeam, useUpdateMember } from '@/hooks/useApi'
import type { TeamMember } from '@/types/api'
import { cn } from '@/utils/format'

const schema = z.object({
  username: z.string().trim().min(3, 'At least 3 characters').max(50).regex(/^[A-Za-z0-9._-]+$/, 'Letters, numbers, dot, dash and underscore only'),
  email: z.string().trim().min(1, 'Enter an email address').email('That email address does not look right'),
  password: z.string().min(8, 'At least 8 characters').max(200),
  role: z.enum(['agent', 'admin']),
})
type Values = z.infer<typeof schema>

const input = (bad: boolean) =>
  `mt-1.5 w-full rounded-lg border bg-white/75 px-3.5 py-2.5 text-sm backdrop-blur focus:outline-none focus:ring-2 ${bad ? 'border-red-400 focus:ring-red-500/20' : 'border-slate-300/80 focus:border-brand-500 focus:ring-brand-500/20'}`

function AddMember() {
  const create = useCreateMember()
  const [open, setOpen] = useState(false)
  const { register, handleSubmit, reset, formState: { errors } } = useForm<Values>({ resolver: zodResolver(schema), defaultValues: { role: 'agent' } })
  if (!open) return <Button icon={<UserPlus className="size-4" />} onClick={() => setOpen(true)}>Add team member</Button>
  return (
    <Card className="w-full">
      <CardHeader title="New team member" description="They start receiving automatic assignments straight away." />
      <form noValidate className="grid gap-4 p-5 sm:grid-cols-2"
        onSubmit={handleSubmit((v) => create.mutate(v, { onSuccess: () => { reset({ role: 'agent' }); setOpen(false) } }))}>
        <div>
          <label htmlFor="m-username" className="text-sm font-medium text-slate-700">Username</label>
          <input id="m-username" autoComplete="off" className={input(!!errors.username)} {...register('username')} />
          {errors.username && <p className="mt-1 text-xs text-red-700">{errors.username.message}</p>}
        </div>
        <div>
          <label htmlFor="m-email" className="text-sm font-medium text-slate-700">Email</label>
          <input id="m-email" type="email" autoComplete="off" className={input(!!errors.email)} {...register('email')} />
          {errors.email && <p className="mt-1 text-xs text-red-700">{errors.email.message}</p>}
        </div>
        <div>
          <label htmlFor="m-password" className="text-sm font-medium text-slate-700">Temporary password</label>
          <input id="m-password" type="password" autoComplete="new-password" className={input(!!errors.password)} {...register('password')} />
          {errors.password && <p className="mt-1 text-xs text-red-700">{errors.password.message}</p>}
        </div>
        <div>
          <label htmlFor="m-role" className="text-sm font-medium text-slate-700">Role</label>
          <select id="m-role" className={input(false)} {...register('role')}>
            <option value="agent">Agent: works enquiries</option>
            <option value="admin">Admin: can also manage the team</option>
          </select>
        </div>
        <div className="flex justify-end gap-2 sm:col-span-2">
          <Button type="button" variant="ghost" onClick={() => setOpen(false)}>Cancel</Button>
          <Button type="submit" loading={create.isPending}>Add member</Button>
        </div>
      </form>
    </Card>
  )
}

function MemberRow({ m, canManage, isSelf, maxOpen }: { m: TeamMember; canManage: boolean; isSelf: boolean; maxOpen: number }) {
  const update = useUpdateMember()
  return (
    <li className={cn('flex flex-col gap-3 px-5 py-4 sm:flex-row sm:items-center', !m.is_active && 'opacity-60')}>
      <div className="flex min-w-0 flex-1 items-center gap-3">
        <div className="flex size-10 shrink-0 items-center justify-center rounded-full bg-[#e8d9c0] text-sm font-semibold uppercase text-[#6b4f1d]" aria-hidden>{m.username.slice(0, 2)}</div>
        <div className="min-w-0">
          <p className="flex flex-wrap items-center gap-2 text-sm font-medium text-slate-900">
            {m.username}
            {isSelf && <span className="text-xs font-normal text-slate-400">(you)</span>}
            <span className={cn('inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium', m.role === 'admin' ? 'bg-[#d9ece8] text-[#175a55]' : 'bg-[#ebe6dc] text-[#5b564b]')}>
              {m.role === 'admin' && <ShieldCheck className="size-3" aria-hidden />}{m.role}
            </span>
            {!m.is_active && <span className="rounded-full bg-[#f6e6c4] px-2 py-0.5 text-xs font-medium text-[#8f6410]">paused</span>}
          </p>
          <p className="truncate text-xs text-slate-500">{m.email}</p>
        </div>
      </div>

      <div className="w-full sm:w-56">
        <div className="flex items-baseline justify-between text-xs">
          <span className="text-slate-500">Open enquiries</span>
          <span className="font-semibold text-slate-900">{m.open_enquiries}<span className="ml-1 font-normal text-slate-400">of {m.total_assigned} total</span></span>
        </div>
        <div className="mt-1.5 h-2 overflow-hidden rounded-full bg-slate-200/70" role="progressbar" aria-label={`${m.username} open workload`} aria-valuenow={m.open_enquiries} aria-valuemin={0} aria-valuemax={maxOpen}>
          <div className="h-full rounded-full bg-brand-600 transition-all" style={{ width: `${maxOpen ? (m.open_enquiries / maxOpen) * 100 : 0}%` }} />
        </div>
      </div>

      {canManage && !isSelf && (
        <Button variant="secondary" loading={update.isPending} icon={m.is_active ? <Pause className="size-4" /> : <Play className="size-4" />}
          onClick={() => update.mutate({ id: m.id, is_active: !m.is_active })}>
          {m.is_active ? 'Pause' : 'Resume'}
        </Button>
      )}
    </li>
  )
}

export default function TeamPage() {
  const { admin } = useAuth()
  const team = useTeam()
  const canManage = admin?.role === 'admin'
  const maxOpen = Math.max(1, ...(team.data?.map((m) => m.open_enquiries) ?? [1]))

  return (
    <div className="space-y-6">
      <Card className="p-5">
        <h2 className="text-sm font-semibold text-slate-900">How enquiries are assigned</h2>
        <ol className="mt-3 grid gap-3 text-sm text-slate-600 md:grid-cols-3">
          <li><span className="font-semibold text-clay">1. Returning customer.</span> If the same email or phone has written before, the same person gets it.</li>
          <li><span className="font-semibold text-clay">2. Lightest workload.</span> Otherwise it goes to whoever has the fewest open enquiries.</li>
          <li><span className="font-semibold text-clay">3. Take turns.</span> Ties go to the person who was given something longest ago. Paused members get nothing new.</li>
        </ol>
      </Card>

      {canManage && <div className="flex justify-end"><AddMember /></div>}

      <Card>
        <CardHeader title="Team" description={team.data ? `${team.data.filter((m) => m.is_active).length} active of ${team.data.length}` : undefined} />
        {team.isLoading ? <LoadingSpinner /> : team.error ? <ErrorMessage error={team.error} onRetry={() => team.refetch()} /> : (
          <ul className="divide-y divide-white/60">
            {team.data?.map((m) => <MemberRow key={m.id} m={m} canManage={!!canManage} isSelf={m.id === admin?.id} maxOpen={maxOpen} />)}
          </ul>
        )}
        {!canManage && <p className="border-t border-white/60 px-5 py-3 text-xs text-slate-500">Only administrators can add or pause team members.</p>}
      </Card>
    </div>
  )
}
