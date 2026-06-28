'use client'

import Link from 'next/link'
import { ShieldCheck, TrendingUp, GitCompare, UserCheck, Layers, FileSearch, AudioLines, ArrowRight } from 'lucide-react'
import PipelineFlow from '@/components/landing/PipelineFlow'
import TickerBar from '@/components/landing/TickerBar'
import FundFlowOrb from '@/components/app/FundFlowOrb'

const FEATURES = [
  { Icon: TrendingUp, title: 'Portfolio tracking', desc: 'Real-time AMFI NAV, gain/loss and holdings — your existing FundFlow portfolio.' },
  { Icon: ShieldCheck, title: 'Manager Said vs Did', desc: 'Match the manager’s stated intentions against what the portfolio actually did.' },
  { Icon: Layers, title: 'Style Drift', desc: 'Check holdings against the scheme’s stated mandate and market-cap floor.' },
  { Icon: UserCheck, title: 'Manager Track-Record Continuity', desc: 'See how much of the advertised return the current manager actually managed.' },
  { Icon: GitCompare, title: 'NFO Clone Detector', desc: 'Deterministic similarity of a new fund against a curated comparison universe.' },
  { Icon: FileSearch, title: 'Evidence-first audit', desc: 'Every finding links to its source document, reporting period and Anakin job ID.' },
]

const SOURCES = ['AMFI', 'Morningstar India', 'Economic Times', 'NSE', 'BSE', 'Anakin Universal Scraper', 'Anakin Wire', 'Gemini', 'ElevenLabs']

