import { create } from 'zustand'
import { persist, subscribeWithSelector } from 'zustand/middleware'
import type { BotConfiguration, ConfigSection, ConfigPreset, ConfigChange } from '@/types/configuration'

interface ConfigurationStore {
  // Current configuration
  config: BotConfiguration
  
  // UI State
  currentSection: string
  searchTerm: string
  showAdvanced: boolean
  isDirty: boolean
  validationErrors: Record<string, string>
  
  // History and presets
  changeHistory: ConfigChange[]
  presets: ConfigPreset[]
  
  // Actions
  updateConfig: (section: keyof BotConfiguration, field: string, value: any) => void
  updateSection: (section: keyof BotConfiguration, updates: any) => void
  setCurrentSection: (section: string) => void
  setSearchTerm: (term: string) => void
  toggleAdvanced: () => void
  validateConfig: () => boolean
  saveConfig: () => Promise<boolean>
  resetConfig: () => void
  loadPreset: (presetId: string) => void
  exportConfig: () => string
  importConfig: (configJson: string) => boolean
  
  // Validation
  validateField: (section: string, field: string, value: any) => string | null
  clearValidationErrors: () => void
}

const defaultConfig: BotConfiguration = {
  general: {
    botName: 'Trading Bot 2105',
    mode: 'DEMO',
    autoStart: false,
    maxConcurrentTrades: 5,
    emergencyStopEnabled: true,
    debugMode: false,
    logLevel: 'INFO',
  },
  
  capital: {
    initialCapital: 10000,
    currentCapital: 10000,
    maxDailyLoss: 200,
    maxDailyLossPercent: 2,
    maxWeeklyLoss: 500,
    maxWeeklyLossPercent: 5,
    maxMonthlyLoss: 1000,
    maxMonthlyLossPercent: 10,
    reserveCapitalPercent: 20,
  },
  
  riskManagement: {
    globalStopLoss: 100,
    globalStopLossPercent: 1,
    maxPositionSize: 1000,
    maxPositionSizePercent: 10,
    maxPositionsPerSymbol: 2,
    maxCorrelationThreshold: 0.7,
    dynamicPositionSizing: true,
    atrMultiplier: 2.0,
    trailingStopEnabled: true,
    trailingStopPercent: 1.5,
    breakEvenStopEnabled: true,
  },
  
  scalping: {
    enabled: true,
    symbols: ['BTCUSDT', 'ETHUSDT', 'BNBUSDT'],
    timeframe: '1m',
    rsiPeriod: 14,
    rsiOverbought: 70,
    rsiOversold: 30,
    macdFast: 12,
    macdSlow: 26,
    macdSignal: 9,
    bollingerPeriod: 20,
    bollingerStdDev: 2,
    volumeThreshold: 1.5,
    spreadThreshold: 0.1,
    minProfitTarget: 0.01,
    maxProfitTarget: 0.1,
    stopLossPercent: 0.05,
    maxHoldTime: 5,
    cooldownTime: 30,
    enableAIValidation: true,
    aiConfidenceThreshold: 80,
  },
  
  dayTrading: {
    enabled: true,
    symbols: ['BTCUSDT', 'ETHUSDT'],
    primaryTimeframe: '15m',
    secondaryTimeframe: '1h',
    supportResistancePeriod: 50,
    breakoutThreshold: 2,
    volumeConfirmation: true,
    volumeMultiplier: 1.5,
    trendStrengthPeriod: 14,
    fibonacciLevels: [0.236, 0.382, 0.5, 0.618, 0.786],
    patternRecognition: true,
    candlestickPatterns: ['hammer', 'doji', 'engulfing', 'shooting_star'],
    profitTargetPercent: 2,
    stopLossPercent: 1,
    trailingStopPercent: 0.5,
    maxHoldTime: 24,
    enableMultiTimeframe: true,
    aiSentimentWeight: 0.3,
  },
  
  arbitrage: {
    enabled: false,
    triangularArbitrage: true,
    spatialArbitrage: false,
    exchanges: ['binance'],
    baseCurrencies: ['BTC', 'ETH', 'BNB'],
    quoteCurrencies: ['USDT', 'BUSD'],
    minSpreadPercent: 0.1,
    maxSpreadPercent: 5,
    executionTimeout: 5000,
    slippageTolerance: 0.1,
    feeConsideration: true,
    networkFees: { BTC: 0.0005, ETH: 0.001, BNB: 0.0001 },
    minProfitUSD: 10,
    maxOrderSize: 5000,
    priceUpdateInterval: 1000,
    orderBookDepth: 10,
  },
  
  ai: {
    enabled: true,
    provider: 'GEMINI',
    apiKey: '',
    model: 'gemini-pro',
    maxTokens: 1000,
    temperature: 0.1,
    sentimentAnalysis: true,
    patternRecognition: true,
    priceprediction: true,
    marketRegimeDetection: true,
    newsAnalysis: false,
    socialMediaAnalysis: false,
    confidenceThreshold: 75,
    updateInterval: 15,
    historicalDataDays: 30,
    features: ['price', 'volume', 'rsi', 'macd', 'bollinger'],
  },
  
  exchanges: {
    binance: {
      enabled: true,
      apiKey: '',
      apiSecret: '',
      sandbox: true,
      enabledPairs: ['BTCUSDT', 'ETHUSDT', 'BNBUSDT'],
      orderTypes: ['MARKET', 'LIMIT', 'STOP_LOSS'],
      maxOrderSize: 10000,
      rateLimitMode: 'NORMAL',
      websocketStreams: ['ticker', 'depth', 'trade'],
    },
    coinbase: {
      enabled: false,
      apiKey: '',
      apiSecret: '',
      passphrase: '',
      sandbox: true,
      enabledPairs: [],
      orderTypes: ['MARKET', 'LIMIT'],
      maxOrderSize: 10000,
    },
    kraken: {
      enabled: false,
      apiKey: '',
      apiSecret: '',
      enabledPairs: [],
      orderTypes: ['MARKET', 'LIMIT'],
      maxOrderSize: 10000,
    },
  },
  
  websocket: {
    enabled: true,
    reconnectInterval: 3000,
    maxReconnectAttempts: 10,
    pingInterval: 30000,
    compression: true,
    dataStreams: ['ticker', 'depth', 'trade'],
    bufferSize: 1000,
    rateLimiting: true,
  },
  
  notifications: {
    telegram: {
      enabled: false,
      botToken: '',
      chatId: '',
      notifications: {
        tradeExecuted: true,
        signalGenerated: true,
        errorOccurred: true,
        dailySummary: true,
        positionOpened: true,
        positionClosed: true,
        stopLossHit: true,
        takeProfitHit: true,
        connectionLost: true,
        highVolatility: false,
      },
    },
    discord: {
      enabled: false,
      webhookUrl: '',
      notifications: {
        tradeExecuted: true,
        signalGenerated: false,
        errorOccurred: true,
        dailySummary: true,
      },
    },
    email: {
      enabled: false,
      smtpServer: '',
      smtpPort: 587,
      username: '',
      password: '',
      fromEmail: '',
      toEmail: '',
      notifications: {
        emergencyStop: true,
        dailySummary: false,
        weeklyReport: true,
        errorOccurred: true,
      },
    },
    push: {
      enabled: false,
      serviceUrl: '',
      apiKey: '',
    },
  },
  
  backtesting: {
    enabled: true,
    startDate: '2024-01-01',
    endDate: '2024-12-31',
    initialBalance: 10000,
    commission: 0.001,
    slippage: 0.001,
    dataSource: 'BINANCE',
    timeframe: '1h',
    symbols: ['BTCUSDT', 'ETHUSDT'],
    strategies: ['scalping', 'day_trading'],
    optimizeParameters: false,
    walkForwardAnalysis: false,
    monteCarlo: false,
    monteCarloRuns: 1000,
  },
  
  database: {
    enabled: true,
    type: 'SQLITE',
    host: 'localhost',
    port: 5432,
    database: 'trading_bot',
    username: '',
    password: '',
    maxConnections: 10,
    retentionDays: 365,
    compressionEnabled: true,
  },
  
  performance: {
    maxCpuUsage: 80,
    maxMemoryUsage: 1024,
    cacheSize: 100,
    threadPoolSize: 4,
    asyncMode: true,
    batchProcessing: true,
    batchSize: 100,
    dataCompression: true,
    heartbeatInterval: 30,
  },
  
  security: {
    encryptionEnabled: true,
    encryptionKey: '',
    apiRateLimit: 1000,
    maxFailedLogins: 5,
    sessionTimeout: 3600,
    ipWhitelist: [],
    twoFactorAuth: false,
    auditLogging: true,
  },
  
  advanced: {
    portfolioRebalancing: false,
    rebalanceInterval: 24,
    rebalanceThreshold: 5,
    hedgingEnabled: false,
    hedgingRatio: 0.5,
    correlationTrading: false,
    meanReversion: false,
    momentumTrading: true,
    newsTrading: false,
    seasonalityAdjustment: false,
    volatilityAdjustment: true,
  },
}

