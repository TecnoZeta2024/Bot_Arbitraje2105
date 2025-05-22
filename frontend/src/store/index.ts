import { create } from 'zustand'
import { subscribeWithSelector } from 'zustand/middleware'
import type {
  AppState,
  MarketData,
  OrderBook,
  Position,
  Trade,
  Portfolio,
  TradingMetrics,
  TradingSignal,
  Notification,
  TradingConfig,
} from '@/types'

interface TradingStore extends AppState {
  // Actions
  setConnected: (connected: boolean) => void
  toggleDarkMode: () => void
  setSelectedSymbol: (symbol: string) => void
  updateMarketData: (data: MarketData) => void
  updateOrderBook: (orderBook: OrderBook) => void
  addPosition: (position: Position) => void
  updatePosition: (positionId: string, updates: Partial<Position>) => void
  removePosition: (positionId: string) => void
  addTrade: (trade: Trade) => void
  updatePortfolio: (portfolio: Partial<Portfolio>) => void
  updateTradingMetrics: (metrics: Partial<TradingMetrics>) => void
  addSignal: (signal: TradingSignal) => void
  addNotification: (notification: Omit<Notification, 'id' | 'timestamp'>) => void
  markNotificationAsRead: (notificationId: string) => void
  clearNotifications: () => void
  
  // Config
  tradingConfig: TradingConfig
  updateTradingConfig: (config: Partial<TradingConfig>) => void
  
  // Reset functions
  resetStore: () => void
}

const initialState: AppState = {
  isConnected: false,
  isDarkMode: true,
  selectedSymbol: 'BTCUSDT',
  symbols: [
    'BTCUSDT',
    'ETHUSDT',
    'BNBUSDT',
    'ADAUSDT',
    'SOLUSDT',
    'XRPUSDT',
    'DOTUSDT',
    'LINKUSDT',
    'LTCUSDT',
    'AVAXUSDT',
  ],
  marketData: {},
  orderBooks: {},
  positions: [],
  trades: [],
  portfolio: {
    totalValue: 10000,
    totalPnL: 0,
    totalPnLPercent: 0,
    availableBalance: 10000,
    positions: [],
    dailyPnL: 0,
    weeklyPnL: 0,
    monthlyPnL: 0,
  },
  tradingMetrics: {
    winRate: 0,
    totalTrades: 0,
    avgWin: 0,
    avgLoss: 0,
    profitFactor: 0,
    sharpeRatio: 0,
    maxDrawdown: 0,
    maxDrawdownPercent: 0,
  },
  signals: [],
  notifications: [],
}

const initialTradingConfig: TradingConfig = {
  enabledStrategies: ['scalping', 'day_trading'],
  riskLevel: 'MEDIUM',
  maxPositions: 5,
  maxPositionSize: 1000,
  stopLossPercent: 2,
  takeProfitPercent: 4,
  enableAI: true,
  autoTrading: false,
}

export const useTradingStore = create<TradingStore>()(
  subscribeWithSelector((set, get) => ({
    ...initialState,
    tradingConfig: initialTradingConfig,

    // Connection
    setConnected: (connected) => set({ isConnected: connected }),

    // UI State
    toggleDarkMode: () => set((state) => ({ isDarkMode: !state.isDarkMode })),

    setSelectedSymbol: (symbol) => set({ selectedSymbol: symbol }),

    // Market Data
    updateMarketData: (data) =>
      set((state) => ({
        marketData: {
          ...state.marketData,
          [data.symbol]: data,
        },
      })),

    updateOrderBook: (orderBook) =>
      set((state) => ({
        orderBooks: {
          ...state.orderBooks,
          [orderBook.symbol]: orderBook,
        },
      })),

    // Positions
    addPosition: (position) =>
      set((state) => ({
        positions: [...state.positions, position],
      })),

    updatePosition: (positionId, updates) =>
      set((state) => ({
        positions: state.positions.map((p) =>
          p.id === positionId ? { ...p, ...updates } : p
        ),
      })),

    removePosition: (positionId) =>
      set((state) => ({
        positions: state.positions.filter((p) => p.id !== positionId),
      })),

    // Trades
    addTrade: (trade) =>
      set((state) => ({
        trades: [trade, ...state.trades.slice(0, 999)], // Keep last 1000 trades
      })),

    // Portfolio
    updatePortfolio: (portfolio) =>
      set((state) => ({
        portfolio: { ...state.portfolio, ...portfolio },
      })),

    // Trading Metrics
    updateTradingMetrics: (metrics) =>
      set((state) => ({
        tradingMetrics: { ...state.tradingMetrics, ...metrics },
      })),

    // Signals
    addSignal: (signal) =>
      set((state) => ({
        signals: [signal, ...state.signals.slice(0, 99)], // Keep last 100 signals
      })),

    // Notifications
    addNotification: (notification) =>
      set((state) => ({
        notifications: [
          {
            ...notification,
            id: Math.random().toString(36).substring(2),
            timestamp: Date.now(),
            read: false,
          },
          ...state.notifications.slice(0, 49), // Keep last 50 notifications
        ],
      })),

    markNotificationAsRead: (notificationId) =>
      set((state) => ({
        notifications: state.notifications.map((n) =>
          n.id === notificationId ? { ...n, read: true } : n
        ),
      })),

    clearNotifications: () => set({ notifications: [] }),

    // Trading Config
    updateTradingConfig: (config) =>
      set((state) => ({
        tradingConfig: { ...state.tradingConfig, ...config },
      })),

    // Reset
    resetStore: () => set({ ...initialState, tradingConfig: initialTradingConfig }),
  }))
)

// Derived state selectors
export const useMarketData = (symbol?: string) =>
  useTradingStore((state) => 
    symbol ? state.marketData[symbol] : state.marketData
  )

export const useOrderBook = (symbol?: string) =>
  useTradingStore((state) => 
    symbol ? state.orderBooks[symbol] : state.orderBooks
  )

export const usePositions = () =>
  useTradingStore((state) => state.positions)

export const useRecentTrades = (limit = 10) =>
  useTradingStore((state) => state.trades.slice(0, limit))

export const useRecentSignals = (limit = 10) =>
  useTradingStore((state) => state.signals.slice(0, limit))

export const useUnreadNotifications = () =>
  useTradingStore((state) => state.notifications.filter((n) => !n.read))

export const usePortfolioMetrics = () =>
  useTradingStore((state) => ({
    portfolio: state.portfolio,
    metrics: state.tradingMetrics,
  }))

// Performance optimization: Create separate stores for high-frequency updates
export const usePriceStore = create<{
  prices: Record<string, number>
  updatePrice: (symbol: string, price: number) => void
}>((set) => ({
  prices: {},
  updatePrice: (symbol, price) =>
    set((state) => ({
      prices: { ...state.prices, [symbol]: price },
    })),
}))

// Connection status hook
export const useConnectionStatus = () =>
  useTradingStore((state) => state.isConnected)

// Trading configuration hook
export const useTradingConfig = () => 
  useTradingStore((state) => ({
    config: state.tradingConfig,
    updateConfig: state.updateTradingConfig,
  }))
