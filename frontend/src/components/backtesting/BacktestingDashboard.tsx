import React, { useState, useEffect } from 'react'
import { 
  Play, 
  Pause, 
  Square, 
  BarChart3, 
  TrendingUp, 
  TrendingDown, 
  Calendar, 
  DollarSign, 
  Target, 
  Activity, 
  Download,
  Upload,
  Settings,
  RefreshCw,
  RotateCcw,
  Save,
  FileText,
  PieChart,
  LineChart,
  Zap,
  Clock
} from 'lucide-react'

import { Card, CardContent, CardHeader, CardTitle, MetricCard } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Switch } from '@/components/ui/switch'
import { useTradingStore } from '@/store'
import { formatCurrency, formatPercentage, cn } from '@/lib/utils'

// Mock backtest data
const mockBacktestResults = {
  totalReturn: 15.67,
  totalReturnPercent: 15.67,
  winRate: 68.5,
  totalTrades: 147,
  avgWin: 45.23,
  avgLoss: -28.17,
  profitFactor: 1.85,
  sharpeRatio: 1.42,
  maxDrawdown: 8.95,
  maxDrawdownPercent: 8.95,
  calmarRatio: 1.75,
  sortino: 1.89,
  equity: Array.from({ length: 100 }, (_, i) => ({
    timestamp: Date.now() - (100 - i) * 24 * 60 * 60 * 1000,
    value: 10000 + Math.random() * 1000 * i - Math.random() * 500 * i,
  })),
  trades: Array.from({ length: 20 }, (_, i) => ({
    id: `trade_${i}`,
    symbol: ['BTCUSDT', 'ETHUSDT', 'BNBUSDT'][Math.floor(Math.random() * 3)],
    side: Math.random() > 0.5 ? 'BUY' : 'SELL',
    entryPrice: 35000 + Math.random() * 10000,
    exitPrice: 35000 + Math.random() * 10000,
    quantity: Math.random() * 0.1,
    pnl: (Math.random() - 0.5) * 200,
    pnlPercent: (Math.random() - 0.5) * 10,
    entryTime: Date.now() - Math.random() * 30 * 24 * 60 * 60 * 1000,
    exitTime: Date.now() - Math.random() * 25 * 24 * 60 * 60 * 1000,
    duration: Math.random() * 24 * 60 * 60 * 1000,
    strategy: ['Scalping', 'DCA', 'Grid'][Math.floor(Math.random() * 3)],
  })),
}

interface BacktestConfig {
  strategy: string
  timeframe: string
  startDate: string
  endDate: string
  initialCapital: number
  symbolPairs: string[]
  commission: number
  slippage: number
  maxPositions: number
}

