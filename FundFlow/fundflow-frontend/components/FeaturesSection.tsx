import { Sparkles, Activity, Target, Newspaper } from 'lucide-react'

const FEATURES = [
  {
    icon: Sparkles,
    title: 'AI Verdict',
    desc: 'Groq Llama 3.3 reads your fund\'s NAV history, category, and risk profile. Tells you HOLD / ADD / EXIT in plain Hindi-English. No jargon.',
  },
  {
    icon: Activity,
    title: 'NAV Pulse',
    desc: 'Real-time NAV from AMFI every day. See exactly how much your ₹ grew or fell since yesterday. Auto-updated at 11:30 PM.',
  },
  {
    icon: Target,
    title: 'Fund Intel',
    desc: '1Y, 3Y, 5Y returns. Expense ratio. Morningstar rating. Category risk. Everything about your fund in one panel.',
  },
  {
    icon: Newspaper,
    title: 'MF News Feed',
    desc: 'Latest mutual fund news from ET Markets and Moneycontrol. Know what\'s affecting your funds before NAV moves.',
  },
]

export default function FeaturesSection() {
  return (
    <section id="features" className="py-20 px-6 max-w-7xl mx-auto">
      <div className="text-center mb-16">
        <p className="text-xs font-bold uppercase tracking-[0.15em] text-[#0B0D12] mb-4">WHAT FUNDFLOW DOES</p>
        <h2 className="text-4xl lg:text-5xl font-extrabold text-[#0A0A0A] mb-4">Every fund. One dashboard.</h2>
        <p className="text-lg text-[#565B66] max-w-xl mx-auto">
          Built for the Indian MFU investor tired of opening 6 apps to check their portfolio.
        </p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {FEATURES.map((f, i) => (
          <div key={i} className="bg-white rounded-xl border border-[#E7E9EE] p-6 hover:shadow-lg hover:border-[#0B0D12]/30 transition-all duration-300 group">
            <div className="w-12 h-12 bg-[#0B0D12]/10 rounded-xl flex items-center justify-center mb-4 group-hover:bg-[#0B0D12]/20 transition-colors">
              <f.icon className="w-6 h-6 text-[#0B0D12]" />
            </div>
            <h3 className="font-bold text-lg text-[#0A0A0A] mb-2">{f.title}</h3>
            <p className="text-[#565B66] text-sm leading-relaxed">{f.desc}</p>
          </div>
        ))}
      </div>
    </section>
  )
}
