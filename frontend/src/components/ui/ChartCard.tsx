import type { ReactNode } from 'react'
import { Card, CardHeader } from './Card'
import { QueryState } from './States'

interface Props {
  title: string
  description?: string
  isLoading: boolean
  error: unknown
  onRetry?: () => void
  isEmpty?: boolean
  emptyText?: string
  action?: ReactNode
  height?: number
  children: ReactNode
}

export function ChartCard({
  title, description, isLoading, error, onRetry, isEmpty, emptyText = 'No data yet', action, height = 260, children,
}: Props) {
  return (
    <Card>
      <CardHeader title={title} description={description} action={action} />
      <div className="p-5" style={{ minHeight: height }}>
        <QueryState
          isLoading={isLoading}
          error={error}
          onRetry={onRetry}
          isEmpty={isEmpty}
          empty={
            <div className="flex items-center justify-center text-sm text-slate-400" style={{ height }}>
              {emptyText}
            </div>
          }
        >
          <div style={{ height }}>{children}</div>
        </QueryState>
      </div>
    </Card>
  )
}
