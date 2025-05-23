import React, { useState, useEffect } from 'react'
import { 
  TrendingUp, 
  TrendingDown, 
  DollarSign, 
  Activity, 
  Target,
  BarChart3,
  Brain,
  AlertTriangle,
  CheckCircle,
  Play,
  Pause,
  Square,
  Wifi,
  Plus,
  Minus,
  Clock,
  Zap,
  Settings2,
  LineChart
} from 'lucide-react'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { cn } from '@/lib/utils'

// Import new AI components
import AIAnalysis from './AIAnalysis'
import StrategyManager from './StrategyManager'

// Enhanced Mock Data with State Management
class TradingSystemState {
  private static instance: TradingSystemState
  
  public isActive = false
  public portfolio = {
    totalValue: 1000.00,
    dailyPnL: 23.45,
    availableBalance: 976.55,
    positions: [] as any[]
  }
  public signals: any[] = []
  public trades: any[] = []
  public signalCount = 0
  public tradeCount = 0
  
  static getInstance() {
    if (!TradingSystemState.instance) {
      TradingSystemState.instance = new TradingSystemState()
    }
    return TradingSystemState.instance
  }
  
  generateSignal() {
    const symbols = ['BTCUSDT', 'ETHUSDT', 'ADAUSDT', 'DOTUSDT', 'LINKUSDT', 'BNBUSDT']
    const actions = ['BUY', 'SELL']
    const strategies = ['AI_Scalping', 'TrendFollowing', 'MeanReversion', 'BreakoutStrategy']
    
    const symbol = symbols[Math.floor(Math.random() * symbols.length)]
    const action = actions[Math.floor(Math.random() * actions.length)]
    const strategy = strategies[Math.floor(Math.random() * strategies.length)]
    const confidence = 65 + Math.random() * 30 // 65-95%
    
    // Get current price from mock data
    const basePrice = this.getBasePrice(symbol)
    const price = basePrice * (1 + (Math.random() - 0.5) * 0.02) // ±1% variation
    
    const signal = {
      id: `signal_${++this.signalCount}`,
      symbol,
      action,
      price,
      strategy,
      confidence: Math.round(confidence * 10) / 10,
      timestamp: Date.now()
    }
    
    this.signals.unshift(signal)
    if (this.signals.length > 10) this.signals.pop()
    
    return signal
  }
  
  executeTrade(symbol: string, side: 'BUY' | 'SELL', quantity: number) {
    const basePrice = this.getBasePrice(symbol)
    const price = basePrice * (1 + (Math.random() - 0.5) * 0.005) // ±0.5% slippage
    
    // Calculate P&L (simulate small profit/loss)
    const pnl = quantity * price * (Math.random() > 0.3 ? 1 : -1) * (0.001 + Math.random() * 0.02) // 70% win rate
    
    const trade = {
      id: `trade_${++this.tradeCount}`,
      symbol,
      side,
      quantity,
      price,
      pnl,
      strategy: 'Manual',
      timestamp: Date.now()
    }
    
    this.trades.unshift(trade)
    if (this.trades.length > 20) this.trades.pop()
    
    // Update portfolio
    this.portfolio.dailyPnL += pnl
    this.portfolio.totalValue += pnl
    this.portfolio.availableBalance += pnl
    
    return trade
  }
  
  private getBasePrice(symbol: string): number {
    const basePrices: Record<string, number> = {
      'BTCUSDT': 97000,
      'ETHUSDT': 3180,
      'ADAUSDT': 0.86,
      'DOTUSDT': 7.25,
      'LINKUSDT': 25.60,
      'BNBUSDT': 650
    }
    return basePrices[symbol] || 50000
  }
}

const tradingState = TradingSystemState.getInstance()

// Datos mockeados realistas
const MOCK_MARKET_DATA = {
  BTCUSDT: { price: 97234.56, changePercent24h: 2.34, volume24h: 1567890000, isUpdating: true },
  ETHUSDT: { price: 3187.42, changePercent24h: 3.21, volume24h: 890345000, isUpdating: true },
  ADAUSDT: { price: 0.8567, changePercent24h: -1.12, volume24h: 234567000, isUpdating: true },
  DOTUSDT: { price: 7.234, changePercent24h: 1.87, volume24h: 167890000, isUpdating: true },
  LINKUSDT: { price: 25.67, changePercent24h: 4.12, volume24h: 145678000, isUpdating: true },
  BNBUSDT: { price: 652.34, changePercent24h: 1.56, volume24h: 298765000, isUpdating: true }
}

