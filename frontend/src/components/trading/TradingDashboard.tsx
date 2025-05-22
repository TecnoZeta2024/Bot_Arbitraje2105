import React, { useState } from 'react'
import { 
  TrendingUp, 
  TrendingDown, 
  DollarSign, 
  Activity, 
  Target,
  BarChart3,
  Zap,
  Brain,
  AlertTriangle,
  CheckCircle,
  Play,
  Pause,
  Square
} from 'lucide-react'

import { Card, CardContent, CardHeader, CardTitle, MetricCard } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { useTradingStore, useMarketData, usePositions, useRecentTrades, useRecentSignals } from '@/store'
import { formatCurrency, formatPercentage, cn } from '@/lib/utils'

// Price Ticker Component
const PriceTicker = ({ symbol }: { symbol: string }) => {
  const marketData = useMarketData(symbol)

  if (!marketData) {
    return (
      <div className="animate-pulse bg-gray-200 rounded-lg h-20"></div>
    )
  }

  const isPositive = marketData.changePercent24h >= 0

  return (
    <Card className="hover:shadow-md transition-shadow">
      <CardContent className="p-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="font-semibold text-lg">{symbol}</h3>
            <p className="text-sm text-muted-foreground">24h Volume: {formatCurrency(marketData.volume24h)}</p>
          </div>
          <div className="text-right">
            <p className="text-xl font-bold">{formatCurrency(marketData.price)}</p>
            <div className={cn('flex items-center text-sm', {
              'text-trading-green': isPositive,
              'text-trading-red': !isPositive,
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
      </CardContent>
    </Card>
  )
}

// Trading Signals Component
const TradingSignals = () => {
  const signals = useRecentSignals(5)

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center">
          <Brain className="w-5 h-5 mr-2 text-purple-500" />
          Recent AI Signals
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {signals.length === 0 ? (
            <p className="text-muted-foreground text-sm">No recent signals</p>
          ) : (
            signals.map((signal) => (
              <div 
                key={signal.id} 
                className="flex items-center justify-between p-3 bg-muted/50 rounded-lg"
              >
                <div>
                  <div className="flex items-center space-x-2">
                    <span className="font-semibold">{signal.symbol}</span>
                    <span className={cn('px-2 py-1 rounded text-xs font-medium', {
                      'bg-trading-green text-white': signal.action === 'BUY',
                      'bg-trading-red text-white': signal.action === 'SELL',
                    })}>
                      {signal.action}
                    </span>
                  </div>
                  <p className="text-sm text-muted-foreground">{signal.strategy}</p>
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

// Active Positions Component
const ActivePositions = () => {
  const positions = usePositions()

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center">
          <Target className="w-5 h-5 mr-2 text-blue-500" />
          Active Positions
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {positions.length === 0 ? (
            <p className="text-muted-foreground text-sm">No active positions</p>
          ) : (
            positions.map((position) => (
              <div 
                key={position.id} 
                className="flex items-center justify-between p-3 bg-muted/50 rounded-lg"
              >
                <div>
                  <div className="flex items-center space-x-2">
                    <span className="font-semibold">{position.symbol}</span>
                    <span className={cn('px-2 py-1 rounded text-xs font-medium', {
                      'bg-blue-100 text-blue-800': position.side === 'LONG',
                      'bg-red-100 text-red-800': position.side === 'SHORT',
                    })}>
                      {position.side}
                    </span>
                  </div>
                  <p className="text-sm text-muted-foreground">
                    Entry: {formatCurrency(position.entryPrice)} | Size: {position.quantity}
                  </p>
                </div>
                <div className="text-right">
                  <p className={cn('font-semibold', {
                    'text-trading-green': position.unrealizedPnL >= 0,
                    'text-trading-red': position.unrealizedPnL < 0,
                  })}>
                    {formatCurrency(position.unrealizedPnL)}
                  </p>
                  <p className={cn('text-sm', {
                    'text-trading-green': position.unrealizedPnLPercent >= 0,
                    'text-trading-red': position.unrealizedPnLPercent < 0,
                  })}>
                    {formatPercentage(position.unrealizedPnLPercent)}
                  </p>
                </div>
              </div>
            ))
          )}
        </div>
      </CardContent>
    </Card>
  )
}

// Recent Trades Component
const RecentTrades = () => {
  const trades = useRecentTrades(5)

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center">
          <Activity className="w-5 h-5 mr-2 text-green-500" />
          Recent Trades
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {trades.length === 0 ? (
            <p className="text-muted-foreground text-sm">No recent trades</p>
          ) : (
            trades.map((trade) => (
              <div 
                key={trade.id} 
                className="flex items-center justify-between p-3 bg-muted/50 rounded-lg"
              >
                <div>
                  <div className="flex items-center space-x-2">
                    <span className="font-semibold">{trade.symbol}</span>
                    <span className={cn('px-2 py-1 rounded text-xs font-medium', {
                      'bg-trading-green text-white': trade.side === 'BUY',
                      'bg-trading-red text-white': trade.side === 'SELL',
                    })}>
                      {trade.side}
                    </span>
                  </div>
                  <p className="text-sm text-muted-foreground">
                    {formatCurrency(trade.price)} × {trade.quantity}
                  </p>
                </div>
                <div className="text-right">
                  <p className={cn('font-semibold', {
                    'text-trading-green': trade.pnl >= 0,
                    'text-trading-red': trade.pnl < 0,
                  })}>
                    {formatCurrency(trade.pnl)}
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

// Trading Controls Component
const TradingControls = () => {
  const [isTradingActive, setIsTradingActive] = useState(false)
  const isConnected = useTradingStore((state) => state.isConnected)

  const handleStart = () => {
    setIsTradingActive(true)
    // Send start command to backend
  }

  const handlePause = () => {
    setIsTradingActive(false)
    // Send pause command to backend
  }

  const handleStop = () => {
    setIsTradingActive(false)
    // Send stop command to backend
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Trading Controls</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <span className="text-sm">Trading Status</span>
            <div className="flex items-center space-x-2">
              {isTradingActive ? (
                <>
                  <CheckCircle className="w-4 h-4 text-trading-green" />
                  <span className="text-sm text-trading-green">Active</span>
                </>
              ) : (
                <>
                  <AlertTriangle className="w-4 h-4 text-yellow-500" />
                  <span className="text-sm text-yellow-600">Inactive</span>
                </>
              )}
            </div>
          </div>

          <div className="flex items-center justify-between">
            <span className="text-sm">Connection</span>
            <div className="flex items-center space-x-2">
              {isConnected ? (
                <>
                  <CheckCircle className="w-4 h-4 text-trading-green" />
                  <span className="text-sm text-trading-green">Connected</span>
                </>
              ) : (
                <>
                  <AlertTriangle className="w-4 h-4 text-trading-red" />
                  <span className="text-sm text-trading-red">Disconnected</span>
                </>
              )}
            </div>
          </div>

          <div className="flex space-x-2">
            <Button 
              onClick={handleStart}
              disabled={!isConnected || isTradingActive}
              variant="success"
              className="flex-1"
            >
              <Play className="w-4 h-4 mr-1" />
              Start
            </Button>
            <Button 
              onClick={handlePause}
              disabled={!isTradingActive}
              variant="warning"
              className="flex-1"
            >
              <Pause className="w-4 h-4 mr-1" />
              Pause
            </Button>
            <Button 
              onClick={handleStop}
              disabled={!isTradingActive}
              variant="destructive"
              className="flex-1"
            >
              <Square className="w-4 h-4 mr-1" />
              Stop
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

// Main Trading Dashboard Component
export default function TradingDashboard() {
  const portfolio = useTradingStore((state) => state.portfolio)
  const tradingMetrics = useTradingStore((state) => state.tradingMetrics)
  const symbols = useTradingStore((state) => state.symbols)

  return (
    <div className="px-6 space-y-6">
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
          change={((portfolio.dailyPnL / portfolio.totalValue) * 100)}
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
          value={`${tradingMetrics.winRate.toFixed(1)}%`}
          icon={<BarChart3 className="w-6 h-6" />}
        />
      </div>

      {/* Price Tickers */}
      <div>
        <h2 className="text-xl font-semibold mb-4">Market Overview</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {symbols.slice(0, 6).map((symbol) => (
            <PriceTicker key={symbol} symbol={symbol} />
          ))}
        </div>
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column */}
        <div className="space-y-6">
          <TradingControls />
          <TradingSignals />
        </div>

        {/* Middle Column */}
        <div className="space-y-6">
          <ActivePositions />
        </div>

        {/* Right Column */}
        <div className="space-y-6">
          <RecentTrades />
        </div>
      </div>
    </div>
  )
}
