import { create } from 'zustand'

interface Holding {
  scheme_code: string
  fund_name: string
  units: number
  buy_nav: number
  investment_date?: string
}

interface PortfolioStore {
  holdings: Holding[]
  addHolding: (h: Holding) => void
  removeHolding: (schemeCode: string) => void
  setHoldings: (holdings: Holding[]) => void
}

export const usePortfolioStore = create<PortfolioStore>((set) => ({
  holdings: [],
  addHolding: (h) => set((s) => ({ holdings: [...s.holdings, h] })),
  removeHolding: (code) => set((s) => ({ holdings: s.holdings.filter((x) => x.scheme_code !== code) })),
  setHoldings: (holdings) => set({ holdings }),
}))
