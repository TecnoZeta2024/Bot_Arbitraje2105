import React, { useState, useEffect } from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate, Link, useLocation } from 'react-router-dom'
import { 
  BarChart3, 
  Settings, 
  Bot, 
  TrendingUp, 
  Activity, 
  Bell, 
  User,
  Menu,
  X,
  ChevronDown,
  Wifi,
  WifiOff
} from 'lucide-react'

// Import store and hooks
import { useTradingStore } from '@/store'
// TEMPORARILY DISABLED - import { useWebSocket, useSymbolSubscription } from '@/hooks/useWebSocket'

// Import UI components
import { ToastProvider } from '@/components/ui/toast'

// Import pages
import TradingDashboard from '@/components/trading/TradingDashboard'
import ConfigurationDashboard from '@/components/configuration/ConfigurationDashboard'
import BacktestingDashboard from '@/components/backtesting/BacktestingDashboard'
import AnalyticsDashboard from '@/components/analytics/AnalyticsDashboard'

// Navigation component
const Sidebar = ({ isOpen, onClose }: { isOpen: boolean; onClose: () => void }) => {
  const location = useLocation()
  // Set as connected for demo mode
  const isConnected = true // useTradingStore((state) => state.isConnected)

  const navigation = [
    { name: 'Trading Dashboard', href: '/', icon: BarChart3 },
    { name: 'Configuration', href: '/config', icon: Settings },
    { name: 'Backtesting', href: '/backtest', icon: Activity },
    { name: 'Analytics', href: '/analytics', icon: TrendingUp },
  ]

  return (
    <>
      {/* Mobile backdrop */}
      {isOpen && (
        <div className="fixed inset-0 z-40 lg:hidden">
          <div className="fixed inset-0 bg-gray-600 bg-opacity-75" onClick={onClose} />
        </div>
      )}

      {/* Sidebar */}
      <div
        className={`fixed inset-y-0 left-0 z-50 w-64 bg-gray-900 transform transition-transform duration-300 ease-in-out lg:translate-x-0 lg:static lg:inset-0 ${
          isOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <div className="flex flex-col h-full">
          {/* Logo and close button */}
          <div className="flex items-center justify-between h-16 px-4 border-b border-gray-700">
            <div className="flex items-center">
              <Bot className="w-8 h-8 text-blue-400" />
              <span className="ml-2 text-xl font-bold text-white">Bot 2105</span>
            </div>
            <button
              onClick={onClose}
              className="lg:hidden text-gray-400 hover:text-white"
            >
              <X className="w-6 h-6" />
            </button>
          </div>

          {/* Connection status */}
          <div className="px-4 py-3 border-b border-gray-700">
            <div className="flex items-center space-x-2">
              <Wifi className="w-4 h-4 text-green-400" />
              <span className="text-sm text-green-400">Demo Mode</span>
            </div>
          </div>

          {/* Navigation */}
          <nav className="flex-1 px-4 py-4 space-y-2">
            {navigation.map((item) => {
              const isActive = location.pathname === item.href
              return (
                <Link
                  key={item.name}
                  to={item.href}
                  onClick={onClose}
                  className={`flex items-center px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                    isActive
                      ? 'bg-gray-800 text-white'
                      : 'text-gray-300 hover:bg-gray-700 hover:text-white'
                  }`}
                >
                  <item.icon className="w-5 h-5 mr-3" />
                  {item.name}
                </Link>
              )
            })}
          </nav>

          {/* User section */}
          <div className="px-4 py-4 border-t border-gray-700">
            <div className="flex items-center">
              <User className="w-8 h-8 text-gray-400" />
              <div className="ml-3">
                <p className="text-sm font-medium text-white">Demo User</p>
                <p className="text-xs text-gray-400">Trading Platform</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  )
}

// Top bar component
const TopBar = ({ onMenuClick }: { onMenuClick: () => void }) => {
  // Mock portfolio data for demo
  const portfolio = {
    totalValue: 1000.00,
    dailyPnL: 23.45
  }
  
  const notifications = [] // Mock empty notifications
  const unreadCount = 0

  return (
    <div className="bg-white border-b border-gray-200 px-4 py-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center">
          <button
            onClick={onMenuClick}
            className="lg:hidden text-gray-500 hover:text-gray-700"
          >
            <Menu className="w-6 h-6" />
          </button>
          
          <div className="ml-4 lg:ml-0">
            <h1 className="text-xl font-semibold text-gray-900">Trading Dashboard - Demo</h1>
          </div>
        </div>

        <div className="flex items-center space-x-4">
          {/* Quick stats */}
          <div className="hidden md:flex items-center space-x-6">
            <div className="text-center">
              <p className="text-xs text-gray-500">Portfolio</p>
              <p className="text-sm font-semibold">
                ${portfolio.totalValue.toLocaleString()}
              </p>
            </div>
            <div className="text-center">
              <p className="text-xs text-gray-500">Daily P&L</p>
              <p className={`text-sm font-semibold ${
                portfolio.dailyPnL >= 0 ? 'text-green-600' : 'text-red-600'
              }`}>
                {portfolio.dailyPnL >= 0 ? '+' : ''}${portfolio.dailyPnL.toFixed(2)}
              </p>
            </div>
          </div>

          {/* Notifications */}
          <div className="relative">
            <button className="text-gray-500 hover:text-gray-700">
              <Bell className="w-6 h-6" />
              {unreadCount > 0 && (
                <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full h-5 w-5 flex items-center justify-center">
                  {unreadCount}
                </span>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

// Loading component
const LoadingScreen = () => (
  <div className="min-h-screen bg-gray-50 flex items-center justify-center">
    <div className="text-center">
      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
      <p className="text-gray-600">Initializing Trading System Demo...</p>
    </div>
  </div>
)

// Main App component
function App() {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [isLoading, setIsLoading] = useState(true)

  // DISABLED WebSocket for demo mode
  // useWebSocket({ ... })
  // useSymbolSubscription()

  // Simulate loading
  useEffect(() => {
    const timer = setTimeout(() => {
      setIsLoading(false)
    }, 1500) // Shorter loading time
    return () => clearTimeout(timer)
  }, [])

  if (isLoading) {
    return <LoadingScreen />
  }

  return (
    <ToastProvider>
      <Router>
        <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
          <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />
          
          <div className="lg:pl-64">
            <TopBar onMenuClick={() => setSidebarOpen(true)} />
            
            <main className="py-6">
              <Routes>
                <Route path="/" element={<TradingDashboard />} />
                <Route path="/config" element={<ConfigurationDashboard />} />
                <Route path="/backtest" element={<BacktestingDashboard />} />
                <Route path="/analytics" element={<AnalyticsDashboard />} />
                <Route path="*" element={<Navigate to="/" replace />} />
              </Routes>
            </main>
          </div>
        </div>
      </Router>
    </ToastProvider>
  )
}

export default App
