// Muted, earthy chart palette. Semantic colours stay consistent across every chart:
// Hot / High = clay red, Warm / Medium = ochre, Cold / Low = steel blue / stone.
export const COLORS = {
  brand: '#1d7069',
  Hot: '#c4553a', Warm: '#d9962b', Cold: '#4a7a9b',
  High: '#c4553a', Medium: '#d9962b', Low: '#a39b8c',
  Positive: '#4f8a5b', Neutral: '#a39b8c', Negative: '#c4553a',
  Successful: '#4f8a5b', Failed: '#c4553a',
  New: '#4a7a9b', 'In Progress': '#d9962b', Converted: '#4f8a5b', Closed: '#a39b8c',
  // one stable colour per service category
  'Website Development': '#1d7069',
  'Mobile Application Development': '#4a7a9b',
  'AI Software Development': '#8a5a6b',
  'Digital Marketing': '#d9962b',
  'E-commerce Development': '#c4553a',
  'Custom Software Development': '#7a9e7e',
  'Other Services': '#a39b8c',
} as Record<string, string>

const PALETTE = ['#1d7069', '#d9962b', '#c4553a', '#7a9e7e', '#4a7a9b', '#8a5a6b', '#a39b8c']
export const colorFor = (name: string, i: number) => COLORS[name] ?? PALETTE[i % PALETTE.length]

export interface Slice {
  name: string
  value: number
}
