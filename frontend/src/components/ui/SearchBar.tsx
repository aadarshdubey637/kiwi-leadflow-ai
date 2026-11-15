import { useEffect, useState } from 'react'
import { Search, X } from 'lucide-react'

/** Debounced search box: calls onChange 350 ms after the user stops typing. */
export function SearchBar({
  value, onChange, placeholder = 'Search…',
}: {
  value: string
  onChange: (v: string) => void
  placeholder?: string
}) {
  const [text, setText] = useState(value)
  const [seen, setSeen] = useState(value)
  if (value !== seen) { // URL changed from outside (e.g. "Clear filters"): adopt it
    setSeen(value)
    setText(value)
  }
  useEffect(() => {
    if (text === value) return
    const t = setTimeout(() => onChange(text), 350)
    return () => clearTimeout(t)
  }, [text, value, onChange])

  return (
    <div className="relative w-full sm:max-w-xs">
      <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-slate-400" aria-hidden />
      <input
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder={placeholder}
        aria-label="Search"
        className="w-full rounded-lg border border-slate-300/80 bg-white/70 backdrop-blur py-2 pl-9 pr-8 text-sm placeholder:text-slate-400 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20"
      />
      {text && (
        <button
          type="button"
          aria-label="Clear search"
          onClick={() => { setText(''); onChange('') }}
          className="absolute right-2 top-1/2 -translate-y-1/2 rounded p-1 text-slate-400 hover:text-slate-600"
        >
          <X className="size-3.5" />
        </button>
      )}
    </div>
  )
}
