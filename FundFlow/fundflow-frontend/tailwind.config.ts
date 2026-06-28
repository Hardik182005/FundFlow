import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        // FundFlow neutral/graphite system (Cadence design migration)
        background: '#F7F8FA',
        accent: '#0B0D12',          // strong black CTA / primary
        accentSoft: '#3A3E47',
        gain: '#0E9F6E',            // green = positive / pass
        warn: '#D98A00',            // amber = warning
        loss: '#E02424',            // red = fail
        textPrimary: '#0B0D12',
        textSecondary: '#565B66',
        textFaint: '#8A8F99',
        cardBg: '#FFFFFF',
        cardBorder: '#E7E9EE',
        tickerBg: '#0B0D12',
      },
      fontFamily: {
        display: ['Space Grotesk', 'system-ui', 'sans-serif'],
        inter: ['Inter', 'sans-serif'],
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      borderRadius: {
        xl2: '1.25rem',
      },
      animation: {
        ticker: 'ticker 40s linear infinite',
        'count-up': 'count-up 1s ease-out',
        'fade-in': 'fade-in 0.5s ease-out',
        shimmer: 'shimmer 2s infinite',
        'orb-pulse': 'orb-pulse 2.4s ease-in-out infinite',
        'flow-dash': 'flow-dash 1.4s linear infinite',
      },
      keyframes: {
        ticker: {
          '0%': { transform: 'translateX(0)' },
          '100%': { transform: 'translateX(-50%)' },
        },
        'fade-in': {
          from: { opacity: '0', transform: 'translateY(10px)' },
          to: { opacity: '1', transform: 'translateY(0)' },
        },
        shimmer: {
          '0%': { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' },
        },
        'orb-pulse': {
          '0%,100%': { transform: 'scale(1)', opacity: '0.9' },
          '50%': { transform: 'scale(1.06)', opacity: '1' },
        },
        'flow-dash': {
          to: { strokeDashoffset: '-24' },
        },
      },
    },
  },
  plugins: [],
}

export default config
