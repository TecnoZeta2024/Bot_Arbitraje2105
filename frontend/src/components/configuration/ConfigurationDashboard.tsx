import React, { useState, useEffect } from 'react'
import { 
  Settings, 
  Shield, 
  Brain, 
  DollarSign, 
  Activity, 
  Bell, 
  Database,
  Key,
  Sliders,
  RefreshCw,
  Save,
  RotateCcw,
  CheckCircle,
  AlertTriangle,
  Info,
  ExternalLink
} from 'lucide-react'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Switch } from '@/components/ui/switch'
import { Input } from '@/components/ui/input'
import { useTradingStore, useTradingConfig } from '@/store'
import { cn } from '@/lib/utils'

// Configuration section interface
interface ConfigSection {
  id: string
  title: string
  icon: React.ReactNode
  description: string
  component: React.ComponentType
}

// Trading Configuration Component
const TradingConfigSection = () => {
  const { config, updateConfig } = useTradingConfig()
  const [localConfig, setLocalConfig] = useState(config)
  const [hasChanges, setHasChanges] = useState(false)

  useEffect(() => {
    setLocalConfig(config)
    setHasChanges(false)
  }, [config])

  const handleConfigChange = (key: string, value: any) => {
    const newConfig = { ...localConfig, [key]: value }
    setLocalConfig(newConfig)
    setHasChanges(JSON.stringify(newConfig) !== JSON.stringify(config))
  }

  const handleSave = () => {
    updateConfig(localConfig)
    setHasChanges(false)
  }

  const handleReset = () => {
    setLocalConfig(config)
    setHasChanges(false)
  }

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Risk Management */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center text-lg">
              <Shield className="w-5 h-5 mr-2 text-blue-500" />
              Risk Management
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">Risk Level</label>
              <select 
                value={localConfig.riskLevel}
                onChange={(e) => handleConfigChange('riskLevel', e.target.value)}
                className="w-full p-2 border border-border rounded-md bg-background"
              >
                <option value="LOW">Conservative (Low Risk)</option>
                <option value="MEDIUM">Balanced (Medium Risk)</option>
                <option value="HIGH">Aggressive (High Risk)</option>
              </select>
            </div>
            
            <div className="space-y-2">
              <label className="text-sm font-medium">Max Positions</label>
              <Input
                type="number"
                min="1"
                max="20"
                value={localConfig.maxPositions}
                onChange={(e) => handleConfigChange('maxPositions', parseInt(e.target.value))}
              />
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Max Position Size ($)</label>
              <Input
                type="number"
                min="100"
                max="50000"
                step="100"
                value={localConfig.maxPositionSize}
                onChange={(e) => handleConfigChange('maxPositionSize', parseFloat(e.target.value))}
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <label className="text-sm font-medium">Stop Loss (%)</label>
                <Input
                  type="number"
                  min="0.5"
                  max="10"
                  step="0.1"
                  value={localConfig.stopLossPercent}
                  onChange={(e) => handleConfigChange('stopLossPercent', parseFloat(e.target.value))}
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Take Profit (%)</label>
                <Input
                  type="number"
                  min="1"
                  max="20"
                  step="0.1"
                  value={localConfig.takeProfitPercent}
                  onChange={(e) => handleConfigChange('takeProfitPercent', parseFloat(e.target.value))}
                />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Trading Strategies */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center text-lg">
              <Activity className="w-5 h-5 mr-2 text-green-500" />
              Trading Strategies
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {[
              { id: 'scalping', name: 'Scalping', description: 'Quick trades for small profits' },
              { id: 'day_trading', name: 'Day Trading', description: 'Intraday position trading' },
              { id: 'swing_trading', name: 'Swing Trading', description: 'Multi-day position holds' },
              { id: 'arbitrage', name: 'Arbitrage', description: 'Price difference exploitation' },
              { id: 'grid_trading', name: 'Grid Trading', description: 'Automated grid orders' },
              { id: 'dca', name: 'DCA Strategy', description: 'Dollar cost averaging' },
            ].map((strategy) => (
              <div key={strategy.id} className="flex items-center justify-between p-3 bg-muted/50 rounded-lg">
                <div>
                  <p className="text-sm font-medium">{strategy.name}</p>
                  <p className="text-xs text-muted-foreground">{strategy.description}</p>
                </div>
                <Switch
                  checked={localConfig.enabledStrategies.includes(strategy.id)}
                  onCheckedChange={(checked) => {
                    const strategies = checked
                      ? [...localConfig.enabledStrategies, strategy.id]
                      : localConfig.enabledStrategies.filter(s => s !== strategy.id)
                    handleConfigChange('enabledStrategies', strategies)
                  }}
                />
              </div>
            ))}
          </CardContent>
        </Card>

        {/* AI Configuration */}
        <Card className="md:col-span-2">
          <CardHeader>
            <CardTitle className="flex items-center text-lg">
              <Brain className="w-5 h-5 mr-2 text-purple-500" />
              AI & Automation
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium">Enable AI Analysis</p>
                    <p className="text-xs text-muted-foreground">Use AI for market analysis</p>
                  </div>
                  <Switch
                    checked={localConfig.enableAI}
                    onCheckedChange={(checked) => handleConfigChange('enableAI', checked)}
                  />
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium">Auto Trading</p>
                    <p className="text-xs text-muted-foreground">Execute trades automatically</p>
                  </div>
                  <Switch
                    checked={localConfig.autoTrading}
                    onCheckedChange={(checked) => handleConfigChange('autoTrading', checked)}
                  />
                </div>
              </div>

              <div className="space-y-4">
                <div className="space-y-2">
                  <label className="text-sm font-medium">AI Confidence Threshold</label>
                  <Input
                    type="number"
                    min="50"
                    max="95"
                    value="75"
                    placeholder="75%"
                  />
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium">Signal Processing Delay</label>
                  <select className="w-full p-2 border border-border rounded-md bg-background">
                    <option value="immediate">Immediate</option>
                    <option value="1s">1 Second</option>
                    <option value="5s">5 Seconds</option>
                    <option value="10s">10 Seconds</option>
                  </select>
                </div>
              </div>

              <div className="space-y-4">
                <div className="space-y-2">
                  <label className="text-sm font-medium">Market Analysis Model</label>
                  <select className="w-full p-2 border border-border rounded-md bg-background">
                    <option value="gpt-4">GPT-4 Enhanced</option>
                    <option value="claude">Claude Sonnet</option>
                    <option value="custom">Custom Model</option>
                  </select>
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium">Technical Indicators</label>
                  <select className="w-full p-2 border border-border rounded-md bg-background">
                    <option value="all">All Indicators</option>
                    <option value="momentum">Momentum Only</option>
                    <option value="trend">Trend Following</option>
                    <option value="volume">Volume Analysis</option>
                  </select>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Action Buttons */}
      {hasChanges && (
        <div className="flex items-center justify-between p-4 bg-blue-50 dark:bg-blue-950/20 border border-blue-200 dark:border-blue-800 rounded-lg">
          <div className="flex items-center space-x-2">
            <Info className="w-4 h-4 text-blue-500" />
            <span className="text-sm text-blue-700 dark:text-blue-300">You have unsaved changes</span>
          </div>
          <div className="flex space-x-2">
            <Button variant="outline" size="sm" onClick={handleReset}>
              <RotateCcw className="w-4 h-4 mr-1" />
              Reset
            </Button>
            <Button size="sm" onClick={handleSave}>
              <Save className="w-4 h-4 mr-1" />
              Save Changes
            </Button>
          </div>
        </div>
      )}
    </div>
  )
}