const defaultPresets: ConfigPreset[] = [
  {
    id: 'conservative',
    name: 'Conservative Trading',
    description: 'Low-risk settings for steady profits',
    level: 'beginner',
    config: {
      riskManagement: {
        maxPositionSizePercent: 5,
        globalStopLossPercent: 0.5,
        maxDailyLossPercent: 1,
      },
      scalping: {
        minProfitTarget: 0.02,
        stopLossPercent: 0.03,
        aiConfidenceThreshold: 90,
      },
    },
    tags: ['safe', 'low-risk', 'steady'],
  },
  {
    id: 'aggressive',
    name: 'Aggressive Trading',
    description: 'High-risk, high-reward settings',
    level: 'advanced',
    config: {
      riskManagement: {
        maxPositionSizePercent: 20,
        globalStopLossPercent: 2,
        maxDailyLossPercent: 5,
      },
      scalping: {
        minProfitTarget: 0.005,
        stopLossPercent: 0.02,
        aiConfidenceThreshold: 70,
      },
    },
    tags: ['aggressive', 'high-risk', 'high-reward'],
  },
  {
    id: 'scalping_focused',
    name: 'Scalping Specialist',
    description: 'Optimized for short-term scalping',
    level: 'intermediate',
    config: {
      scalping: { enabled: true },
      dayTrading: { enabled: false },
      arbitrage: { enabled: false },
    },
    tags: ['scalping', 'short-term', 'fast'],
  },
]

