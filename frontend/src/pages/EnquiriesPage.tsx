import { useCallback, useMemo } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { Download, FileSpreadsheet, FilterX, Plus } from 'lucide-react'
import { EnquiryTable } from '@/components/enquiry/EnquiryTable'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { FilterDropdown } from '@/components/ui/FilterDropdown'
import { Pagination } from '@/components/ui/Pagination'
import { SearchBar } from '@/components/ui/SearchBar'
import { EmptyState, ErrorMessage, LoadingSpinner } from '@/components/ui/States'
import { useEnquiries, useTeam } from '@/hooks/useApi'
import { useExport } from '@/hooks/useExport'
import {
  ENQUIRY_STATUSES, PRIORITIES, SERVICE_CATEGORIES, TEMPERATURES,
  type EnquiryFilters, type EnquiryStatus, type Priority, type ServiceCategory, type Temperature,
} from '@/types/api'

const PAGE_SIZE = 10

/** URL query string -> the filters sent to the API. A plain function so it can also be applied to the LIVE URL. */
function toFilters(params: URLSearchParams): EnquiryFilters {
  return {
    page: Number(params.get('page')) || 1,
    page_size: PAGE_SIZE,
    search: params.get('search') ?? undefined,
    category: (params.get('category') as ServiceCategory) ?? undefined,
    priority: (params.get('priority') as Priority) ?? undefined,
    status: (params.get('status') as EnquiryStatus) ?? undefined,
    temperature: (params.get('temperature') as Temperature) ?? undefined,
    assignee_id: params.get('assignee') && params.get('assignee') !== 'none' ? Number(params.get('assignee')) : undefined,
    unassigned: params.get('assignee') === 'none' ? true : undefined,
    // inclusive day range: the backend compares datetimes, so end the "to" date at 23:59:59
    date_from: params.get('from') ? `${params.get('from')}T00:00:00` : undefined,
    date_to: params.get('to') ? `${params.get('to')}T23:59:59` : undefined,
  }
}

/** Export what the user is looking at RIGHT NOW: read the live URL, not the last render's copy (which can lag a click behind). */
const exportFilters = () => {
  const { page: _p, page_size: _s, ...rest } = toFilters(new URLSearchParams(window.location.search))
  return rest
}
const dateInput = 'rounded-lg border border-slate-300/80 bg-white/70 backdrop-blur px-3 py-2 text-sm text-slate-700 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20'

export default function EnquiriesPage() {
  // Filters live in the URL, so a filtered view can be bookmarked/shared and survives refresh & back-navigation.
  const [params, setParams] = useSearchParams()
  const { exportFile, exporting } = useExport()
  const team = useTeam()

  const filters: EnquiryFilters = useMemo(() => toFilters(params), [params])

  const set = useCallback((key: string, value: string) => {
    // Build from the *live* URL, not the last render's params: two quick changes (before React re-renders)
    // would otherwise each start from stale params and the second would undo the first.
    const next = new URLSearchParams(window.location.search)
    if (value) next.set(key, value); else next.delete(key)
    if (key !== 'page') next.delete('page') // any filter change returns to page 1
    setParams(next, { replace: true })
  }, [setParams])

  const query = useEnquiries(filters)
  const hasFilters = ['search', 'category', 'priority', 'status', 'temperature', 'assignee', 'from', 'to'].some((k) => params.has(k))

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <p className="text-sm text-slate-500">{query.data ? `${query.data.meta.total} enquiries` : 'Enquiries'}{hasFilters && ' match your filters'}</p>
        <div className="flex gap-2">
<Button variant="secondary" icon={<Download className="size-4" />} loading={exporting === 'csv'} onClick={() => exportFile('csv', exportFilters())}>CSV</Button>
          <Button variant="secondary" icon={<FileSpreadsheet className="size-4" />} loading={exporting === 'xlsx'} onClick={() => exportFile('xlsx', exportFilters())}>Excel</Button>
          <Link to="/admin/enquiries/new" className="inline-flex items-center gap-2 rounded-lg bg-brand-600 px-3.5 py-2 text-sm font-medium text-white shadow-sm shadow-brand-900/20 hover:bg-brand-700">
            <Plus className="size-4" /> Add enquiry
          </Link>
        </div>
      </div>

      <Card>
        <div className="flex flex-wrap items-center gap-3 border-b border-slate-100 p-4">
          <SearchBar value={params.get('search') ?? ''} onChange={(v) => set('search', v)} placeholder="Search name, email, phone, message…" />
          <FilterDropdown label="Category" value={(params.get('category') ?? '') as ServiceCategory | ''} options={SERVICE_CATEGORIES} onChange={(v) => set('category', v)} />
          <FilterDropdown label="Priority" value={(params.get('priority') ?? '') as Priority | ''} options={PRIORITIES} onChange={(v) => set('priority', v)} />
          <FilterDropdown label="Status" value={(params.get('status') ?? '') as EnquiryStatus | ''} options={ENQUIRY_STATUSES} onChange={(v) => set('status', v)} />
          <FilterDropdown label="Lead" value={(params.get('temperature') ?? '') as Temperature | ''} options={TEMPERATURES} onChange={(v) => set('temperature', v)} />
          <select aria-label="Assigned to" value={params.get('assignee') ?? ''} onChange={(e) => set('assignee', e.target.value)}
            className="rounded-lg border border-slate-300/80 bg-white/70 py-2 pl-3 pr-8 text-sm text-slate-700 backdrop-blur focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20">
            <option value="">Assigned to: Anyone</option>
            <option value="none">Unassigned</option>
            {team.data?.map((m) => <option key={m.id} value={m.id}>{m.username}</option>)}
          </select>
          <label className="flex items-center gap-1.5 text-xs text-slate-500">From
            <input type="date" className={dateInput} value={params.get('from') ?? ''} max={params.get('to') ?? undefined} onChange={(e) => set('from', e.target.value)} />
          </label>
          <label className="flex items-center gap-1.5 text-xs text-slate-500">To
            <input type="date" className={dateInput} value={params.get('to') ?? ''} min={params.get('from') ?? undefined} onChange={(e) => set('to', e.target.value)} />
          </label>
          {hasFilters && <Button variant="ghost" icon={<FilterX className="size-4" />} onClick={() => setParams({}, { replace: true })}>Clear</Button>}
        </div>

        {query.isLoading ? <LoadingSpinner /> : query.error ? <ErrorMessage error={query.error} onRetry={() => query.refetch()} /> :
          query.data && query.data.data.length === 0 ? (
            <EmptyState
              title={hasFilters ? 'No enquiries match your filters' : 'No enquiries yet'}
              description={hasFilters ? 'Try removing a filter or searching for something else.' : 'Add the first enquiry to see AI analysis in action.'}
            />
          ) : query.data && (
            <>
              <EnquiryTable rows={query.data.data} />
              <Pagination meta={query.data.meta} onPage={(p) => set('page', String(p))} />
            </>
          )}
      </Card>
    </div>
  )
}
