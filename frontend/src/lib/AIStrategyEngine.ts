// AI Strategy Engine - Core Trading Intelligence

import { 
  Strategy, 
  StrategyType, 
  Signal, 
  Trade, 
  MarketSentiment,
  PatternDetection,
  StrategyPerformance,
  IndicatorSignal
} from '@/types/strategy.types'

// Singleton AI Strategy Engine
export class AIStrategyEngine {
  private static instance: AIStrategyEngine
  private strategies: Map<string, Strategy> = new Map()
  private activeStrategies: Set<string> = new Set()
  private marketData: Map<string, any> = new Map()
  private signals: Signal[] = []
  private patterns: PatternDetection[] = []
  
  private constructor() {
    this.initializeDefaultStrategies()
  }
  
  static getInstance(): AIStrategyEngine {
    if (!AIStrategyEngine.instance) {
      AIStrategyEngine.instance = new AIStrategyEngine()
    }
    return AIStrategyEngine.instance
  }
  
  // Initialize default strategies
  private initializeDefaultStrategies() {
    const defaultStrategies: Strategy[] = [
      {
        id: 'trend_following_001',
        name: 'AI Trend Follower',
        type: StrategyType.TREND_FOLLOWING,
        description: 'Advanced trend following strategy using AI to identify and ride market trends',
        isActive: false,
        parameters: {
          timeframe: '4h',
          stopLoss: 2,
          takeProfit: 6,
          positionSize: 0.1,
          maxDailyLoss: 5,
          maxOpenPositions: 3,
          indicators: [
            { name: 'EMA', params: { period: 20 }, weight: 0.3 },
            { name: 'RSI', params: { period: 14 }, weight: 0.2 },
            { name: 'MACD', params: { fast: 12, slow: 26, signal: 9 }, weight: 0.5 }
          ]
        },
        performance: this.createEmptyPerformance(),
        riskProfile: {
          riskLevel: 'MEDIUM',
          maxLeverage: 5,
          maxExposure: 20,
          stopLossEnabled: true,
          trailingStopEnabled: true,
          riskRewardRatio: 3
        },
        signals: [],
        trades: [],
        createdAt: Date.now(),
        lastUpdated: Date.now()
      },
      {
        id: 'mean_reversion_001',
        name: 'Smart Mean Reversion',
        type: StrategyType.MEAN_REVERSION,
        description: 'Identifies overbought/oversold conditions using AI pattern recognition',
        isActive: false,
        parameters: {
          timeframe: '1h',
          stopLoss: 1.5,
          takeProfit: 3,
          positionSize: 0.15,
          maxDailyLoss: 4,
          maxOpenPositions: 5,
          indicators: [
            { name: 'BOLLINGER', params: { period: 20, stdDev: 2 }, weight: 0.4 },
            { name: 'RSI', params: { period: 14 }, weight: 0.4 },
            { name: 'STOCHASTIC', params: { k: 14, d: 3 }, weight: 0.2 }
          ]
        },
        performance: this.createEmptyPerformance(),
        riskProfile: {
          riskLevel: 'LOW',
          maxLeverage: 3,
          maxExposure: 15,
          stopLossEnabled: true,
          trailingStopEnabled: false,
          riskRewardRatio: 2
        },
        signals: [],
        trades: [],
        createdAt: Date.now(),
        lastUpdated: Date.now()
      },
      {
        id: 'momentum_001',
        name: 'AI Momentum Hunter',
        type: StrategyType.MOMENTUM,
        description: 'Captures strong momentum moves using machine learning predictions',
        isActive: false,
        parameters: {
          timeframe: '15m',
          stopLoss: 1,
          takeProfit: 4,
          positionSize: 0.2,
          maxDailyLoss: 6,
          maxOpenPositions: 4,
          indicators: [
            { name: 'ADX', params: { period: 14 }, weight: 0.3 },
            { name: 'MOMENTUM', params: { period: 10 }, weight: 0.4 },
            { name: 'VOLUME', params: { period: 20 }, weight: 0.3 }
          ]
        },
        performance: this.createEmptyPerformance(),
        riskProfile: {
          riskLevel: 'HIGH',
          maxLeverage: 10,
          maxExposure: 30,
          stopLossEnabled: true,
          trailingStopEnabled: true,
          riskRewardRatio: 4
        },
        signals: [],
        trades: [],
        createdAt: Date.now(),
        lastUpdated: Date.now()
      },
      {
        id: 'scalping_001',
        name: 'Neural Scalper',
        type: StrategyType.SCALPING,
        description: 'High-frequency scalping using neural network predictions',
        isActive: false,
        parameters: {
          timeframe: '1m',
          stopLoss: 0.3,
          takeProfit: 0.5,
          positionSize: 0.5,
          maxDailyLoss: 3,
          maxOpenPositions: 10,
          indicators: [
            { name: 'VWAP', params: {}, weight: 0.3 },
            { name: 'ATR', params: { period: 14 }, weight: 0.2 },
            { name: 'ORDERFLOW', params: {}, weight: 0.5 }
          ]
        },
        performance: this.createEmptyPerformance(),
        riskProfile: {
          riskLevel: 'AGGRESSIVE',
          maxLeverage: 20,
          maxExposure: 50,
          stopLossEnabled: true,
          trailingStopEnabled: false,
          riskRewardRatio: 1.5
        },
        signals: [],
        trades: [],
        createdAt: Date.now(),
        lastUpdated: Date.now()
      },
      {
        id: 'arbitrage_001',
        name: 'Cross-Exchange Arbitrage',
        type: StrategyType.ARBITRAGE,
        description: 'Detects and exploits price differences across exchanges',
        isActive: false,
        parameters: {
          timeframe: 'tick',
          stopLoss: 0.1,
          takeProfit: 0.3,
          positionSize: 1,
          maxDailyLoss: 2,
          maxOpenPositions: 20,
          indicators: [
            { name: 'SPREAD', params: {}, weight: 0.6 },
            { name: 'LIQUIDITY', params: {}, weight: 0.4 }
          ],
          customParams: {
            minSpread: 0.1,
            exchanges: ['Binance', 'Coinbase', 'Kraken']
          }
        },
        performance: this.createEmptyPerformance(),
        riskProfile: {
          riskLevel: 'LOW',
          maxLeverage: 1,
          maxExposure: 80,
          stopLossEnabled: false,
          trailingStopEnabled: false,
          riskRewardRatio: 3
        },
        signals: [],
        trades: [],
        createdAt: Date.now(),
        lastUpdated: Date.now()
      },
      {
        id: 'ai_hybrid_001',
        name: 'AI Hybrid Master',
        type: StrategyType.AI_HYBRID,
        description: 'Combines multiple AI models for optimal trading decisions',
        isActive: false,
        parameters: {
          timeframe: 'multi',
          stopLoss: 1.5,
          takeProfit: 5,
          positionSize: 0.25,
          maxDailyLoss: 5,
          maxOpenPositions: 6,
          indicators: [
            { name: 'ML_ENSEMBLE', params: {}, weight: 0.5 },
            { name: 'SENTIMENT', params: {}, weight: 0.3 },
            { name: 'PATTERN', params: {}, weight: 0.2 }
          ],
          customParams: {
            models: ['LSTM', 'RandomForest', 'XGBoost'],
            sentimentSources: ['twitter', 'reddit', 'news']
          }
        },
        performance: this.createEmptyPerformance(),
        riskProfile: {
          riskLevel: 'MEDIUM',
          maxLeverage: 5,
          maxExposure: 25,
          stopLossEnabled: true,
          trailingStopEnabled: true,
          riskRewardRatio: 3.5
        },
        signals: [],
        trades: [],
        createdAt: Date.now(),
        lastUpdated: Date.now()
      }
    ]
    
    defaultStrategies.forEach(strategy => {
      this.strategies.set(strategy.id, strategy)
    })
  }
  
