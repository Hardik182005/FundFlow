const MODELS = [
  {
    tag: '70B', badge: 'Primary Analysis',
    name: 'Groq Llama 3.3',
    desc: 'Reads your fund\'s 12-month NAV, category, and risk signals. Gives verdict and recommendation.',
    color: '#0B0D12',
  },
  {
    tag: '1.5', badge: 'Fallback + PDF',
    name: 'Gemini Flash',
    desc: 'Generates detailed fund research PDF. Acts as fallback when Groq is processing.',
    color: '#0E9F6E',
  },
  {
    tag: '4o', badge: 'Fund Compare',
    name: 'GPT-4o',
    desc: 'Compares multiple funds head-to-head. Used only when you ask \'which fund is better\'.',
    color: '#FFA500',
  },
  {
    tag: 'V2', badge: 'Voice Agent',
    name: 'ElevenLabs',
    desc: 'Answers \'how is my portfolio today?\' in natural voice. Daily morning briefing mode.',
    color: '#E02424',
  },
]

export default function AIModelsSection() {
  return (
    <section className="py-20 px-6 bg-[#0A0A0A]">
      <div className="max-w-7xl mx-auto">
        <div className="text-center mb-16">
          <p className="text-xs font-bold uppercase tracking-[0.15em] text-[#0B0D12] mb-4">POWERED BY</p>
          <h2 className="text-4xl lg:text-5xl font-extrabold text-white mb-4">Four AI models. One portfolio read.</h2>
          <p className="text-lg text-[#888] max-w-xl mx-auto">
            Each model handles what it does best. Combined output in under 5 seconds.
          </p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {MODELS.map((m, i) => (
            <div key={i} className="bg-[#111] rounded-xl border border-[#222] p-6 hover:border-[#0B0D12]/40 transition-all">
              <div className="flex items-center justify-between mb-4">
                <span
                  className="text-2xl font-extrabold font-mono"
                  style={{ color: m.color }}
                >
                  {m.tag}
                </span>
                <span className="text-xs font-semibold uppercase tracking-wider text-[#666] border border-[#333] px-2 py-1 rounded-full">
                  {m.badge}
                </span>
              </div>
              <h3 className="font-bold text-white text-lg mb-2">{m.name}</h3>
              <p className="text-[#666] text-sm leading-relaxed">{m.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