// Exchange Configuration Component
const ExchangeConfigSection = () => {
  const [exchanges, setExchanges] = useState([
    { name: 'Binance', enabled: true, status: 'connected', apiKey: '***************' },
    { name: 'Coinbase Pro', enabled: false, status: 'disconnected', apiKey: '' },
    { name: 'Kraken', enabled: false, status: 'disconnected', apiKey: '' },
    { name: 'KuCoin', enabled: false, status: 'disconnected', apiKey: '' },
  ])

  const [showApiKey, setShowApiKey] = useState<string | null>(null)

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {exchanges.map((exchange) => (
          <Card key={exchange.name}>
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                <div className="flex items-center">
                  <Database className="w-5 h-5 mr-2 text-blue-500" />
                  {exchange.name}
                </div>
                <div className={cn('status-indicator', {
                  'status-online': exchange.status === 'connected',
                  'status-error': exchange.status === 'error',
                  'status-offline': exchange.status === 'disconnected',
                })}>
                  {exchange.status}
                </div>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Enable Exchange</span>
                <Switch
                  checked={exchange.enabled}
                  onCheckedChange={(checked) => {
                    setExchanges(prev => prev.map(ex => 
                      ex.name === exchange.name ? { ...ex, enabled: checked } : ex
                    ))
                  }}
                />
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium">API Key</label>
                <div className="flex space-x-2">
                  <Input
                    type={showApiKey === exchange.name ? 'text' : 'password'}
                    value={exchange.apiKey}
                    placeholder="Enter API Key"
                    onChange={(e) => {
                      setExchanges(prev => prev.map(ex => 
                        ex.name === exchange.name ? { ...ex, apiKey: e.target.value } : ex
                      ))
                    }}
                  />
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setShowApiKey(showApiKey === exchange.name ? null : exchange.name)}
                  >
                    <Key className="w-4 h-4" />
                  </Button>
                </div>
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium">API Secret</label>
                <Input
                  type="password"
                  placeholder="Enter API Secret"
                />
              </div>

              <div className="flex items-center space-x-2">
                <Switch />
                <span className="text-sm">Use Sandbox Mode</span>
              </div>

              <Button className="w-full" variant="outline">
                <RefreshCw className="w-4 h-4 mr-2" />
                Test Connection
              </Button>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Global Exchange Settings */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <Settings className="w-5 h-5 mr-2 text-gray-500" />
            Global Exchange Settings
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">Default Order Type</label>
              <select className="w-full p-2 border border-border rounded-md bg-background">
                <option value="limit">Limit Orders</option>
                <option value="market">Market Orders</option>
                <option value="stop_limit">Stop Limit</option>
              </select>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Rate Limit Buffer</label>
              <Input type="number" min="0" max="100" placeholder="10%" />
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Timeout (seconds)</label>
              <Input type="number" min="5" max="60" placeholder="30" />
            </div>
          </div>

          <div className="flex flex-wrap gap-4">
            <div className="flex items-center space-x-2">
              <Switch />
              <span className="text-sm">Enable Order Batching</span>
            </div>
            <div className="flex items-center space-x-2">
              <Switch />
              <span className="text-sm">Auto-retry Failed Orders</span>
            </div>
            <div className="flex items-center space-x-2">
              <Switch />
              <span className="text-sm">Log All API Calls</span>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

// Notification Settings Component
const NotificationConfigSection = () => {
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <Bell className="w-5 h-5 mr-2 text-yellow-500" />
              Trading Alerts
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {[
              { id: 'position_opened', name: 'Position Opened', description: 'New position created' },
              { id: 'position_closed', name: 'Position Closed', description: 'Position closed with P&L' },
              { id: 'stop_loss_hit', name: 'Stop Loss Triggered', description: 'Stop loss order executed' },
              { id: 'take_profit_hit', name: 'Take Profit Hit', description: 'Take profit target reached' },
              { id: 'large_movement', name: 'Large Price Movement', description: 'Significant price changes' },
              { id: 'ai_signal', name: 'AI Trading Signal', description: 'New AI-generated signal' },
            ].map((alert) => (
              <div key={alert.id} className="flex items-center justify-between p-3 bg-muted/50 rounded-lg">
                <div>
                  <p className="text-sm font-medium">{alert.name}</p>
                  <p className="text-xs text-muted-foreground">{alert.description}</p>
                </div>
                <Switch defaultChecked />
              </div>
            ))}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <AlertTriangle className="w-5 h-5 mr-2 text-red-500" />
              System Alerts
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {[
              { id: 'connection_lost', name: 'Connection Lost', description: 'Exchange connection issues' },
              { id: 'api_errors', name: 'API Errors', description: 'Exchange API error responses' },
              { id: 'low_balance', name: 'Low Balance', description: 'Insufficient funds warning' },
              { id: 'system_errors', name: 'System Errors', description: 'Bot system malfunctions' },
              { id: 'security_alerts', name: 'Security Alerts', description: 'Unusual activity detected' },
              { id: 'maintenance', name: 'Maintenance Mode', description: 'System maintenance updates' },
            ].map((alert) => (
              <div key={alert.id} className="flex items-center justify-between p-3 bg-muted/50 rounded-lg">
                <div>
                  <p className="text-sm font-medium">{alert.name}</p>
                  <p className="text-xs text-muted-foreground">{alert.description}</p>
                </div>
                <Switch defaultChecked />
              </div>
            ))}
          </CardContent>
        </Card>
      </div>

      {/* Notification Channels */}
      <Card>
        <CardHeader>
          <CardTitle>Notification Channels</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="space-y-4">
              <h4 className="font-medium">Email Notifications</h4>
              <div className="space-y-2">
                <Input placeholder="email@example.com" />
                <div className="flex items-center space-x-2">
                  <Switch />
                  <span className="text-sm">Enable Email Alerts</span>
                </div>
              </div>
            </div>

            <div className="space-y-4">
              <h4 className="font-medium">Telegram Bot</h4>
              <div className="space-y-2">
                <Input placeholder="Bot Token" />
                <Input placeholder="Chat ID" />
                <div className="flex items-center space-x-2">
                  <Switch />
                  <span className="text-sm">Enable Telegram</span>
                </div>
              </div>
            </div>

            <div className="space-y-4">
              <h4 className="font-medium">Discord Webhook</h4>
              <div className="space-y-2">
                <Input placeholder="Webhook URL" />
                <div className="flex items-center space-x-2">
                  <Switch />
                  <span className="text-sm">Enable Discord</span>
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

// Advanced Settings Component
const AdvancedConfigSection = () => {
  return (
    <div className="space-y-6">
      {/* System Performance */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <Sliders className="w-5 h-5 mr-2 text-purple-500" />
            System Performance
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">Data Update Frequency</label>
              <select className="w-full p-2 border border-border rounded-md bg-background">
                <option value="100ms">100ms (High CPU)</option>
                <option value="500ms">500ms (Balanced)</option>
                <option value="1s">1 Second (Low CPU)</option>
              </select>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Chart Data Points</label>
              <select className="w-full p-2 border border-border rounded-md bg-background">
                <option value="500">500 Points</option>
                <option value="1000">1000 Points</option>
                <option value="2000">2000 Points</option>
              </select>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Log Level</label>
              <select className="w-full p-2 border border-border rounded-md bg-background">
                <option value="error">Error Only</option>
                <option value="warning">Warning & Error</option>
                <option value="info">Info & Above</option>
                <option value="debug">Debug (Verbose)</option>
              </select>
            </div>
          </div>

          <div className="flex flex-wrap gap-4">
            <div className="flex items-center space-x-2">
              <Switch />
              <span className="text-sm">Enable GPU Acceleration</span>
            </div>
            <div className="flex items-center space-x-2">
              <Switch />
              <span className="text-sm">Optimize Memory Usage</span>
            </div>
            <div className="flex items-center space-x-2">
              <Switch />
              <span className="text-sm">Cache Market Data</span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Data Management */}
      <Card>
        <CardHeader>
          <CardTitle>Data Management</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-4">
              <h4 className="font-medium">Data Retention</h4>
              <div className="space-y-2">
                <label className="text-sm font-medium">Trade History</label>
                <select className="w-full p-2 border border-border rounded-md bg-background">
                  <option value="30d">30 Days</option>
                  <option value="90d">90 Days</option>
                  <option value="1y">1 Year</option>
                  <option value="forever">Forever</option>
                </select>
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium">Market Data</label>
                <select className="w-full p-2 border border-border rounded-md bg-background">
                  <option value="7d">7 Days</option>
                  <option value="30d">30 Days</option>
                  <option value="90d">90 Days</option>
                </select>
              </div>
            </div>

            <div className="space-y-4">
              <h4 className="font-medium">Backup Settings</h4>
              <div className="flex items-center space-x-2">
                <Switch />
                <span className="text-sm">Auto Backup</span>
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Backup Frequency</label>
                <select className="w-full p-2 border border-border rounded-md bg-background">
                  <option value="daily">Daily</option>
                  <option value="weekly">Weekly</option>
                  <option value="monthly">Monthly</option>
                </select>
              </div>
              <Button variant="outline" className="w-full">
                <Database className="w-4 h-4 mr-2" />
                Create Backup Now
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Developer Settings */}
      <Card>
        <CardHeader>
          <CardTitle>Developer Settings</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="flex items-center space-x-2">
              <Switch />
              <span className="text-sm">Enable Debug Mode</span>
            </div>
            <div className="flex items-center space-x-2">
              <Switch />
              <span className="text-sm">API Request Logging</span>
            </div>
            <div className="flex items-center space-x-2">
              <Switch />
              <span className="text-sm">Performance Metrics</span>
            </div>
            <div className="flex items-center space-x-2">
              <Switch />
              <span className="text-sm">Error Reporting</span>
            </div>
          </div>

          <div className="flex space-x-2">
            <Button variant="outline" className="flex-1">
              <ExternalLink className="w-4 h-4 mr-2" />
              View Logs
            </Button>
            <Button variant="outline" className="flex-1">
              <Activity className="w-4 h-4 mr-2" />
              System Metrics
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

// Main Configuration Dashboard Component
export default function ConfigurationDashboard() {
  const [activeSection, setActiveSection] = useState('trading')

  const sections: ConfigSection[] = [
    {
      id: 'trading',
      title: 'Trading',
      icon: <DollarSign className="w-5 h-5" />,
      description: 'Trading strategies and risk management',
      component: TradingConfigSection,
    },
    {
      id: 'exchanges',
      title: 'Exchanges',
      icon: <Database className="w-5 h-5" />,
      description: 'Exchange connections and API settings',
      component: ExchangeConfigSection,
    },
    {
      id: 'notifications',
      title: 'Notifications',
      icon: <Bell className="w-5 h-5" />,
      description: 'Alerts and notification channels',
      component: NotificationConfigSection,
    },
    {
      id: 'advanced',
      title: 'Advanced',
      icon: <Sliders className="w-5 h-5" />,
      description: 'System performance and developer settings',
      component: AdvancedConfigSection,
    },
  ]

  const ActiveComponent = sections.find(s => s.id === activeSection)?.component || TradingConfigSection

  return (
    <div className="px-6 py-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Configuration</h1>
          <p className="text-muted-foreground">Manage your trading bot settings and preferences</p>
        </div>
        <div className="flex items-center space-x-2">
          <Button variant="outline" size="sm">
            <RefreshCw className="w-4 h-4 mr-2" />
            Reset All
          </Button>
          <Button size="sm">
            <Save className="w-4 h-4 mr-2" />
            Save All Changes
          </Button>
        </div>
      </div>

      <div className="flex flex-col lg:flex-row gap-6">
        {/* Sidebar Navigation */}
        <div className="lg:w-64">
          <Card>
            <CardContent className="p-4">
              <nav className="space-y-2">
                {sections.map((section) => (
                  <button
                    key={section.id}
                    onClick={() => setActiveSection(section.id)}
                    className={cn(
                      'w-full flex items-center space-x-3 px-3 py-2 rounded-lg text-left transition-colors',
                      activeSection === section.id
                        ? 'bg-primary text-primary-foreground'
                        : 'hover:bg-muted text-muted-foreground hover:text-foreground'
                    )}
                  >
                    {section.icon}
                    <div>
                      <p className="text-sm font-medium">{section.title}</p>
                      <p className="text-xs opacity-70">{section.description}</p>
                    </div>
                  </button>
                ))}
              </nav>
            </CardContent>
          </Card>
        </div>

        {/* Main Content */}
        <div className="flex-1">
          <ActiveComponent />
        </div>
      </div>
    </div>
  )
}
