import { useState } from 'react'
import { Download, FileSpreadsheet } from 'lucide-react'
import { DonutChart, HorizontalBars, TrendArea } from '@/components/charts/charts'
import { Button } from '@/components/ui/Button'
import { Card, CardHeader } from '@/components/ui/Card'
import { ChartCard } from '@/components/ui/ChartCard'
import { ErrorMessage, LoadingSpinner, NotAvailable } from '@/components/ui/States'
import { useCategories, useConversion, useFunnel, useLeadDistribution, usePipeline, usePriorities, useStats, useTrends } from '@/hooks/useApi'
import { useExport } from '@/hooks/useExport'
import type { TrendPeriod } from '@/types/api'
import { cn, formatMoney } from '@/utils/format'

const RANGES = [
  { label: '7 days', days: 7, period: 'daily' as TrendPeriod },
  { label: '30 days', days: 30, period: 'daily' as TrendPeriod },
  { label: '90 days', days: 90, period: 'weekly' as TrendPeriod },
  { label: '1 year', days: 365, period: 'monthly' as TrendPeriod },
]

export default function AnalyticsPage() {
  const [range, setRange] = useState(RANGES[1])
  const [period, setPeriod] = useState<TrendPeriod>(range.period)
  const trends = useTrends(period, range.days)
  const categories = useCategories()
  const priorities = usePriorities()
  const leads = useLeadDistribution()
  const conversion = useConversion()
  const funnel = useFunnel()
  const stats = useStats()
  const pipeline = usePipeline()
  const { exportFile, exporting } = useExport()

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex rounded-lg bg-slate-100 p-0.5" role="group" aria-label="Date range">
          {RANGES.map((r) => (
            <button key={r.label} aria-pressed={r.label === range.label} onClick={() => { setRange(r); setPeriod(r.period) }}
              className={cn('rounded-md px-3 py-1.5 text-xs font-medium transition-colors', r.label === range.label ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-500 hover:text-slate-700')}>
              {r.label}
            </button>
          ))}
        </div>
<div className="flex gap-2">
          <Button variant="secondary" icon={<Download className="size-4" />} loading={exporting === 'csv'} onClick={() => exportFile('csv')}>Export CSV</Button>
          <Button variant="secondary" icon={<FileSpreadsheet className="size-4" />} loading={exporting === 'xlsx'} onClick={() => exportFile('xlsx')}>Export Excel</Button>
        </div>
      </div>

      <ChartCard title="Total enquiries over time" description={`Last ${range.label}, grouped ${period}`} isLoading={trends.isLoading} error={trends.error} onRetry={() => trends.refetch()}
        isEmpty={!trends.data?.some((p) => p.count > 0)} emptyText="No enquiries in this period" height={280}
        action={
          <select aria-label="Group by" value={period} onChange={(e) => setPeriod(e.target.value as TrendPeriod)}
            className="rounded-lg border border-slate-300/80 bg-white/70 backdrop-blur px-2.5 py-1.5 text-xs focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20">
            <option value="daily">Daily</option><option value="weekly">Weekly</option><option value="monthly">Monthly</option>
          </select>
        }>
        <TrendArea data={trends.data ?? []} />
      </ChartCard>

      <div className="grid gap-6 lg:grid-cols-2">
        <ChartCard title="Category-wise distribution" isLoading={categories.isLoading} error={categories.error} onRetry={() => categories.refetch()}
          isEmpty={!categories.data?.some((c) => c.count > 0)} height={300}>
          <HorizontalBars data={(categories.data ?? []).map((c) => ({ name: c.label, value: c.count }))} />
        </ChartCard>
        <ChartCard title="Priority distribution" isLoading={priorities.isLoading} error={priorities.error} onRetry={() => priorities.refetch()}
          isEmpty={!priorities.data?.some((c) => c.count > 0)} height={300}>
          <DonutChart centerLabel="enquiries" data={(priorities.data ?? []).map((p) => ({ name: p.label, value: p.count }))} />
        </ChartCard>
        <ChartCard title="Hot / Warm / Cold" isLoading={leads.isLoading} error={leads.error} onRetry={() => leads.refetch()}
          isEmpty={!leads.data || leads.data.hot + leads.data.warm + leads.data.cold === 0} height={220}>
          {leads.data && <DonutChart centerLabel="scored leads" data={[{ name: 'Hot', value: leads.data.hot }, { name: 'Warm', value: leads.data.warm }, { name: 'Cold', value: leads.data.cold }]} />}
        </ChartCard>
        <ChartCard title="Enquiry status distribution" isLoading={stats.isLoading} error={stats.error} onRetry={() => stats.refetch()}
          isEmpty={!stats.data || stats.data.total_enquiries === 0} height={220}>
          {stats.data && <DonutChart centerLabel="enquiries" data={[
            { name: 'New', value: stats.data.new_enquiries }, { name: 'In Progress', value: stats.data.in_progress_enquiries },
            { name: 'Converted', value: stats.data.converted_enquiries }, { name: 'Closed', value: stats.data.closed_enquiries },
          ]} />}
        </ChartCard>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader title="Lead conversion" description="Converted enquiries as a share of all enquiries" />
          <div className="p-5">
            {conversion.isLoading ? <LoadingSpinner /> : conversion.error ? <ErrorMessage error={conversion.error} onRetry={() => conversion.refetch()} /> : conversion.data && (
              <>
                <p className="text-4xl font-semibold tracking-tight">{conversion.data.conversion_rate}%</p>
                <p className="text-xs text-slate-500">{conversion.data.converted} converted of {conversion.data.total_enquiries} · {conversion.data.open} open · {conversion.data.closed} closed</p>
                <table className="mt-5 w-full text-sm">
                  <thead className="text-xs uppercase tracking-wide text-slate-400">
                    <tr><th className="pb-2 text-left font-medium">Lead</th><th className="pb-2 text-right font-medium">Enquiries</th><th className="pb-2 text-right font-medium">Converted</th><th className="pb-2 text-right font-medium">Rate</th></tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {conversion.data.by_temperature.map((t) => (
                      <tr key={t.temperature}><td className="py-2 font-medium">{t.temperature}</td><td className="py-2 text-right">{t.enquiries}</td><td className="py-2 text-right">{t.converted}</td><td className="py-2 text-right">{t.conversion_rate}%</td></tr>
                    ))}
                  </tbody>
                </table>
              </>
            )}
          </div>
        </Card>
        <ChartCard title="Lead funnel" description="Where enquiries drop off" isLoading={funnel.isLoading} error={funnel.error} onRetry={() => funnel.refetch()}
          isEmpty={!funnel.data?.[0]?.count} height={260}>
          <HorizontalBars data={(funnel.data ?? []).map((f) => ({ name: f.stage, value: f.count }))} />
        </ChartCard>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader title="Estimated pipeline value" description="Stated budgets of open enquiries — not revenue" />
          <div className="p-5">
            {pipeline.isLoading ? <LoadingSpinner /> : pipeline.error ? <ErrorMessage error={pipeline.error} onRetry={() => pipeline.refetch()} /> : pipeline.data && (
              <>
                {pipeline.data.by_currency.length ? (
                  <ul className="space-y-2">
                    {pipeline.data.by_currency.map((c) => (
                      <li key={c.currency} className="flex items-baseline justify-between">
                        <span className="text-2xl font-semibold tracking-tight">{formatMoney(c.estimated_pipeline_value, c.currency === 'Unspecified' ? null : c.currency)}</span>
                        <span className="text-xs text-slate-500">{c.enquiries} enquiries · {c.currency}</span>
                      </li>
                    ))}
                  </ul>
                ) : <p className="text-sm text-slate-400">No open enquiries with a stated budget.</p>}
                <p className="mt-3 text-xs text-slate-500">{pipeline.data.open_enquiries_without_budget} open enquiries have no stated budget.</p>
                <p className="mt-2 rounded-lg bg-slate-50 p-3 text-xs text-slate-500">{pipeline.data.note}</p>
              </>
            )}
          </div>
        </Card>
        <Card>
          <CardHeader title="Sentiment analysis distribution" />
          <NotAvailable title="Not provided by the backend"
            reason="Sentiment is stored per enquiry but the API has no aggregate endpoint for it. Add one to chart it here (see docs/API_MAPPING.md)." />
        </Card>
      </div>
    </div>
  )
}
