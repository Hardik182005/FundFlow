'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import AppShell from '@/components/app/AppShell'
import { getPortfolioValuation } from '@/lib/api'

interface Holding { scheme_code: string; fund_name: string; current_value?: number; gain_loss?: number; gain_loss_pct?: number }

export default function PortfolioPage() {
  const [holdings, setHoldings] = useState<Holding[]>([])
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getPortfolioValuation('demo-user')
      .then((r) => setHoldings(r.holdings || r.valuations || []))
      .catch(() => setError('Could not load portfolio. Add funds from Explore.'))
      .finally(() => setLoading(false))
  }, [])

  return (
    <AppShell title="Portfolio">
      {loading ? <div className="ff-card h-40 animate-pulse" /> : error ? (
        <div className="ff-card p-6 text-textFaint">{error}</div>
      ) : (
        <div className="space-y-3">
          {holdings.map((h) => (
            <div key={h.scheme_code} className="ff-card flex items-center justify-between p-4">
              <div>
                <div className="font-semibold">{h.fund_name}</div>
                <div className="text-xs text-textFaint">{h.scheme_code}</div>
              </div>
              <div className="flex items-center gap-4">
                {h.gain_loss_pct != null && (
                  <span className={`font-mono-num text-sm ${h.gain_loss_pct >= 0 ? 'text-gain' : 'text-loss'}`}>
                    {h.gain_loss_pct >= 0 ? '+' : ''}{h.gain_loss_pct}%
                  </span>
                )}
                <Link href={`/audit`} className="ff-btn-ghost text-xs">Audit</Link>
              </div>
            </div>
          ))}
        </div>
      )}
    </AppShell>
  )
}
