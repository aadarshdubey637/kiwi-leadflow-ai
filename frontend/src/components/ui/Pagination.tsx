import { ChevronLeft, ChevronRight } from 'lucide-react'
import type { PageMeta } from '@/types/api'
import { Button } from './Button'

export function Pagination({ meta, onPage }: { meta: PageMeta; onPage: (p: number) => void }) {
  const from = meta.total === 0 ? 0 : (meta.page - 1) * meta.page_size + 1
  const to = Math.min(meta.page * meta.page_size, meta.total)
  return (
    <div className="flex flex-col items-center justify-between gap-3 border-t border-slate-100 px-5 py-3 sm:flex-row">
      <p className="text-xs text-slate-500">
        Showing <span className="font-medium text-slate-700">{from}–{to}</span> of{' '}
        <span className="font-medium text-slate-700">{meta.total}</span>
      </p>
      <div className="flex items-center gap-2">
        <Button variant="secondary" className="px-2 py-1.5" aria-label="Previous page" disabled={meta.page <= 1} onClick={() => onPage(meta.page - 1)}>
          <ChevronLeft className="size-4" />
        </Button>
        <span className="text-xs text-slate-600">Page {meta.page} of {meta.total_pages}</span>
        <Button variant="secondary" className="px-2 py-1.5" aria-label="Next page" disabled={meta.page >= meta.total_pages} onClick={() => onPage(meta.page + 1)}>
          <ChevronRight className="size-4" />
        </Button>
      </div>
    </div>
  )
}
