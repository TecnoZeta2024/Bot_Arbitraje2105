import { useEffect, useRef, useCallback } from 'react'
import { useTradingStore } from '@/store'
import type {
  WebSocketMessage,
  MarketDataMessage,
  TradingSignalMessage,
  PositionUpdateMessage,
  TradeExecutedMessage,
} from '@/types'

interface UseWebSocketOptions {
  url?: string
  reconnectInterval?: number
  maxReconnectAttempts?: number
  onConnect?: () => void
  onDisconnect?: () => void
  onError?: (error: Event) => void
}

export function useWebSocket({
  url = 'ws://localhost:8000/ws',
  reconnectInterval = 3000,
  maxReconnectAttempts = 10,
  onConnect,
  onDisconnect,
  onError,
}: UseWebSocketOptions = {}) {
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>()
  const reconnectAttemptsRef = useRef(0)
  const isManualCloseRef = useRef(false)

  const {
    setConnected,
    updateMarketData,
    updateOrderBook,
    addPosition,
    updatePosition,
    addTrade,
    addSignal,
    addNotification,
    updatePortfolio,
  } = useTradingStore()

  const handleMessage = useCallback((event: MessageEvent) => {
    try {
      const message: WebSocketMessage = JSON.parse(event.data)
      
      // Log para debugging
      console.log('WebSocket message received:', message.type, message)
      
      switch (message.type) {
        case 'connection_ack': {
          console.log('✅ Connected to enhanced trading server')
          addNotification({
            type: 'success',
            title: 'Connected',
            message: 'Connected to enhanced trading server with real Binance data',
          })
          break
        }
        
        case 'market_data': {
          const { data } = message as MarketDataMessage
          updateMarketData({
            symbol: data.symbol,
            price: data.price,
            volume24h: data.volume24h,
            changePercent24h: data.changePercent24h,
            high24h: data.high24h || data.price,
            low24h: data.low24h || data.price,
            change24h: (data.changePercent24h / 100) * data.price,
            timestamp: data.timestamp
          })
          break
        }
        
        case 'trading_signal': {
          const { data } = message as TradingSignalMessage
          addSignal({
            id: data.id,
            symbol: data.symbol,
            action: data.action as 'BUY' | 'SELL',
            price: data.price,
            quantity: 0.001, // Default quantity
            confidence: data.confidence,
            strategy: data.strategy,
            riskLevel: 'MEDIUM' as const,
            timestamp: data.timestamp
          })
          
          addNotification({
            type: 'info',
            title: 'New Trading Signal',
            message: `${data.action} ${data.symbol} at $${data.price.toFixed(2)} (${data.confidence}% confidence)`,
          })
          break
        }
        
        case 'position_update': {
          const { data } = message as PositionUpdateMessage
          updatePosition(data.id, {
            id: data.id,
            symbol: data.symbol,
            side: data.side as 'LONG' | 'SHORT',
            entryPrice: data.entryPrice,
            currentPrice: data.currentPrice,
            quantity: data.quantity,
            unrealizedPnL: data.unrealizedPnL,
            unrealizedPnLPercent: data.unrealizedPnLPercent,
            realizedPnL: 0,
            timestamp: data.timestamp
          })
          break
        }
        
        case 'trade_executed': {
          const { data } = message as TradeExecutedMessage
          addTrade({
            id: data.id,
            symbol: data.symbol,
            side: data.side as 'BUY' | 'SELL',
            price: data.price,
            quantity: data.quantity,
            fee: data.price * data.quantity * 0.001, // 0.1% fee
            pnl: data.pnl,
            pnlPercent: (data.pnl / (data.price * data.quantity)) * 100,
            timestamp: data.timestamp,
            strategy: data.strategy
          })
          
          addNotification({
            type: data.pnl >= 0 ? 'success' : 'error',
            title: 'Trade Executed',
            message: `${data.side} ${data.quantity} ${data.symbol} at $${data.price} (P&L: ${data.pnl >= 0 ? '+' : ''}$${data.pnl.toFixed(2)})`,
          })
          break
        }
        
        case 'portfolio_update': {
          const portfolioData = message.data as any
          updatePortfolio({
            totalValue: portfolioData.totalValue,
            totalPnL: portfolioData.totalPnL,
            totalPnLPercent: portfolioData.totalPnLPercent,
            availableBalance: portfolioData.availableBalance,
            dailyPnL: portfolioData.dailyPnL,
            positions: portfolioData.positions || []
          })
          break
        }
        
        case 'trading_status': {
          const statusData = message.data as any
          const isActive = statusData.status === 'ACTIVE'
          addNotification({
            type: isActive ? 'success' : 'warning',
            title: 'Trading Status',
            message: statusData.message,
          })
          break
        }
        
        case 'orderbook_update': {
          const orderbookData = message.data as any
          updateOrderBook({
            symbol: orderbookData.symbol,
            bids: orderbookData.bids.map((bid: number[]) => ({
              price: bid[0],
              quantity: bid[1],
              total: bid[0] * bid[1]
            })),
            asks: orderbookData.asks.map((ask: number[]) => ({
              price: ask[0],
              quantity: ask[1],
              total: ask[0] * ask[1]
            })),
            timestamp: orderbookData.timestamp
          })
          break
        }
        
        case 'kline_data': {
          // Handle candlestick data for charts
          const klineData = message.data as any
          console.log('📊 Kline data received:', klineData.symbol, klineData.close)
          break
        }
        
        case 'system_metrics': {
          // Handle system metrics
          const metricsData = message.data as any
          console.log('📈 System metrics:', metricsData)
          break
        }
        
        case 'error': {
          console.error('WebSocket error message:', message.data)
          addNotification({
            type: 'error',
            title: 'Trading Error',
            message: message.data as string,
          })
          break
        }
        
        default:
          console.warn('Unknown message type:', message.type)
      }
    } catch (error) {
      console.error('Failed to parse WebSocket message:', error)
      addNotification({
        type: 'error',
        title: 'Connection Error',
        message: 'Failed to parse server message',
      })
    }
  }, [updateMarketData, updateOrderBook, addPosition, updatePosition, addTrade, addSignal, addNotification, updatePortfolio])

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return
    }

    try {
      wsRef.current = new WebSocket(url)

      wsRef.current.onopen = () => {
        console.log('🔗 WebSocket connected to enhanced server')
        setConnected(true)
        reconnectAttemptsRef.current = 0
        onConnect?.()
        
        // Subscribe to trading data
        wsRef.current?.send(JSON.stringify({
          type: 'subscribe',
          channels: ['market_data', 'trading_signals', 'positions', 'trades', 'portfolio']
        }))
      }

      wsRef.current.onmessage = handleMessage

      wsRef.current.onclose = (event) => {
        console.log('🔌 WebSocket disconnected:', event.code, event.reason)
        setConnected(false)
        onDisconnect?.()

        if (!isManualCloseRef.current && reconnectAttemptsRef.current < maxReconnectAttempts) {
          reconnectTimeoutRef.current = setTimeout(() => {
            console.log(`🔄 Reconnecting... (attempt ${reconnectAttemptsRef.current + 1}/${maxReconnectAttempts})`)
            reconnectAttemptsRef.current++
            connect()
          }, reconnectInterval)
        }
      }

      wsRef.current.onerror = (error) => {
        console.error('❌ WebSocket error:', error)
        onError?.(error)
        addNotification({
          type: 'error',
          title: 'Connection Error',
          message: 'Failed to connect to trading server',
        })
      }
    } catch (error) {
      console.error('Failed to create WebSocket connection:', error)
      addNotification({
        type: 'error',
        title: 'Connection Error',
        message: 'Failed to create WebSocket connection',
      })
    }
  }, [url, setConnected, onConnect, onDisconnect, onError, handleMessage, maxReconnectAttempts, reconnectInterval, addNotification])

  const disconnect = useCallback(() => {
    isManualCloseRef.current = true
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
    }
    if (wsRef.current) {
      wsRef.current.close(1000, 'Manual disconnect')
      wsRef.current = null
    }
    setConnected(false)
  }, [setConnected])

  const sendMessage = useCallback((message: object) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message))
    } else {
      console.warn('⚠️ WebSocket is not connected')
      addNotification({
        type: 'warning',
        title: 'Connection Issue',
        message: 'Not connected to trading server',
      })
    }
  }, [addNotification])

  const subscribeToSymbol = useCallback((symbol: string) => {
    sendMessage({
      type: 'subscribe_symbol',
      symbol,
    })
  }, [sendMessage])

  const unsubscribeFromSymbol = useCallback((symbol: string) => {
    sendMessage({
      type: 'unsubscribe_symbol',
      symbol,
    })
  }, [sendMessage])

  const executeOrder = useCallback((order: {
    symbol: string
    side: 'BUY' | 'SELL'
    quantity: number
    price?: number
    type?: 'MARKET' | 'LIMIT'
  }) => {
    sendMessage({
      type: 'execute_order',
      ...order,
    })
  }, [sendMessage])

  const controlTrading = useCallback((action: 'start' | 'pause' | 'stop') => {
    sendMessage({
      type: 'trading_control',
      action,
    })
  }, [sendMessage])

  const updateTradingConfig = useCallback((config: object) => {
    sendMessage({
      type: 'update_config',
      config,
    })
  }, [sendMessage])

  useEffect(() => {
    connect()

    return () => {
      disconnect()
    }
  }, [connect, disconnect])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current)
      }
    }
  }, [])

  return {
    connect,
    disconnect,
    sendMessage,
    subscribeToSymbol,
    unsubscribeFromSymbol,
    executeOrder,
    controlTrading,
    updateTradingConfig,
    isConnected: wsRef.current?.readyState === WebSocket.OPEN,
  }
}

