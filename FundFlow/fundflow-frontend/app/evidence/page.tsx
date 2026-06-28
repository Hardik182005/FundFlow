'use client'

import { useEffect, useState } from 'react'
import AppShell from '@/components/app/AppShell'
import { getAuditHistory, getFundAudit } from '@/lib/api'
import type { SourceEvidence } from '@/lib/types'

export default function EvidencePage() {
  const [evidence, setEvidence] = useState<(SourceEvidence & { fund?: string })[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    (async () => {
      try {
        const { audits } = await getAuditHistory()
        const full = await Promise.all(audits.slice(0, 5).map((a) => getFundAudit(a.audit_id).catch(() => null)))
        const all: (SourceEvidence & { fund?: string })[] = []
        full.forEach((au) => au?.evidence.forEach((e) => all.push({ ...e, fund: au.fund_name })))
        setEvidence(all)
      } finally { setLoading(false) }
    })()
  }, [])

  return (
    <AppShell title="Evidence">
      <p className="mb-4 text-sm text-textFaint">Every audit conclusion is linked to a retrieved source. All web intelligence is fetched through Anakin.</p>
      {loading ? <div className="ff-card h-40 animate-pulse" /> : evidence.length === 0 ? (
        <div className="ff-card p-8 text-center text-textFaint">No evidence yet — run an audit to collect sources.</div>
      ) : (
        <div className="space-y-3">
          {evidence.map((e, i) => (
            <div key={i} className="ff-card p-4">
              <div className="flex flex-wrap items-center gap-2 text-xs text-textFaint">
                <span className="ff-badge bg-background">{e.source_type}</span>
                {e.fund && <span className="font-medium text-textSecondary">{e.fund}</span>}
                {e.reporting_period && <span>{e.reporting_period}</span>}
                <span className={e.cached ? 'text-textFaint' : 'text-gain'}>{e.cached ? 'cached' : 'fresh'}</span>
                {e.anakin_job_id && <span>Anakin job: {e.anakin_job_id}</span>}
              </div>
              <div className="mt-1 font-semibold">{e.title}</div>
              {e.excerpt && <p className="mt-1 text-sm text-textSecondary">“{e.excerpt}”</p>}
              {e.url && !e.url.startsWith('anakin-wire://') && (
                <a href={e.url} target="_blank" rel="noreferrer" className="mt-2 inline-block text-xs font-medium text-accent underline">View source</a>
              )}
            </div>
          ))}
        </div>
      )}
    </AppShell>
  )
}
