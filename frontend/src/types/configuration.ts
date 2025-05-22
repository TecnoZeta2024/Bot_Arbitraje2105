// Configuration Types - Complete System
export interface BotConfiguration {
  // === GENERAL SETTINGS ===
  general: {
    botName: string
    mode: 'DEMO' | 'LIVE' | 'PAPER_TRADING'
    autoStart: boolean
    maxConcurrentTrades: number
    emergencyStopEnabled: boolean
    debugMode: boolean
    logLevel: 'DEBUG' | 'INFO' | 'WARNING' | 'ERROR'
  }

  // === CAPITAL & RISK MANAGEMENT ===
  capital: {
    initialCapital: number
    currentCapital: number
    maxDailyLoss: number
    maxDailyLossPercent: number
    maxWeeklyLoss: number
    maxWeeklyLossPercent: number
    maxMonthlyLoss: number
    maxMonthlyLossPercent: number
    reserveCapitalPercent: number
  }

  // === RISK MANAGEMENT ===
  riskManagement: {
    globalStopLoss: number
    globalStopLossPercent: number
    maxPositionSize: number
    maxPositionSizePercent: number
    maxPositionsPerSymbol: number
    maxCorrelationThreshold: number
    dynamicPositionSizing: boolean
    atrMultiplier: number
    trailingStopEnabled: boolean
    trailingStopPercent: number
    breakEvenStopEnabled: boolean
  }

  // === SCALPING STRATEGY ===
  scalping: {
    enabled: boolean
    symbols: string[]
    timeframe: '1m' | '3m' | '5m'
    rsiPeriod: number
    rsiOverbought: number
    rsiOversold: number
    macdFast: number
    macdSlow: number
    macdSignal: number
    bollingerPeriod: number
    bollingerStdDev: number
    volumeThreshold: number
    spreadThreshold: number
    minProfitTarget: number
    maxProfitTarget: number
    stopLossPercent: number
    maxHoldTime: number // minutes
    cooldownTime: number // seconds
    enableAIValidation: boolean
    aiConfidenceThreshold: number
  }

  // === DAY TRADING STRATEGY ===
  dayTrading: {
    enabled: boolean
    symbols: string[]
    primaryTimeframe: '5m' | '15m' | '30m' | '1h'
    secondaryTimeframe: '1h' | '4h' | '1d'
    supportResistancePeriod: number
    breakoutThreshold: number
    volumeConfirmation: boolean
    volumeMultiplier: number
    trendStrengthPeriod: number
    fibonacciLevels: number[]
    patternRecognition: boolean
    candlestickPatterns: string[]
    profitTargetPercent: number
    stopLossPercent: number
    trailingStopPercent: number
    maxHoldTime: number // hours
    enableMultiTimeframe: boolean
    aiSentimentWeight: number
  }

  // === ARBITRAGE STRATEGY ===
  arbitrage: {
    enabled: boolean
    triangularArbitrage: boolean
    spatialArbitrage: boolean
    exchanges: string[]
    baseCurrencies: string[]
    quoteCurrencies: string[]
    minSpreadPercent: number
    maxSpreadPercent: number
    executionTimeout: number // milliseconds
    slippageTolerance: number
    feeConsideration: boolean
    networkFees: Record<string, number>
    minProfitUSD: number
    maxOrderSize: number
    priceUpdateInterval: number
    orderBookDepth: number
  }

  // === AI/MACHINE LEARNING ===
  ai: {
    enabled: boolean
    provider: 'GEMINI' | 'OPENAI' | 'CLAUDE' | 'LOCAL'
    apiKey: string
    model: string
    maxTokens: number
    temperature: number
    sentimentAnalysis: boolean
    patternRecognition: boolean
    priceprediction: boolean
    marketRegimeDetection: boolean
    newsAnalysis: boolean
    socialMediaAnalysis: boolean
    confidenceThreshold: number
    updateInterval: number // minutes
    historicalDataDays: number
    features: string[]
  }

  // === EXCHANGES CONFIGURATION ===
  exchanges: {
    binance: {
      enabled: boolean
      apiKey: string
      apiSecret: string
      sandbox: boolean
      enabledPairs: string[]
      orderTypes: string[]
      maxOrderSize: number
      rateLimitMode: 'CONSERVATIVE' | 'NORMAL' | 'AGGRESSIVE'
      websocketStreams: string[]
    }
    coinbase: {
      enabled: boolean
      apiKey: string
      apiSecret: string
      passphrase: string
      sandbox: boolean
      enabledPairs: string[]
      orderTypes: string[]
      maxOrderSize: number
    }
    kraken: {
      enabled: boolean
      apiKey: string
      apiSecret: string
      enabledPairs: string[]
      orderTypes: string[]
      maxOrderSize: number
    }
    // Add more exchanges as needed
  }

