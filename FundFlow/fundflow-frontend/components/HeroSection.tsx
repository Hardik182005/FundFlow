'use client'
import Link from 'next/link'
import { LineChart, Line, ResponsiveContainer } from 'recharts'

const sparkData = [
  { v: 4210 }, { v: 4225 }, { v: 4218 }, { v: 4240 }, { v: 4252 },
  { v: 4248 }, { v: 4261 }, { v: 4270 }, { v: 4278 }, { v: 4287 },
]

export default function HeroSection() {
  return (
    <section className="pt-32 pb-24 px-6 max-w-7xl mx-auto">
      <div className="grid lg:grid-cols-2 gap-16 items-center">
        {/* Left */}
        <div className="animate-[fade-in_0.6s_ease-out]">
          <h1 className="text-6xl lg:text-7xl font-extrabold text-[#0A0A0A] leading-tight mb-2">
            Your funds grow.
          </h1>
          <h1 className="text-6xl lg:text-7xl font-extrabold text-[#0B0D12] leading-tight mb-6">
            We track every rupee.
          </h1>
          <p className="text-xl text-[#565B66] mb-10 max-w-lg leading-relaxed">
            Connect your MFU portfolio. Get real NAV from AMFI daily. AI tells you what to do next.
          </p>
          <div className="flex flex-wrap gap-4">
            <Link
              href="/dashboard"
              className="bg-[#0B0D12] text-white font-semibold px-8 py-4 rounded-lg hover:bg-[#000000] transition-all hover:shadow-lg hover:shadow-[#0B0D12]/20 text-base"
            >
              Track My Portfolio
            </Link>
            <a
              href="#how-it-works"
              className="border-2 border-[#E7E9EE] text-[#0A0A0A] font-semibold px-8 py-4 rounded-lg hover:border-[#0B0D12] hover:text-[#0B0D12] transition-colors text-base"
            >
              See How It Works
            </a>
          </div>
        </div>

        {/* Right — NAV Card */}
        <div className="flex justify-center lg:justify-end animate-[fade-in_0.8s_ease-out]">
          <div className="bg-white rounded-2xl border border-[#E7E9EE] shadow-xl p-6 w-80">
            <div className="flex items-start justify-between mb-4">
              <div>
                <p className="text-xs font-semibold uppercase tracking-widest text-[#565B66] mb-1">AMC: TATA</p>
                <h3 className="font-bold text-[#0A0A0A] text-base leading-tight">TATA MONEY MARKET FUND</h3>
              </div>
              <span className="bg-[#0E9F6E]/10 text-[#0E9F6E] text-xs font-bold px-2 py-1 rounded-full">HOLD</span>
            </div>
            <div className="mb-1">
              <span className="text-4xl font-mono font-bold text-[#0A0A0A]">4,287.54</span>
            </div>
            <div className="flex items-center gap-2 mb-4">
              <span className="text-[#0E9F6E] text-sm font-semibold">▲ +1.24%</span>
              <span className="text-[#565B66] text-xs">from yesterday</span>
            </div>
            <div className="h-20">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={sparkData}>
                  <Line type="monotone" dataKey="v" stroke="#0B0D12" strokeWidth={2} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
            <p className="text-xs text-[#565B66] mt-2 text-right">NAV as of today · AMFI</p>
          </div>
        </div>
      </div>
    </section>
  )
}
