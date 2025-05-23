import React, { useState, useEffect } from 'react'
import { 
  Brain, 
  TrendingUp, 
  TrendingDown, 
  BarChart3, 
  Activity,
  AlertTriangle,
  Zap,
  Target,
  Shield,
  ChevronRight
} from 'lucide-react'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'
import { aiStrategyEngine } from '@/lib/AIStrategyEngine'
import { MarketSentiment, PatternDetection } from '@/types/strategy.types'

// Market Sentiment Component
const MarketSentimentCard = ({ sentiment }: { sentiment: MarketSentiment }) => {
  const getSentimentColor = (score: number) => {
    if (score > 20) return 'text-green-600'
    if (score < -20) return 'text-red-600'
    return 'text-yellow-600'
  }
  
  const getSentimentIcon = (sentiment: string) => {
    if (sentiment === 'BULLISH') return <TrendingUp className="w-6 h-6" />
    if (sentiment === 'BEARISH') return <TrendingDown className="w-6 h-6" />
    return <Activity className="w-6 h-6" />
  }
  
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <span className="flex items-center">
            <Brain className="w-5 h-5 mr-2 text-purple-500" />
            Market Sentiment Analysis
          </span>
          <span className={cn('flex items-center text-lg font-bold', getSentimentColor(sentiment.score))}>
            {getSentimentIcon(sentiment.overall)}
            {sentiment.overall}
          </span>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {/* Overall Score */}
          <div className="relative">
            <div className="flex justify-between text-sm mb-1">
              <span>Overall Score</span>
              <span className={cn('font-bold', getSentimentColor(sentiment.score))}>
                {sentiment.score > 0 ? '+' : ''}{sentiment.score}
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
              <div 
                className={cn('h-full transition-all duration-500', {
                  'bg-green-500': sentiment.score > 20,
                  'bg-red-500': sentiment.score < -20,
                  'bg-yellow-500': sentiment.score >= -20 && sentiment.score <= 20
                })}
                style={{ 
                  width: `${Math.abs(sentiment.score)}%`,
                  marginLeft: sentiment.score < 0 ? `${50 - Math.abs(sentiment.score) / 2}%` : '50%'
                }}
              />
            </div>
            <div className="flex justify-between text-xs text-gray-500 mt-1">
              <span>Extreme Fear</span>
              <span>Neutral</span>
              <span>Extreme Greed</span>
            </div>
          </div>
          
          {/* Components */}
          <div className="grid grid-cols-2 gap-3">
            <div className="bg-gray-50 p-3 rounded-lg">
              <p className="text-xs text-gray-600">Technical</p>
              <p className={cn('text-lg font-bold', getSentimentColor(sentiment.components.technical))}>
                {sentiment.components.technical > 0 ? '+' : ''}{sentiment.components.technical}
              </p>
            </div>
            <div className="bg-gray-50 p-3 rounded-lg">
              <p className="text-xs text-gray-600">Fundamental</p>
              <p className={cn('text-lg font-bold', getSentimentColor(sentiment.components.fundamental))}>
                {sentiment.components.fundamental > 0 ? '+' : ''}{sentiment.components.fundamental}
              </p>
            </div>
            <div className="bg-gray-50 p-3 rounded-lg">
              <p className="text-xs text-gray-600">Social</p>
              <p className={cn('text-lg font-bold', getSentimentColor(sentiment.components.social))}>
                {sentiment.components.social > 0 ? '+' : ''}{sentiment.components.social}
              </p>
            </div>
            <div className="bg-gray-50 p-3 rounded-lg">
              <p className="text-xs text-gray-600">On-Chain</p>
              <p className={cn('text-lg font-bold', getSentimentColor(sentiment.components.onChain))}>
                {sentiment.components.onChain > 0 ? '+' : ''}{sentiment.components.onChain}
              </p>
            </div>
          </div>
          
          {/* Additional Signals */}
          <div className="border-t pt-3 space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-gray-600">Fear & Greed Index</span>
              <span className="font-medium">{sentiment.signals.fearGreedIndex}/100</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-gray-600">Volume Analysis</span>
              <span className={cn('font-medium', {
                'text-green-600': sentiment.signals.volumeAnalysis === 'Increasing',
                'text-red-600': sentiment.signals.volumeAnalysis === 'Decreasing'
              })}>
                {sentiment.signals.volumeAnalysis}
              </span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-gray-600">Trend Strength</span>
              <span className="font-medium">{sentiment.signals.trendStrength}%</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-gray-600">Market Volatility</span>
              <span className={cn('font-medium', {
                'text-green-600': sentiment.signals.volatility === 'LOW',
                'text-yellow-600': sentiment.signals.volatility === 'MEDIUM',
                'text-red-600': sentiment.signals.volatility === 'HIGH'
              })}>
                {sentiment.signals.volatility}
              </span>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

// Pattern Detection Component
const PatternDetectionCard = ({ patterns }: { patterns: PatternDetection[] }) => {
  const formatPrice = (price: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(price)
  }
  
  const getTimeAgo = (timestamp: number) => {
    const seconds = Math.floor((Date.now() - timestamp) / 1000)
    if (seconds < 60) return `${seconds}s ago`
    const minutes = Math.floor(seconds / 60)
    if (minutes < 60) return `${minutes}m ago`
    const hours = Math.floor(minutes / 60)
    return `${hours}h ago`
  }
  
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <span className="flex items-center">
            <Target className="w-5 h-5 mr-2 text-blue-500" />
            Pattern Recognition
          </span>
          <span className="text-sm font-normal text-muted-foreground">
            {patterns.length} patterns
          </span>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {patterns.length === 0 ? (
            <div className="text-center py-8">
              <Target className="w-12 h-12 text-gray-300 mx-auto mb-3" />
              <p className="text-muted-foreground text-sm">
                No patterns detected. AI is continuously scanning...
              </p>
            </div>
          ) : (
            patterns.slice(0, 5).map((pattern) => (
              <div 
                key={pattern.id} 
                className="p-3 bg-muted/50 rounded-lg border-l-4 border-l-blue-500 hover:bg-muted/70 transition-colors"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-2 mb-1">
                      <span className="font-semibold text-sm">{pattern.pattern}</span>
                      <span className={cn('px-2 py-0.5 rounded text-xs font-medium', {
                        'bg-green-100 text-green-800': pattern.direction === 'BULLISH',
                        'bg-red-100 text-red-800': pattern.direction === 'BEARISH'
                      })}>
                        {pattern.direction}
                      </span>
                    </div>
                    <div className="flex items-center space-x-4 text-xs text-muted-foreground">
                      <span>{pattern.symbol}</span>
                      <span>{pattern.timeframe}</span>
                      <span>{getTimeAgo(pattern.detectedAt)}</span>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-medium">
                      {Math.round(pattern.confidence)}% confidence
                    </p>
                  </div>
                </div>
                <div className="mt-2 grid grid-cols-3 gap-2 text-xs">
                  <div>
                    <span className="text-gray-600">Target:</span>
                    <p className="font-medium text-green-600">{formatPrice(pattern.targetPrice)}</p>
                  </div>
                  <div>
                    <span className="text-gray-600">Stop Loss:</span>
                    <p className="font-medium text-red-600">{formatPrice(pattern.stopLoss)}</p>
                  </div>
                  <div>
                    <span className="text-gray-600">R:R Ratio:</span>
                    <p className="font-medium">
                      1:{Math.round(Math.abs(pattern.targetPrice - pattern.stopLoss) / Math.abs(pattern.stopLoss - pattern.targetPrice) * 10) / 10}
                    </p>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
        {patterns.length > 5 && (
          <Button variant="ghost" className="w-full mt-3" size="sm">
            View All Patterns
            <ChevronRight className="w-4 h-4 ml-1" />
          </Button>
        )}
      </CardContent>
    </Card>
  )
}

// AI Insights Component
const AIInsights = () => {
  const insights = [
    {
      type: 'bullish',
      title: 'Strong Uptrend Detected',
      description: 'BTC showing strong momentum with 85% probability of continuation',
      confidence: 85,
      action: 'Consider long positions with tight stops'
    },
    {
      type: 'warning',
      title: 'Increased Volatility Expected',
      description: 'Major economic data release in 2 hours may cause market swings',
      confidence: 92,
      action: 'Reduce position sizes or hedge existing positions'
    },
    {
      type: 'bearish',
      title: 'Resistance Level Approaching',
      description: 'ETH approaching major resistance at $3,250 with weakening momentum',
      confidence: 78,
      action: 'Consider taking profits or tightening stops'
    }
  ]
  
  const getInsightIcon = (type: string) => {
    if (type === 'bullish') return <TrendingUp className="w-5 h-5 text-green-500" />
    if (type === 'bearish') return <TrendingDown className="w-5 h-5 text-red-500" />
    return <AlertTriangle className="w-5 h-5 text-yellow-500" />
  }
  
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center">
          <Zap className="w-5 h-5 mr-2 text-yellow-500" />
          AI-Powered Insights
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {insights.map((insight, index) => (
            <div 
              key={index}
              className={cn('p-3 rounded-lg border', {
                'bg-green-50 border-green-200': insight.type === 'bullish',
                'bg-red-50 border-red-200': insight.type === 'bearish',
                'bg-yellow-50 border-yellow-200': insight.type === 'warning'
              })}
            >
              <div className="flex items-start space-x-3">
                {getInsightIcon(insight.type)}
                <div className="flex-1">
                  <h4 className="font-semibold text-sm mb-1">{insight.title}</h4>
                  <p className="text-xs text-gray-600 mb-2">{insight.description}</p>
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-gray-500">
                      Confidence: {insight.confidence}%
                    </span>
                    <span className="text-xs font-medium text-gray-700">
                      {insight.action}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}

// Main AI Analysis Component
export default function AIAnalysis() {
  const [sentiment, setSentiment] = useState<MarketSentiment>(aiStrategyEngine.getMarketSentiment())
  const [patterns, setPatterns] = useState<PatternDetection[]>([])
  const [isScanning, setIsScanning] = useState(false)
  
  useEffect(() => {
    // Update sentiment every 30 seconds
    const sentimentInterval = setInterval(() => {
      setSentiment(aiStrategyEngine.getMarketSentiment())
    }, 30000)
    
    // Scan for patterns every 20 seconds
    const patternInterval = setInterval(() => {
      setIsScanning(true)
      setTimeout(() => {
        const symbols = ['BTCUSDT', 'ETHUSDT', 'ADAUSDT', 'DOTUSDT']
        symbols.forEach(symbol => {
          aiStrategyEngine.detectPatterns(symbol)
        })
        setPatterns(aiStrategyEngine.getRecentPatterns())
        setIsScanning(false)
      }, 1000)
    }, 20000)
    
    // Initial pattern scan
    const symbols = ['BTCUSDT', 'ETHUSDT', 'ADAUSDT', 'DOTUSDT']
    symbols.forEach(symbol => {
      aiStrategyEngine.detectPatterns(symbol)
    })
    setPatterns(aiStrategyEngine.getRecentPatterns())
    
    return () => {
      clearInterval(sentimentInterval)
      clearInterval(patternInterval)
    }
  }, [])
  
  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <div className="space-y-6">
        <MarketSentimentCard sentiment={sentiment} />
        <AIInsights />
      </div>
      <div className="space-y-6">
        <PatternDetectionCard patterns={patterns} />
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <Shield className="w-5 h-5 mr-2 text-green-500" />
              Risk Analysis
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                <span className="text-sm">Portfolio Risk Level</span>
                <span className="text-sm font-bold text-yellow-600">MEDIUM</span>
              </div>
              <div className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                <span className="text-sm">Max Drawdown Protection</span>
                <span className="text-sm font-bold text-green-600">ACTIVE</span>
              </div>
              <div className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                <span className="text-sm">Correlation Risk</span>
                <span className="text-sm font-bold text-blue-600">LOW</span>
              </div>
              <div className="text-xs text-muted-foreground bg-blue-50 p-3 rounded">
                💡 AI continuously monitors risk factors and adjusts strategy parameters
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
