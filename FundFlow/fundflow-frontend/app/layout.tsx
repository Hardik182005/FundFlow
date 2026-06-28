import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'FundFlow — Your funds. Real NAV. Zero noise.',
  description: 'Track your MFU mutual fund portfolio with real-time AMFI NAV data and AI-powered analysis.',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="bg-[#F7F8FA] min-h-screen">
        {children}
      </body>
    </html>
  )
}
