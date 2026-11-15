import type { ReactNode } from 'react'
import { cn } from '@/utils/format'

export interface Column<T> {
  key: string
  header: string
  cell: (row: T) => ReactNode
  className?: string
  hideBelow?: 'md' | 'lg' // hide this column on smaller screens
}

const hide = { md: 'hidden md:table-cell', lg: 'hidden lg:table-cell' }

export function DataTable<T>({
  columns, rows, rowKey, onRowClick,
}: {
  columns: Column<T>[]
  rows: T[]
  rowKey: (r: T) => string | number
  onRowClick?: (r: T) => void
}) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-left text-sm">
        <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
          <tr>
            {columns.map((c) => (
              <th key={c.key} scope="col" className={cn('px-5 py-3 font-medium', c.hideBelow && hide[c.hideBelow], c.className)}>
                {c.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {rows.map((r) => (
            <tr
              key={rowKey(r)}
              onClick={onRowClick ? () => onRowClick(r) : undefined}
              className={cn('transition-colors', onRowClick && 'cursor-pointer hover:bg-slate-50')}
            >
              {columns.map((c) => (
                <td key={c.key} className={cn('px-5 py-3 align-middle text-slate-700', c.hideBelow && hide[c.hideBelow], c.className)}>
                  {c.cell(r)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
