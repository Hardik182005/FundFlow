export default function DataSourcesMarquee() {
  const labels = [
    'DATA SOURCES', 'AMFI DAILY NAV', 'MFAPI.IN',
    'ET MARKETS NEWS', 'MONEYCONTROL', 'MFU IMPORT',
    'GROQ AI', 'GEMINI FLASH', 'FIREBASE', 'SEBI DATA',
  ]
  const doubled = [...labels, ...labels]
  return (
    <div className="border-y border-[#E7E9EE] py-4 overflow-hidden bg-white">
      <div className="ticker-track flex items-center" style={{ animationDuration: '25s' }}>
        {doubled.map((label, i) => (
          <span key={i} className="text-xs font-bold uppercase tracking-[0.12em] text-[#565B66] mr-10 shrink-0">
            {i % (labels.length) === 0 ? (
              <span className="text-[#0B0D12]">{label}</span>
            ) : (
              <>
                <span className="text-[#E7E9EE] mr-10">•</span>
                {label}
              </>
            )}
          </span>
        ))}
      </div>
    </div>
  )
}
