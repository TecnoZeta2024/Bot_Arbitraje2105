import React, { useState, useEffect } from 'react'
import { 
  Brain, 
  Play, 
  Pause, 
  Settings, 
  TrendingUp,
  Activity,
  DollarSign,
  BarChart3,
  Shield,
  Zap,
  ChevronDown,
  ChevronUp,
  Info,
  AlertTriangle
} from 'lucide-react'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'
import { aiStrategyEngine } from '@/lib/AIStrategyEngine'
import { Strategy, StrategyType, Signal } from '@/types/strategy.types'

// Strategy Type Icon
const getStrategyIcon = (type: StrategyType) => {
  switch (type) {
    case StrategyType.TREND_FOLLOWING:
      return <TrendingUp className="w-5 h-5 text-blue-500" />
    case StrategyType.MEAN_REVERSION:
      return <Activity className="w-5 h-5 text-purple-500" />
    case StrategyType.MOMENTUM:
      return <Zap className="w-5 h-5 text-yellow-500" />
    case StrategyType.SCALPING:
      return <BarChart3 className="w-5 h-5 text-green-500" />
    case StrategyType.ARBITRAGE:
      return <Shield className="w-5 h-5 text-cyan-500" />
    case StrategyType.AI_HYBRID:
      return <Brain className="w-5 h-5 text-pink-500" />
    default:
      return <Brain className="w-5 h-5 text-gray-500" />
  }
}

