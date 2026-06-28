'use client'

import { useEffect, useState } from 'react'
import { FileText, Globe2, Cpu, AudioLines } from 'lucide-react'

const STAGES = [
  { key: 'claim', label: 'Claim Layer', tech: 'Anakin Universal Scraper', desc: 'Retrieves factsheets, manager commentary, SID & annual reports as clean Markdown.', Icon: FileText },
  { key: 'reality', label: 'Reality Layer', tech: 'Anakin Wire', desc: 'Pulls structured fund holdings, ISIN & ratings via discovered Wire actions.', Icon: Globe2 },
  { key: 'reasoning', label: 'Reasoning Layer', tech: 'Gemini + deterministic scoring', desc: 'Extracts claims with Gemini; every number is computed in Python.', Icon: Cpu },
  { key: 'voice', label: 'Voice Layer', tech: 'ElevenLabs', desc: 'Narrates the evidence-linked verdict and answers your questions.', Icon: AudioLines },
]

export default function PipelineFlow() {
  const [active, setActive] = useState(0)
  useEffect(() => {
    const t = setInterval(() => setActive((a) => (a + 1) % STAGES.length), 2200)
    return () => clearInterval(t)
  }, [])

  return (
    <section className="mx-auto max-w-5xl px-6 py-20">
      <div className="mb-3 text-center text-xs font-semibold uppercase tracking-widest text-textFaint">How Anakin powers FundFlow</div>
      <h2 className="mb-12 text-center font-display text-3xl font-semibold">The audit pipeline</h2>

      <div className="relative grid gap-4 md:grid-cols-4">
        {/* connecting animated line (desktop) */}
        <div className="pointer-events-none absolute left-0 right-0 top-12 hidden md:block">
          <svg width="100%" height="4" className="overflow-visible">
            <line x1="6%" y1="2" x2="94%" y2="2" stroke="#E7E9EE" strokeWidth="2" />
            <line x1="6%" y1="2" x2="94%" y2="2" stroke="#0B0D12" strokeWidth="2"
              strokeDasharray="6 6" className="animate-flow-dash" />
          </svg>
        </div>

        {STAGES.map((s, i) => {
          const on = i <= active
          return (
            <div key={s.key} className={`relative rounded-2xl border bg-white p-5 transition-all duration-500 ${i === active ? 'border-accent shadow-lg' : 'border-cardBorder'}`}>
              <div className={`mb-3 grid h-12 w-12 place-items-center rounded-xl transition-colors duration-500 ${on ? 'bg-accent text-white' : 'bg-background text-textFaint'}`}>
                <s.Icon size={20} />
              </div>
              <div className="text-xs font-semibold uppercase tracking-wide text-textFaint">{`0${i + 1}`}</div>
              <div className="font-display text-lg font-semibold">{s.label}</div>
              <div className="mt-0.5 text-xs font-medium text-accent">{s.tech}</div>
              <p className="mt-2 text-sm text-textSecondary">{s.desc}</p>
            </div>
          )
        })}
      </div>

      <div className="mt-10 rounded-2xl border border-cardBorder bg-white p-5 text-center text-sm text-textSecondary">
        <span className="font-semibold text-textPrimary">Evidence-first:</span> every verdict links back to the exact source document,
        reporting period, Anakin job ID and cache status — no score appears without visible methodology.
      </div>
    </section>
  )
}
