'use client'

const TICKER_ITEMS = [
  { name: 'TATA MONEY MARKET', nav: '4287.54', change: '+1.24%', up: true },
  { name: 'SBI BLUECHIP', nav: '98.23', change: '+0.34%', up: true },
  { name: 'HDFC MIDCAP OPP', nav: '145.67', change: '-0.82%', up: false },
  { name: 'AXIS ELSS', nav: '78.90', change: '+0.61%', up: true },
  { name: 'PARAG PARIKH FLEXI', nav: '72.45', change: '+0.91%', up: true },
  { name: 'MIRAE LARGE CAP', nav: '118.34', change: '+0.23%', up: true },
  { name: 'KOTAK EMERGING', nav: '89.12', change: '-0.44%', up: false },
  { name: 'NIPPON SMALLCAP', nav: '156.78', change: '+1.12%', up: true },
  { name: 'DSP MIDCAP', nav: '102.45', change: '+0.55%', up: true },
  { name: 'ICICI PRU TECH', nav: '234.56', change: '-1.23%', up: false },
]

export default function NavTicker() {
  const doubled = [...TICKER_ITEMS, ...TICKER_ITEMS]
  return (
    <div className="bg-[#0A0A0A] text-white overflow-hidden py-2.5 border-b border-[#1a1a1a]">
      <div className="ticker-track flex">
        {doubled.map((item, i) => (
          <div key={i} className="flex items-center gap-2 mr-10 shrink-0">
            <span className="text-xs font-semibold tracking-widest text-[#888888] uppercase">{item.name}</span>
            <span className="text-sm font-mono font-medium text-white">{item.nav}</span>
            <span className={`text-xs font-semibold ${item.up ? 'text-[#0E9F6E]' : 'text-[#E02424]'}`}>
              {item.up ? '▲' : '▼'} {item.change}
            </span>
            <span className="text-[#333] ml-4">|</span>
          </div>
        ))}
      </div>
    </div>
  )
}
