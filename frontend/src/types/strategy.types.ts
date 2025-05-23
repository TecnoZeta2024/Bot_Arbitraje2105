// Strategy Types for AI Trading System

export interface Strategy {
  id: string
  name: string
  type: StrategyType
  description: string
  isActive: boolean
  parameters: StrategyParameters
  performance: StrategyPerformance
  riskProfile: RiskProfile
  signals: Signal[]
  trades: Trade[]
  createdAt: number
  lastUpdated: number
}

export enum StrategyType {
  TREND_FOLLOWING = 'TREND_FOLLOWING',
  MEAN_REVERSION = 'MEAN_REVERSION',
  MOMENTUM = 'MOMENTUM',
  SCALPING = 'SCALPING',
  ARBITRAGE = 'ARBITRAGE',
  AI_HYBRID = 'AI_HYBRID'
}

export interface StrategyParameters {
  timeframe: string
  stopLoss: number
  takeProfit: number
  positionSize: number
  maxDailyLoss: number
  maxOpenPositions: number
  indicators: IndicatorConfig[]
  customParams?: Record<string, any>
}

export interface IndicatorConfig {
  name: string
  params: Record<string, number>
  weight: number
}

export interface StrategyPerformance {
  totalTrades: number
  winRate: number
  profitFactor: number
  sharpeRatio: number
  maxDrawdown: number
  totalPnL: number
  avgWin: number
  avgLoss: number
  bestTrade: number
  worstTrade: number
  currentStreak: number
  roi: number
}

export interface RiskProfile {
  riskLevel: 'LOW' | 'MEDIUM' | 'HIGH' | 'AGGRESSIVE'
  maxLeverage: number
  maxExposure: number
  stopLossEnabled: boolean
  trailingStopEnabled: boolean
  riskRewardRatio: number
}

export interface Signal {
  id: string
  strategyId: string
  symbol: string
  action: 'BUY' | 'SELL' | 'HOLD'
  price: number
  confidence: number
  indicators: IndicatorSignal[]
  timestamp: number
  metadata?: Record<string, any>
}

export interface IndicatorSignal {
  name: string
  value: number
  signal: 'BULLISH' | 'BEARISH' | 'NEUTRAL'
  strength: number
}

export interface Trade {
  id: string
  strategyId: string
  symbol: string
  side: 'BUY' | 'SELL'
  quantity: number
  entryPrice: number
  exitPrice?: number
  pnl?: number
  status: 'OPEN' | 'CLOSED' | 'CANCELLED'
  openTime: number
  closeTime?: number
  stopLoss?: number
  takeProfit?: number
}

export interface MarketSentiment {
  overall: 'BULLISH' | 'BEARISH' | 'NEUTRAL'
  score: number // -100 to 100
  components: {
    technical: number
    fundamental: number
    social: number
    onChain: number
  }
  signals: {
    fearGreedIndex: number
    volumeAnalysis: string
    trendStrength: number
    volatility: 'LOW' | 'MEDIUM' | 'HIGH'
  }
}

export interface PatternDetection {
  id: string
  symbol: string
  pattern: string
  confidence: number
  direction: 'BULLISH' | 'BEARISH'
  targetPrice: number
  stopLoss: number
  timeframe: string
  detectedAt: number
}