// Utility functions
const formatCurrency = (amount: number): string => {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 6
  }).format(amount)
}

const formatPercentage = (percent: number): string => {
  return `${percent >= 0 ? '+' : ''}${percent.toFixed(2)}%`
}

const formatTime = (timestamp: number): string => {
  return new Date(timestamp).toLocaleTimeString()
}

// MetricCard Component
const MetricCard = ({ title, value, change, trend, icon }: {
  title: string
  value: string
  change?: number
  trend?: 'up' | 'down'
  icon: React.ReactNode
}) => (
  <Card>
    <CardContent className="p-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-muted-foreground">{title}</p>
          <p className="text-2xl font-bold">{value}</p>
          {change !== undefined && (
            <p className={cn('text-sm flex items-center', {
              'text-green-600': trend === 'up',
              'text-red-600': trend === 'down',
              'text-gray-500': !trend
            })}>
              {trend === 'up' && <TrendingUp className="w-4 h-4 mr-1" />}
              {trend === 'down' && <TrendingDown className="w-4 h-4 mr-1" />}
              {formatPercentage(change)}
            </p>
          )}
        </div>
        <div className="text-muted-foreground">
          {icon}
        </div>
      </div>
    </CardContent>
  </Card>
)

// Enhanced Price Ticker Component
const PriceTicker = ({ symbol, data, onTradeExecuted }: { 
  symbol: string, 
  data: any,
  onTradeExecuted?: (trade: any) => void 
}) => {
  const [currentPrice, setCurrentPrice] = useState(data.price)
  const [isAnimating, setIsAnimating] = useState(false)
  const [lastTrade, setLastTrade] = useState<any>(null)
  
  // Simulate price updates
  useEffect(() => {
    const interval = setInterval(() => {
      const change = (Math.random() - 0.5) * 0.01 // ±0.5% change
      const newPrice = currentPrice * (1 + change)
      setCurrentPrice(newPrice)
      setIsAnimating(true)
      setTimeout(() => setIsAnimating(false), 500)
    }, 3000 + Math.random() * 2000) // 3-5 seconds
    
    return () => clearInterval(interval)
  }, [currentPrice])

  const handleQuickTrade = (side: 'BUY' | 'SELL') => {
    const quantity = 0.001 // Small test quantity
    const trade = tradingState.executeTrade(symbol, side, quantity)
    setLastTrade(trade)
    onTradeExecuted?.(trade)
    
    // Show detailed notification
    const notification = `
🎯 Quick ${side} Order Executed!

Symbol: ${symbol}
Quantity: ${quantity}
Price: ${formatCurrency(trade.price)}
P&L: ${trade.pnl >= 0 ? '+' : ''}${formatCurrency(trade.pnl)}
Status: ${trade.pnl >= 0 ? '✅ Profit' : '❌ Loss'}
    `.trim()
    
    alert(notification)
    
    // Clear last trade after 3 seconds
    setTimeout(() => setLastTrade(null), 3000)
  }

  const isPositive = data.changePercent24h >= 0

  return (
    <Card className={cn('hover:shadow-lg transition-all duration-200 border-l-4', {
      'border-l-green-500': isPositive,
      'border-l-red-500': !isPositive,
      'ring-2 ring-blue-200': isAnimating,
      'ring-2 ring-green-300': lastTrade && lastTrade.pnl >= 0,
      'ring-2 ring-red-300': lastTrade && lastTrade.pnl < 0
    })}>
      <CardContent className="p-4">
        <div className="flex items-center justify-between mb-3">
          <div>
            <h3 className="font-semibold text-lg flex items-center gap-2">
              {symbol}
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
              {lastTrade && (
                <span className={cn('text-xs px-2 py-1 rounded', {
                  'bg-green-100 text-green-700': lastTrade.pnl >= 0,
                  'bg-red-100 text-red-700': lastTrade.pnl < 0
                })}>
                  {lastTrade.pnl >= 0 ? '+' : ''}{formatCurrency(lastTrade.pnl)}
                </span>
              )}
            </h3>
            <p className="text-sm text-muted-foreground">
              Vol: {formatCurrency(data.volume24h)}
            </p>
          </div>
          <div className="text-right">
            <p className={cn('text-xl font-bold transition-colors', {
              'text-green-600': isAnimating && Math.random() > 0.5,
              'text-red-600': isAnimating && Math.random() <= 0.5
            })}>
              {formatCurrency(currentPrice)}
            </p>
            <div className={cn('flex items-center text-sm font-medium', {
              'text-green-600': isPositive,
              'text-red-600': !isPositive,
            })}>
              {isPositive ? (
                <TrendingUp className="w-4 h-4 mr-1" />
              ) : (
                <TrendingDown className="w-4 h-4 mr-1" />
              )}
              {formatPercentage(data.changePercent24h)}
            </div>
          </div>
        </div>
        
        <div className="flex gap-2">
          <Button 
            size="sm" 
            variant="outline"
            className="flex-1 text-green-600 border-green-200 hover:bg-green-50"
            onClick={() => handleQuickTrade('BUY')}
          >
            <Plus className="w-3 h-3 mr-1" />
            Quick Buy
          </Button>
          <Button 
            size="sm" 
            variant="outline"
            className="flex-1 text-red-600 border-red-200 hover:bg-red-50"
            onClick={() => handleQuickTrade('SELL')}
          >
            <Minus className="w-3 h-3 mr-1" />
            Quick Sell
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}

// Enhanced Trading Controls
const TradingControls = ({ onStateChange }: { onStateChange?: (state: any) => void }) => {
  const [isTradingActive, setIsTradingActive] = useState(false)
  const [signalInterval, setSignalInterval] = useState<NodeJS.Timeout | null>(null)
  const [systemStats, setSystemStats] = useState({
    signalsGenerated: 0,
    tradesExecuted: 0,
    uptime: 0
  })

  useEffect(() => {
    let uptimeInterval: NodeJS.Timeout

    if (isTradingActive) {
      // Generate signals every 10-30 seconds
      const interval = setInterval(() => {
        const signal = tradingState.generateSignal()
        setSystemStats(prev => ({ ...prev, signalsGenerated: prev.signalsGenerated + 1 }))
        
        // Notify parent component
        onStateChange?.(tradingState)
        
        // Show notification
        console.log(`🤖 New ${signal.action} Signal: ${signal.symbol} at ${formatCurrency(signal.price)}`)
      }, 15000 + Math.random() * 15000) // 15-30 seconds
      
      setSignalInterval(interval)
      
      // Track uptime
      uptimeInterval = setInterval(() => {
        setSystemStats(prev => ({ ...prev, uptime: prev.uptime + 1 }))
      }, 1000)
    }

    return () => {
      if (signalInterval) clearInterval(signalInterval)
      if (uptimeInterval) clearInterval(uptimeInterval)
    }
  }, [isTradingActive, onStateChange])

  const handleStart = async () => {
    tradingState.isActive = true
    setIsTradingActive(true)
    setSystemStats(prev => ({ ...prev, uptime: 0 }))
    
    alert('🚀 Trading system activated!\n\n• AI signals will be generated every 15-30 seconds\n• Paper trading mode active\n• Check console for signal notifications')
  }

  const handlePause = () => {
    tradingState.isActive = false
    setIsTradingActive(false)
    if (signalInterval) {
      clearInterval(signalInterval)
      setSignalInterval(null)
    }
    alert('⏸️ Trading system paused\n\nSignal generation stopped.')
  }

  const handleStop = () => {
    tradingState.isActive = false
    setIsTradingActive(false)
    if (signalInterval) {
      clearInterval(signalInterval)
      setSignalInterval(null)
    }
    setSystemStats({ signalsGenerated: 0, tradesExecuted: 0, uptime: 0 })
    alert('🛑 Trading system stopped\n\nAll activities halted.')
  }

  const formatUptime = (seconds: number) => {
    const hrs = Math.floor(seconds / 3600)
    const mins = Math.floor((seconds % 3600) / 60)
    const secs = seconds % 60
    return `${hrs.toString().padStart(2, '0')}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center">
          <Zap className="w-5 h-5 mr-2 text-orange-500" />
          Trading System Control
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {/* System Status */}
          <div className="grid grid-cols-2 gap-4">
            <div className="flex items-center justify-between">
              <span className="text-sm">Status</span>
              <div className="flex items-center space-x-2">
                {isTradingActive ? (
                  <>
                    <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
                    <span className="text-sm text-green-600 font-medium">Active</span>
                  </>
                ) : (
                  <>
                    <div className="w-2 h-2 bg-gray-400 rounded-full" />
                    <span className="text-sm text-gray-600 font-medium">Inactive</span>
                  </>
                )}
              </div>
            </div>

            <div className="flex items-center justify-between">
              <span className="text-sm">Mode</span>
              <span className="text-sm text-blue-600 font-medium">Paper Trading</span>
            </div>
          </div>

          {/* Performance Stats */}
          <div className="bg-muted/30 rounded-lg p-3 space-y-2">
            <div className="flex justify-between text-xs">
              <span>Signals Generated:</span>
              <span className="font-mono font-medium">{systemStats.signalsGenerated}</span>
            </div>
            <div className="flex justify-between text-xs">
              <span>Trades Executed:</span>
              <span className="font-mono font-medium">{systemStats.tradesExecuted}</span>
            </div>
            <div className="flex justify-between text-xs">
              <span>Uptime:</span>
              <span className="font-mono font-medium">{formatUptime(systemStats.uptime)}</span>
            </div>
          </div>

          {/* Control Buttons */}
          <div className="flex space-x-2">
            <Button 
              onClick={handleStart}
              disabled={isTradingActive}
              className="flex-1 bg-green-600 hover:bg-green-700"
            >
              <Play className="w-4 h-4 mr-1" />
              Start
            </Button>
            <Button 
              onClick={handlePause}
              disabled={!isTradingActive}
              variant="outline"
              className="flex-1 border-yellow-200 text-yellow-600 hover:bg-yellow-50"
            >
              <Pause className="w-4 h-4 mr-1" />
              Pause
            </Button>
            <Button 
              onClick={handleStop}
              disabled={!isTradingActive}
              variant="outline"
              className="flex-1 border-red-200 text-red-600 hover:bg-red-50"
            >
              <Square className="w-4 h-4 mr-1" />
              Stop
            </Button>
          </div>

          {/* Quick Actions */}
          <div className="border-t pt-3">
            <p className="text-xs text-muted-foreground mb-2">Quick Actions:</p>
            <div className="grid grid-cols-2 gap-2">
              <Button
                size="sm"
                variant="outline"
                onClick={() => {
                  const signal = tradingState.generateSignal()
                  setSystemStats(prev => ({ ...prev, signalsGenerated: prev.signalsGenerated + 1 }))
                  onStateChange?.(tradingState)
                  alert(`🔮 Manual signal generated:\n${signal.action} ${signal.symbol} at ${formatCurrency(signal.price)}`)
                }}
                className="text-xs"
              >
                <Brain className="w-3 h-3 mr-1" />
                Generate Signal
              </Button>
              <Button
                size="sm"
                variant="outline"
                onClick={() => {
                  const symbols = ['BTCUSDT', 'ETHUSDT', 'ADAUSDT']
                  const symbol = symbols[Math.floor(Math.random() * symbols.length)]
                  const side = Math.random() > 0.5 ? 'BUY' : 'SELL'
                  const trade = tradingState.executeTrade(symbol, side, 0.001)
                  setSystemStats(prev => ({ ...prev, tradesExecuted: prev.tradesExecuted + 1 }))
                  onStateChange?.(tradingState)
                  alert(`📈 Test trade executed:\n${trade.side} ${trade.quantity} ${trade.symbol}\nP&L: ${formatCurrency(trade.pnl)}`)
                }}
                className="text-xs"
              >
                <Activity className="w-3 h-3 mr-1" />
                Test Trade
              </Button>
            </div>
          </div>

          <div className="text-xs text-muted-foreground bg-blue-50 p-3 rounded">
            💡 <strong>Enhanced Paper Trading:</strong> Real signal generation and trade simulation
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

// Trading Signals Component
const TradingSignals = ({ signals }: { signals: any[] }) => (
  <Card>
    <CardHeader>
      <CardTitle className="flex items-center">
        <Brain className="w-5 h-5 mr-2 text-purple-500" />
        AI Trading Signals
        <span className="ml-auto text-sm font-normal text-muted-foreground">
          {signals.length}
        </span>
      </CardTitle>
    </CardHeader>
    <CardContent>
      <div className="space-y-3">
        {signals.length === 0 ? (
          <div className="text-center py-8">
            <Brain className="w-12 h-12 text-gray-300 mx-auto mb-3" />
            <p className="text-muted-foreground text-sm">
              No recent signals. Start trading to see AI-generated signals.
            </p>
          </div>
        ) : (
          signals.slice(0, 5).map((signal) => (
            <div 
              key={signal.id} 
              className="flex items-center justify-between p-3 bg-muted/50 rounded-lg border-l-4 border-l-purple-500"
            >
              <div>
                <div className="flex items-center space-x-2">
                  <span className="font-semibold">{signal.symbol}</span>
                  <span className={cn('px-2 py-1 rounded text-xs font-medium', {
                    'bg-green-100 text-green-800': signal.action === 'BUY',
                    'bg-red-100 text-red-800': signal.action === 'SELL',
                  })}>
                    {signal.action}
                  </span>
                </div>
                <p className="text-sm text-muted-foreground">{signal.strategy}</p>
                <p className="text-xs text-muted-foreground">{formatTime(signal.timestamp)}</p>
              </div>
              <div className="text-right">
                <p className="font-semibold">{formatCurrency(signal.price)}</p>
                <p className="text-sm text-muted-foreground">{signal.confidence}% confidence</p>
              </div>
            </div>
          ))
        )}
      </div>
    </CardContent>
  </Card>
)

// Recent Trades Component
const RecentTrades = ({ trades }: { trades: any[] }) => (
  <Card>
    <CardHeader>
      <CardTitle className="flex items-center">
        <Activity className="w-5 h-5 mr-2 text-green-500" />
        Recent Trades
        <span className="ml-auto text-sm font-normal text-muted-foreground">{trades.length}</span>
      </CardTitle>
    </CardHeader>
    <CardContent>
      <div className="space-y-3">
        {trades.length === 0 ? (
          <div className="text-center py-8">
            <Activity className="w-12 h-12 text-gray-300 mx-auto mb-3" />
            <p className="text-muted-foreground text-sm">
              No recent trades. Execute some orders to see trade history.
            </p>
          </div>
        ) : (
          trades.slice(0, 5).map((trade) => (
            <div 
              key={trade.id} 
              className="flex items-center justify-between p-3 bg-muted/50 rounded-lg border-l-4 border-l-blue-500"
            >
              <div>
                <div className="flex items-center space-x-2">
                  <span className="font-semibold">{trade.symbol}</span>
                  <span className={cn('px-2 py-1 rounded text-xs font-medium', {
                    'bg-green-100 text-green-800': trade.side === 'BUY',
                    'bg-red-100 text-red-800': trade.side === 'SELL',
                  })}>
                    {trade.side}
                  </span>
                </div>
                <p className="text-sm text-muted-foreground">
                  {formatCurrency(trade.price)} × {trade.quantity}
                </p>
                <p className="text-xs text-muted-foreground">{formatTime(trade.timestamp)}</p>
              </div>
              <div className="text-right">
                <p className={cn('font-semibold', {
                  'text-green-600': trade.pnl >= 0,
                  'text-red-600': trade.pnl < 0,
                })}>
                  {trade.pnl >= 0 ? '+' : ''}{formatCurrency(trade.pnl)}
                </p>
                <p className="text-sm text-muted-foreground">{trade.strategy}</p>
              </div>
            </div>
          ))
        )}
      </div>
    </CardContent>
  </Card>
)

// Main Dashboard Component
export default function TradingDashboard() {
  const [systemState, setSystemState] = useState(tradingState)
  const [lastUpdate, setLastUpdate] = useState(Date.now())

  const handleStateChange = (newState: any) => {
    setSystemState({ ...newState })
    setLastUpdate(Date.now())
  }

  const handleTradeExecuted = (trade: any) => {
    setSystemState({ ...tradingState })
    setLastUpdate(Date.now())
  }

  return (
    <div className="px-6 space-y-6">
      {/* Demo Mode Banner */}
      <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-lg p-4">
        <div className="flex items-center">
          <Brain className="w-6 h-6 text-blue-600 mr-3" />
          <div>
            <h3 className="text-sm font-medium text-blue-800">Advanced Trading Platform - Enhanced Demo</h3>
            <p className="text-sm text-blue-700">
              Fully functional demo with real-time signal generation, paper trading, and AI analysis
            </p>
          </div>
        </div>
      </div>

      {/* Portfolio Overview */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <MetricCard
          title="Portfolio Value"
          value={formatCurrency(systemState.portfolio.totalValue)}
          change={((systemState.portfolio.dailyPnL / 1000.0) * 100)}
          trend={systemState.portfolio.dailyPnL >= 0 ? 'up' : 'down'}
          icon={<DollarSign className="w-6 h-6" />}
        />
        <MetricCard
          title="Daily P&L"
          value={formatCurrency(systemState.portfolio.dailyPnL)}
          change={((systemState.portfolio.dailyPnL / systemState.portfolio.totalValue) * 100)}
          trend={systemState.portfolio.dailyPnL >= 0 ? 'up' : 'down'}
          icon={<TrendingUp className="w-6 h-6" />}
        />
        <MetricCard
          title="Active Positions"
          value={systemState.portfolio.positions.length.toString()}
          icon={<Target className="w-6 h-6" />}
        />
        <MetricCard
          title="Win Rate"
          value="72.3%"
          icon={<BarChart3 className="w-6 h-6" />}
        />
      </div>

      {/* Market Overview */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold">Market Overview</h2>
          <div className="flex items-center space-x-2 text-sm text-muted-foreground">
            <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
            <span>Enhanced live demo data</span>
          </div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {Object.entries(MOCK_MARKET_DATA).map(([symbol, data]) => (
            <PriceTicker 
              key={symbol} 
              symbol={symbol} 
              data={data} 
              onTradeExecuted={handleTradeExecuted}
            />
          ))}
        </div>
      </div>

      {/* Main Content with Tabs */}
      <Tabs defaultValue="trading" className="space-y-4">
        <TabsList className="grid grid-cols-3 w-full lg:w-auto">
          <TabsTrigger value="trading" className="flex items-center gap-2">
            <Activity className="w-4 h-4" />
            Trading Overview
          </TabsTrigger>
          <TabsTrigger value="ai-analysis" className="flex items-center gap-2">
            <Brain className="w-4 h-4" />
            AI Analysis
          </TabsTrigger>
          <TabsTrigger value="strategies" className="flex items-center gap-2">
            <Settings2 className="w-4 h-4" />
            Strategy Manager
          </TabsTrigger>
        </TabsList>
        
        <TabsContent value="trading" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="space-y-6">
              <TradingControls onStateChange={handleStateChange} />
              <TradingSignals signals={systemState.signals} />
            </div>
            <div className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center">
                    <Target className="w-5 h-5 mr-2 text-blue-500" />
                    Active Positions
                    <span className="ml-auto text-sm font-normal text-muted-foreground">
                      {systemState.portfolio.positions.length}
                    </span>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-center py-8">
                    <Target className="w-12 h-12 text-gray-300 mx-auto mb-3" />
                    <p className="text-muted-foreground text-sm">
                      No active positions. Execute trades to see positions here.
                    </p>
                    <p className="text-xs text-muted-foreground mt-2">
                      Available Balance: {formatCurrency(systemState.portfolio.availableBalance)}
                    </p>
                  </div>
                </CardContent>
              </Card>
            </div>
            <div className="space-y-6">
              <RecentTrades trades={systemState.trades} />
            </div>
          </div>
        </TabsContent>
        
        <TabsContent value="ai-analysis" className="space-y-6">
          <AIAnalysis />
        </TabsContent>
        
        <TabsContent value="strategies" className="space-y-6">
          <StrategyManager />
        </TabsContent>
      </Tabs>
    </div>
  )
}
