// Trading Types
export interface MarketData {
  symbol: string
  price: number
  change24h: number
  changePercent24h: number
  volume24h: number
  high24h: number
  low24h: number
  timestamp: number
}

export interface OrderBookEntry {
  price: number
  quantity: number
  total: number
}

export interface OrderBook {
  symbol: string
  bids: OrderBookEntry[]
  asks: OrderBookEntry[]
  timestamp: number
}

export interface TradingSignal {
  id: string
  symbol: string
  action: 'BUY' | 'SELL'
  price: number
  quantity: number
  confidence: number
  strategy: string
  riskLevel: 'LOW' | 'MEDIUM' | 'HIGH'
  aiAnalysis?: {
    sentiment: number
    patterns: string[]
    prediction: string
  }
  timestamp: number
}

export interface Position {
  id: string
  symbol: string
  side: 'LONG' | 'SHORT'
  entryPrice: number
  currentPrice: number
  quantity: number
  unrealizedPnL: number
  unrealizedPnLPercent: number
  realizedPnL: number
  timestamp: number
  stopLoss?: number
  takeProfit?: number
}

export interface Trade {
  id: string
  symbol: string
  side: 'BUY' | 'SELL'
  price: number
  quantity: number
  fee: number
  pnl: number
  pnlPercent: number
  timestamp: number
  strategy: string
}

export interface Portfolio {
  totalValue: number
  totalPnL: number
  totalPnLPercent: number
  availableBalance: number
  positions: Position[]
  dailyPnL: number
  weeklyPnL: number
  monthlyPnL: number
}

export interface TradingMetrics {
  winRate: number
  totalTrades: number
  avgWin: number
  avgLoss: number
  profitFactor: number
  sharpeRatio: number
  maxDrawdown: number
  maxDrawdownPercent: number
}

// WebSocket Types
export interface WebSocketMessage {
  type: 'market_data' | 'trading_signal' | 'position_update' | 'trade_executed' | 'error'
  data: unknown
  timestamp: number
}

export interface MarketDataMessage extends WebSocketMessage {
  type: 'market_data'
  data: MarketData
}

export interface TradingSignalMessage extends WebSocketMessage {
  type: 'trading_signal'
  data: TradingSignal
}

export interface PositionUpdateMessage extends WebSocketMessage {
  type: 'position_update'
  data: Position
}

export interface TradeExecutedMessage extends WebSocketMessage {
  type: 'trade_executed'
  data: Trade
}

// Chart Types
export interface CandlestickData {
  timestamp: number
  open: number
  high: number
  low: number
  close: number
  volume: number
}

export interface ChartIndicator {
  name: string
  values: { timestamp: number; value: number }[]
  color: string
}

// UI Types
export interface Tab {
  id: string
  label: string
  icon?: React.ComponentType<{ className?: string }>
  component: React.ComponentType
}

export interface DashboardWidget {
  id: string
  title: string
  component: React.ComponentType<{ data?: unknown }>
  gridArea?: string
  minWidth?: number
  minHeight?: number
}

// API Types
export interface ApiResponse<T = unknown> {
  success: boolean
  data?: T
  error?: string
  timestamp: number
}

export interface BacktestResult {
  strategy: string
  timeframe: string
  totalReturn: number
  totalReturnPercent: number
  winRate: number
  totalTrades: number
  avgWin: number
  avgLoss: number
  profitFactor: number
  sharpeRatio: number
  maxDrawdown: number
  maxDrawdownPercent: number
  trades: Trade[]
  equity: { timestamp: number; value: number }[]
}

// Store Types
export interface AppState {
  isConnected: boolean
  isDarkMode: boolean
  selectedSymbol: string
  symbols: string[]
  marketData: Record<string, MarketData>
  orderBooks: Record<string, OrderBook>
  positions: Position[]
  trades: Trade[]
  portfolio: Portfolio
  tradingMetrics: TradingMetrics
  signals: TradingSignal[]
  notifications: Notification[]
}

export interface Notification {
  id: string
  type: 'success' | 'error' | 'warning' | 'info'
  title: string
  message: string
  timestamp: number
  read: boolean
}

// Configuration Types
export interface TradingConfig {
  enabledStrategies: string[]
  riskLevel: 'LOW' | 'MEDIUM' | 'HIGH'
  maxPositions: number
  maxPositionSize: number
  stopLossPercent: number
  takeProfitPercent: number
  enableAI: boolean
  autoTrading: boolean
}

export interface ExchangeConfig {
  name: string
  apiKey: string
  apiSecret: string
  sandbox: boolean
  enabledPairs: string[]
}
