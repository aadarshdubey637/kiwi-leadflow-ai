import { ChevronDown } from 'lucide-react'

interface Props<T extends string> {
  label: string
  value: T | ''
  options: readonly T[]
  onChange: (v: T | '') => void
}

export function FilterDropdown<T extends string>({ label, value, options, onChange }: Props<T>) {
  return (
    <div className="relative">
      <select
        aria-label={label}
        value={value}
        onChange={(e) => onChange(e.target.value as T | '')}
        className="w-full appearance-none rounded-lg border border-slate-300/80 bg-white/70 backdrop-blur py-2 pl-3 pr-8 text-sm text-slate-700 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20"
      >
        <option value="">{label}: All</option>
        {options.map((o) => (
          <option key={o} value={o}>{o}</option>
        ))}
      </select>
      <ChevronDown className="pointer-events-none absolute right-2.5 top-1/2 size-4 -translate-y-1/2 text-slate-400" aria-hidden />
    </div>
  )
}
