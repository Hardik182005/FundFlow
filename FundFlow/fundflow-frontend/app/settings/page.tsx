'use client'

import { useEffect, useState } from 'react'
import AppShell from '@/components/app/AppShell'
import { getFundSources, updateFundSources, validateFundSource } from '@/lib/api'
import type { FundSource } from '@/lib/types'
import { Check, AlertCircle, Loader2 } from 'lucide-react'

const FIELDS: [keyof FundSource, string][] = [
  ['factsheet_current_url', 'Current factsheet'],
  ['factsheet_previous_url', 'Previous factsheet'],
  ['manager_commentary_url', 'Manager commentary'],
  ['sid_url', 'SID'],
  ['annual_report_url', 'Annual report'],
  ['manager_profile_url', 'Manager profile'],
]

export default function SettingsPage() {
  const [funds, setFunds] = useState<FundSource[]>([])
  const [active, setActive] = useState<FundSource | null>(null)
  const [saving, setSaving] = useState(false)
  const [validation, setValidation] = useState<Record<string, { valid: boolean; reason?: string; loading?: boolean }>>({})

  useEffect(() => { getFundSources().then((r) => setFunds(r.funds)) }, [])

  async function save() {
    if (!active) return
    setSaving(true)
    try { await updateFundSources(active.scheme_code, active) } finally { setSaving(false) }
  }

  async function validate(field: keyof FundSource) {
    if (!active) return
    const url = active[field] as string
    if (!url) return
    setValidation((v) => ({ ...v, [field]: { valid: false, loading: true } }))
    try {
      const r = await validateFundSource(url)
      setValidation((v) => ({ ...v, [field]: { valid: r.valid, reason: r.reason } }))
    } catch {
      setValidation((v) => ({ ...v, [field]: { valid: false, reason: 'Validation failed' } }))
    }
  }

  return (
    <AppShell title="Settings — Fund Sources">
      <div className="grid gap-6 lg:grid-cols-3">
        <div className="space-y-2">
          {funds.map((f) => (
            <button key={f.scheme_code} onClick={() => { setActive(f); setValidation({}) }}
              className={`ff-card w-full p-3 text-left ${active?.scheme_code === f.scheme_code ? 'ring-2 ring-accent' : ''}`}>
              <div className="text-xs text-textFaint">{f.amc}</div>
              <div className="text-sm font-semibold">{f.fund_name}</div>
            </button>
          ))}
        </div>

        <div className="lg:col-span-2">
          {active ? (
            <div className="ff-card space-y-4 p-5">
              <h3 className="font-display font-semibold">{active.fund_name}</h3>
              {FIELDS.map(([k, label]) => (
                <div key={k}>
                  <label className="text-xs font-medium text-textSecondary">{label}</label>
                  <div className="mt-1 flex gap-2">
                    <input className="ff-input" placeholder="https://… (verified URL only)" value={(active[k] as string) || ''}
                      onChange={(e) => setActive({ ...active, [k]: e.target.value })} />
                    <button className="ff-btn-ghost text-xs" onClick={() => validate(k)}>
                      {validation[k]?.loading ? <Loader2 className="animate-spin" size={14} /> : 'Validate'}
                    </button>
                  </div>
                  {validation[k] && !validation[k].loading && (
                    <div className={`mt-1 flex items-center gap-1 text-xs ${validation[k].valid ? 'text-gain' : 'text-loss'}`}>
                      {validation[k].valid ? <Check size={12} /> : <AlertCircle size={12} />}
                      {validation[k].valid ? 'Source reachable & non-empty' : (validation[k].reason || 'Unreachable')}
                    </div>
                  )}
                </div>
              ))}
              <button onClick={save} className="ff-btn-primary">{saving ? 'Saving…' : 'Save sources'}</button>
            </div>
          ) : (
            <div className="ff-card p-8 text-center text-textFaint">Select a fund to edit its verified source URLs.</div>
          )}
        </div>
      </div>
    </AppShell>
  )
}