export const useConfigurationStore = create<ConfigurationStore>()(
  persist(
    subscribeWithSelector((set, get) => ({
      config: defaultConfig,
      currentSection: 'general',
      searchTerm: '',
      showAdvanced: false,
      isDirty: false,
      validationErrors: {},
      changeHistory: [],
      presets: defaultPresets,

      updateConfig: (section, field, value) => {
        const oldValue = get().config[section][field]
        
        set((state) => ({
          config: {
            ...state.config,
            [section]: {
              ...state.config[section],
              [field]: value,
            },
          },
          isDirty: true,
          changeHistory: [
            {
              id: Date.now().toString(),
              timestamp: Date.now(),
              userId: 'user',
              section,
              field,
              oldValue,
              newValue: value,
            },
            ...state.changeHistory.slice(0, 99),
          ],
        }))

        // Validate the field
        const error = get().validateField(section, field, value)
        if (error) {
          set((state) => ({
            validationErrors: {
              ...state.validationErrors,
              [`${section}.${field}`]: error,
            },
          }))
        } else {
          set((state) => {
            const newErrors = { ...state.validationErrors }
            delete newErrors[`${section}.${field}`]
            return { validationErrors: newErrors }
          })
        }
      },

      updateSection: (section, updates) => {
        set((state) => ({
          config: {
            ...state.config,
            [section]: {
              ...state.config[section],
              ...updates,
            },
          },
          isDirty: true,
        }))
      },

      setCurrentSection: (section) => set({ currentSection: section }),
      setSearchTerm: (term) => set({ searchTerm: term }),
      toggleAdvanced: () => set((state) => ({ showAdvanced: !state.showAdvanced })),

      validateConfig: () => {
        const { config } = get()
        let isValid = true
        const errors: Record<string, string> = {}

        // Validate capital management
        if (config.capital.maxDailyLossPercent > 10) {
          errors['capital.maxDailyLossPercent'] = 'Daily loss limit too high (max 10%)'
          isValid = false
        }

        // Validate risk management
        if (config.riskManagement.maxPositionSizePercent > 25) {
          errors['riskManagement.maxPositionSizePercent'] = 'Position size too large (max 25%)'
          isValid = false
        }

        // Validate AI settings
        if (config.ai.enabled && !config.ai.apiKey) {
          errors['ai.apiKey'] = 'AI API key is required when AI is enabled'
          isValid = false
        }

        set({ validationErrors: errors })
        return isValid
      },

      validateField: (section, field, value) => {
        // Field-specific validation logic
        if (section === 'capital') {
          if (field.includes('Percent') && (value < 0 || value > 100)) {
            return 'Percentage must be between 0 and 100'
          }
          if (field.includes('Loss') && value < 0) {
            return 'Loss values must be positive'
          }
        }

        if (section === 'riskManagement') {
          if (field === 'maxPositionSizePercent' && value > 25) {
            return 'Position size cannot exceed 25% of capital'
          }
          if (field === 'maxCorrelationThreshold' && (value < 0 || value > 1)) {
            return 'Correlation threshold must be between 0 and 1'
          }
        }

        if (section === 'scalping') {
          if (field === 'rsiOverbought' && (value < 50 || value > 100)) {
            return 'RSI overbought level must be between 50 and 100'
          }
          if (field === 'rsiOversold' && (value < 0 || value > 50)) {
            return 'RSI oversold level must be between 0 and 50'
          }
        }

        return null
      },

      clearValidationErrors: () => set({ validationErrors: {} }),

      saveConfig: async () => {
        const { validateConfig, config } = get()
        
        if (!validateConfig()) {
          return false
        }

        try {
          // Send config to backend
          const response = await fetch('/api/config', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(config),
          })

          if (response.ok) {
            set({ isDirty: false })
            return true
          }
        } catch (error) {
          console.error('Failed to save configuration:', error)
        }

        return false
      },

      resetConfig: () => {
        set({
          config: defaultConfig,
          isDirty: false,
          validationErrors: {},
          changeHistory: [],
        })
      },

      loadPreset: (presetId) => {
        const preset = get().presets.find(p => p.id === presetId)
        if (preset) {
          set((state) => ({
            config: {
              ...state.config,
              ...preset.config,
            },
            isDirty: true,
          }))
        }
      },

      exportConfig: () => {
        const { config } = get()
        const exportData = {
          version: '1.0.0',
          timestamp: Date.now(),
          config,
          metadata: {
            botVersion: '2105.1.0',
            exportedBy: 'user',
            description: 'Trading bot configuration export',
          },
        }
        return JSON.stringify(exportData, null, 2)
      },

      importConfig: (configJson) => {
        try {
          const importData = JSON.parse(configJson)
          if (importData.config) {
            set({
              config: { ...defaultConfig, ...importData.config },
              isDirty: true,
            })
            return true
          }
        } catch (error) {
          console.error('Failed to import configuration:', error)
        }
        return false
      },
    })),
    {
      name: 'trading-bot-config',
      partialize: (state) => ({
        config: state.config,
        presets: state.presets,
      }),
    }
  )
)