  private createEmptyPerformance(): StrategyPerformance {
    return {
      totalTrades: 0,
      winRate: 0,
      profitFactor: 0,
      sharpeRatio: 0,
      maxDrawdown: 0,
      totalPnL: 0,
      avgWin: 0,
      avgLoss: 0,
      bestTrade: 0,
      worstTrade: 0,
      currentStreak: 0,
      roi: 0
    }
  }
  
  // Get all strategies
  getAllStrategies(): Strategy[] {
    return Array.from(this.strategies.values())
  }
  
  // Get active strategies
  getActiveStrategies(): Strategy[] {
    return Array.from(this.strategies.values()).filter(s => s.isActive)
  }
  
  // Activate strategy
  activateStrategy(strategyId: string): boolean {
    const strategy = this.strategies.get(strategyId)
    if (strategy) {
      strategy.isActive = true
      this.activeStrategies.add(strategyId)
      console.log(`🚀 Strategy activated: ${strategy.name}`)
      return true
    }
    return false
  }
  
  // Deactivate strategy
  deactivateStrategy(strategyId: string): boolean {
    const strategy = this.strategies.get(strategyId)
    if (strategy) {
      strategy.isActive = false
      this.activeStrategies.delete(strategyId)
      console.log(`⏸️ Strategy deactivated: ${strategy.name}`)
      return true
    }
    return false
  }
  
