import type { LucideIcon } from 'lucide-react'
import { Card } from './Card'
import { cn } from '@/utils/format'

interface Props {
  label: string
  value: string | number
  icon: LucideIcon
  hint?: string
  tone?: 'brand' | 'sky' | 'red' | 'amber' | 'emerald' | 'slate'
  delay?: number // ms, for the staggered entrance
}

// Flat, muted tinted tiles — each metric keeps its own colour identity without glow or gradients.
const tones = {
  brand: 'bg-[#d9ece8] text-[#175a55]',
  sky: 'bg-[#dbe7f0] text-[#2f6285]',
  red: 'bg-[#f6dcd3] text-[#a9452d]',
  amber: 'bg-[#f6e6c4] text-[#8f6410]',
  emerald: 'bg-[#dbead9] text-[#2f6b3f]',
  slate: 'bg-[#ebe6dc] text-[#5b564b]',
}

export function StatCard({ label, value, icon: Icon, hint, tone = 'brand', delay = 0 }: Props) {
  return (
    <Card
      className="animate-fade-up p-5 transition-all duration-200 hover:-translate-y-0.5 hover:shadow-lg"
      style={{ animationDelay: `${delay}ms` }}
    >
      <div className="flex items-center gap-4">
        <div className={cn('flex size-11 shrink-0 items-center justify-center rounded-xl', tones[tone])}>
          <Icon className="size-5" aria-hidden />
        </div>
        <div className="min-w-0">
          <p className="truncate text-xs font-medium text-slate-500">{label}</p>
          <p className="text-[1.65rem] font-semibold leading-tight tracking-tight text-slate-900">{value}</p>
          {hint && <p className="truncate text-xs text-slate-400">{hint}</p>}
        </div>
      </div>
    </Card>
  )
}
