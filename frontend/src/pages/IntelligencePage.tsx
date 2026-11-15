import { Link } from 'react-router-dom'
import { Flame, Snowflake, Sun, TrendingUp } from 'lucide-react'
import { DonutChart, HorizontalBars, VerticalBars } from '@/components/charts/charts'
import { EnquiryTable } from '@/components/enquiry/EnquiryTable'
import { Card, CardHeader } from '@/components/ui/Card'
import { ChartCard } from '@/components/ui/ChartCard'
import { EmptyState, ErrorMessage, LoadingSpinner, NotAvailable } from '@/components/ui/States'
import { StatCard } from '@/components/ui/StatCard'
import { useCategories, useEnquiries, useLeadDistribution, useStats } from '@/hooks/useApi'

function EnquiryList({ title, description, query, viewAll }: {
  title: string; description: string; viewAll: string; query: ReturnType<typeof useEnquiries>
}) {
  return (
    <Card>
      <CardHeader title={title} description={description} action={<Link to={viewAll} className="text-xs font-medium text-brand-700 hover:underline">View all</Link>} />
      {query.isLoading ? <LoadingSpinner /> : query.error ? <ErrorMessage error={query.error} onRetry={() => query.refetch()} /> :
        query.data && query.data.data.length ? <EnquiryTable rows={query.data.data} compact /> : <EmptyState title="Nothing here right now" />}
    </Card>
  )
}

export default function IntelligencePage() {
  const leads = useLeadDistribution()
  const categories = useCategories()
  const stats = useStats()
  const highPriority = useEnquiries({ page: 1, page_size: 5, priority: 'High' })
  const hotNew = useEnquiries({ page: 1, page_size: 5, temperature: 'Hot', status: 'New' })

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard label="Hot leads" value={leads.data?.hot ?? '—'} icon={Flame} tone="red" hint="Score 80–100" />
        <StatCard label="Warm leads" value={leads.data?.warm ?? '—'} icon={Sun} tone="amber" hint="Score 50–79" />
        <StatCard label="Cold leads" value={leads.data?.cold ?? '—'} icon={Snowflake} tone="sky" hint="Score 0–49" />
        <StatCard label="Average lead score" value={leads.data?.average_score ?? '—'} icon={TrendingUp} tone="brand" hint={leads.data ? `${leads.data.unscored} not yet scored` : undefined} />
      </div>
      {leads.error && <Card><ErrorMessage error={leads.error} onRetry={() => leads.refetch()} /></Card>}

      <div className="grid gap-6 lg:grid-cols-2">
        <ChartCard title="Lead score distribution" description="Number of leads per score band" isLoading={leads.isLoading} error={leads.error}
          isEmpty={!leads.data?.score_buckets.some((b) => b.count > 0)} emptyText="No scored leads yet">
          <VerticalBars data={(leads.data?.score_buckets ?? []).map((b) => ({ name: b.label, value: b.count }))} />
        </ChartCard>
        <ChartCard title="Hot / Warm / Cold" isLoading={leads.isLoading} error={leads.error}
          isEmpty={!leads.data || leads.data.hot + leads.data.warm + leads.data.cold === 0} emptyText="No scored leads yet">
          {leads.data && <DonutChart centerLabel="scored leads" data={[{ name: 'Hot', value: leads.data.hot }, { name: 'Warm', value: leads.data.warm }, { name: 'Cold', value: leads.data.cold }]} />}
        </ChartCard>
        <ChartCard title="Service category distribution" isLoading={categories.isLoading} error={categories.error}
          isEmpty={!categories.data?.some((c) => c.count > 0)} height={300}>
          <HorizontalBars data={(categories.data ?? []).map((c) => ({ name: c.label, value: c.count }))} />
        </ChartCard>
        <Card>
          <CardHeader title="Sentiment distribution" />
          <NotAvailable title="Not provided by the backend"
            reason="Sentiment is stored for each enquiry (see an enquiry's detail page) but the API has no endpoint that aggregates it, so no chart is shown rather than inventing numbers." />
        </Card>
      </div>

      <div className="grid gap-6 xl:grid-cols-2">
        <EnquiryList title="High-priority enquiries" description={`${stats.data?.high_priority_enquiries ?? 0} in total`} query={highPriority} viewAll="/admin/enquiries?priority=High" />
        <EnquiryList title="Hot leads awaiting first contact" description="Hot leads still marked New — contact these first" query={hotNew} viewAll="/admin/enquiries?temperature=Hot&status=New" />
      </div>
      {!!stats.data?.needs_manual_review && (
        <p className="text-xs text-slate-500">{stats.data.needs_manual_review} enquiry(ies) are flagged for manual review by the AI.</p>
      )}
    </div>
  )
}