  // Generate AI signal
  generateSignal(strategyId: string, symbol: string): Signal | null {
    const strategy = this.strategies.get(strategyId)
    if (!strategy || !strategy.isActive) return null
    
    // Simulate AI analysis
    const indicators = this.analyzeIndicators(strategy, symbol)
    const confidence = this.calculateConfidence(indicators)
    const action = this.determineAction(indicators, confidence)
    
    const signal: Signal = {
      id: `sig_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      strategyId,
      symbol,
      action,
      price: this.getCurrentPrice(symbol),
      confidence,
      indicators,
      timestamp: Date.now(),
      metadata: {
        strategy: strategy.name,
        timeframe: strategy.parameters.timeframe
      }
    }
    
    strategy.signals.unshift(signal)
    if (strategy.signals.length > 100) strategy.signals.pop()
    
    this.signals.unshift(signal)
    if (this.signals.length > 500) this.signals.pop()
    
    return signal
  }
  
  // Analyze indicators
  private analyzeIndicators(strategy: Strategy, symbol: string): IndicatorSignal[] {
    return strategy.parameters.indicators.map(indicator => {
      const value = Math.random() * 100
      const signal = value > 70 ? 'BULLISH' : value < 30 ? 'BEARISH' : 'NEUTRAL'
      const strength = Math.abs(value - 50) / 50
      
      return {
        name: indicator.name,
        value,
        signal,
        strength: Math.round(strength * 100) / 100
      }
    })
  }
  
  // Calculate confidence
  private calculateConfidence(indicators: IndicatorSignal[]): number {
    const bullishCount = indicators.filter(i => i.signal === 'BULLISH').length
    const bearishCount = indicators.filter(i => i.signal === 'BEARISH').length
    const totalStrength = indicators.reduce((sum, i) => sum + i.strength, 0)
    
    const directionConfidence = Math.abs(bullishCount - bearishCount) / indicators.length
    const strengthConfidence = totalStrength / indicators.length
    
    return Math.round((directionConfidence * 0.6 + strengthConfidence * 0.4) * 100)
  }
  
  // Determine action
  private determineAction(indicators: IndicatorSignal[], confidence: number): 'BUY' | 'SELL' | 'HOLD' {
    if (confidence < 60) return 'HOLD'
    
    const bullishCount = indicators.filter(i => i.signal === 'BULLISH').length
    const bearishCount = indicators.filter(i => i.signal === 'BEARISH').length
    
    if (bullishCount > bearishCount) return 'BUY'
    if (bearishCount > bullishCount) return 'SELL'
    return 'HOLD'
  }
  
  // Get current price
  private getCurrentPrice(symbol: string): number {
    const basePrices: Record<string, number> = {
      'BTCUSDT': 97000,
      'ETHUSDT': 3180,
      'ADAUSDT': 0.86,
      'DOTUSDT': 7.25,
      'LINKUSDT': 25.60,
      'BNBUSDT': 650
    }
    const basePrice = basePrices[symbol] || 50000
    return basePrice * (1 + (Math.random() - 0.5) * 0.02)
  }
  
  // Get market sentiment
  getMarketSentiment(): MarketSentiment {
    const score = (Math.random() - 0.5) * 200 // -100 to 100
    const overall = score > 20 ? 'BULLISH' : score < -20 ? 'BEARISH' : 'NEUTRAL'
    
    return {
      overall,
      score: Math.round(score),
      components: {
        technical: Math.round((Math.random() - 0.5) * 200),
        fundamental: Math.round((Math.random() - 0.5) * 200),
        social: Math.round((Math.random() - 0.5) * 200),
        onChain: Math.round((Math.random() - 0.5) * 200)
      },
      signals: {
        fearGreedIndex: Math.round(Math.random() * 100),
        volumeAnalysis: Math.random() > 0.5 ? 'Increasing' : 'Decreasing',
        trendStrength: Math.round(Math.random() * 100),
        volatility: Math.random() > 0.7 ? 'HIGH' : Math.random() > 0.3 ? 'MEDIUM' : 'LOW'
      }
    }
  }
  
  // Detect patterns
  detectPatterns(symbol: string): PatternDetection[] {
    const patterns = [
      'Head and Shoulders', 'Double Top', 'Double Bottom', 
      'Ascending Triangle', 'Descending Triangle', 'Bull Flag',
      'Bear Flag', 'Cup and Handle', 'Inverse Cup and Handle'
    ]
    
    const detectedPatterns: PatternDetection[] = []
    
    // Simulate pattern detection (20% chance)
    if (Math.random() < 0.2) {
      const pattern = patterns[Math.floor(Math.random() * patterns.length)]
      const isBullish = pattern.includes('Bull') || pattern.includes('Ascending') || 
                       pattern.includes('Bottom') || pattern.includes('Cup and Handle')
      
      const currentPrice = this.getCurrentPrice(symbol)
      const targetMove = currentPrice * (0.05 + Math.random() * 0.15) // 5-20% move
      
      detectedPatterns.push({
        id: `pattern_${Date.now()}`,
        symbol,
        pattern,
        confidence: 60 + Math.random() * 35,
        direction: isBullish ? 'BULLISH' : 'BEARISH',
        targetPrice: isBullish ? currentPrice + targetMove : currentPrice - targetMove,
        stopLoss: isBullish ? currentPrice - targetMove * 0.5 : currentPrice + targetMove * 0.5,
        timeframe: '4h',
        detectedAt: Date.now()
      })
    }
    
    this.patterns = [...detectedPatterns, ...this.patterns].slice(0, 50)
    return detectedPatterns
  }
  
  // Execute trade
  executeTrade(strategyId: string, signal: Signal): Trade | null {
    const strategy = this.strategies.get(strategyId)
    if (!strategy) return null
    
    const quantity = strategy.parameters.positionSize
    const trade: Trade = {
      id: `trade_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      strategyId,
      symbol: signal.symbol,
      side: signal.action as 'BUY' | 'SELL',
      quantity,
      entryPrice: signal.price,
      status: 'OPEN',
      openTime: Date.now(),
      stopLoss: signal.action === 'BUY' 
        ? signal.price * (1 - strategy.parameters.stopLoss / 100)
        : signal.price * (1 + strategy.parameters.stopLoss / 100),
      takeProfit: signal.action === 'BUY'
        ? signal.price * (1 + strategy.parameters.takeProfit / 100)
        : signal.price * (1 - strategy.parameters.takeProfit / 100)
    }
    
    strategy.trades.push(trade)
    this.updatePerformance(strategy)
    
    return trade
  }
  
