import { Activity, CheckCircle2, Clock, Coins, Cpu, RefreshCw, XCircle } from 'lucide-react'
import { DonutChart } from '@/components/charts/charts'
import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { Card, CardHeader } from '@/components/ui/Card'
import { ChartCard } from '@/components/ui/ChartCard'
import { DataTable, type Column } from '@/components/ui/DataTable'
import { EmptyState, ErrorMessage, LoadingSpinner } from '@/components/ui/States'
import { StatCard } from '@/components/ui/StatCard'
import { useAiUsage, usePerformance } from '@/hooks/useApi'
import type { ProviderUsage } from '@/types/api'
import { formatNumber, formatSeconds } from '@/utils/format'

const axis = { fontSize: 11, fill: '#7a7366' }
const tip = { borderRadius: 10, border: '1px solid rgb(255 255 255 / 0.8)', fontSize: 12, background: 'rgb(255 253 249 / 0.92)', boxShadow: '0 8px 24px rgb(60 45 30 / 0.15)' }

export default function MonitoringPage() {
  const usage = useAiUsage()
  const perf = usePerformance()

  if (usage.isLoading || perf.isLoading) return <LoadingSpinner />
  if (usage.error || perf.error) return <Card><ErrorMessage error={usage.error ?? perf.error} onRetry={() => { usage.refetch(); perf.refetch() }} /></Card>
  const u = usage.data!
  const p = perf.data!

  if (u.total_requests === 0) {
    return <Card><EmptyState title="No AI requests yet" description="Metrics appear after the first enquiry has been analysed." /></Card>
  }

  const columns: Column<ProviderUsage>[] = [
    { key: 'provider', header: 'Provider', cell: (r) => <span className="font-medium capitalize text-slate-900">{r.provider}</span> },
    { key: 'model', header: 'Model', hideBelow: 'md', cell: (r) => <code className="text-xs text-slate-600">{r.model_name}</code> },
    { key: 'req', header: 'Requests', cell: (r) => formatNumber(r.requests) },
    { key: 'ok', header: 'Success / Failed', cell: (r) => <span><span className="text-emerald-600">{r.successful}</span> / <span className="text-red-600">{r.failed}</span></span> },
    { key: 'tok', header: 'Tokens in / out', hideBelow: 'md', cell: (r) => `${formatNumber(r.input_tokens)} / ${formatNumber(r.output_tokens)}` },
    { key: 'time', header: 'Avg time', hideBelow: 'md', cell: (r) => formatSeconds(r.average_response_time) },
    { key: 'cost', header: 'Est. cost', cell: (r) => `$${r.estimated_cost_usd.toFixed(4)}` },
  ]

  const tokenData = u.by_provider.map((r) => ({ name: r.provider, Input: r.input_tokens, Output: r.output_tokens }))
  const latencyData = p.latency_by_provider.map((r) => ({ name: r.provider, Average: r.average, P95: r.p95 }))

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard label="Total AI requests" value={formatNumber(u.total_requests)} icon={Activity} tone="brand" hint={`${u.retry_count} were retries`} />
        <StatCard label="Successful" value={formatNumber(u.successful_requests)} icon={CheckCircle2} tone="emerald" hint={`${p.ai_success_rate}% success rate`} />
        <StatCard label="Failed" value={formatNumber(u.failed_requests)} icon={XCircle} tone="red" hint="Incl. invalid output" />
        <StatCard label="Avg response time" value={formatSeconds(u.average_response_time)} icon={Clock} tone="amber" hint={`p95 ${formatSeconds(p.p95_latency_seconds)}`} />
        <StatCard label="Input tokens" value={formatNumber(u.input_tokens)} icon={Cpu} tone="sky" />
        <StatCard label="Output tokens" value={formatNumber(u.output_tokens)} icon={Cpu} tone="sky" />
        <StatCard label="Estimated cost" value={`$${u.estimated_cost_usd.toFixed(4)}`} icon={Coins} tone="slate" hint="Estimate, not an invoice" />
        <StatCard label="Workflows completed" value={`${p.workflows_completed}`} icon={RefreshCw} tone="emerald" hint={`${p.workflows_failed} failed · avg ${formatSeconds(p.average_workflow_seconds)}`} />
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <ChartCard title="Request outcomes" height={220}  isLoading={false} error={null}>
          <DonutChart centerLabel="requests" data={[{ name: 'Successful', value: u.successful_requests }, { name: 'Failed', value: u.failed_requests }]} />
        </ChartCard>
        <ChartCard title="Token usage by provider" height={220} isLoading={false} error={null}>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={tokenData} margin={{ left: -8, right: 8, top: 8 }}>
              <CartesianGrid vertical={false} stroke="#e6e0d6" />
              <XAxis dataKey="name" tick={axis} axisLine={false} tickLine={false} />
              <YAxis tick={axis} axisLine={false} tickLine={false} />
              <Tooltip contentStyle={tip} />
              <Legend wrapperStyle={{ fontSize: 12 }} />
              <Bar dataKey="Input" fill="#1d7069" radius={[4, 4, 0, 0]} maxBarSize={40} />
              <Bar dataKey="Output" fill="#d9962b" radius={[4, 4, 0, 0]} maxBarSize={40} />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>
        <ChartCard title="Latency by provider (seconds)" height={220} isLoading={false} error={null}>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={latencyData} margin={{ left: -8, right: 8, top: 8 }}>
              <CartesianGrid vertical={false} stroke="#e6e0d6" />
              <XAxis dataKey="name" tick={axis} axisLine={false} tickLine={false} />
              <YAxis tick={axis} axisLine={false} tickLine={false} />
              <Tooltip contentStyle={tip} />
              <Legend wrapperStyle={{ fontSize: 12 }} />
              <Bar dataKey="Average" fill="#1d7069" radius={[4, 4, 0, 0]} maxBarSize={40} />
              <Bar dataKey="P95" fill="#c4553a" radius={[4, 4, 0, 0]} maxBarSize={40} />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>
      </div>

      <Card>
        <CardHeader title="Providers & models" description="Every LLM call attempt, including retries and failures" />
        <DataTable columns={columns} rows={u.by_provider} rowKey={(r) => `${r.provider}/${r.model_name}`} />
        <p className="border-t border-slate-100 px-5 py-3 text-xs text-slate-500">{u.cost_note}</p>
      </Card>
    </div>
  )
}