export default function HomePage() {
  return (
    <div className="min-h-screen bg-background">
      <TickerBar />
      <header className="sticky top-[34px] z-40 border-b border-cardBorder bg-white/80 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
          <Link href="/" className="flex items-center gap-2">
            <span className="grid h-8 w-8 place-items-center rounded-lg bg-accent text-sm font-bold text-white">F</span>
            <span className="font-display text-lg font-semibold">FundFlow</span>
          </Link>
          <div className="flex items-center gap-3">
            <Link href="/audit" className="ff-btn-ghost text-sm">Audit a Fund</Link>
            <Link href="/dashboard" className="ff-btn-primary text-sm">Open FundFlow <ArrowRight size={15} /></Link>
          </div>
        </div>
      </header>

      <section className="relative overflow-hidden">
        <div className="pointer-events-none absolute -left-40 -top-40 h-96 w-96 rounded-full bg-gradient-to-br from-black/[0.04] to-transparent blur-3xl" />
        <div className="pointer-events-none absolute -right-40 top-20 h-96 w-96 rounded-full bg-gradient-to-br from-black/[0.04] to-transparent blur-3xl" />
        <div className="mx-auto grid max-w-6xl items-center gap-10 px-6 py-20 lg:grid-cols-2">
          <div className="animate-fade-in">
            <div className="mb-5 inline-flex items-center gap-2 rounded-full border border-cardBorder bg-white px-3 py-1 text-xs font-medium text-textSecondary">
              <span className="h-1.5 w-1.5 rounded-full bg-gain" /> Powered by Anakin Universal Scraper + Wire
            </div>
            <h1 className="font-display text-5xl font-bold leading-[1.05] md:text-6xl">
              Track your funds.<br />
              <span className="bg-gradient-to-r from-accent via-textSecondary to-accent bg-[length:200%_auto] bg-clip-text text-transparent animate-[shimmer_4s_linear_infinite]">
                Trust your funds.
              </span>
            </h1>
            <p className="mt-6 max-w-xl text-lg text-textSecondary">
              Your portfolio tells you what your mutual funds are worth. FundFlow Audit tells you whether
              the manager is keeping their promises.
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              <Link href="/dashboard" className="ff-btn-primary px-6 py-3">Open FundFlow</Link>
              <Link href="/audit" className="ff-btn-ghost px-6 py-3">Audit a Fund</Link>
            </div>
          </div>

          {/* Floating audit preview card */}
          <div className="relative animate-fade-in">
            <div className="ff-card animate-[orb-pulse_6s_ease-in-out_infinite] p-6 shadow-[0_30px_80px_-24px_rgba(11,13,18,0.22)]">
              <div className="flex items-start justify-between">
                <div>
                  <div className="text-xs text-textFaint">FundFlow Audit · Mid Cap</div>
                  <div className="font-display text-lg font-semibold leading-tight">HDFC Mid-Cap Opportunities</div>
                </div>
                <div className="text-right">
                  <div className="font-mono-num text-3xl font-bold">58</div>
                  <div className="rounded-full border border-warn/20 bg-warn/10 px-2 py-0.5 text-[10px] font-bold text-warn">REVIEW</div>
                </div>
              </div>
              {/* sparkline */}
              <svg viewBox="0 0 320 80" className="mt-4 w-full" preserveAspectRatio="none">
                <polyline fill="none" stroke="#0B0D12" strokeWidth="2"
                  points="0,60 40,52 80,56 120,40 160,44 200,28 240,32 280,18 320,22" />
                <polyline fill="rgba(11,13,18,0.06)" stroke="none"
                  points="0,60 40,52 80,56 120,40 160,44 200,28 240,32 280,18 320,22 320,80 0,80" />
              </svg>
              <div className="mt-4 space-y-2 text-sm">
                <div className="flex items-center justify-between"><span className="text-textSecondary">Manager Said vs Did</span><span className="font-semibold text-loss">Mismatch</span></div>
                <div className="flex items-center justify-between"><span className="text-textSecondary">Style Drift</span><span className="font-semibold text-warn">Warning</span></div>
                <div className="flex items-center justify-between"><span className="text-textSecondary">Manager Continuity</span><span className="font-semibold text-gain">Stable</span></div>
              </div>
              <div className="mt-4 rounded-lg bg-background p-2 text-[11px] text-textFaint">
                “Financials rose 28% → 34% despite an <span className="font-medium text-textSecondary">underweight</span> statement.”
              </div>
            </div>
          </div>
        </div>

        <div className="border-y border-cardBorder bg-white py-4">
          <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-center gap-x-8 gap-y-2 px-6 text-sm font-medium text-textFaint">
            {SOURCES.map((s) => <span key={s}>{s}</span>)}
          </div>
        </div>
      </section>

      <PipelineFlow />

      <section className="mx-auto max-w-6xl px-6 pb-20">
        <h2 className="mb-10 text-center font-display text-3xl font-semibold">What FundFlow checks</h2>
        <div className="grid gap-4 md:grid-cols-3">
          {FEATURES.map(({ Icon, title, desc }) => (
            <div key={title} className="ff-card p-6">
              <div className="mb-3 grid h-11 w-11 place-items-center rounded-xl bg-background"><Icon size={20} /></div>
              <div className="font-display text-lg font-semibold">{title}</div>
              <p className="mt-1.5 text-sm text-textSecondary">{desc}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="mx-auto max-w-4xl px-6 pb-24 text-center">
        <div className="ff-card p-10">
          <AudioLines className="mx-auto mb-4 text-accent" size={32} />
          <h2 className="font-display text-2xl font-semibold">Ask FundFlow, out loud</h2>
          <p className="mx-auto mt-2 max-w-xl text-textSecondary">
            The FundFlow Orb narrates any audit verdict and answers questions grounded in your saved
            evidence — in simple English or Hinglish.
          </p>
        </div>
      </section>

      <footer className="border-t border-cardBorder bg-white py-8 text-center text-sm text-textFaint">
        <p>FundFlow — AI-assisted document & portfolio consistency audit, not investment advice.</p>
        <p className="mt-1">Verify source documents and consult a SEBI-registered investment adviser before making decisions.</p>
      </footer>

      <FundFlowOrb />
    </div>
  )
}