// Backtest Configuration Component
const BacktestConfigPanel = ({ 
  config, 
  onConfigChange, 
  onStart, 
  onStop, 
  isRunning 
}: {
  config: BacktestConfig
  onConfigChange: (config: BacktestConfig) => void
  onStart: () => void
  onStop: () => void
  isRunning: boolean
}) => {
  const handleInputChange = (field: keyof BacktestConfig, value: any) => {
    onConfigChange({ ...config, [field]: value })
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center">
          <Settings className="w-5 h-5 mr-2 text-blue-500" />
          Backtest Configuration
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Strategy Selection */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="space-y-2">
            <label className="text-sm font-medium">Strategy</label>
            <select 
              value={config.strategy}
              onChange={(e) => handleInputChange('strategy', e.target.value)}
              className="w-full p-2 border border-border rounded-md bg-background"
            >
              <option value="scalping">Scalping Strategy</option>
              <option value="day_trading">Day Trading</option>
              <option value="swing_trading">Swing Trading</option>
              <option value="arbitrage">Arbitrage</option>
              <option value="grid_trading">Grid Trading</option>
              <option value="dca">DCA Strategy</option>
              <option value="custom">Custom Strategy</option>
            </select>
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium">Timeframe</label>
            <select 
              value={config.timeframe}
              onChange={(e) => handleInputChange('timeframe', e.target.value)}
              className="w-full p-2 border border-border rounded-md bg-background"
            >
              <option value="1m">1 Minute</option>
              <option value="5m">5 Minutes</option>
              <option value="15m">15 Minutes</option>
              <option value="1h">1 Hour</option>
              <option value="4h">4 Hours</option>
              <option value="1d">1 Day</option>
            </select>
          </div>
        </div>

        {/* Date Range */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="space-y-2">
            <label className="text-sm font-medium">Start Date</label>
            <Input
              type="date"
              value={config.startDate}
              onChange={(e) => handleInputChange('startDate', e.target.value)}
            />
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium">End Date</label>
            <Input
              type="date"
              value={config.endDate}
              onChange={(e) => handleInputChange('endDate', e.target.value)}
            />
          </div>
        </div>

        {/* Trading Parameters */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="space-y-2">
            <label className="text-sm font-medium">Initial Capital ($)</label>
            <Input
              type="number"
              min="1000"
              max="1000000"
              step="1000"
              value={config.initialCapital}
              onChange={(e) => handleInputChange('initialCapital', parseFloat(e.target.value))}
            />
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium">Commission (%)</label>
            <Input
              type="number"
              min="0"
              max="1"
              step="0.01"
              value={config.commission}
              onChange={(e) => handleInputChange('commission', parseFloat(e.target.value))}
            />
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium">Slippage (%)</label>
            <Input
              type="number"
              min="0"
              max="0.5"
              step="0.01"
              value={config.slippage}
              onChange={(e) => handleInputChange('slippage', parseFloat(e.target.value))}
            />
          </div>
        </div>

        {/* Symbol Selection */}
        <div className="space-y-2">
          <label className="text-sm font-medium">Trading Pairs</label>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
            {['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT', 'SOLUSDT', 'XRPUSDT', 'DOTUSDT', 'LINKUSDT'].map((symbol) => (
              <div key={symbol} className="flex items-center space-x-2">
                <Switch
                  checked={config.symbolPairs.includes(symbol)}
                  onCheckedChange={(checked) => {
                    const newPairs = checked
                      ? [...config.symbolPairs, symbol]
                      : config.symbolPairs.filter(s => s !== symbol)
                    handleInputChange('symbolPairs', newPairs)
                  }}
                />
                <span className="text-sm">{symbol}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Control Buttons */}
        <div className="flex space-x-2">
          <Button 
            onClick={onStart}
            disabled={isRunning || config.symbolPairs.length === 0}
            className="flex-1"
          >
            <Play className="w-4 h-4 mr-2" />
            Start Backtest
          </Button>
          <Button 
            onClick={onStop}
            disabled={!isRunning}
            variant="destructive"
            className="flex-1"
          >
            <Square className="w-4 h-4 mr-2" />
            Stop
          </Button>
          <Button variant="outline">
            <Upload className="w-4 h-4 mr-2" />
            Load Config
          </Button>
          <Button variant="outline">
            <Save className="w-4 h-4 mr-2" />
            Save Config
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}

// Performance Metrics Component
const PerformanceMetrics = ({ results }: { results: any }) => {
  const metrics = [
    { label: 'Total Return', value: formatCurrency(results.totalReturn), change: results.totalReturnPercent, icon: DollarSign },
    { label: 'Win Rate', value: `${results.winRate}%`, icon: Target },
    { label: 'Total Trades', value: results.totalTrades.toString(), icon: Activity },
    { label: 'Profit Factor', value: results.profitFactor.toFixed(2), icon: TrendingUp },
    { label: 'Sharpe Ratio', value: results.sharpeRatio.toFixed(2), icon: BarChart3 },
    { label: 'Max Drawdown', value: `${results.maxDrawdownPercent.toFixed(2)}%`, icon: TrendingDown },
  ]

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {metrics.map((metric) => (
        <MetricCard
          key={metric.label}
          title={metric.label}
          value={metric.value}
          change={metric.change}
          trend={metric.change && metric.change > 0 ? 'up' : 'down'}
          icon={<metric.icon className="w-5 h-5" />}
        />
      ))}
    </div>
  )
}

// Equity Curve Component
const EquityCurve = ({ data }: { data: any[] }) => {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center">
          <LineChart className="w-5 h-5 mr-2 text-blue-500" />
          Equity Curve
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-64 bg-muted/20 rounded-lg flex items-center justify-center">
          <div className="text-center">
            <LineChart className="w-12 h-12 mx-auto text-muted-foreground mb-2" />
            <p className="text-sm text-muted-foreground">Equity curve visualization would render here</p>
            <p className="text-xs text-muted-foreground mt-1">Using Recharts or similar charting library</p>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

// Trade Analysis Component
const TradeAnalysis = ({ trades }: { trades: any[] }) => {
  const [sortBy, setSortBy] = useState('entryTime')
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc')
  const [filterSymbol, setFilterSymbol] = useState('all')

  const sortedTrades = trades
    .filter(trade => filterSymbol === 'all' || trade.symbol === filterSymbol)
    .sort((a, b) => {
      const aVal = a[sortBy]
      const bVal = b[sortBy]
      return sortOrder === 'asc' ? aVal - bVal : bVal - aVal
    })

  const uniqueSymbols = [...new Set(trades.map(t => t.symbol))]

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <div className="flex items-center">
            <FileText className="w-5 h-5 mr-2 text-green-500" />
            Trade Analysis
          </div>
          <div className="flex items-center space-x-2">
            <select 
              value={filterSymbol}
              onChange={(e) => setFilterSymbol(e.target.value)}
              className="text-sm p-1 border border-border rounded bg-background"
            >
              <option value="all">All Symbols</option>
              {uniqueSymbols.map(symbol => (
                <option key={symbol} value={symbol}>{symbol}</option>
              ))}
            </select>
            <Button variant="outline" size="sm">
              <Download className="w-4 h-4 mr-1" />
              Export
            </Button>
          </div>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <table className="trading-table">
            <thead>
              <tr>
                <th>Symbol</th>
                <th>Side</th>
                <th>Entry Price</th>
                <th>Exit Price</th>
                <th>Quantity</th>
                <th>P&L</th>
                <th>P&L %</th>
                <th>Duration</th>
                <th>Strategy</th>
              </tr>
            </thead>
            <tbody>
              {sortedTrades.slice(0, 10).map((trade) => (
                <tr key={trade.id}>
                  <td className="font-semibold">{trade.symbol}</td>
                  <td>
                    <span className={cn('px-2 py-1 rounded text-xs font-medium', {
                      'bg-trading-green text-white': trade.side === 'BUY',
                      'bg-trading-red text-white': trade.side === 'SELL',
                    })}>
                      {trade.side}
                    </span>
                  </td>
                  <td className="font-mono-tabular">{formatCurrency(trade.entryPrice)}</td>
                  <td className="font-mono-tabular">{formatCurrency(trade.exitPrice)}</td>
                  <td className="font-mono-tabular">{trade.quantity.toFixed(4)}</td>
                  <td className={cn('font-mono-tabular font-semibold', {
                    'text-trading-green': trade.pnl >= 0,
                    'text-trading-red': trade.pnl < 0,
                  })}>
                    {formatCurrency(trade.pnl)}
                  </td>
                  <td className={cn('font-mono-tabular', {
                    'text-trading-green': trade.pnlPercent >= 0,
                    'text-trading-red': trade.pnlPercent < 0,
                  })}>
                    {formatPercentage(trade.pnlPercent)}
                  </td>
                  <td className="text-sm">
                    {Math.round(trade.duration / (1000 * 60 * 60))}h
                  </td>
                  <td className="text-sm">{trade.strategy}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  )
}

// Distribution Analysis Component
const DistributionAnalysis = ({ trades }: { trades: any[] }) => {
  const winningTrades = trades.filter(t => t.pnl > 0)
  const losingTrades = trades.filter(t => t.pnl < 0)
  
  const pnlDistribution = {
    wins: winningTrades.length,
    losses: losingTrades.length,
    avgWin: winningTrades.reduce((sum, t) => sum + t.pnl, 0) / winningTrades.length || 0,
    avgLoss: losingTrades.reduce((sum, t) => sum + t.pnl, 0) / losingTrades.length || 0,
    maxWin: Math.max(...winningTrades.map(t => t.pnl), 0),
    maxLoss: Math.min(...losingTrades.map(t => t.pnl), 0),
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <PieChart className="w-5 h-5 mr-2 text-purple-500" />
            P&L Distribution
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="text-center p-4 bg-trading-green/10 rounded-lg">
              <p className="text-2xl font-bold text-trading-green">{pnlDistribution.wins}</p>
              <p className="text-sm text-muted-foreground">Winning Trades</p>
            </div>
            <div className="text-center p-4 bg-trading-red/10 rounded-lg">
              <p className="text-2xl font-bold text-trading-red">{pnlDistribution.losses}</p>
              <p className="text-sm text-muted-foreground">Losing Trades</p>
            </div>
          </div>
          
          <div className="space-y-2">
            <div className="flex justify-between">
              <span className="text-sm">Average Win</span>
              <span className="text-sm font-semibold text-trading-green">
                {formatCurrency(pnlDistribution.avgWin)}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm">Average Loss</span>
              <span className="text-sm font-semibold text-trading-red">
                {formatCurrency(pnlDistribution.avgLoss)}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm">Best Trade</span>
              <span className="text-sm font-semibold text-trading-green">
                {formatCurrency(pnlDistribution.maxWin)}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm">Worst Trade</span>
              <span className="text-sm font-semibold text-trading-red">
                {formatCurrency(pnlDistribution.maxLoss)}
              </span>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <Clock className="w-5 h-5 mr-2 text-orange-500" />
            Time Analysis
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-48 bg-muted/20 rounded-lg flex items-center justify-center">
            <div className="text-center">
              <BarChart3 className="w-12 h-12 mx-auto text-muted-foreground mb-2" />
              <p className="text-sm text-muted-foreground">Time-based performance analysis</p>
              <p className="text-xs text-muted-foreground mt-1">Hourly/Daily performance breakdown</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

// Main Backtesting Dashboard Component
export default function BacktestingDashboard() {
  const [isRunning, setIsRunning] = useState(false)
  const [progress, setProgress] = useState(0)
  const [results, setResults] = useState(mockBacktestResults)
  const [config, setConfig] = useState<BacktestConfig>({
    strategy: 'scalping',
    timeframe: '5m',
    startDate: '2024-01-01',
    endDate: '2024-12-31',
    initialCapital: 10000,
    symbolPairs: ['BTCUSDT', 'ETHUSDT'],
    commission: 0.1,
    slippage: 0.05,
    maxPositions: 5,
  })

  const handleStartBacktest = () => {
    setIsRunning(true)
    setProgress(0)
    
    // Simulate backtest progress
    const interval = setInterval(() => {
      setProgress(prev => {
        if (prev >= 100) {
          clearInterval(interval)
          setIsRunning(false)
          return 100
        }
        return prev + Math.random() * 10
      })
    }, 200)
  }

  const handleStopBacktest = () => {
    setIsRunning(false)
    setProgress(0)
  }

  return (
    <div className="px-6 py-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Backtesting</h1>
          <p className="text-muted-foreground">Test your trading strategies with historical data</p>
        </div>
        <div className="flex items-center space-x-2">
          <Button variant="outline" size="sm">
            <RefreshCw className="w-4 h-4 mr-2" />
            Refresh Data
          </Button>
          <Button variant="outline" size="sm">
            <Download className="w-4 h-4 mr-2" />
            Export Results
          </Button>
        </div>
      </div>

      {/* Progress Bar */}
      {isRunning && (
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center space-x-4">
              <Zap className="w-5 h-5 text-blue-500 animate-pulse" />
              <div className="flex-1">
                <div className="flex justify-between text-sm mb-1">
                  <span>Running backtest...</span>
                  <span>{progress.toFixed(1)}%</span>
                </div>
                <div className="w-full bg-muted rounded-full h-2">
                  <div 
                    className="bg-blue-500 h-2 rounded-full transition-all duration-300" 
                    style={{ width: `${progress}%` }}
                  />
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Configuration Panel */}
      <BacktestConfigPanel
        config={config}
        onConfigChange={setConfig}
        onStart={handleStartBacktest}
        onStop={handleStopBacktest}
        isRunning={isRunning}
      />

      {/* Results Section */}
      {results && !isRunning && (
        <div className="space-y-6">
          {/* Performance Metrics */}
          <div>
            <h2 className="text-xl font-semibold mb-4">Performance Overview</h2>
            <PerformanceMetrics results={results} />
          </div>

          {/* Charts */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <EquityCurve data={results.equity} />
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <BarChart3 className="w-5 h-5 mr-2 text-green-500" />
                  Drawdown Analysis
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="h-64 bg-muted/20 rounded-lg flex items-center justify-center">
                  <div className="text-center">
                    <TrendingDown className="w-12 h-12 mx-auto text-muted-foreground mb-2" />
                    <p className="text-sm text-muted-foreground">Drawdown visualization</p>
                    <p className="text-xs text-muted-foreground mt-1">Max DD: {formatPercentage(results.maxDrawdownPercent)}</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Distribution Analysis */}
          <div>
            <h2 className="text-xl font-semibold mb-4">Distribution Analysis</h2>
            <DistributionAnalysis trades={results.trades} />
          </div>

          {/* Trade Analysis */}
          <TradeAnalysis trades={results.trades} />
        </div>
      )}
    </div>
  )
}
