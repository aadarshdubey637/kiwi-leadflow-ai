import { useState } from 'react'
import { Link } from 'react-router-dom'
import { BellRing, CheckCircle2, Flame, Inbox, Loader2, Users } from 'lucide-react'
import { primaryLinkClass } from '@/components/ui/Button'
import { ChartCard } from '@/components/ui/ChartCard'
import { Card, CardHeader } from '@/components/ui/Card'
import { EmptyState, ErrorMessage, LoadingSpinner } from '@/components/ui/States'
import { StatCard } from '@/components/ui/StatCard'
import { DonutChart, HorizontalBars, TrendArea } from '@/components/charts/charts'
import { EnquiryTable } from '@/components/enquiry/EnquiryTable'
import { useCategories, useConversion, useEnquiries, useLeadDistribution, usePriorities, useStats, useTrends } from '@/hooks/useApi'
import type { TrendPeriod } from '@/types/api'
import { cn } from '@/utils/format'

const PERIODS: { value: TrendPeriod; label: string; days: number }[] = [
  { value: 'daily', label: 'Daily', days: 30 },
  { value: 'weekly', label: 'Weekly', days: 90 },
  { value: 'monthly', label: 'Monthly', days: 365 },
]

export default function OverviewPage() {
  const stats = useStats()
  const categories = useCategories()
  const priorities = usePriorities()
  const leads = useLeadDistribution()
  const conversion = useConversion()
  const recent = useEnquiries({ page: 1, page_size: 6 })
  const [period, setPeriod] = useState(PERIODS[0])
  const trends = useTrends(period.value, period.days)

  return (
    <div className="space-y-6">
      {stats.isLoading ? <LoadingSpinner /> : stats.error ? (
        <Card><ErrorMessage error={stats.error} onRetry={() => stats.refetch()} /></Card>
      ) : stats.data && (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-5">
          <StatCard delay={0} label="Total enquiries" value={stats.data.total_enquiries} icon={Inbox} tone="brand" />
          <StatCard delay={60} label="New enquiries" value={stats.data.new_enquiries} icon={BellRing} tone="sky" />
          <StatCard delay={120} label="High priority" value={stats.data.high_priority_enquiries} icon={Flame} tone="red" />
          <StatCard delay={180} label="In progress" value={stats.data.in_progress_enquiries} icon={Loader2} tone="amber" />
          <StatCard delay={240} label="Converted" value={stats.data.converted_enquiries} icon={CheckCircle2} tone="emerald" />
        </div>
      )}

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <ChartCard
            title="Enquiry growth" description="New enquiries received over time"
            isLoading={trends.isLoading} error={trends.error} onRetry={() => trends.refetch()}
            isEmpty={!trends.data?.some((p) => p.count > 0)} emptyText="No enquiries in this period"
            action={
              <div className="flex rounded-lg bg-slate-100 p-0.5" role="group" aria-label="Time period">
                {PERIODS.map((p) => (
                  <button key={p.value} onClick={() => setPeriod(p)} aria-pressed={p.value === period.value}
                    className={cn('rounded-md px-2.5 py-1 text-xs font-medium transition-colors', p.value === period.value ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-500 hover:text-slate-700')}>
                    {p.label}
                  </button>
                ))}
              </div>
            }
          >
            <TrendArea data={trends.data ?? []} />
          </ChartCard>
        </div>
        <ChartCard title="Hot / Warm / Cold leads" description="Lead temperature from AI scoring"
          isLoading={leads.isLoading} error={leads.error} onRetry={() => leads.refetch()}
          isEmpty={!leads.data || leads.data.hot + leads.data.warm + leads.data.cold === 0}>
          {leads.data && (
            <DonutChart centerLabel="scored leads"
              data={[{ name: 'Hot', value: leads.data.hot }, { name: 'Warm', value: leads.data.warm }, { name: 'Cold', value: leads.data.cold }]} />
          )}
        </ChartCard>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <ChartCard title="Enquiries by service category" isLoading={categories.isLoading} error={categories.error}
            onRetry={() => categories.refetch()} isEmpty={!categories.data?.some((c) => c.count > 0)} height={300}>
            <HorizontalBars data={(categories.data ?? []).map((c) => ({ name: c.label, value: c.count }))} />
          </ChartCard>
        </div>
        <div className="space-y-6">
          <ChartCard title="Priority distribution" isLoading={priorities.isLoading} error={priorities.error}
            onRetry={() => priorities.refetch()} isEmpty={!priorities.data?.some((c) => c.count > 0)} height={140}>
            <DonutChart centerLabel="enquiries" data={(priorities.data ?? []).map((p) => ({ name: p.label, value: p.count }))} />
          </ChartCard>
          <Card>
            <CardHeader title="Conversion overview" />
            <div className="p-5">
              {conversion.isLoading ? <LoadingSpinner /> : conversion.error ? <ErrorMessage error={conversion.error} onRetry={() => conversion.refetch()} /> : conversion.data && (
                <div>
                  <div className="flex items-end justify-between">
                    <div>
                      <p className="text-3xl font-semibold tracking-tight">{conversion.data.conversion_rate}%</p>
                      <p className="text-xs text-slate-500">conversion rate</p>
                    </div>
                    <p className="text-right text-xs text-slate-500">
                      {conversion.data.converted} converted · {conversion.data.open} open · {conversion.data.closed} closed
                    </p>
                  </div>
                  <div className="mt-4 h-2 overflow-hidden rounded-full bg-slate-100" role="progressbar" aria-valuenow={conversion.data.conversion_rate} aria-valuemin={0} aria-valuemax={100} aria-label="Conversion rate">
                    <div className="h-full rounded-full bg-brand-600 transition-all" style={{ width: `${conversion.data.conversion_rate}%` }} />
                  </div>
                </div>
              )}
            </div>
          </Card>
        </div>
      </div>

      <Card>
        <CardHeader title="Recent enquiries" description="Latest submissions"
          action={<Link to="/admin/enquiries" className="text-xs font-medium text-brand-700 hover:underline">View all</Link>} />
        {recent.isLoading ? <LoadingSpinner /> : recent.error ? <ErrorMessage error={recent.error} onRetry={() => recent.refetch()} /> :
          recent.data && recent.data.data.length > 0 ? <EnquiryTable rows={recent.data.data} compact /> : (
            <EmptyState title="No enquiries yet" description="Submitted enquiries and their AI analysis will appear here."
              action={<Link to="/admin/enquiries/new" className={`mt-2 ${primaryLinkClass}`}><Users className="size-4" /> Add the first enquiry</Link>} />
          )}
      </Card>
    </div>
  )
}
