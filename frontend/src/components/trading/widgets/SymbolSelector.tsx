import React, { useState, useMemo } from 'react'
import { Search, Star, TrendingUp, TrendingDown, Volume2 } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { useMarketData, useTradingStore } from '@/store'
import { formatCurrency, formatPercentage, formatLargeNumber, cn } from '@/lib/utils'

interface SymbolSelectorProps {
  onSymbolSelect?: (symbol: string) => void
  showFavorites?: boolean
  showVolume?: boolean
  showPriceChange?: boolean
}

export const SymbolSelector: React.FC<SymbolSelectorProps> = ({
  onSymbolSelect,
  showFavorites = true,
  showVolume = true,
  showPriceChange = true,
}) => {
  const [searchQuery, setSearchQuery] = useState('')
  const [favorites, setFavorites] = useState<string[]>(['BTCUSDT', 'ETHUSDT'])
  const [sortBy, setSortBy] = useState<'symbol' | 'price' | 'change' | 'volume'>('volume')
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc')

  const symbols = useTradingStore((state) => state.symbols)
  const selectedSymbol = useTradingStore((state) => state.selectedSymbol)
  const setSelectedSymbol = useTradingStore((state) => state.setSelectedSymbol)
  const marketData = useMarketData()

  const toggleFavorite = (symbol: string) => {
    setFavorites(prev => 
      prev.includes(symbol) 
        ? prev.filter(s => s !== symbol)
        : [...prev, symbol]
    )
  }

  const filteredAndSortedSymbols = useMemo(() => {
    let filtered = symbols.filter(symbol =>
      symbol.toLowerCase().includes(searchQuery.toLowerCase())
    )

    if (showFavorites && searchQuery === '') {
      const favoriteSymbols = filtered.filter(s => favorites.includes(s))
      const otherSymbols = filtered.filter(s => !favorites.includes(s))
      filtered = [...favoriteSymbols, ...otherSymbols]
    }

    return filtered.sort((a, b) => {
      const aData = marketData[a]
      const bData = marketData[b]

      if (!aData || !bData) return 0

      let aValue: number, bValue: number

      switch (sortBy) {
        case 'symbol':
          return sortOrder === 'asc' ? a.localeCompare(b) : b.localeCompare(a)
        case 'price':
          aValue = aData.price
          bValue = bData.price
          break
        case 'change':
          aValue = aData.changePercent24h
          bValue = bData.changePercent24h
          break
        case 'volume':
          aValue = aData.volume24h
          bValue = bData.volume24h
          break
        default:
          return 0
      }

      return sortOrder === 'asc' ? aValue - bValue : bValue - aValue
    })
  }, [symbols, searchQuery, favorites, showFavorites, sortBy, sortOrder, marketData])

  const handleSymbolClick = (symbol: string) => {
    setSelectedSymbol(symbol)
    onSymbolSelect?.(symbol)
  }

  const handleSort = (field: typeof sortBy) => {
    if (sortBy === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')
    } else {
      setSortBy(field)
      setSortOrder('desc')
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <span>Market</span>
          <div className="flex items-center space-x-2">
            {showFavorites && (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setSearchQuery('')}
              >
                <Star className="w-4 h-4" />
              </Button>
            )}
          </div>
        </CardTitle>
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <Input
            placeholder="Search symbols..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10"
          />
        </div>
      </CardHeader>
      <CardContent className="p-0">
        {/* Header */}
        <div className="grid grid-cols-12 gap-2 p-3 border-b bg-muted/50 text-xs font-medium text-muted-foreground">
          <div className="col-span-1"></div>
          <button 
            className="col-span-3 text-left hover:text-foreground"
            onClick={() => handleSort('symbol')}
          >
            Symbol {sortBy === 'symbol' && (sortOrder === 'asc' ? '↑' : '↓')}
          </button>
          <button 
            className="col-span-3 text-right hover:text-foreground"
            onClick={() => handleSort('price')}
          >
            Price {sortBy === 'price' && (sortOrder === 'asc' ? '↑' : '↓')}
          </button>
          {showPriceChange && (
            <button 
              className="col-span-2 text-right hover:text-foreground"
              onClick={() => handleSort('change')}
            >
              24h% {sortBy === 'change' && (sortOrder === 'asc' ? '↑' : '↓')}
            </button>
          )}
          {showVolume && (
            <button 
              className="col-span-3 text-right hover:text-foreground"
              onClick={() => handleSort('volume')}
            >
              Volume {sortBy === 'volume' && (sortOrder === 'asc' ? '↑' : '↓')}
            </button>
          )}
        </div>

        {/* Symbol List */}
        <div className="max-h-96 overflow-y-auto">
          {filteredAndSortedSymbols.map((symbol) => {
            const data = marketData[symbol]
            const isFavorite = favorites.includes(symbol)
            const isSelected = selectedSymbol === symbol

            return (
              <div
                key={symbol}
                className={cn(
                  'grid grid-cols-12 gap-2 p-3 border-b border-border/50 hover:bg-muted/50 cursor-pointer transition-colors',
                  isSelected && 'bg-primary/10 border-primary/20'
                )}
                onClick={() => handleSymbolClick(symbol)}
              >
                <div className="col-span-1 flex items-center">
                  <button
                    onClick={(e) => {
                      e.stopPropagation()
                      toggleFavorite(symbol)
                    }}
                    className={cn(
                      'text-muted-foreground hover:text-foreground transition-colors',
                      isFavorite && 'text-yellow-500'
                    )}
                  >
                    <Star className={cn('w-3 h-3', isFavorite && 'fill-current')} />
                  </button>
                </div>
                
                <div className="col-span-3 flex items-center">
                  <span className="text-sm font-medium">{symbol}</span>
                </div>

                <div className="col-span-3 flex items-center justify-end">
                  {data ? (
                    <span className="text-sm font-mono">
                      {formatCurrency(data.price)}
                    </span>
                  ) : (
                    <div className="w-16 h-4 bg-muted animate-pulse rounded" />
                  )}
                </div>

                {showPriceChange && (
                  <div className="col-span-2 flex items-center justify-end">
                    {data ? (
                      <span className={cn('text-sm font-mono flex items-center', {
                        'text-trading-green': data.changePercent24h > 0,
                        'text-trading-red': data.changePercent24h < 0,
                        'text-muted-foreground': data.changePercent24h === 0,
                      })}>
                        {data.changePercent24h > 0 ? (
                          <TrendingUp className="w-3 h-3 mr-1" />
                        ) : data.changePercent24h < 0 ? (
                          <TrendingDown className="w-3 h-3 mr-1" />
                        ) : null}
                        {formatPercentage(data.changePercent24h)}
                      </span>
                    ) : (
                      <div className="w-12 h-4 bg-muted animate-pulse rounded" />
                    )}
                  </div>
                )}

                {showVolume && (
                  <div className="col-span-3 flex items-center justify-end">
                    {data ? (
                      <span className="text-xs text-muted-foreground flex items-center">
                        <Volume2 className="w-3 h-3 mr-1" />
                        {formatLargeNumber(data.volume24h)}
                      </span>
                    ) : (
                      <div className="w-16 h-4 bg-muted animate-pulse rounded" />
                    )}
                  </div>
                )}
              </div>
            )
          })}
        </div>

        {filteredAndSortedSymbols.length === 0 && (
          <div className="p-8 text-center text-muted-foreground">
            <Search className="w-8 h-8 mx-auto mb-2 opacity-50" />
            <p className="text-sm">No symbols found</p>
          </div>
        )}
      </CardContent>
    </Card>
  )
}

export default SymbolSelector
