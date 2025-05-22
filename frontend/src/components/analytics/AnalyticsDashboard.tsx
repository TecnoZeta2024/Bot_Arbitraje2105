import React, { useState, useEffect } from 'react'
import { 
  BarChart3, 
  TrendingUp, 
  TrendingDown, 
  PieChart, 
  LineChart, 
  Activity, 
  Target, 
  DollarSign, 
  Brain, 
  Calendar, 
  Filter, 
  Download, 
  RefreshCw,
  Eye,
  Zap,
  Clock,
  Award,
  AlertCircle,
  Layers,
  Globe,
  Users,
  Smartphone
} from 'lucide-react'

import { Card, CardContent, CardHeader, CardTitle, MetricCard } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Switch } from '@/components/ui/switch'
import { useTradingStore, usePortfolioMetrics } from '@/store'
import { formatCurrency, formatPercentage, formatLargeNumber, cn } from '@/lib/utils'

// Mock analytics data
const mockAnalyticsData = {
  portfolioGrowth: [
    { month: 'Jan', value: 10000, benchmark: 10000 },
    { month: 'Feb', value: 10500, benchmark: 10200 },
    { month: 'Mar', value: 11200, benchmark: 10400 },
    { month: 'Apr', value: 10800, benchmark: 10600 },
    { month: 'May', value: 12100, benchmark: 10800 },
    { month: 'Jun', value: 11900, benchmark: 11000 },
    { month: 'Jul', value: 12800, benchmark: 11200 },
    { month: 'Aug', value: 13200, benchmark: 11400 },
    { month: 'Sep', value: 12900, benchmark: 11600 },
    { month: 'Oct', value: 13800, benchmark: 11800 },
    { month: 'Nov', value: 14200, benchmark: 12000 },
    { month: 'Dec', value: 15200, benchmark: 12200 },
  ],
  strategyPerformance: [
    { name: 'Scalping', trades: 245, winRate: 72.5, totalPnL: 2840.50, avgHoldTime: '12m' },
    { name: 'Day Trading', trades: 89, winRate: 65.2, totalPnL: 3120.80, avgHoldTime: '3.2h' },
    { name: 'Swing Trading', trades: 34, winRate: 58.8, totalPnL: 1890.20, avgHoldTime: '2.1d' },
    { name: 'Arbitrage', trades: 156, winRate: 91.0, totalPnL: 890.45, avgHoldTime: '5m' },
    { name: 'Grid Trading', trades: 78, winRate: 75.6, totalPnL: 1560.30, avgHoldTime: '8.5h' },
  ],
  marketAnalysis: {
    volatility: 0.28,
    correlation: {
      btc: 1.0,
      eth: 0.89,
      market: 0.72,
    },
    sentiment: {
      fear_greed: 65,
      social: 0.72,
      news: 0.58,
    },
    volume: {
      total24h: 28500000000,
      change24h: 15.2,
    },
  },
  riskMetrics: {
    var95: 0.032,
    expectedShortfall: 0.048,
    betaToMarket: 1.15,
    informationRatio: 1.42,
    trackingError: 0.028,
  },
}

// Time Period Selector Component
const TimePeriodSelector = ({ 
  selected, 
  onSelect 
}: { 
  selected: string
  onSelect: (period: string) => void 
}) => {
  const periods = [
    { value: '7d', label: '7D' },
    { value: '30d', label: '30D' },
    { value: '90d', label: '3M' },
    { value: '1y', label: '1Y' },
    { value: 'all', label: 'All' },
  ]

  return (
    <div className="flex items-center space-x-1 bg-muted p-1 rounded-lg">
      {periods.map((period) => (
        <button
          key={period.value}
          onClick={() => onSelect(period.value)}
          className={cn(
            'px-3 py-1 text-sm rounded transition-colors',
            selected === period.value
              ? 'bg-background text-foreground shadow-sm'
              : 'text-muted-foreground hover:text-foreground'
          )}
        >
          {period.label}
        </button>
      ))}
    </div>
  )
}

