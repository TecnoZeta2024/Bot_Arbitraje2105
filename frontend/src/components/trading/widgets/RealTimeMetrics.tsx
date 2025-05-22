import React, { useEffect, useState } from 'react'
import { 
  DollarSign, 
  TrendingUp, 
  TrendingDown, 
  Activity, 
  Target, 
  Zap, 
  Clock, 
  BarChart3,
  Wifi,
  WifiOff
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle, MetricCard } from '@/components/ui/card'
import { useTradingStore, usePortfolioMetrics, useConnectionStatus } from '@/store'
import { formatCurrency, formatPercentage, formatNumber, cn } from '@/lib/utils'

interface RealTimeMetricsProps {
  compact?: boolean
  showConnectionStatus?: boolean
  refreshInterval?: number
}

export const RealTimeMetrics: React.FC<RealTimeMetricsProps> = ({
  compact = false,
  showConnectionStatus = true,
  refreshInterval = 1000,
}) => {
  const [lastUpdate, setLastUpdate] = useState(Date.now())
  const [updateIndicator, setUpdateIndicator] = useState(false)
  
  const { portfolio, metrics } = usePortfolioMetrics()
  const isConnected = useConnectionStatus()
  const trades = useTradingStore((state) => state.trades)
  const positions = useTradingStore((state) => state.positions)
  const signals = useTradingStore((state) => state.signals)

  // Update indicator animation
  useEffect(() => {
    const interval = setInterval(() => {
      setLastUpdate(Date.now())
      setUpdateIndicator(true)
      setTimeout(() => setUpdateIndicator(false), 200)
    }, refreshInterval)

    return () => clearInterval(interval)
  }, [refreshInterval])

  // Calculate real-time stats
  const recentTrades = trades.slice(0, 10)
  const todaysTrades = trades.filter(t => 
    new Date(t.timestamp).toDateString() === new Date().toDateString()
  )
  const recentSignals = signals.slice(0, 5)
  
  const stats = {
    totalValue: portfolio.totalValue,
    dailyPnL: portfolio.dailyPnL,
    dailyPnLPercent: portfolio.totalValue > 0 ? (portfolio.dailyPnL / portfolio.totalValue) * 100 : 0,
    activePositions: positions.length,
    todaysTrades: todaysTrades.length,
    winningPositions: positions.filter(p => p.unrealizedPnL > 0).length,
    recentSignalsCount: recentSignals.length,
    avgPositionSize: positions.length > 0 
      ? positions.reduce((sum, p) => sum + (p.quantity * p.currentPrice), 0) / positions.length 
      : 0,
  }

  if (compact) {
    return (
      <Card className="bg-gradient-to-br from-card to-card/80">
        <CardContent className="p-4">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold flex items-center">
              <Activity className="w-4 h-4 mr-2 text-blue-500" />
              Live Metrics
            </h3>
            <div className="flex items-center space-x-2">
              {showConnectionStatus && (
                <div className="flex items-center space-x-1">
                  {isConnected ? (
                    <Wifi className="w-3 h-3 text-trading-green" />
                  ) : (
                    <WifiOff className="w-3 h-3 text-trading-red" />
                  )}
                </div>
              )}
              <div className={cn(
                'w-2 h-2 rounded-full transition-all duration-200',
                updateIndicator 
                  ? 'bg-trading-green shadow-lg shadow-trading-green/50' 
                  : 'bg-muted-foreground/30'
              )} />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div className="text-center">
              <p className="text-lg font-bold">
                {formatCurrency(stats.totalValue)}
              </p>
              <p className="text-xs text-muted-foreground">Portfolio</p>
            </div>
            
            <div className="text-center">
              <p className={cn('text-lg font-bold', {
                'text-trading-green': stats.dailyPnL >= 0,
                'text-trading-red': stats.dailyPnL < 0,
              })}>
                {stats.dailyPnL >= 0 ? '+' : ''}{formatCurrency(stats.dailyPnL)}
              </p>
              <p className="text-xs text-muted-foreground">Daily P&L</p>
            </div>
            
            <div className="text-center">
              <p className="text-lg font-bold text-blue-500">
                {stats.activePositions}
              </p>
              <p className="text-xs text-muted-foreground">Positions</p>
            </div>
            
            <div className="text-center">
              <p className="text-lg font-bold text-purple-500">
                {stats.todaysTrades}
              </p>
              <p className="text-xs text-muted-foreground">Trades Today</p>
            </div>
          </div>

          {/* Quick Status Indicators */}
          <div className="flex justify-between mt-4 pt-3 border-t border-border/50">
            <div className="flex items-center space-x-1">
              <div className={cn('w-2 h-2 rounded-full', {
                'bg-trading-green': stats.winningPositions > stats.activePositions / 2,
                'bg-trading-red': stats.winningPositions <= stats.activePositions / 2,
                'bg-muted-foreground': stats.activePositions === 0,
              })} />
              <span className="text-xs text-muted-foreground">
                {stats.activePositions > 0 
                  ? `${stats.winningPositions}/${stats.activePositions} winning`
                  : 'No positions'
                }
              </span>
            </div>
            
            <span className="text-xs text-muted-foreground">
              {new Date(lastUpdate).toLocaleTimeString()}
            </span>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="space-y-6">
      {/* Connection Status */}
      {showConnectionStatus && (
        <Card className={cn(
          'border-2 transition-colors',
          isConnected 
            ? 'border-trading-green/20 bg-trading-green/5' 
            : 'border-trading-red/20 bg-trading-red/5'
        )}>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                {isConnected ? (
                  <Wifi className="w-5 h-5 text-trading-green" />
                ) : (
                  <WifiOff className="w-5 h-5 text-trading-red" />
                )}
                <div>
                  <p className="font-medium">
                    {isConnected ? 'Connected' : 'Disconnected'}
                  </p>
                  <p className="text-sm text-muted-foreground">
                    {isConnected 
                      ? 'Real-time data streaming' 
                      : 'Connection to trading server lost'
                    }
                  </p>
                </div>
              </div>
              
              <div className="flex items-center space-x-2">
                <div className={cn(
                  'w-3 h-3 rounded-full transition-all duration-200',
                  updateIndicator && isConnected
                    ? 'bg-trading-green shadow-lg shadow-trading-green/50' 
                    : 'bg-muted-foreground/30'
                )} />
                <span className="text-xs text-muted-foreground">
                  {new Date(lastUpdate).toLocaleTimeString()}
                </span>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Portfolio Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="Portfolio Value"
          value={formatCurrency(stats.totalValue)}
          icon={<DollarSign className="w-5 h-5" />}
        />
        
        <MetricCard
          title="Daily P&L"
          value={formatCurrency(stats.dailyPnL)}
          change={stats.dailyPnLPercent}
          trend={stats.dailyPnL >= 0 ? 'up' : 'down'}
          icon={<TrendingUp className="w-5 h-5" />}
        />
        
        <MetricCard
          title="Active Positions"
          value={stats.activePositions.toString()}
          icon={<Target className="w-5 h-5" />}
        />
        
        <MetricCard
          title="Today's Trades"
          value={stats.todaysTrades.toString()}
          icon={<Activity className="w-5 h-5" />}
        />
      </div>

      {/* Performance Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <MetricCard
          title="Win Rate"
          value={`${metrics.winRate.toFixed(1)}%`}
          icon={<BarChart3 className="w-5 h-5" />}
        />
        
        <MetricCard
          title="Profit Factor"
          value={metrics.profitFactor.toFixed(2)}
          icon={<TrendingUp className="w-5 h-5" />}
        />
        
        <MetricCard
          title="Sharpe Ratio"
          value={metrics.sharpeRatio.toFixed(2)}
          icon={<Zap className="w-5 h-5" />}
        />
      </div>

      {/* Position Summary */}
      {positions.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <Target className="w-5 h-5 mr-2 text-blue-500" />
              Position Summary
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="text-center p-3 bg-trading-green/10 rounded-lg">
                <p className="text-2xl font-bold text-trading-green">
                  {stats.winningPositions}
                </p>
                <p className="text-sm text-muted-foreground">Winning</p>
              </div>
              
              <div className="text-center p-3 bg-trading-red/10 rounded-lg">
                <p className="text-2xl font-bold text-trading-red">
                  {stats.activePositions - stats.winningPositions}
                </p>
                <p className="text-sm text-muted-foreground">Losing</p>
              </div>
              
              <div className="text-center p-3 bg-blue-50 dark:bg-blue-950/20 rounded-lg">
                <p className="text-2xl font-bold text-blue-500">
                  {formatCurrency(stats.avgPositionSize)}
                </p>
                <p className="text-sm text-muted-foreground">Avg Size</p>
              </div>
              
              <div className="text-center p-3 bg-purple-50 dark:bg-purple-950/20 rounded-lg">
                <p className="text-2xl font-bold text-purple-500">
                  {formatPercentage((stats.winningPositions / stats.activePositions) * 100)}
                </p>
                <p className="text-sm text-muted-foreground">Win Rate</p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Recent Activity */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <Clock className="w-5 h-5 mr-2 text-orange-500" />
            Recent Activity
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {recentTrades.slice(0, 5).map((trade) => (
              <div key={trade.id} className="flex items-center justify-between p-2 bg-muted/30 rounded">
                <div className="flex items-center space-x-2">
                  <span className={cn('px-2 py-1 rounded text-xs font-medium', {
                    'bg-trading-green text-white': trade.side === 'BUY',
                    'bg-trading-red text-white': trade.side === 'SELL',
                  })}>
                    {trade.side}
                  </span>
                  <span className="font-medium">{trade.symbol}</span>
                </div>
                <div className="text-right">
                  <p className={cn('font-semibold', {
                    'text-trading-green': trade.pnl >= 0,
                    'text-trading-red': trade.pnl < 0,
                  })}>
                    {formatCurrency(trade.pnl)}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    {new Date(trade.timestamp).toLocaleTimeString()}
                  </p>
                </div>
              </div>
            ))}
            
            {recentTrades.length === 0 && (
              <p className="text-center text-muted-foreground text-sm py-4">
                No recent trades
              </p>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

export default RealTimeMetrics
