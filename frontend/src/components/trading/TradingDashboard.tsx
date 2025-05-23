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
  LineChart,
  WifiOff
} from 'lucide-react'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { cn } from '@/lib/utils'
import { useTradingStore } from '@/store'
import { useTradingControls, useOrderExecution } from '@/hooks/useWebSocket'

// Import AI components
import AIAnalysis from './AIAnalysis'
import StrategyManager from './StrategyManager'

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

// Enhanced Price Ticker Component (Now with Real Data)
const PriceTicker = ({ symbol }: { symbol: string }) => {
  const marketData = useTradingStore((state) => state.marketData[symbol])
  const { placeBuyOrder, placeSellOrder } = useOrderExecution()
  const [isAnimating, setIsAnimating] = useState(false)
  
  // Animate on price updates
  useEffect(() => {
    if (marketData) {
      setIsAnimating(true)
      const timer = setTimeout(() => setIsAnimating(false), 500)
      return () => clearTimeout(timer)
    }
  }, [marketData?.price])

  if (!marketData) {
    return (
      <Card className="animate-pulse">
        <CardContent className="p-4">
          <div className="h-20 bg-gray-200 rounded"></div>
        </CardContent>
      </Card>
    )
  }

  const handleQuickTrade = (side: 'BUY' | 'SELL') => {
    const quantity = 0.001 // Small test quantity
    if (side === 'BUY') {
      placeBuyOrder(symbol, quantity)
    } else {
      placeSellOrder(symbol, quantity)
    }
  }

  const isPositive = marketData.changePercent24h >= 0

  return (
    <Card className={cn('hover:shadow-lg transition-all duration-200 border-l-4', {
      'border-l-green-500': isPositive,
      'border-l-red-500': !isPositive,
      'ring-2 ring-blue-200': isAnimating
    })}>
      <CardContent className="p-4">
        <div className="flex items-center justify-between mb-3">
          <div>
            <h3 className="font-semibold text-lg flex items-center gap-2">
              {symbol.replace('USDT', '/USDT')}
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
            </h3>
            <p className="text-sm text-muted-foreground">
              Vol: {formatCurrency(marketData.volume24h)}
            </p>
          </div>
          <div className="text-right">
            <p className={cn('text-xl font-bold transition-colors', {
              'text-green-600': isAnimating && isPositive,
              'text-red-600': isAnimating && !isPositive
            })}>
              {formatCurrency(marketData.price)}
            </p>
            <div className={cn('flex items-center justify-end text-sm font-medium', {
              'text-green-600': isPositive,
              'text-red-600': !isPositive,
            })}>
              {isPositive ? (
                <TrendingUp className="w-4 h-4 mr-1" />
              ) : (
                <TrendingDown className="w-4 h-4 mr-1" />
              )}
              {formatPercentage(marketData.changePercent24h)}
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

// Enhanced Trading Controls with Real Server Integration
const TradingControls = () => {
  const isConnected = useTradingStore((state) => state.isConnected)
  const tradingState = useTradingStore((state) => state.tradingState) || 'IDLE'
  const { startTrading, pauseTrading, stopTrading } = useTradingControls()
  const systemMetrics = useTradingStore((state) => state.systemMetrics)
  
  const [uptime, setUptime] = useState(0)

  useEffect(() => {
    if (tradingState === 'RUNNING') {
      const startTime = Date.now()
      const interval = setInterval(() => {
        setUptime(Math.floor((Date.now() - startTime) / 1000))
      }, 1000)
      return () => clearInterval(interval)
    } else {
      setUptime(0)
    }
  }, [tradingState])

  const formatUptime = (seconds: number) => {
    const hrs = Math.floor(seconds / 3600)
    const mins = Math.floor((seconds % 3600) / 60)
    const secs = seconds % 60
    return `${hrs.toString().padStart(2, '0')}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
  }

  const isTradingActive = tradingState === 'RUNNING'

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <div className="flex items-center">
            <Zap className="w-5 h-5 mr-2 text-orange-500" />
            Trading System Control
          </div>
          {isConnected ? (
            <div className="flex items-center text-sm text-green-600">
              <Wifi className="w-4 h-4 mr-1" />
              Live
            </div>
          ) : (
            <div className="flex items-center text-sm text-red-600">
              <WifiOff className="w-4 h-4 mr-1" />
              Offline
            </div>
          )}
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
                    <span className="text-sm text-gray-600 font-medium">{tradingState}</span>
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
              <span className="font-mono font-medium">{systemMetrics?.signals_count || 0}</span>
            </div>
            <div className="flex justify-between text-xs">
              <span>Trades Executed:</span>
              <span className="font-mono font-medium">{systemMetrics?.trades_count || 0}</span>
            </div>
            <div className="flex justify-between text-xs">
              <span>Uptime:</span>
              <span className="font-mono font-medium">{formatUptime(uptime)}</span>
            </div>
          </div>

          {/* Control Buttons */}
          <div className="flex space-x-2">
            <Button 
              onClick={startTrading}
              disabled={!isConnected || isTradingActive}
              className="flex-1 bg-green-600 hover:bg-green-700"
            >
              <Play className="w-4 h-4 mr-1" />
              Start
            </Button>
            <Button 
              onClick={pauseTrading}
              disabled={!isConnected || !isTradingActive}
              variant="outline"
              className="flex-1 border-yellow-200 text-yellow-600 hover:bg-yellow-50"
            >
              <Pause className="w-4 h-4 mr-1" />
              Pause
            </Button>
            <Button 
              onClick={stopTrading}
              disabled={!isConnected || tradingState === 'IDLE'}
              variant="outline"
              className="flex-1 border-red-200 text-red-600 hover:bg-red-50"
            >
              <Square className="w-4 h-4 mr-1" />
              Stop
            </Button>
          </div>

          {!isConnected && (
            <div className="text-xs text-red-600 bg-red-50 p-3 rounded">
              ⚠️ <strong>Disconnected:</strong> Connect to server to enable trading
            </div>
          )}
          
          {isConnected && (
            <div className="text-xs text-muted-foreground bg-blue-50 p-3 rounded">
              💡 <strong>Production Mode:</strong> Real-time data with paper trading
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  )
}

// Trading Signals Component with Real Data
const TradingSignals = () => {
  const signals = useTradingStore((state) => state.signals)
  
  return (
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
                No signals yet. Start trading to see AI-generated signals.
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
                    <span className="font-semibold">{signal.symbol.replace('USDT', '/USDT')}</span>
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
}

// Recent Trades Component with Real Data
const RecentTrades = () => {
  const trades = useTradingStore((state) => state.trades)
  
  return (
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
                No trades yet. Execute orders to see trade history.
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
                    <span className="font-semibold">{trade.symbol.replace('USDT', '/USDT')}</span>
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
}

// Active Positions Component
const ActivePositions = () => {
  const positions = useTradingStore((state) => state.positions)
  
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center">
          <Target className="w-5 h-5 mr-2 text-blue-500" />
          Active Positions
          <span className="ml-auto text-sm font-normal text-muted-foreground">
            {positions.length}
          </span>
        </CardTitle>
      </CardHeader>
      <CardContent>
        {positions.length === 0 ? (
          <div className="text-center py-8">
            <Target className="w-12 h-12 text-gray-300 mx-auto mb-3" />
            <p className="text-muted-foreground text-sm">
              No active positions
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {positions.map((position) => (
              <div key={position.id} className="p-3 bg-muted/50 rounded-lg">
                <div className="flex justify-between items-start">
                  <div>
                    <div className="flex items-center space-x-2">
                      <span className="font-semibold">{position.symbol}</span>
                      <span className={cn('px-2 py-1 rounded text-xs font-medium', {
                        'bg-blue-100 text-blue-800': position.side === 'LONG',
                        'bg-orange-100 text-orange-800': position.side === 'SHORT',
                      })}>
                        {position.side}
                      </span>
                    </div>
                    <p className="text-sm text-muted-foreground">
                      Entry: {formatCurrency(position.entryPrice)} × {position.quantity}
                    </p>
                  </div>
                  <div className="text-right">
                    <p className={cn('font-semibold', {
                      'text-green-600': position.unrealizedPnL >= 0,
                      'text-red-600': position.unrealizedPnL < 0,
                    })}>
                      {position.unrealizedPnL >= 0 ? '+' : ''}{formatCurrency(position.unrealizedPnL)}
                    </p>
                    <p className="text-sm text-muted-foreground">
                      {position.unrealizedPnLPercent >= 0 ? '+' : ''}{position.unrealizedPnLPercent.toFixed(2)}%
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  )
}

// Main Dashboard Component
export default function TradingDashboard() {
  const isConnected = useTradingStore((state) => state.isConnected)
  const portfolio = useTradingStore((state) => state.portfolio)
  const symbols = useTradingStore((state) => state.symbols)
  
  return (
    <div className="px-6 space-y-6">
      {/* Connection Status Banner */}
      {!isConnected && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-center">
            <WifiOff className="w-6 h-6 text-red-600 mr-3" />
            <div>
              <h3 className="text-sm font-medium text-red-800">Connection Lost</h3>
              <p className="text-sm text-red-700">
                Attempting to reconnect to trading server...
              </p>
            </div>
          </div>
        </div>
      )}
      
      {isConnected && (
        <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-lg p-4">
          <div className="flex items-center">
            <Brain className="w-6 h-6 text-blue-600 mr-3" />
            <div>
              <h3 className="text-sm font-medium text-blue-800">Production Trading Platform</h3>
              <p className="text-sm text-blue-700">
                Connected to live market data with AI-powered analysis and paper trading
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Portfolio Overview */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <MetricCard
          title="Portfolio Value"
          value={formatCurrency(portfolio.totalValue)}
          change={portfolio.totalPnLPercent}
          trend={portfolio.totalPnL >= 0 ? 'up' : 'down'}
          icon={<DollarSign className="w-6 h-6" />}
        />
        <MetricCard
          title="Daily P&L"
          value={formatCurrency(portfolio.dailyPnL)}
          change={(portfolio.dailyPnL / portfolio.totalValue) * 100}
          trend={portfolio.dailyPnL >= 0 ? 'up' : 'down'}
          icon={<TrendingUp className="w-6 h-6" />}
        />
        <MetricCard
          title="Active Positions"
          value={portfolio.positions.length.toString()}
          icon={<Target className="w-6 h-6" />}
        />
        <MetricCard
          title="Win Rate"
          value={`${portfolio.winRate.toFixed(1)}%`}
          icon={<BarChart3 className="w-6 h-6" />}
        />
      </div>

      {/* Market Overview */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold">Market Overview</h2>
          <div className="flex items-center space-x-2 text-sm text-muted-foreground">
            {isConnected ? (
              <>
                <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                <span>Live market data</span>
              </>
            ) : (
              <>
                <div className="w-2 h-2 bg-gray-400 rounded-full"></div>
                <span>Offline</span>
              </>
            )}
          </div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {symbols.map((symbol) => (
            <PriceTicker key={symbol} symbol={symbol} />
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
              <TradingControls />
              <TradingSignals />
            </div>
            <div className="space-y-6">
              <ActivePositions />
            </div>
            <div className="space-y-6">
              <RecentTrades />
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
