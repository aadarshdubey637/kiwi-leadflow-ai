import {
  Area, AreaChart, Bar, BarChart, CartesianGrid, Cell, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from 'recharts'
import { COLORS, colorFor, type Slice } from './palette'

const tooltipStyle = {
  borderRadius: 10, border: '1px solid rgb(255 255 255 / 0.8)', fontSize: 12, color: '#1f2422',
  background: 'rgb(255 253 249 / 0.92)', backdropFilter: 'blur(8px)', boxShadow: '0 8px 24px rgb(60 45 30 / 0.15)',
}
const axisTick = { fontSize: 11, fill: '#7a7366' }
const grid = '#e6e0d6'

export function DonutChart({ data, centerLabel }: { data: Slice[]; centerLabel?: string }) {
  const total = data.reduce((s, d) => s + d.value, 0)
  return (
    <div className="flex h-full flex-col items-center gap-3 sm:flex-row">
      <div className="relative h-full min-h-[180px] w-full sm:w-1/2">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie data={data} dataKey="value" nameKey="name" innerRadius="64%" outerRadius="92%" paddingAngle={data.length > 1 ? 2 : 0} stroke="none" cornerRadius={4}>
              {data.map((d, i) => <Cell key={d.name} fill={colorFor(d.name, i)} />)}
            </Pie>
            <Tooltip contentStyle={tooltipStyle} />
          </PieChart>
        </ResponsiveContainer>
        <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-2xl font-semibold text-slate-900">{total}</span>
          {centerLabel && <span className="text-xs text-slate-500">{centerLabel}</span>}
        </div>
      </div>
      <ul className="w-full space-y-2 sm:w-1/2">
        {data.map((d, i) => (
          <li key={d.name} className="flex items-center justify-between gap-2 text-sm">
            <span className="flex items-center gap-2 text-slate-600">
              <span className="size-2.5 rounded-sm" style={{ background: colorFor(d.name, i) }} aria-hidden />
              {d.name}
            </span>
            <span className="font-medium text-slate-900">
              {d.value}
              <span className="ml-1 text-xs font-normal text-slate-400">{total ? Math.round((d.value / total) * 100) : 0}%</span>
            </span>
          </li>
        ))}
      </ul>
    </div>
  )
}

/** Horizontal bars; each bar takes its own colour from the palette (stable per category / stage name). */
export function HorizontalBars({ data, single }: { data: Slice[]; single?: boolean }) {
  return (
    <ResponsiveContainer width="100%" height="100%">
      <BarChart data={data} layout="vertical" margin={{ left: 8, right: 16, top: 4, bottom: 4 }}>
        <CartesianGrid horizontal={false} stroke={grid} />
        <XAxis type="number" allowDecimals={false} tick={axisTick} axisLine={false} tickLine={false} />
        <YAxis type="category" dataKey="name" width={190} tick={axisTick} axisLine={false} tickLine={false} />
        <Tooltip contentStyle={tooltipStyle} cursor={{ fill: 'rgb(120 110 95 / 0.08)' }} />
        <Bar dataKey="value" name="Enquiries" radius={[0, 6, 6, 0]} barSize={16} fill={COLORS.brand}>
          {!single && data.map((d, i) => <Cell key={d.name} fill={colorFor(d.name, i)} />)}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}

export function VerticalBars({ data, colorByName }: { data: Slice[]; colorByName?: boolean }) {
  return (
    <ResponsiveContainer width="100%" height="100%">
      <BarChart data={data} margin={{ left: -16, right: 8, top: 8, bottom: 0 }}>
        <CartesianGrid vertical={false} stroke={grid} />
        <XAxis dataKey="name" tick={axisTick} axisLine={false} tickLine={false} />
        <YAxis allowDecimals={false} tick={axisTick} axisLine={false} tickLine={false} />
        <Tooltip contentStyle={tooltipStyle} cursor={{ fill: 'rgb(120 110 95 / 0.08)' }} />
        <Bar dataKey="value" name="Enquiries" radius={[6, 6, 0, 0]} maxBarSize={46} fill={COLORS.brand}>
          {colorByName && data.map((d, i) => <Cell key={d.name} fill={colorFor(d.name, i)} />)}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}

export function TrendArea({ data }: { data: { period: string; count: number }[] }) {
  return (
    <ResponsiveContainer width="100%" height="100%">
      <AreaChart data={data} margin={{ left: -16, right: 8, top: 8, bottom: 0 }}>
        <defs>
          <linearGradient id="trendFill" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={COLORS.brand} stopOpacity={0.28} />
            <stop offset="100%" stopColor={COLORS.brand} stopOpacity={0.02} />
          </linearGradient>
        </defs>
        <CartesianGrid vertical={false} stroke={grid} />
        <XAxis dataKey="period" tick={axisTick} axisLine={false} tickLine={false} minTickGap={24}
          tickFormatter={(v: string) => (v.length === 10 ? v.slice(5) : v)} />
        <YAxis allowDecimals={false} tick={axisTick} axisLine={false} tickLine={false} />
        <Tooltip contentStyle={tooltipStyle} />
        <Area type="monotone" dataKey="count" name="Enquiries" stroke={COLORS.brand} strokeWidth={2.25} fill="url(#trendFill)" activeDot={{ r: 4, fill: COLORS.brand, stroke: '#fff', strokeWidth: 2 }} />
      </AreaChart>
    </ResponsiveContainer>
  )
}