// Hook for easier order execution
export function useOrderExecution() {
  const { executeOrder } = useWebSocket()
  const { addNotification } = useTradingStore()

  const placeBuyOrder = useCallback(
    (symbol: string, quantity: number, price?: number) => {
      executeOrder({
        symbol,
        side: 'BUY',
        quantity,
        price,
        type: price ? 'LIMIT' : 'MARKET',
      })
      
      addNotification({
        type: 'info',
        title: 'Order Placed',
        message: `BUY ${quantity} ${symbol}${price ? ` at $${price}` : ' (Market)'}`,
      })
    },
    [executeOrder, addNotification]
  )

  const placeSellOrder = useCallback(
    (symbol: string, quantity: number, price?: number) => {
      executeOrder({
        symbol,
        side: 'SELL',
        quantity,
        price,
        type: price ? 'LIMIT' : 'MARKET',
      })
      
      addNotification({
        type: 'info',
        title: 'Order Placed',
        message: `SELL ${quantity} ${symbol}${price ? ` at $${price}` : ' (Market)'}`,
      })
    },
    [executeOrder, addNotification]
  )

  return {
    placeBuyOrder,
    placeSellOrder,
    executeOrder,
  }
}

// Hook for trading controls
export function useTradingControls() {
  const { controlTrading } = useWebSocket()
  const { addNotification } = useTradingStore()

  const startTrading = useCallback(() => {
    controlTrading('start')
    addNotification({
      type: 'success',
      title: 'Trading Started',
      message: 'AI-powered trading system is now active',
    })
  }, [controlTrading, addNotification])

  const pauseTrading = useCallback(() => {
    controlTrading('pause')
    addNotification({
      type: 'warning',
      title: 'Trading Paused',
      message: 'Trading system has been paused',
    })
  }, [controlTrading, addNotification])

  const stopTrading = useCallback(() => {
    controlTrading('stop')
    addNotification({
      type: 'info',
      title: 'Trading Stopped',
      message: 'Trading system has been stopped',
    })
  }, [controlTrading, addNotification])

  return {
    startTrading,
    pauseTrading,
    stopTrading,
    controlTrading,
  }
}

// Hook for symbol subscription management
export function useSymbolSubscription() {
  const { subscribeToSymbol, unsubscribeFromSymbol } = useWebSocket()
  const selectedSymbol = useTradingStore((state) => state.selectedSymbol)
  const symbols = useTradingStore((state) => state.symbols)

  useEffect(() => {
    // Subscribe to selected symbol
    if (selectedSymbol) {
      subscribeToSymbol(selectedSymbol)
    }

    // Subscribe to all symbols for basic data
    symbols.forEach(symbol => {
      subscribeToSymbol(symbol)
    })

    return () => {
      // Cleanup subscriptions
      if (selectedSymbol) {
        unsubscribeFromSymbol(selectedSymbol)
      }
      symbols.forEach(symbol => {
        unsubscribeFromSymbol(symbol)
      })
    }
  }, [selectedSymbol, symbols, subscribeToSymbol, unsubscribeFromSymbol])

  return {
    subscribeToSymbol,
    unsubscribeFromSymbol,
  }
}
