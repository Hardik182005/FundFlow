'use client'

import { useEffect, useState } from 'react'
import AppShell from '@/components/app/AppShell'
import { getAnakinUsage, discoverWireActions, getWireActions } from '@/lib/api'
import type { AnakinUsageReport } from '@/lib/types'
import { RefreshCw } from 'lucide-react'

export default function AnakinUsagePage() {
  const [usage, setUsage] = useState<AnakinUsageReport | null>(null)
  const [wire, setWire] = useState<Record<string, { action_id?: string; catalog?: string; source?: string } | null>>({})
  const [discovering, setDiscovering] = useState(false)

  const load = () => {
    getAnakinUsage().then(setUsage).catch(() => {})
    getWireActions().then((r) => setWire(r.actions)).catch(() => {})
  }
  useEffect(load, [])

  async function discover() {
    setDiscovering(true)
    try { await discoverWireActions(); load() } finally { setDiscovering(false) }
  }

  return (
    <AppShell title="Anakin Usage">
      <p className="mb-4 text-sm text-textFaint">{usage?.label || 'Locally tracked Anakin usage'} — this is FundFlow’s local estimate, not Anakin’s official account balance.</p>

      {usage && (
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          {[['Configured budget', usage.configured_budget], ['Est. credits used', usage.estimated_credits_used],
            ['Used today', usage.estimated_credits_today], ['Cache hit rate', `${Math.round(usage.cache_hit_rate * 100)}%`]].map(([l, v]) => (
            <div key={l as string} className="ff-card p-4">
              <div className="font-mono-num text-2xl font-semibold">{v as string}</div>
              <div className="text-xs text-textFaint">{l as string}</div>
            </div>
          ))}
        </div>
      )}

      <div className="mt-6 ff-card p-4">
        <div className="mb-3 flex items-center justify-between">
          <h3 className="font-semibold">Wire actions (discovered)</h3>
          <button onClick={discover} className="ff-btn-ghost text-xs"><RefreshCw size={14} className={discovering ? 'animate-spin' : ''} /> Discover</button>
        </div>
        <div className="space-y-2 text-sm">
          {Object.entries(wire).map(([logical, a]) => (
            <div key={logical} className="flex items-center justify-between border-t border-cardBorder pt-2 first:border-0 first:pt-0">
              <span className="text-textSecondary">{logical}</span>
              <span className="font-mono-num text-xs">{a?.action_id || '—'} <span className="text-textFaint">({a?.source})</span></span>
            </div>
          ))}
        </div>
      </div>

      {usage && usage.recent_calls.length > 0 && (
        <div className="mt-6 ff-card overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-background text-left text-xs text-textFaint">
              <tr>{['Time', 'Operation', 'Target', 'Cached', 'Credits'].map((h) => <th key={h} className="px-4 py-2.5 font-medium">{h}</th>)}</tr>
            </thead>
            <tbody>
              {usage.recent_calls.slice(0, 20).map((c, i) => (
                <tr key={i} className="border-t border-cardBorder">
                  <td className="px-4 py-2 text-xs">{String(c.timestamp || '').slice(0, 19)}</td>
                  <td className="px-4 py-2">{String(c.operation)}</td>
                  <td className="px-4 py-2 max-w-xs truncate text-xs">{String(c.target)}</td>
                  <td className="px-4 py-2">{c.cached ? 'yes' : 'no'}</td>
                  <td className="px-4 py-2 font-mono-num">{String(c.estimated_credits)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </AppShell>
  )
}
