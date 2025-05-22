import React, { useState, useMemo } from 'react'
import { TrendingUp, TrendingDown, BarChart3, Layers } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { useOrderBook, useTradingStore } from '@/store'
import { formatCurrency, formatNumber, cn } from '@/lib/utils'

interface OrderBookProps {
  symbol?: string
  depth?: number
  showSpread?: boolean
  showChart?: boolean
  onOrderClick?: (price: number, quantity: number, side: 'buy' | 'sell') => void
}

export const OrderBook: React.FC<OrderBookProps> = ({
  symbol,
  depth = 20,
  showSpread = true,
  showChart = false,
  onOrderClick,
}) => {
  const [view, setView] = useState<'full' | 'bids' | 'asks'>('full')
  const [precision, setPrecision] = useState(2)
  
  const selectedSymbol = useTradingStore((state) => state.selectedSymbol)
  const currentSymbol = symbol || selectedSymbol
  const orderBook = useOrderBook(currentSymbol)

  const processedData = useMemo(() => {
    if (!orderBook) return null

    const bids = orderBook.bids.slice(0, depth)
    const asks = orderBook.asks.slice(0, depth)

    // Calculate cumulative volumes
    let bidCumulative = 0
    let askCumulative = 0

    const processedBids = bids.map((bid) => {
      bidCumulative += bid.quantity
      return {
        ...bid,
        cumulative: bidCumulative,
      }
    })

    const processedAsks = asks.map((ask) => {
      askCumulative += ask.quantity
      return {
        ...ask,
        cumulative: askCumulative,
      }
    }).reverse() // Reverse asks for display

    const maxBidVolume = Math.max(...processedBids.map(b => b.cumulative), 0)
    const maxAskVolume = Math.max(...processedAsks.map(a => a.cumulative), 0)
    const maxVolume = Math.max(maxBidVolume, maxAskVolume)

    // Calculate spread
    const bestBid = bids[0]?.price || 0
    const bestAsk = asks[0]?.price || 0
    const spread = bestAsk - bestBid
    const spreadPercent = bestBid > 0 ? (spread / bestBid) * 100 : 0

    return {
      bids: processedBids,
      asks: processedAsks,
      maxVolume,
      spread,
      spreadPercent,
      bestBid,
      bestAsk,
    }
  }, [orderBook, depth])

  if (!processedData) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <Layers className="w-5 h-5 mr-2 text-blue-500" />
            Order Book
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {Array.from({ length: 10 }).map((_, i) => (
              <div key={i} className="grid grid-cols-3 gap-2">
                <div className="h-4 bg-muted animate-pulse rounded" />
                <div className="h-4 bg-muted animate-pulse rounded" />
                <div className="h-4 bg-muted animate-pulse rounded" />
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    )
  }

  const handleOrderClick = (price: number, quantity: number, side: 'buy' | 'sell') => {
    onOrderClick?.(price, quantity, side)
  }

  const OrderRow = ({ 
    order, 
    maxVolume, 
    side, 
    showBackground = true 
  }: { 
    order: any
    maxVolume: number
    side: 'buy' | 'sell'
    showBackground?: boolean
  }) => {
    const volumePercent = maxVolume > 0 ? (order.cumulative / maxVolume) * 100 : 0
    
    return (
      <div
        className={cn(
          'relative grid grid-cols-3 gap-2 p-1 text-sm font-mono hover:bg-muted/50 cursor-pointer transition-colors',
          'border-b border-border/30'
        )}
        onClick={() => handleOrderClick(order.price, order.quantity, side)}
      >
        {showBackground && (
          <div
            className={cn(
              'absolute inset-0 opacity-10',
              side === 'buy' ? 'bg-trading-green' : 'bg-trading-red'
            )}
            style={{ 
              width: `${volumePercent}%`,
              [side === 'buy' ? 'left' : 'right']: 0 
            }}
          />
        )}
        
        <div className={cn(
          'text-right z-10 relative',
          side === 'buy' ? 'text-trading-green' : 'text-trading-red'
        )}>
          {formatCurrency(order.price)}
        </div>
        
        <div className="text-right text-muted-foreground z-10 relative">
          {formatNumber(order.quantity, 4)}
        </div>
        
        <div className="text-right text-muted-foreground text-xs z-10 relative">
          {formatNumber(order.cumulative, 2)}
        </div>
      </div>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <div className="flex items-center">
            <Layers className="w-5 h-5 mr-2 text-blue-500" />
            Order Book
            <span className="ml-2 text-sm font-normal text-muted-foreground">
              {currentSymbol}
            </span>
          </div>
          
          <div className="flex items-center space-x-1">
            {/* View Toggle */}
            <div className="flex items-center bg-muted p-0.5 rounded">
              <button
                onClick={() => setView('bids')}
                className={cn(
                  'px-2 py-1 text-xs rounded transition-colors',
                  view === 'bids' ? 'bg-trading-green text-white' : 'text-muted-foreground'
                )}
              >
                <TrendingUp className="w-3 h-3" />
              </button>
              <button
                onClick={() => setView('full')}
                className={cn(
                  'px-2 py-1 text-xs rounded transition-colors',
                  view === 'full' ? 'bg-background text-foreground shadow-sm' : 'text-muted-foreground'
                )}
              >
                <BarChart3 className="w-3 h-3" />
              </button>
              <button
                onClick={() => setView('asks')}
                className={cn(
                  'px-2 py-1 text-xs rounded transition-colors',
                  view === 'asks' ? 'bg-trading-red text-white' : 'text-muted-foreground'
                )}
              >
                <TrendingDown className="w-3 h-3" />
              </button>
            </div>

            {/* Precision Controls */}
            <select
              value={precision}
              onChange={(e) => setPrecision(Number(e.target.value))}
              className="text-xs bg-background border border-border rounded px-1 py-0.5"
            >
              <option value={0}>1</option>
              <option value={1}>0.1</option>
              <option value={2}>0.01</option>
              <option value={3}>0.001</option>
              <option value={4}>0.0001</option>
            </select>
          </div>
        </CardTitle>
      </CardHeader>

      <CardContent className="p-0">
        {/* Header */}
        <div className="grid grid-cols-3 gap-2 p-3 border-b bg-muted/50 text-xs font-medium text-muted-foreground">
          <div className="text-right">Price</div>
          <div className="text-right">Size</div>
          <div className="text-right">Total</div>
        </div>

        <div className="max-h-96 overflow-y-auto">
          {/* Asks (Sell Orders) */}
          {(view === 'full' || view === 'asks') && (
            <div className="space-y-0">
              {processedData.asks.map((ask, index) => (
                <OrderRow
                  key={`ask-${ask.price}-${index}`}
                  order={ask}
                  maxVolume={processedData.maxVolume}
                  side="sell"
                />
              ))}
            </div>
          )}

          {/* Spread */}
          {showSpread && view === 'full' && (
            <div className="p-3 bg-muted/30 border-y border-border/50">
              <div className="text-center">
                <div className="text-sm font-semibold">
                  {formatCurrency(processedData.spread)}
                </div>
                <div className="text-xs text-muted-foreground">
                  Spread ({formatNumber(processedData.spreadPercent, 3)}%)
                </div>
              </div>
            </div>
          )}

          {/* Bids (Buy Orders) */}
          {(view === 'full' || view === 'bids') && (
            <div className="space-y-0">
              {processedData.bids.map((bid, index) => (
                <OrderRow
                  key={`bid-${bid.price}-${index}`}
                  order={bid}
                  maxVolume={processedData.maxVolume}
                  side="buy"
                />
              ))}
            </div>
          )}
        </div>

        {/* Quick Actions */}
        <div className="p-3 border-t bg-muted/30">
          <div className="flex justify-between text-xs">
            <div className="flex items-center space-x-4">
              <span className="text-muted-foreground">Best Bid:</span>
              <span className="font-mono text-trading-green">
                {formatCurrency(processedData.bestBid)}
              </span>
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-muted-foreground">Best Ask:</span>
              <span className="font-mono text-trading-red">
                {formatCurrency(processedData.bestAsk)}
              </span>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

export default OrderBook
