'use client'

import { TrendingUp, TrendingDown } from 'lucide-react'

// Illustrative market ticker (a UI element, not live quotes).
const ITEMS = [
  { label: 'SENSEX', value: '73,903.91', up: true },
  { label: 'NIFTY 50', value: '22,453.30', up: true },
  { label: 'RELIANCE', value: '2,934.50', up: false },
  { label: 'HDFCBANK', value: '1,450.20', up: true },
  { label: 'TCS', value: '3,980.00', up: false },
  { label: 'INFY', value: '1,495.65', up: true },
  { label: 'HDFC Mid-Cap', value: 'Trust 58', up: false },
  { label: 'SBI Bluechip', value: 'Trust 83', up: true },
  { label: 'Axis Bluechip', value: 'Trust 83', up: true },
  { label: 'Nippon Small Cap', value: 'Trust 42', up: false },
]

function Row() {
  return (
    <>
      {ITEMS.map((it, i) => (
        <span key={i} className="mx-5 inline-flex items-center gap-1.5 text-xs font-medium tracking-wide">
          <span className="text-white/60">{it.label}</span>
          <span className="font-mono-num text-white">{it.value}</span>
          {it.up ? <TrendingUp size={13} className="text-gain" /> : <TrendingDown size={13} className="text-loss" />}
        </span>
      ))}
    </>
  )
}

export default function TickerBar() {
  return (
    <div className="sticky top-0 z-50 w-full overflow-hidden bg-accent py-2">
      <div className="flex w-max animate-ticker whitespace-nowrap">
        <Row /><Row />
      </div>
    </div>
  )
}