// Strategy Card Component
const StrategyCard = ({ 
  strategy, 
  onToggle, 
  onGenerateSignal 
}: { 
  strategy: Strategy
  onToggle: (strategyId: string, activate: boolean) => void
  onGenerateSignal: (strategyId: string) => void
}) => {
  const [isExpanded, setIsExpanded] = useState(false)
  const [lastSignal, setLastSignal] = useState<Signal | null>(null)
  
  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(amount)
  }
  
  const formatPercentage = (percent: number) => {
    return `${percent >= 0 ? '+' : ''}${percent.toFixed(2)}%`
  }
  
  const getRiskColor = (level: string) => {
    switch (level) {
      case 'LOW': return 'text-green-600'
      case 'MEDIUM': return 'text-yellow-600'
      case 'HIGH': return 'text-orange-600'
      case 'AGGRESSIVE': return 'text-red-600'
      default: return 'text-gray-600'
    }
  }
  
  const handleGenerateSignal = () => {
    const symbols = ['BTCUSDT', 'ETHUSDT', 'ADAUSDT', 'DOTUSDT', 'LINKUSDT', 'BNBUSDT']
    const symbol = symbols[Math.floor(Math.random() * symbols.length)]
    const signal = aiStrategyEngine.generateSignal(strategy.id, symbol)
    if (signal) {
      setLastSignal(signal)
      onGenerateSignal(strategy.id)
      
      // Clear signal after 5 seconds
      setTimeout(() => setLastSignal(null), 5000)
    }
  }
  
  return (
    <Card className={cn('transition-all duration-200', {
      'ring-2 ring-green-200': strategy.isActive,
      'opacity-75': !strategy.isActive
    })}>
      <CardHeader>
        <div className="flex items-start justify-between">
          <div className="flex items-start space-x-3">
            {getStrategyIcon(strategy.type)}
            <div>
              <CardTitle className="text-lg flex items-center">
                {strategy.name}
                {strategy.isActive && (
                  <div className="ml-2 w-2 h-2 bg-green-500 rounded-full animate-pulse" />
                )}
              </CardTitle>
              <p className="text-sm text-muted-foreground mt-1">{strategy.description}</p>
            </div>
          </div>
          <Button
            size="sm"
            variant={strategy.isActive ? "destructive" : "default"}
            onClick={() => onToggle(strategy.id, !strategy.isActive)}
          >
            {strategy.isActive ? (
              <>
                <Pause className="w-4 h-4 mr-1" />
                Pause
              </>
            ) : (
              <>
                <Play className="w-4 h-4 mr-1" />
                Start
              </>
            )}
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {/* Quick Stats */}
          <div className="grid grid-cols-4 gap-3">
            <div className="text-center">
              <p className="text-xs text-muted-foreground">Win Rate</p>
              <p className={cn('text-sm font-bold', {
                'text-green-600': strategy.performance.winRate > 60,
                'text-yellow-600': strategy.performance.winRate >= 40 && strategy.performance.winRate <= 60,
                'text-red-600': strategy.performance.winRate < 40
              })}>
                {strategy.performance.winRate.toFixed(1)}%
              </p>
            </div>
            <div className="text-center">
              <p className="text-xs text-muted-foreground">Total P&L</p>
              <p className={cn('text-sm font-bold', {
                'text-green-600': strategy.performance.totalPnL > 0,
                'text-red-600': strategy.performance.totalPnL < 0
              })}>
                {formatCurrency(strategy.performance.totalPnL)}
              </p>
            </div>
            <div className="text-center">
              <p className="text-xs text-muted-foreground">Trades</p>
              <p className="text-sm font-bold">{strategy.performance.totalTrades}</p>
            </div>
            <div className="text-center">
              <p className="text-xs text-muted-foreground">Risk</p>
              <p className={cn('text-sm font-bold', getRiskColor(strategy.riskProfile.riskLevel))}>
                {strategy.riskProfile.riskLevel}
              </p>
            </div>
          </div>
          
          {/* Last Signal Alert */}
          {lastSignal && (
            <div className={cn('p-3 rounded-lg border animate-pulse', {
              'bg-green-50 border-green-200': lastSignal.action === 'BUY',
              'bg-red-50 border-red-200': lastSignal.action === 'SELL',
              'bg-yellow-50 border-yellow-200': lastSignal.action === 'HOLD'
            })}>
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <Zap className="w-4 h-4 text-yellow-500" />
                  <span className="text-sm font-medium">New Signal Generated!</span>
                </div>
                <span className={cn('px-2 py-1 rounded text-xs font-medium', {
                  'bg-green-100 text-green-800': lastSignal.action === 'BUY',
                  'bg-red-100 text-red-800': lastSignal.action === 'SELL',
                  'bg-yellow-100 text-yellow-800': lastSignal.action === 'HOLD'
                })}>
                  {lastSignal.action} {lastSignal.symbol}
                </span>
              </div>
            </div>
          )}
          
          {/* Action Buttons */}
          <div className="flex space-x-2">
            <Button 
              size="sm" 
              variant="outline"
              disabled={!strategy.isActive}
              onClick={handleGenerateSignal}
              className="flex-1"
            >
              <Brain className="w-4 h-4 mr-1" />
              Generate Signal
            </Button>
            <Button 
              size="sm" 
              variant="outline"
              onClick={() => setIsExpanded(!isExpanded)}
              className="flex-1"
            >
              <Settings className="w-4 h-4 mr-1" />
              Details
              {isExpanded ? (
                <ChevronUp className="w-4 h-4 ml-1" />
              ) : (
                <ChevronDown className="w-4 h-4 ml-1" />
              )}
            </Button>
          </div>
          
          {/* Expanded Details */}
          {isExpanded && (
            <div className="border-t pt-4 space-y-3">
              {/* Parameters */}
              <div>
                <h4 className="text-sm font-semibold mb-2">Strategy Parameters</h4>
                <div className="grid grid-cols-2 gap-2 text-xs">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Timeframe:</span>
                    <span className="font-medium">{strategy.parameters.timeframe}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Stop Loss:</span>
                    <span className="font-medium text-red-600">{strategy.parameters.stopLoss}%</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Take Profit:</span>
                    <span className="font-medium text-green-600">{strategy.parameters.takeProfit}%</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Position Size:</span>
                    <span className="font-medium">{strategy.parameters.positionSize}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Max Daily Loss:</span>
                    <span className="font-medium">{strategy.parameters.maxDailyLoss}%</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Max Positions:</span>
                    <span className="font-medium">{strategy.parameters.maxOpenPositions}</span>
                  </div>
                </div>
              </div>
              
              {/* Performance Metrics */}
              <div>
                <h4 className="text-sm font-semibold mb-2">Performance Metrics</h4>
                <div className="grid grid-cols-2 gap-2 text-xs">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Profit Factor:</span>
                    <span className="font-medium">{strategy.performance.profitFactor.toFixed(2)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Sharpe Ratio:</span>
                    <span className="font-medium">{strategy.performance.sharpeRatio.toFixed(2)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Max Drawdown:</span>
                    <span className="font-medium text-red-600">{strategy.performance.maxDrawdown.toFixed(2)}%</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">ROI:</span>
                    <span className={cn('font-medium', {
                      'text-green-600': strategy.performance.roi > 0,
                      'text-red-600': strategy.performance.roi < 0
                    })}>
                      {formatPercentage(strategy.performance.roi)}
                    </span>
                  </div>
                </div>
              </div>
              
              {/* Indicators */}
              <div>
                <h4 className="text-sm font-semibold mb-2">Active Indicators</h4>
                <div className="space-y-1">
                  {strategy.parameters.indicators.map((indicator, index) => (
                    <div key={index} className="flex items-center justify-between text-xs bg-gray-50 p-2 rounded">
                      <span className="font-medium">{indicator.name}</span>
                      <span className="text-gray-600">Weight: {(indicator.weight * 100).toFixed(0)}%</span>
                    </div>
                  ))}
                </div>
              </div>
              
              {/* Risk Profile */}
              <div>
                <h4 className="text-sm font-semibold mb-2">Risk Management</h4>
                <div className="grid grid-cols-2 gap-2 text-xs">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Max Leverage:</span>
                    <span className="font-medium">{strategy.riskProfile.maxLeverage}x</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Max Exposure:</span>
                    <span className="font-medium">{strategy.riskProfile.maxExposure}%</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Stop Loss:</span>
                    <span className={cn('font-medium', {
                      'text-green-600': strategy.riskProfile.stopLossEnabled,
                      'text-red-600': !strategy.riskProfile.stopLossEnabled
                    })}>
                      {strategy.riskProfile.stopLossEnabled ? 'Enabled' : 'Disabled'}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">R:R Ratio:</span>
                    <span className="font-medium">1:{strategy.riskProfile.riskRewardRatio}</span>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  )
}

// Strategy Overview Card
const StrategyOverview = ({ strategies }: { strategies: Strategy[] }) => {
  const activeStrategies = strategies.filter(s => s.isActive)
  const totalPnL = strategies.reduce((sum, s) => sum + s.performance.totalPnL, 0)
  const totalTrades = strategies.reduce((sum, s) => sum + s.performance.totalTrades, 0)
  const avgWinRate = strategies.length > 0 
    ? strategies.reduce((sum, s) => sum + s.performance.winRate, 0) / strategies.length 
    : 0
  
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center">
          <Brain className="w-5 h-5 mr-2 text-purple-500" />
          Strategy Portfolio Overview
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="text-center">
            <p className="text-sm text-muted-foreground">Active Strategies</p>
            <p className="text-2xl font-bold text-green-600">{activeStrategies.length}/{strategies.length}</p>
          </div>
          <div className="text-center">
            <p className="text-sm text-muted-foreground">Total P&L</p>
            <p className={cn('text-2xl font-bold', {
              'text-green-600': totalPnL > 0,
              'text-red-600': totalPnL < 0
            })}>
              ${Math.abs(totalPnL).toFixed(2)}
            </p>
          </div>
          <div className="text-center">
            <p className="text-sm text-muted-foreground">Total Trades</p>
            <p className="text-2xl font-bold">{totalTrades}</p>
          </div>
          <div className="text-center">
            <p className="text-sm text-muted-foreground">Avg Win Rate</p>
            <p className={cn('text-2xl font-bold', {
              'text-green-600': avgWinRate > 60,
              'text-yellow-600': avgWinRate >= 40 && avgWinRate <= 60,
              'text-red-600': avgWinRate < 40
            })}>
              {avgWinRate.toFixed(1)}%
            </p>
          </div>
        </div>
        
        <div className="mt-4 p-3 bg-blue-50 rounded-lg">
          <div className="flex items-start space-x-2">
            <Info className="w-4 h-4 text-blue-600 mt-0.5" />
            <div className="text-xs text-blue-800">
              <p className="font-semibold mb-1">AI Strategy Management Active</p>
              <p>Strategies are continuously optimized using machine learning algorithms. Performance metrics are updated in real-time.</p>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

// Main Strategy Manager Component
export default function StrategyManager() {
  const [strategies, setStrategies] = useState<Strategy[]>([])
  const [signalCount, setSignalCount] = useState(0)
  
  useEffect(() => {
    // Load strategies
    const loadedStrategies = aiStrategyEngine.getAllStrategies()
    setStrategies(loadedStrategies)
    
    // Auto-generate signals for active strategies
    const signalInterval = setInterval(() => {
      const activeStrategies = aiStrategyEngine.getActiveStrategies()
      activeStrategies.forEach(strategy => {
        if (Math.random() < 0.3) { // 30% chance per interval
          const symbols = ['BTCUSDT', 'ETHUSDT', 'ADAUSDT', 'DOTUSDT', 'LINKUSDT', 'BNBUSDT']
          const symbol = symbols[Math.floor(Math.random() * symbols.length)]
          const signal = aiStrategyEngine.generateSignal(strategy.id, symbol)
          if (signal) {
            console.log(`📊 [${strategy.name}] Generated ${signal.action} signal for ${symbol}`)
            setSignalCount(prev => prev + 1)
          }
        }
      })
      
      // Refresh strategies to show updated data
      setStrategies(aiStrategyEngine.getAllStrategies())
    }, 10000) // Every 10 seconds
    
    return () => clearInterval(signalInterval)
  }, [])
  
  const handleToggleStrategy = (strategyId: string, activate: boolean) => {
    if (activate) {
      aiStrategyEngine.activateStrategy(strategyId)
      alert(`✅ Strategy activated! AI will now generate trading signals based on this strategy.`)
    } else {
      aiStrategyEngine.deactivateStrategy(strategyId)
      alert(`⏸️ Strategy paused. Signal generation stopped for this strategy.`)
    }
    setStrategies(aiStrategyEngine.getAllStrategies())
  }
  
  const handleGenerateSignal = (strategyId: string) => {
    setSignalCount(prev => prev + 1)
    console.log(`📊 Manual signal generated for strategy: ${strategyId}`)
  }
  
  return (
    <div className="space-y-6">
      <StrategyOverview strategies={strategies} />
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {strategies.map(strategy => (
          <StrategyCard
            key={strategy.id}
            strategy={strategy}
            onToggle={handleToggleStrategy}
            onGenerateSignal={handleGenerateSignal}
          />
        ))}
      </div>
      
      {signalCount > 0 && (
        <div className="fixed bottom-4 right-4 bg-green-500 text-white px-4 py-2 rounded-lg shadow-lg animate-pulse">
          {signalCount} signals generated in this session
        </div>
      )}
    </div>
  )
}
