import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatCurrency(value: number, currency = 'USD'): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency,
    minimumFractionDigits: 2,
    maximumFractionDigits: 8,
  }).format(value)
}

export function formatNumber(value: number, decimals = 2): string {
  return new Intl.NumberFormat('en-US', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(value)
}

export function formatPercentage(value: number, decimals = 2): string {
  return `${value >= 0 ? '+' : ''}${formatNumber(value, decimals)}%`
}

export function formatLargeNumber(value: number): string {
  if (value >= 1e9) {
    return `${(value / 1e9).toFixed(2)}B`
  }
  if (value >= 1e6) {
    return `${(value / 1e6).toFixed(2)}M`
  }
  if (value >= 1e3) {
    return `${(value / 1e3).toFixed(2)}K`
  }
  return formatNumber(value)
}

export function debounce<T extends (...args: unknown[]) => unknown>(
  func: T,
  wait: number
): (...args: Parameters<T>) => void {
  let timeout: NodeJS.Timeout
  return (...args: Parameters<T>) => {
    clearTimeout(timeout)
    timeout = setTimeout(() => func(...args), wait)
  }
}

export function throttle<T extends (...args: unknown[]) => unknown>(
  func: T,
  limit: number
): (...args: Parameters<T>) => void {
  let inThrottle: boolean
  return (...args: Parameters<T>) => {
    if (!inThrottle) {
      func(...args)
      inThrottle = true
      setTimeout(() => (inThrottle = false), limit)
    }
  }
}

export function getRandomId(): string {
  return Math.random().toString(36).substring(2, 15)
}

export function calculatePnL(entry: number, current: number, quantity: number): {
  pnl: number
  pnlPercentage: number
} {
  const pnl = (current - entry) * quantity
  const pnlPercentage = ((current - entry) / entry) * 100
  return { pnl, pnlPercentage }
}

export function isValidPrice(price: number): boolean {
  return price > 0 && !isNaN(price) && isFinite(price)
}

export function getTradingPairSymbol(base: string, quote: string): string {
  return `${base}${quote}`.toUpperCase()
}

export function parseTradingPair(symbol: string): { base: string; quote: string } {
  // Common quote currencies to check against
  const quoteCurrencies = ['USDT', 'BTC', 'ETH', 'BUSD', 'USDC', 'BNB']
  
  for (const quote of quoteCurrencies) {
    if (symbol.endsWith(quote)) {
      return {
        base: symbol.substring(0, symbol.length - quote.length),
        quote,
      }
    }
  }
  
  // Fallback if no known quote currency found
  return {
    base: symbol.substring(0, symbol.length - 4),
    quote: symbol.substring(symbol.length - 4),
  }
}
