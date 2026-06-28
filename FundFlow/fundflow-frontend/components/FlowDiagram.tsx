import { ArrowRight } from 'lucide-react'

const STEPS = [
  {
    label: 'Your MFU Holdings',
    tags: ['MFU Import', 'Manual Entry'],
  },
  {
    label: 'AMFI NAV Engine',
    tags: ['AMFI', 'mfapi.in', 'NAV History'],
    badge: 'LIVE',
  },
  {
    label: 'Structured Data',
    tags: ['NAV', 'Units', 'Value', 'Fund Category'],
  },
  {
    label: 'AI Reasoning',
    tags: ['Groq', 'Gemini', 'News'],
    badge: 'verdict',
  },
  {
    label: 'Your Action',
    isAction: true,
  },
]

export default function FlowDiagram() {
  return (
    <section id="how-it-works" className="py-20 px-6 max-w-7xl mx-auto">
      <div className="text-center mb-16">
        <p className="text-xs font-bold uppercase tracking-[0.15em] text-[#0B0D12] mb-4">HOW IT WORKS</p>
        <h2 className="text-4xl lg:text-5xl font-extrabold text-[#0A0A0A] mb-4">How FundFlow works</h2>
      </div>

      <div className="flex flex-col lg:flex-row items-center justify-center gap-4">
        {STEPS.map((step, i) => (
          <div key={i} className="flex items-center gap-4">
            <div className="relative">
              {step.isAction ? (
                <div className="bg-[#0B0D12] rounded-xl p-5 flex flex-col gap-2 min-w-[140px]">
                  <p className="text-white font-bold text-sm text-center mb-2">{step.label}</p>
                  {['● HOLD', '◎ ADD', '✕ EXIT'].map((btn, j) => (
                    <button key={j} className="text-white text-xs border border-white/30 rounded px-3 py-1 font-semibold hover:bg-white/10 transition-colors">
                      {btn}
                    </button>
                  ))}
                </div>
              ) : (
                <div className="bg-white border border-[#E7E9EE] rounded-xl p-4 min-w-[140px] shadow-sm">
                  {step.badge && (
                    <span className="text-xs font-bold text-[#0B0D12] uppercase tracking-wider mb-2 block">{step.badge}</span>
                  )}
                  <p className="font-bold text-[#0A0A0A] text-sm mb-3">{step.label}</p>
                  <div className="flex flex-wrap gap-1">
                    {step.tags?.map((tag, j) => (
                      <span key={j} className="text-xs bg-[#F7F8FA] text-[#565B66] px-2 py-0.5 rounded-full border border-[#E7E9EE]">
                        {tag}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
            {i < STEPS.length - 1 && (
              <ArrowRight className="w-5 h-5 text-[#0B0D12] shrink-0 hidden lg:block" />
            )}
          </div>
        ))}
      </div>
    </section>
  )
}
