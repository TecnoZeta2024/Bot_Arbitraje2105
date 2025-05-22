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
  } = useTradingStore()

  const handleMessage = useCallback((event: MessageEvent) => {
    try {
      const message: WebSocketMessage = JSON.parse(event.data)
      
      switch (message.type) {
        case 'market_data': {
          const { data } = message as MarketDataMessage
          updateMarketData(data)
          break
        }
        
        case 'trading_signal': {
          const { data } = message as TradingSignalMessage
          addSignal(data)
          addNotification({
            type: 'info',
            title: 'New Trading Signal',
            message: `${data.action} ${data.symbol} at ${data.price} (${data.strategy})`,
          })
          break
        }
        
        case 'position_update': {
          const { data } = message as PositionUpdateMessage
          updatePosition(data.id, data)
          break
        }
        
        case 'trade_executed': {
          const { data } = message as TradeExecutedMessage
          addTrade(data)
          addNotification({
            type: data.pnl >= 0 ? 'success' : 'error',
            title: 'Trade Executed',
            message: `${data.side} ${data.quantity} ${data.symbol} at ${data.price}`,
          })
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
  }, [updateMarketData, updateOrderBook, addPosition, updatePosition, addTrade, addSignal, addNotification])

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return
    }

    try {
      wsRef.current = new WebSocket(url)

      wsRef.current.onopen = () => {
        console.log('WebSocket connected')
        setConnected(true)
        reconnectAttemptsRef.current = 0
        onConnect?.()
        
        // Subscribe to trading data
        wsRef.current?.send(JSON.stringify({
          type: 'subscribe',
          channels: ['market_data', 'trading_signals', 'positions', 'trades']
        }))
      }

      wsRef.current.onmessage = handleMessage

      wsRef.current.onclose = (event) => {
        console.log('WebSocket disconnected:', event.code, event.reason)
        setConnected(false)
        onDisconnect?.()

        if (!isManualCloseRef.current && reconnectAttemptsRef.current < maxReconnectAttempts) {
          reconnectTimeoutRef.current = setTimeout(() => {
            console.log(`Reconnecting... (attempt ${reconnectAttemptsRef.current + 1}/${maxReconnectAttempts})`)
            reconnectAttemptsRef.current++
            connect()
          }, reconnectInterval)
        }
      }

      wsRef.current.onerror = (error) => {
        console.error('WebSocket error:', error)
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
      console.warn('WebSocket is not connected')
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
        message: `BUY ${quantity} ${symbol}${price ? ` at ${price}` : ' (Market)'}`,
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
        message: `SELL ${quantity} ${symbol}${price ? ` at ${price}` : ' (Market)'}`,
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