  // === WEBSOCKET & DATA ===
  websocket: {
    enabled: boolean
    reconnectInterval: number
    maxReconnectAttempts: number
    pingInterval: number
    compression: boolean
    dataStreams: string[]
    bufferSize: number
    rateLimiting: boolean
  }

  // === NOTIFICATIONS ===
  notifications: {
    telegram: {
      enabled: boolean
      botToken: string
      chatId: string
      notifications: {
        tradeExecuted: boolean
        signalGenerated: boolean
        errorOccurred: boolean
        dailySummary: boolean
        positionOpened: boolean
        positionClosed: boolean
        stopLossHit: boolean
        takeProfitHit: boolean
        connectionLost: boolean
        highVolatility: boolean
      }
    }
    discord: {
      enabled: boolean
      webhookUrl: string
      notifications: {
        tradeExecuted: boolean
        signalGenerated: boolean
        errorOccurred: boolean
        dailySummary: boolean
      }
    }
    email: {
      enabled: boolean
      smtpServer: string
      smtpPort: number
      username: string
      password: string
      fromEmail: string
      toEmail: string
      notifications: {
        emergencyStop: boolean
        dailySummary: boolean
        weeklyReport: boolean
        errorOccurred: boolean
      }
    }
    push: {
      enabled: boolean
      serviceUrl: string
      apiKey: string
    }
  }

  // === BACKTESTING ===
  backtesting: {
    enabled: boolean
    startDate: string
    endDate: string
    initialBalance: number
    commission: number
    slippage: number
    dataSource: 'BINANCE' | 'COINBASE' | 'KRAKEN' | 'LOCAL'
    timeframe: string
    symbols: string[]
    strategies: string[]
    optimizeParameters: boolean
    walkForwardAnalysis: boolean
    monteCarlo: boolean
    monteCarloRuns: number
  }

  // === DATABASE ===
  database: {
    enabled: boolean
    type: 'SQLITE' | 'POSTGRESQL' | 'MYSQL' | 'MONGODB'
    host: string
    port: number
    database: string
    username: string
    password: string
    maxConnections: number
    retentionDays: number
    compressionEnabled: boolean
  }

  // === PERFORMANCE TUNING ===
  performance: {
    maxCpuUsage: number
    maxMemoryUsage: number
    cacheSize: number
    threadPoolSize: number
    asyncMode: boolean
    batchProcessing: boolean
    batchSize: number
    dataCompression: boolean
    heartbeatInterval: number
  }

  // === SECURITY ===
  security: {
    encryptionEnabled: boolean
    encryptionKey: string
    apiRateLimit: number
    maxFailedLogins: number
    sessionTimeout: number
    ipWhitelist: string[]
    twoFactorAuth: boolean
    auditLogging: boolean
  }

  // === ADVANCED FEATURES ===
  advanced: {
    portfolioRebalancing: boolean
    rebalanceInterval: number // hours
    rebalanceThreshold: number // percent
    hedgingEnabled: boolean
    hedgingRatio: number
    correlationTrading: boolean
    meanReversion: boolean
    momentumTrading: boolean
    newsTrading: boolean
    seasonalityAdjustment: boolean
    volatilityAdjustment: boolean
  }
}

// Configuration validation schemas
export interface ConfigValidationRule {
  field: string
  type: 'number' | 'string' | 'boolean' | 'array' | 'object'
  required: boolean
  min?: number
  max?: number
  pattern?: string
  options?: string[]
  dependencies?: string[]
}

export interface ConfigSection {
  id: string
  title: string
  description: string
  icon: string
  fields: ConfigField[]
  validation: ConfigValidationRule[]
  category: 'basic' | 'advanced' | 'expert'
}

export interface ConfigField {
  id: string
  label: string
  description: string
  type: 'text' | 'number' | 'boolean' | 'select' | 'multiselect' | 'textarea' | 'password' | 'slider' | 'range'
  value: any
  options?: { label: string; value: any }[]
  min?: number
  max?: number
  step?: number
  placeholder?: string
  required?: boolean
  disabled?: boolean
  tooltip?: string
  validation?: (value: any) => string | null
}

// Configuration presets for different user levels
export interface ConfigPreset {
  id: string
  name: string
  description: string
  level: 'beginner' | 'intermediate' | 'advanced' | 'expert'
  config: Partial<BotConfiguration>
  tags: string[]
}

// Configuration change history
export interface ConfigChange {
  id: string
  timestamp: number
  userId: string
  section: string
  field: string
  oldValue: any
  newValue: any
  reason?: string
}

// Configuration export/import
export interface ConfigExport {
  version: string
  timestamp: number
  config: BotConfiguration
  metadata: {
    botVersion: string
    exportedBy: string
    description?: string
  }
}
