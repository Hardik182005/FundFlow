'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import {
  BarChart, Bar, XAxis, ResponsiveContainer, Cell, Tooltip,
} from 'recharts'
import { TrendingUp, ShieldCheck, Wallet, Gauge, ArrowRight } from 'lucide-react'
import AppShell from '@/components/app/AppShell'
import { verdictColor } from '@/components/app/StatusBadge'
import { getPortfolioValuation, getAuditHistory, getAnakinUsage } from '@/lib/api'
import type { AuditSummary, AnakinUsageReport } from '@/lib/types'

interface Holding {
  scheme_code: string; fund_name: string
  current_value?: number; invested_amount?: number; gain_loss_pct?: number
}

function inr(n: number): string {
  if (n >= 1e7) return `₹${(n / 1e7).toFixed(2)}Cr`
  if (n >= 1e5) return `₹${(n / 1e5).toFixed(2)}L`
  return `₹${Math.round(n).toLocaleString('en-IN')}`
}

export default function DashboardOverview() {
  const [holdings, setHoldings] = useState<Holding[]>([])
  const [totals, setTotals] = useState<{ value: number; gainPct: number }>({ value: 0, gainPct: 0 })
  const [audits, setAudits] = useState<AuditSummary[]>([])
  const [usage, setUsage] = useState<AnakinUsageReport | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    (async () => {
      try {
        const v = await getPortfolioValuation('demo-user')
        const hs: Holding[] = v.holdings || []
        setHoldings(hs)
        const value = v.total_current_value ?? hs.reduce((s, h) => s + (h.current_value || 0), 0)
        const gainPct = v.total_gain_loss_pct ?? 0
        setTotals({ value, gainPct })
      } catch { /* no portfolio in prod demo-off */ }
      try { setAudits((await getAuditHistory('demo-user')).audits) } catch { /* */ }
      try { setUsage(await getAnakinUsage()) } catch { /* */ }
      setLoading(false)
    })()
  }, [])

  const avgTrust = audits.length
    ? Math.round(audits.reduce((s, a) => s + (a.trust_score || 0), 0) / audits.length)
    : 0

  const chartData = (holdings.length
    ? holdings.map((h) => ({ name: (h.fund_name || '').split(' ')[0], v: Number((h.gain_loss_pct || 0).toFixed(1)) }))
    : audits.map((a) => ({ name: (a.fund_name || '').split(' ')[0], v: a.trust_score }))
  ).slice(0, 12)

  const today = new Date().toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' })

  const stats = [
    { label: 'Total Portfolio Value', value: totals.value ? inr(totals.value) : '—', sub: 'across holdings', Icon: Wallet },
    { label: 'Total Gain / Loss', value: totals.value ? `${totals.gainPct >= 0 ? '+' : ''}${totals.gainPct.toFixed(1)}%` : '—', sub: 'since investment', Icon: TrendingUp, tone: totals.gainPct >= 0 ? 'gain' : 'loss' },
    { label: 'Funds Audited', value: String(audits.length), sub: 'evidence-linked', Icon: ShieldCheck },
    { label: 'Average Trust Score', value: audits.length ? String(avgTrust) : '—', sub: 'out of 100', Icon: Gauge },
  ]

  return (
    <AppShell title="Overview">
      <div className="mb-6">
        <div className="text-xs text-textFaint">{today} · everything at a glance</div>
        <h2 className="mt-1 font-display text-3xl font-semibold">Welcome back</h2>
      </div>

      {/* stat cards */}
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {stats.map(({ label, value, sub, Icon, tone }) => (
          <div key={label} className="ff-card p-5">
            <div className="flex items-center justify-between">
              <span className="text-sm text-textSecondary">{label}</span>
              <Icon size={16} className="text-textFaint" />
            </div>
            <div className={`mt-3 font-display text-3xl font-bold ${tone === 'gain' ? 'text-gain' : tone === 'loss' ? 'text-loss' : ''}`}>{value}</div>
            <div className="mt-1 text-xs text-textFaint">{sub}</div>
          </div>
        ))}
      </div>

      <div className="mt-4 grid gap-4 lg:grid-cols-5">
        {/* chart */}
        <div className="ff-card p-5 lg:col-span-3">
          <div className="mb-1 font-display text-lg font-semibold">{holdings.length ? 'Holdings Performance' : 'Audited Funds — Trust Scores'}</div>
          <div className="mb-4 text-xs text-textFaint">{holdings.length ? 'Gain / loss % per holding' : 'Trust score per audited fund'}</div>
          {loading ? <div className="h-56 animate-pulse rounded-xl bg-background" /> : chartData.length === 0 ? (
            <div className="grid h-56 place-items-center text-sm text-textFaint">No data yet — run an audit to populate this.</div>
          ) : (
            <ResponsiveContainer width="100%" height={224}>
              <BarChart data={chartData}>
                <XAxis dataKey="name" tick={{ fontSize: 11, fill: '#8A8F99' }} axisLine={false} tickLine={false} />
                <Tooltip cursor={{ fill: '#0B0D1208' }} contentStyle={{ borderRadius: 12, border: '1px solid #E7E9EE', fontSize: 12 }} />
                <Bar dataKey="v" radius={[6, 6, 0, 0]}>
                  {chartData.map((d, i) => <Cell key={i} fill={d.v >= 0 ? '#0E9F6E' : '#E02424'} />)}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* latest audits */}
        <div className="ff-card p-5 lg:col-span-2">
          <div className="mb-1 flex items-center justify-between">
            <span className="font-display text-lg font-semibold">Latest Audits</span>
            <Link href="/audit/history" className="text-xs font-medium text-accent">View all</Link>
          </div>
          <div className="mb-3 text-xs text-textFaint">Ranked by trust score</div>
          {audits.length === 0 ? (
            <div className="text-sm text-textFaint">No audits yet. <Link href="/audit" className="text-accent underline">Run one</Link>.</div>
          ) : (
            <div className="space-y-3">
              {audits.slice(0, 4).map((a) => (
                <Link key={a.audit_id} href={`/audit/view?id=${a.audit_id}`} className="block rounded-xl border border-cardBorder p-3 transition-shadow hover:shadow-sm">
                  <div className="flex items-start justify-between gap-2">
                    <div className="text-sm font-semibold leading-tight">{a.fund_name}</div>
                    <span className="font-mono-num text-lg font-bold">{a.trust_score}</span>
                  </div>
                  <div className="mt-2 h-1.5 w-full rounded-full bg-background">
                    <div className="h-1.5 rounded-full bg-accent" style={{ width: `${a.trust_score}%` }} />
                  </div>
                  <span className={`mt-2 inline-block rounded-full border px-2 py-0.5 text-[10px] font-bold ${verdictColor(a.verdict)}`}>{a.verdict}</span>
                </Link>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* anakin usage band */}
      <div className="mt-4 ff-card p-5">
        <div className="mb-3 flex items-center justify-between">
          <span className="font-display text-lg font-semibold">Anakin usage</span>
          <Link href="/settings/usage" className="text-xs font-medium text-accent">Details <ArrowRight size={12} className="inline" /></Link>
        </div>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          {[['Budget', usage?.configured_budget ?? '—'], ['Est. used', usage?.estimated_credits_used ?? '—'],
            ['Used today', usage?.estimated_credits_today ?? '—'], ['Cache hit rate', usage ? `${Math.round(usage.cache_hit_rate * 100)}%` : '—']].map(([l, v]) => (
            <div key={l as string}>
              <div className="font-mono-num text-2xl font-semibold">{v as string}</div>
              <div className="text-xs text-textFaint">{l as string}</div>
            </div>
          ))}
        </div>
        <div className="mt-2 text-[10px] text-textFaint">Locally tracked Anakin usage — not Anakin&apos;s official balance.</div>
      </div>
    </AppShell>
  )
}
