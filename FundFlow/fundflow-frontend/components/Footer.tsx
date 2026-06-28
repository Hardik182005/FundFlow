import Link from 'next/link'

export default function Footer() {
  return (
    <footer className="bg-[#0A0A0A] text-white pt-16 pb-8 px-6">
      <div className="max-w-7xl mx-auto">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-12 mb-12">
          <div>
            <div className="flex items-center gap-2 mb-4">
              <div className="w-8 h-8 bg-[#0B0D12] rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-sm">F</span>
              </div>
              <span className="font-bold text-xl">FundFlow</span>
            </div>
            <p className="text-[#666] text-sm leading-relaxed">Your MFU portfolio. Fully intelligent.</p>
          </div>
          <div className="flex flex-col gap-3">
            <p className="text-xs font-bold uppercase tracking-widest text-[#444] mb-2">Navigation</p>
            {['Home', 'Features', 'How it works', 'Portfolio', 'News'].map((l) => (
              <Link key={l} href={l === 'Home' ? '/' : l === 'Portfolio' ? '/dashboard' : `/#${l.toLowerCase().replace(' ', '-')}`}
                className="text-sm text-[#666] hover:text-white transition-colors"
              >
                {l}
              </Link>
            ))}
          </div>
          <div>
            <p className="text-xs font-bold uppercase tracking-widest text-[#444] mb-4">Infrastructure</p>
            <p className="text-sm text-[#666]">Powered by Mediflow Nexus</p>
          </div>
        </div>
        <div className="border-t border-[#1a1a1a] pt-8">
          <p className="text-xs text-[#444] text-center">
            NAV data sourced from AMFI India. Updated daily. Not SEBI registered investment advice.
          </p>
        </div>
      </div>
    </footer>
  )
}