// Portfolio Growth Chart Component
const PortfolioGrowthChart = ({ data }: { data: any[] }) => {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <div className="flex items-center">
            <LineChart className="w-5 h-5 mr-2 text-blue-500" />
            Portfolio Growth
          </div>
          <div className="flex items-center space-x-2">
            <Switch />
            <span className="text-sm text-muted-foreground">vs Benchmark</span>
          </div>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-80 bg-muted/20 rounded-lg flex items-center justify-center mb-4">
          <div className="text-center">
            <TrendingUp className="w-12 h-12 mx-auto text-muted-foreground mb-2" />
            <p className="text-sm text-muted-foreground">Portfolio performance vs benchmark</p>
            <p className="text-xs text-muted-foreground mt-1">Integration with Recharts for real charts</p>
          </div>
        </div>
        
        {/* Performance Summary */}
        <div className="grid grid-cols-3 gap-4">
          <div className="text-center">
            <p className="text-2xl font-bold text-trading-green">+24.5%</p>
            <p className="text-xs text-muted-foreground">Total Return</p>
          </div>
          <div className="text-center">
            <p className="text-2xl font-bold text-blue-500">+12.2%</p>
            <p className="text-xs text-muted-foreground">Benchmark</p>
          </div>
          <div className="text-center">
            <p className="text-2xl font-bold text-purple-500">+12.3%</p>
            <p className="text-xs text-muted-foreground">Alpha</p>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

// Strategy Performance Component
const StrategyPerformance = ({ strategies }: { strategies: any[] }) => {
  const [sortBy, setSortBy] = useState('totalPnL')
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc')

  const sortedStrategies = [...strategies].sort((a, b) => {
    const aVal = a[sortBy]
    const bVal = b[sortBy]
    return sortOrder === 'asc' ? aVal - bVal : bVal - aVal
  })

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center">
          <Layers className="w-5 h-5 mr-2 text-purple-500" />
          Strategy Performance Analysis
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <table className="trading-table">
            <thead>
              <tr>
                <th>Strategy</th>
                <th>Trades</th>
                <th>Win Rate</th>
                <th>Total P&L</th>
                <th>Avg Hold Time</th>
                <th>Performance</th>
              </tr>
            </thead>
            <tbody>
              {sortedStrategies.map((strategy) => (
                <tr key={strategy.name}>
                  <td className="font-semibold">{strategy.name}</td>
                  <td className="font-mono-tabular">{strategy.trades}</td>
                  <td className="font-mono-tabular">
                    <span className={cn('font-semibold', {
                      'text-trading-green': strategy.winRate >= 70,
                      'text-trading-yellow': strategy.winRate >= 50 && strategy.winRate < 70,
                      'text-trading-red': strategy.winRate < 50,
                    })}>
                      {strategy.winRate.toFixed(1)}%
                    </span>
                  </td>
                  <td className={cn('font-mono-tabular font-semibold', {
                    'text-trading-green': strategy.totalPnL >= 0,
                    'text-trading-red': strategy.totalPnL < 0,
                  })}>
                    {formatCurrency(strategy.totalPnL)}
                  </td>
                  <td className="font-mono-tabular text-sm">{strategy.avgHoldTime}</td>
                  <td>
                    <div className="flex items-center space-x-2">
                      <div className="w-16 bg-muted rounded-full h-2">
                        <div 
                          className={cn('h-2 rounded-full', {
                            'bg-trading-green': strategy.winRate >= 70,
                            'bg-trading-yellow': strategy.winRate >= 50 && strategy.winRate < 70,
                            'bg-trading-red': strategy.winRate < 50,
                          })}
                          style={{ width: `${strategy.winRate}%` }}
                        />
                      </div>
                      <span className="text-xs text-muted-foreground">
                        {strategy.winRate >= 70 ? 'Excellent' : strategy.winRate >= 50 ? 'Good' : 'Poor'}
                      </span>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  )
}

// Market Analysis Component
const MarketAnalysis = ({ data }: { data: any }) => {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <Globe className="w-5 h-5 mr-2 text-green-500" />
            Market Overview
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-sm">Market Volatility</span>
              <span className="font-semibold">{(data.volatility * 100).toFixed(1)}%</span>
            </div>
            
            <div className="flex justify-between items-center">
              <span className="text-sm">24h Volume</span>
              <div className="text-right">
                <p className="font-semibold">{formatLargeNumber(data.volume.total24h)}</p>
                <p className={cn('text-xs', {
                  'text-trading-green': data.volume.change24h > 0,
                  'text-trading-red': data.volume.change24h < 0,
                })}>
                  {data.volume.change24h > 0 ? '+' : ''}{data.volume.change24h.toFixed(1)}%
                </p>
              </div>
            </div>

            <div className="space-y-2">
              <span className="text-sm font-medium">Correlation Matrix</span>
              <div className="space-y-1">
                <div className="flex justify-between text-sm">
                  <span>BTC Correlation</span>
                  <span className="font-mono-tabular">{data.correlation.btc.toFixed(2)}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span>ETH Correlation</span>
                  <span className="font-mono-tabular">{data.correlation.eth.toFixed(2)}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span>Market Correlation</span>
                  <span className="font-mono-tabular">{data.correlation.market.toFixed(2)}</span>
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <Brain className="w-5 h-5 mr-2 text-purple-500" />
            Sentiment Analysis
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-4">
            <div>
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm">Fear & Greed Index</span>
                <span className="font-semibold">{data.sentiment.fear_greed}/100</span>
              </div>
              <div className="w-full bg-muted rounded-full h-2">
                <div 
                  className={cn('h-2 rounded-full', {
                    'bg-trading-red': data.sentiment.fear_greed < 30,
                    'bg-trading-yellow': data.sentiment.fear_greed >= 30 && data.sentiment.fear_greed < 70,
                    'bg-trading-green': data.sentiment.fear_greed >= 70,
                  })}
                  style={{ width: `${data.sentiment.fear_greed}%` }}
                />
              </div>
              <p className="text-xs text-muted-foreground mt-1">
                {data.sentiment.fear_greed < 30 ? 'Extreme Fear' : 
                 data.sentiment.fear_greed < 70 ? 'Neutral' : 'Extreme Greed'}
              </p>
            </div>

            <div>
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm">Social Sentiment</span>
                <span className="font-semibold">{(data.sentiment.social * 100).toFixed(0)}%</span>
              </div>
              <div className="w-full bg-muted rounded-full h-2">
                <div 
                  className="bg-blue-500 h-2 rounded-full"
                  style={{ width: `${data.sentiment.social * 100}%` }}
                />
              </div>
            </div>

            <div>
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm">News Sentiment</span>
                <span className="font-semibold">{(data.sentiment.news * 100).toFixed(0)}%</span>
              </div>
              <div className="w-full bg-muted rounded-full h-2">
                <div 
                  className="bg-orange-500 h-2 rounded-full"
                  style={{ width: `${data.sentiment.news * 100}%` }}
                />
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

// Risk Analytics Component
const RiskAnalytics = ({ metrics }: { metrics: any }) => {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center">
          <AlertCircle className="w-5 h-5 mr-2 text-red-500" />
          Risk Analytics
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <div className="space-y-3">
            <h4 className="font-medium text-sm text-muted-foreground uppercase tracking-wide">Value at Risk</h4>
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-sm">95% VaR (1-day)</span>
                <span className="font-semibold text-trading-red">
                  {formatPercentage(metrics.var95 * 100)}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm">Expected Shortfall</span>
                <span className="font-semibold text-trading-red">
                  {formatPercentage(metrics.expectedShortfall * 100)}
                </span>
              </div>
            </div>
          </div>

          <div className="space-y-3">
            <h4 className="font-medium text-sm text-muted-foreground uppercase tracking-wide">Market Risk</h4>
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-sm">Beta to Market</span>
                <span className="font-semibold">{metrics.betaToMarket.toFixed(2)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm">Tracking Error</span>
                <span className="font-semibold">{formatPercentage(metrics.trackingError * 100)}</span>
              </div>
            </div>
          </div>

          <div className="space-y-3">
            <h4 className="font-medium text-sm text-muted-foreground uppercase tracking-wide">Performance</h4>
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-sm">Information Ratio</span>
                <span className={cn('font-semibold', {
                  'text-trading-green': metrics.informationRatio > 0.5,
                  'text-trading-yellow': metrics.informationRatio > 0,
                  'text-trading-red': metrics.informationRatio <= 0,
                })}>
                  {metrics.informationRatio.toFixed(2)}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm">Risk Score</span>
                <div className="flex items-center space-x-2">
                  <span className="font-semibold">7.2/10</span>
                  <div className="flex space-x-1">
                    {[1,2,3,4,5].map((i) => (
                      <div 
                        key={i}
                        className={cn('w-2 h-2 rounded-full', {
                          'bg-trading-green': i <= 3,
                          'bg-trading-yellow': i === 4,
                          'bg-trading-red': i === 5,
                        })}
                      />
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="mt-6 p-4 bg-blue-50 dark:bg-blue-950/20 rounded-lg">
          <div className="flex items-start space-x-3">
            <AlertCircle className="w-5 h-5 text-blue-500 mt-0.5" />
            <div>
              <h4 className="font-medium text-blue-900 dark:text-blue-100">Risk Assessment</h4>
              <p className="text-sm text-blue-700 dark:text-blue-300 mt-1">
                Your portfolio shows moderate risk levels with good diversification. 
                Current VaR suggests maximum daily loss of 3.2% with 95% confidence.
              </p>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

// Performance Summary Component
const PerformanceSummary = () => {
  const { portfolio, metrics } = usePortfolioMetrics()
  
  const performanceMetrics = [
    {
      title: 'Total Return',
      value: formatCurrency(portfolio.totalPnL),
      change: portfolio.totalPnLPercent,
      icon: DollarSign,
      trend: portfolio.totalPnL >= 0 ? 'up' : 'down'
    },
    {
      title: 'Sharpe Ratio',
      value: metrics.sharpeRatio.toFixed(2),
      icon: Award,
    },
    {
      title: 'Win Rate',
      value: `${metrics.winRate.toFixed(1)}%`,
      icon: Target,
    },
    {
      title: 'Profit Factor',
      value: metrics.profitFactor.toFixed(2),
      icon: TrendingUp,
    },
    {
      title: 'Max Drawdown',
      value: `${metrics.maxDrawdownPercent.toFixed(1)}%`,
      icon: TrendingDown,
      trend: 'down'
    },
    {
      title: 'Total Trades',
      value: metrics.totalTrades.toString(),
      icon: Activity,
    },
  ]

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {performanceMetrics.map((metric) => (
        <MetricCard
          key={metric.title}
          title={metric.title}
          value={metric.value}
          change={metric.change}
          trend={metric.trend}
          icon={<metric.icon className="w-5 h-5" />}
        />
      ))}
    </div>
  )
}

// Main Analytics Dashboard Component
export default function AnalyticsDashboard() {
  const [timePeriod, setTimePeriod] = useState('30d')
  const [activeTab, setActiveTab] = useState('overview')
  
  const tabs = [
    { id: 'overview', label: 'Overview', icon: BarChart3 },
    { id: 'performance', label: 'Performance', icon: TrendingUp },
    { id: 'risk', label: 'Risk Analysis', icon: AlertCircle },
    { id: 'market', label: 'Market Analysis', icon: Globe },
  ]

  return (
    <div className="px-6 py-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Analytics Dashboard</h1>
          <p className="text-muted-foreground">Comprehensive analysis of your trading performance</p>
        </div>
        <div className="flex items-center space-x-2">
          <TimePeriodSelector selected={timePeriod} onSelect={setTimePeriod} />
          <Button variant="outline" size="sm">
            <RefreshCw className="w-4 h-4 mr-2" />
            Refresh
          </Button>
          <Button variant="outline" size="sm">
            <Download className="w-4 h-4 mr-2" />
            Export
          </Button>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="border-b border-border">
        <nav className="flex space-x-8">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={cn(
                'flex items-center space-x-2 py-2 px-1 border-b-2 font-medium text-sm transition-colors',
                activeTab === tab.id
                  ? 'border-primary text-primary'
                  : 'border-transparent text-muted-foreground hover:text-foreground hover:border-muted-foreground'
              )}
            >
              <tab.icon className="w-4 h-4" />
              <span>{tab.label}</span>
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      <div className="space-y-6">
        {activeTab === 'overview' && (
          <>
            <PerformanceSummary />
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <PortfolioGrowthChart data={mockAnalyticsData.portfolioGrowth} />
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center">
                    <PieChart className="w-5 h-5 mr-2 text-orange-500" />
                    Asset Allocation
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="h-64 bg-muted/20 rounded-lg flex items-center justify-center">
                    <div className="text-center">
                      <PieChart className="w-12 h-12 mx-auto text-muted-foreground mb-2" />
                      <p className="text-sm text-muted-foreground">Portfolio allocation breakdown</p>
                      <p className="text-xs text-muted-foreground mt-1">By asset type and strategy</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </>
        )}

        {activeTab === 'performance' && (
          <>
            <PortfolioGrowthChart data={mockAnalyticsData.portfolioGrowth} />
            <StrategyPerformance strategies={mockAnalyticsData.strategyPerformance} />
          </>
        )}

        {activeTab === 'risk' && (
          <>
            <RiskAnalytics metrics={mockAnalyticsData.riskMetrics} />
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center">
                    <BarChart3 className="w-5 h-5 mr-2 text-red-500" />
                    Risk Distribution
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="h-64 bg-muted/20 rounded-lg flex items-center justify-center">
                    <div className="text-center">
                      <BarChart3 className="w-12 h-12 mx-auto text-muted-foreground mb-2" />
                      <p className="text-sm text-muted-foreground">Risk distribution analysis</p>
                      <p className="text-xs text-muted-foreground mt-1">VaR and stress testing results</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center">
                    <LineChart className="w-5 h-5 mr-2 text-purple-500" />
                    Volatility Analysis
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="h-64 bg-muted/20 rounded-lg flex items-center justify-center">
                    <div className="text-center">
                      <Activity className="w-12 h-12 mx-auto text-muted-foreground mb-2" />
                      <p className="text-sm text-muted-foreground">Historical volatility trends</p>
                      <p className="text-xs text-muted-foreground mt-1">Rolling volatility and correlation</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </>
        )}

        {activeTab === 'market' && (
          <>
            <MarketAnalysis data={mockAnalyticsData.marketAnalysis} />
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center">
                    <Clock className="w-5 h-5 mr-2 text-blue-500" />
                    Market Timing Analysis
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="h-64 bg-muted/20 rounded-lg flex items-center justify-center">
                    <div className="text-center">
                      <Clock className="w-12 h-12 mx-auto text-muted-foreground mb-2" />
                      <p className="text-sm text-muted-foreground">Best trading hours analysis</p>
                      <p className="text-xs text-muted-foreground mt-1">Performance by time of day</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center">
                    <Zap className="w-5 h-5 mr-2 text-yellow-500" />
                    Market Regime Detection
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="h-64 bg-muted/20 rounded-lg flex items-center justify-center">
                    <div className="text-center">
                      <Zap className="w-12 h-12 mx-auto text-muted-foreground mb-2" />
                      <p className="text-sm text-muted-foreground">Bull/Bear market detection</p>
                      <p className="text-xs text-muted-foreground mt-1">Strategy adaptation recommendations</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </>
        )}
      </div>
    </div>
  )
}