  // Update performance
  private updatePerformance(strategy: Strategy) {
    const closedTrades = strategy.trades.filter(t => t.status === 'CLOSED')
    if (closedTrades.length === 0) return
    
    const wins = closedTrades.filter(t => t.pnl && t.pnl > 0)
    const losses = closedTrades.filter(t => t.pnl && t.pnl < 0)
    
    strategy.performance.totalTrades = closedTrades.length
    strategy.performance.winRate = (wins.length / closedTrades.length) * 100
    strategy.performance.totalPnL = closedTrades.reduce((sum, t) => sum + (t.pnl || 0), 0)
    
    if (wins.length > 0) {
      strategy.performance.avgWin = wins.reduce((sum, t) => sum + (t.pnl || 0), 0) / wins.length
    }
    
    if (losses.length > 0) {
      strategy.performance.avgLoss = Math.abs(losses.reduce((sum, t) => sum + (t.pnl || 0), 0) / losses.length)
    }
    
    strategy.performance.profitFactor = strategy.performance.avgLoss > 0 
      ? strategy.performance.avgWin / strategy.performance.avgLoss 
      : strategy.performance.avgWin
    
    strategy.lastUpdated = Date.now()
  }
  
  // Get recent patterns
  getRecentPatterns(): PatternDetection[] {
    return this.patterns
  }
  
  // Get all signals
  getAllSignals(): Signal[] {
    return this.signals
  }
}

// Export singleton instance
export const aiStrategyEngine = AIStrategyEngine.getInstance()