// Hooks for specific configuration sections
export const useGeneralConfig = () => 
  useConfigurationStore((state) => ({
    config: state.config.general,
    update: (field: string, value: any) => state.updateConfig('general', field, value),
  }))

export const useCapitalConfig = () =>
  useConfigurationStore((state) => ({
    config: state.config.capital,
    update: (field: string, value: any) => state.updateConfig('capital', field, value),
  }))

export const useRiskConfig = () =>
  useConfigurationStore((state) => ({
    config: state.config.riskManagement,
    update: (field: string, value: any) => state.updateConfig('riskManagement', field, value),
  }))

export const useScalpingConfig = () =>
  useConfigurationStore((state) => ({
    config: state.config.scalping,
    update: (field: string, value: any) => state.updateConfig('scalping', field, value),
  }))

export const useDayTradingConfig = () =>
  useConfigurationStore((state) => ({
    config: state.config.dayTrading,
    update: (field: string, value: any) => state.updateConfig('dayTrading', field, value),
  }))

export const useArbitrageConfig = () =>
  useConfigurationStore((state) => ({
    config: state.config.arbitrage,
    update: (field: string, value: any) => state.updateConfig('arbitrage', field, value),
  }))

export const useAIConfig = () =>
  useConfigurationStore((state) => ({
    config: state.config.ai,
    update: (field: string, value: any) => state.updateConfig('ai', field, value),
  }))

export const useNotificationConfig = () =>
  useConfigurationStore((state) => ({
    config: state.config.notifications,
    update: (section: string, field: string, value: any) => {
      const updates = { [field]: value }
      state.updateSection('notifications', {
        ...state.config.notifications,
        [section]: {
          ...state.config.notifications[section as keyof typeof state.config.notifications],
          ...updates,
        },
      })
    },
  }))

// Configuration validation hook
export const useConfigValidation = () =>
  useConfigurationStore((state) => ({
    errors: state.validationErrors,
    isValid: Object.keys(state.validationErrors).length === 0,
    validateConfig: state.validateConfig,
    clearErrors: state.clearValidationErrors,
  }))

// Configuration presets hook
export const useConfigPresets = () =>
  useConfigurationStore((state) => ({
    presets: state.presets,
    loadPreset: state.loadPreset,
  }))
