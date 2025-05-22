"""
Enhanced Trading Engine with Full Integration
Main orchestrator with Supabase, Telegram, Mobula, and Binance APIs
"""

import asyncio
import logging
import os
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from decimal import Decimal

from ...domain.trading_signals.trading_signal import TradingSignal, StrategyType
from ...domain.entities.market_data import MarketData
from ...domain.strategies.base_strategy import TradingStrategy
from ...domain.strategies.scalping_strategy import ScalpingStrategy
from ...domain.strategies.day_trading_strategy import DayTradingStrategy
from ...domain.risk_management.advanced_risk_manager import AdvancedRiskManager, RiskParameters
from ...infrastructure.websockets.websocket_manager import ExchangeWebSocketManager, ExchangeType
from ...infrastructure.websockets.binance_websocket import BinanceWebSocketClient
from ...infrastructure.ai_analysis.gemini_analyzer import GeminiMarketAnalyzer
from ...infrastructure.real_time_data.stream_processor import RealTimeDataProcessor
from ...infrastructure.database.supabase_client import supabase_client
from ...infrastructure.messaging.telegram_notifier import telegram_notifier
from ...infrastructure.external_apis.mobula_client import mobula_client


class EnhancedTradingEngineConfig:
    """Enhanced configuration with all integrations"""
    
    def __init__(self):
        # Capital configuration
        self.initial_capital = Decimal(os.getenv('INITIAL_CAPITAL', '10000'))
        
        # Trading symbols
        symbols_str = os.getenv('TRADING_SYMBOLS', 'BTCUSDT,ETHUSDT,ADAUSDT,DOTUSDT,LINKUSDT')
        self.trading_symbols = [s.strip() for s in symbols_str.split(',')]
        
        # Strategy configuration
        strategies_str = os.getenv('ENABLED_STRATEGIES', 'scalping,day_trading')
        strategy_mapping = {
            'scalping': StrategyType.SCALPING,
            'day_trading': StrategyType.DAY_TRADING,
            'triangular_arbitrage': StrategyType.TRIANGULAR_ARBITRAGE
        }
        
        self.enabled_strategies = [
            strategy_mapping[s.strip().lower()] 
            for s in strategies_str.split(',')
            if s.strip().lower() in strategy_mapping
        ]
        
        # Strategy weights
        weights_str = os.getenv('STRATEGY_WEIGHTS', '0.4,0.6')
        weights = [float(w.strip()) for w in weights_str.split(',')]
        self.strategy_weights = {}
        for i, strategy in enumerate(self.enabled_strategies):
            if i < len(weights):
                self.strategy_weights[strategy] = weights[i]
            else:
                self.strategy_weights[strategy] = 1.0 / len(self.enabled_strategies)
        
        # Exchange configuration
        exchanges_str = os.getenv('ENABLED_EXCHANGES', 'binance')
        exchange_mapping = {
            'binance': ExchangeType.BINANCE,
            'coinbase': ExchangeType.COINBASE,
            'kraken': ExchangeType.KRAKEN
        }
        
        self.enabled_exchanges = [
            exchange_mapping[e.strip().lower()]
            for e in exchanges_str.split(',')
            if e.strip().lower() in exchange_mapping
        ]
        
        # API Keys
        self.gemini_api_key = os.getenv('GEMINI_API_KEY', '')
        self.binance_api_key = os.getenv('BINANCE_API_KEY', '')
        self.binance_secret_key = os.getenv('BINANCE_SECRET_KEY', '')
        
        # AI configuration
        self.ai_enabled = os.getenv('AI_ENABLED', 'true').lower() == 'true'
        
        # Risk management
        self.risk_params = RiskParameters(
            max_daily_loss=Decimal(os.getenv('MAX_DAILY_LOSS', '0.02')),
            max_position_size=Decimal(os.getenv('MAX_POSITION_SIZE', '0.05')),
            max_concurrent_positions=int(os.getenv('MAX_CONCURRENT_POSITIONS', '8')),
            require_ai_validation=True
        )
        
        # Performance settings
        self.max_signals_per_minute = int(os.getenv('MAX_SIGNALS_PER_MINUTE', '10'))
        self.signal_cooldown_seconds = int(os.getenv('SIGNAL_COOLDOWN_SECONDS', '30'))
        
        # Notification settings
        self.telegram_enabled = bool(os.getenv('TELEGRAM_BOT_TOKEN'))
        self.daily_summary_time = "18:00"  # 6 PM daily summary
        
        # Database settings
        self.database_enabled = bool(os.getenv('SUPABASE_URL'))
        
        # External APIs
        self.mobula_enabled = bool(os.getenv('MOBULA_API_KEY'))
        
        # Development settings
        self.paper_trading = os.getenv('PAPER_TRADING', 'true').lower() == 'true'
        self.development_mode = os.getenv('DEVELOPMENT_MODE', 'false').lower() == 'true'


class EnhancedTradingEngine:
    """
    Enhanced trading engine with full integration
    
    Features:
    - Database persistence with Supabase
    - Telegram notifications
    - Enhanced market data with Mobula
    - Full Binance integration
    - Advanced analytics and reporting
    """
    
    def __init__(self, config: EnhancedTradingEngineConfig):
        self.config = config
        self.logger = logging.getLogger("trading.engine.enhanced")
        
        # Core components
        self.websocket_manager: Optional[ExchangeWebSocketManager] = None
        self.data_processor: Optional[RealTimeDataProcessor] = None
        self.ai_analyzer: Optional[GeminiMarketAnalyzer] = None
        self.risk_manager: Optional[AdvancedRiskManager] = None
        self.strategies: Dict[StrategyType, TradingStrategy] = {}
        
        # State management
        self.is_running = False
        self.start_time: Optional[datetime] = None
        self.market_data_cache: Dict[str, MarketData] = {}
        self.active_signals: List[TradingSignal] = []
        self.signal_history: List[TradingSignal] = []
        
        # Performance tracking
        self.signals_generated_today = 0
        self.trades_executed_today = 0
        self.last_signal_time = datetime.now()
        self.last_daily_summary = None
        
        # Integration status
        self.integrations_status = {
            'database': False,
            'telegram': False,
            'mobula': False,
            'ai': False
        }
        
        self.logger.info("Enhanced trading engine initialized")
    
    async def initialize(self):
        """Initialize all components and integrations"""
        try:
            self.logger.info("Initializing enhanced trading engine...")
            
            # Initialize database
            if self.config.database_enabled:
                await self._initialize_database()
            
            # Initialize AI analyzer
            if self.config.ai_enabled and self.config.gemini_api_key:
                self.ai_analyzer = GeminiMarketAnalyzer(self.config.gemini_api_key)
                self.integrations_status['ai'] = True
                self.logger.info("AI analyzer initialized")
            
            # Initialize external APIs
            if self.config.mobula_enabled:
                self.integrations_status['mobula'] = True
                self.logger.info("Mobula API integration enabled")
            
            # Initialize notifications
            if self.config.telegram_enabled:
                self.integrations_status['telegram'] = True
                await telegram_notifier.send_startup_message()
                self.logger.info("Telegram notifications enabled")
            
            # Initialize risk manager
            self.risk_manager = AdvancedRiskManager(
                self.config.initial_capital,
                self.config.risk_params
            )
            self.logger.info("Risk manager initialized")
            
            # Initialize strategies
            await self._initialize_strategies()
            
            # Initialize real-time data processor
            self.data_processor = RealTimeDataProcessor()
            self.data_processor.subscribe_globally(self._on_market_data_update)
            await self.data_processor.start_processing()
            self.logger.info("Real-time data processor initialized")
            
            # Initialize WebSocket manager
            await self._initialize_websockets()
            
            # Load configuration from database
            await self._load_system_configuration()
            
            self.logger.info("Enhanced trading engine initialization complete")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize enhanced trading engine: {e}")
            await self._send_error_notification("INITIALIZATION_ERROR", str(e))
            raise
    
    async def _initialize_database(self):
        """Initialize Supabase database connection"""
        try:
            await supabase_client.initialize()
            self.integrations_status['database'] = True
            self.logger.info("Supabase database initialized")
        except Exception as e:
            self.logger.error(f"Database initialization failed: {e}")
            self.integrations_status['database'] = False
    
    async def _initialize_strategies(self):
        """Initialize trading strategies with enhanced features"""
        if not self.ai_analyzer:
            self.logger.error("Cannot initialize strategies without AI analyzer")
            return
        
        for strategy_type in self.config.enabled_strategies:
            if strategy_type == StrategyType.SCALPING:
                self.strategies[strategy_type] = ScalpingStrategy(self.ai_analyzer)
            elif strategy_type == StrategyType.DAY_TRADING:
                self.strategies[strategy_type] = DayTradingStrategy(self.ai_analyzer)
            
            self.logger.info(f"Initialized {strategy_type.value} strategy")
    
    async def _initialize_websockets(self):
        """Initialize WebSocket connections with enhanced monitoring"""
        self.websocket_manager = ExchangeWebSocketManager()
        
        # Add configured exchanges
        for exchange_type in self.config.enabled_exchanges:
            if exchange_type == ExchangeType.BINANCE:
                binance_client = BinanceWebSocketClient()
                self.websocket_manager.add_exchange(binance_client)
        
        # Connect to exchanges
        connection_results = await self.websocket_manager.connect_all()
        
        for exchange, connected in connection_results.items():
            if connected:
                self.logger.info(f"Connected to {exchange.value}")
            else:
                self.logger.error(f"Failed to connect to {exchange.value}")
                await self._send_error_notification("WEBSOCKET_CONNECTION_FAILED", f"Failed to connect to {exchange.value}")
        
        # Subscribe to data streams
        await self._subscribe_to_data_streams()
    
    async def _subscribe_to_data_streams(self):
        """Subscribe to required data streams"""
        # Subscribe to ticker data
        await self.websocket_manager.subscribe_ticker(
            self.config.trading_symbols,
            self._on_websocket_ticker_data
        )
        
        # Subscribe to order book data
        await self.websocket_manager.subscribe_orderbook(
            self.config.trading_symbols,
            self._on_websocket_orderbook_data
        )
        
        self.logger.info(f"Subscribed to data streams for {len(self.config.trading_symbols)} symbols")
    
    async def _load_system_configuration(self):
        """Load system configuration from database"""
        if not self.integrations_status['database']:
            return
        
        try:
            # Load strategy configurations
            for strategy_type in self.config.enabled_strategies:
                config_key = f"strategy_{strategy_type.value}_config"
                config_data = await supabase_client.get_configuration(config_key)
                
                if config_data and strategy_type in self.strategies:
                    # Apply configuration to strategy
                    self.logger.info(f"Loaded configuration for {strategy_type.value}")
            
            # Load risk management configuration
            risk_config = await supabase_client.get_configuration("risk_management_config")
            if risk_config:
                # Update risk parameters
                self.logger.info("Loaded risk management configuration")
                
        except Exception as e:
            self.logger.error(f"Failed to load system configuration: {e}")
    
    async def _on_websocket_ticker_data(self, data: Dict[str, Any]):
        """Handle incoming ticker data from WebSocket"""
        try:
            await self.data_processor.process_websocket_message(data)
        except Exception as e:
            self.logger.error(f"Error processing ticker data: {e}")
    
    async def _on_websocket_orderbook_data(self, data: Dict[str, Any]):
        """Handle incoming order book data from WebSocket"""
        try:
            await self.data_processor.process_websocket_message(data)
        except Exception as e:
            self.logger.error(f"Error processing order book data: {e}")
    
    async def _on_market_data_update(self, symbol: str, market_data: MarketData):
        """Handle processed market data updates with enhanced analytics"""
        try:
            # Update cache
            self.market_data_cache[symbol] = market_data
            
            # Enhance with Mobula data if available
            if self.integrations_status['mobula']:
                await self._enhance_market_data_with_mobula(symbol, market_data)
            
            # Trigger strategy analysis if enough data
            if len(self.market_data_cache) >= 3:
                await self._analyze_trading_opportunities()
                
        except Exception as e:
            self.logger.error(f"Error handling market data update for {symbol}: {e}")
    
    async def _enhance_market_data_with_mobula(self, symbol: str, market_data: MarketData):
        """Enhance market data with Mobula API information"""
        try:
            # Remove 'USDT' suffix for Mobula API
            mobula_symbol = symbol.replace('USDT', '').replace('BUSD', '')
            
            # Get enhanced data from Mobula
            mobula_data = await mobula_client.get_market_data([mobula_symbol])
            
            if mobula_data and mobula_symbol in mobula_data:
                enhanced_data = mobula_data[mobula_symbol]
                
                # Add enhanced technical indicators
                if market_data.technical_indicators is None:
                    market_data.technical_indicators = {}
                
                market_data.technical_indicators.update({
                    'market_cap': enhanced_data.get('market_cap', 0),
                    'volume_24h_enhanced': enhanced_data.get('volume_24h', 0),
                    'ath': enhanced_data.get('ath', 0),
                    'atl': enhanced_data.get('atl', 0),
                    'rank': enhanced_data.get('rank', 0)
                })
                
        except Exception as e:
            self.logger.debug(f"Failed to enhance market data with Mobula for {symbol}: {e}")
    
    async def _analyze_trading_opportunities(self):
        """Enhanced trading opportunities analysis"""
        
        # Rate limiting
        if not self._can_generate_signal():
            return
        
        try:
            all_signals = []
            
            # Run each strategy
            for strategy_type, strategy in self.strategies.items():
                try:
                    strategy_signals = await strategy.analyze_market(self.market_data_cache)
                    
                    # Apply strategy weight
                    weight = self.config.strategy_weights.get(strategy_type, 1.0)
                    for signal in strategy_signals:
                        signal.confidence *= weight
                    
                    all_signals.extend(strategy_signals)
                    
                    self.logger.debug(f"{strategy_type.value} generated {len(strategy_signals)} signals")
                    
                except Exception as e:
                    self.logger.error(f"Error in {strategy_type.value} strategy: {e}")
                    await self._send_error_notification("STRATEGY_ERROR", f"{strategy_type.value}: {e}")
            
            # Process signals through enhanced risk management
            if all_signals:
                await self._process_trading_signals_enhanced(all_signals)
                
        except Exception as e:
            self.logger.error(f"Error analyzing trading opportunities: {e}")
    
    async def _process_trading_signals_enhanced(self, signals: List[TradingSignal]):
        """Process trading signals with enhanced features"""
        
        approved_signals = []
        
        for signal in signals:
            try:
                # Get market data for the signal
                market_data = self.market_data_cache.get(signal.symbol)
                if not market_data:
                    continue
                
                # Enhanced risk assessment
                risk_assessment = await self.risk_manager.evaluate_signal_risk(signal, market_data)
                
                if risk_assessment['approved']:
                    # Update signal with risk management parameters
                    signal.stop_loss = risk_assessment['stop_loss']
                    signal.take_profit = risk_assessment['take_profit']
                    
                    approved_signals.append(signal)
                    self.logger.info(f"Signal APPROVED: {signal.symbol} {signal.action.value} - Confidence: {signal.confidence:.2f}")
                else:
                    self.logger.info(f"Signal REJECTED: {signal.symbol} - Reasons: {risk_assessment['risk_factors']}")
                    
            except Exception as e:
                self.logger.error(f"Error processing signal for {signal.symbol}: {e}")
        
        # Execute approved signals with full integration
        if approved_signals:
            await self._execute_trading_signals_enhanced(approved_signals)
    
    async def _execute_trading_signals_enhanced(self, signals: List[TradingSignal]):
        """Execute trading signals with database logging and notifications"""
        
        for signal in signals:
            try:
                # Calculate position size
                position_size = self._calculate_position_size(signal)
                entry_price = signal.entry_price or 0
                
                # Log to database
                if self.integrations_status['database']:
                    await supabase_client.log_trading_operation(signal)
                
                # Send Telegram notification
                if self.integrations_status['telegram']:
                    await telegram_notifier.send_trade_execution_alert(signal, position_size)
                
                # Add position to risk manager
                self.risk_manager.add_position(signal, Decimal(str(position_size)), Decimal(str(entry_price)))
                
                # Update state
                self.active_signals.append(signal)
                self.signal_history.append(signal)
                self.signals_generated_today += 1
                self.trades_executed_today += 1
                self.last_signal_time = datetime.now()
                
                self.logger.info(f"EXECUTED: {signal.symbol} {signal.action.value} - Size: {position_size:.6f}")
                
            except Exception as e:
                self.logger.error(f"Error executing signal for {signal.symbol}: {e}")
                await self._send_error_notification("SIGNAL_EXECUTION_ERROR", f"{signal.symbol}: {e}")
    
    async def start_trading(self):
        """Start the enhanced trading engine"""
        if self.is_running:
            self.logger.warning("Trading engine already running")
            return
        
        try:
            self.start_time = datetime.now()
            await self.initialize()
            
            self.is_running = True
            self.logger.info("🚀 ENHANCED TRADING ENGINE STARTED 🚀")
            
            # Start monitoring tasks
            asyncio.create_task(self._monitor_positions_enhanced())
            asyncio.create_task(self._periodic_status_report_enhanced())
            asyncio.create_task(self._daily_summary_task())
            asyncio.create_task(self._performance_analytics_task())
            
            # Keep the engine running
            while self.is_running:
                await asyncio.sleep(1)
                
        except Exception as e:
            self.logger.error(f"Enhanced trading engine error: {e}")
            await self._send_error_notification("ENGINE_ERROR", str(e))
            await self.stop_trading()
    
    async def stop_trading(self):
        """Stop the enhanced trading engine"""
        self.logger.info("Stopping enhanced trading engine...")
        
        self.is_running = False
        
        # Send shutdown notification
        if self.integrations_status['telegram']:
            await telegram_notifier.send_shutdown_message()
        
        # Save final performance data
        if self.integrations_status['database']:
            await self._save_final_performance_data()
        
        # Disconnect WebSockets
        if self.websocket_manager:
            await self.websocket_manager.disconnect_all()
        
        # Close database connections
        if self.integrations_status['database']:
            await supabase_client.close()
        
        self.logger.info("Enhanced trading engine stopped")
    
    async def _monitor_positions_enhanced(self):
        """Enhanced position monitoring with notifications"""
        while self.is_running:
            try:
                # Get current prices
                current_prices = {
                    symbol: data.current_price 
                    for symbol, data in self.market_data_cache.items()
                }
                
                # Monitor positions
                positions_to_close = await self.risk_manager.monitor_positions(current_prices)
                
                # Close positions with enhanced logging
                for position_id, reason in positions_to_close:
                    symbol = position_id.split('_')[0]
                    current_price = current_prices.get(symbol, Decimal('0'))
                    
                    if current_price > 0:
                        # Get position info before closing
                        position = self.risk_manager.open_positions.get(position_id)
                        
                        if position:
                            # Calculate P&L
                            if position.quantity > 0:  # Long position
                                pnl = (current_price - position.entry_price) * position.quantity
                            else:  # Short position
                                pnl = (position.entry_price - current_price) * abs(position.quantity)
                            
                            # Close position
                            self.risk_manager.close_position(position_id, current_price, reason)
                            
                            # Update database
                            if self.integrations_status['database']:
                                await supabase_client.update_operation_exit(
                                    position_id, current_price, pnl, Decimal('0.001') * current_price
                                )
                            
                            # Send notification
                            if self.integrations_status['telegram']:
                                await telegram_notifier.send_position_closed_alert(
                                    symbol, position.strategy, pnl, reason,
                                    float(position.entry_price), float(current_price)
                                )
                            
                            self.logger.info(f"Position closed: {position_id} - Reason: {reason} - P&L: {pnl}")
                
                await asyncio.sleep(5)  # Check every 5 seconds
                
            except Exception as e:
                self.logger.error(f"Error monitoring positions: {e}")
                await asyncio.sleep(10)
    
    async def _periodic_status_report_enhanced(self):
        """Enhanced periodic status reports"""
        while self.is_running:
            try:
                await asyncio.sleep(1800)  # Every 30 minutes
                
                # Generate enhanced status
                status = self.get_enhanced_status()
                
                # Send to Telegram
                if self.integrations_status['telegram']:
                    await telegram_notifier.send_system_status(status)
                
                # Save to database
                if self.integrations_status['database']:
                    await supabase_client.save_performance_metrics(status, "system_status")
                
                self.logger.info("Periodic status report sent")
                
            except Exception as e:
                self.logger.error(f"Error generating status report: {e}")
    
    async def _daily_summary_task(self):
        """Daily performance summary task"""
        while self.is_running:
            try:
                now = datetime.now()
                target_time = now.replace(hour=18, minute=0, second=0, microsecond=0)  # 6 PM
                
                if now >= target_time and (not self.last_daily_summary or 
                                         self.last_daily_summary.date() < now.date()):
                    
                    # Generate daily summary
                    if self.integrations_status['database']:
                        performance_data = await supabase_client.get_performance_summary(days=1)
                        
                        if self.integrations_status['telegram']:
                            await telegram_notifier.send_daily_summary(performance_data)
                        
                        self.last_daily_summary = now
                        self.logger.info("Daily summary sent")
                
                await asyncio.sleep(300)  # Check every 5 minutes
                
            except Exception as e:
                self.logger.error(f"Error in daily summary task: {e}")
    
    async def _performance_analytics_task(self):
        """Advanced performance analytics task"""
        while self.is_running:
            try:
                await asyncio.sleep(3600)  # Every hour
                
                # Calculate and save performance metrics
                performance_metrics = self.get_performance_metrics()
                
                if self.integrations_status['database']:
                    await supabase_client.save_performance_metrics(
                        performance_metrics['trading_engine'], 
                        "hourly_performance"
                    )
                
                # Strategy-specific metrics
                for strategy_name, strategy_stats in performance_metrics.get('strategies', {}).items():
                    if self.integrations_status['database']:
                        await supabase_client.save_performance_metrics(
                            strategy_stats, 
                            strategy_name
                        )
                
                self.logger.info("Performance analytics saved")
                
            except Exception as e:
                self.logger.error(f"Error in performance analytics: {e}")
    
    async def _save_final_performance_data(self):
        """Save final performance data on shutdown"""
        try:
            if self.integrations_status['database']:
                final_metrics = self.get_performance_metrics()
                await supabase_client.save_performance_metrics(
                    final_metrics['trading_engine'], 
                    "final_session"
                )
                self.logger.info("Final performance data saved")
        except Exception as e:
            self.logger.error(f"Error saving final performance data: {e}")
    
    async def _send_error_notification(self, error_type: str, error_message: str, component: str = None):
        """Send error notification via Telegram"""
        if self.integrations_status['telegram']:
            await telegram_notifier.send_error_alert(error_type, error_message, component)
    
    def _can_generate_signal(self) -> bool:
        """Enhanced signal rate limiting"""
        now = datetime.now()
        
        # Check overall rate limit
        if (now - self.last_signal_time).total_seconds() < self.config.signal_cooldown_seconds:
            return False
        
        # Check max signals per minute
        recent_signals = [
            s for s in self.signal_history 
            if (now - s.timestamp).total_seconds() < 60
        ]
        
        if len(recent_signals) >= self.config.max_signals_per_minute:
            return False
        
        return True
    
    def _calculate_position_size(self, signal: TradingSignal) -> float:
        """Enhanced position size calculation"""
        strategy = self.strategies.get(signal.strategy_name)
        if strategy:
            risk_params = strategy.get_risk_parameters()
            max_position = risk_params.get('max_position_size', 0.02)
        else:
            max_position = 0.02
        
        # Adjust based on confidence and market conditions
        confidence_factor = signal.confidence
        risk_factor = 1.0 if signal.risk_level.value == 'LOW' else 0.8 if signal.risk_level.value == 'MEDIUM' else 0.6
        
        position_size = max_position * confidence_factor * risk_factor
        
        return position_size
    
    def get_enhanced_status(self) -> Dict[str, Any]:
        """Get enhanced system status"""
        websocket_status = "DISCONNECTED"
        if self.websocket_manager:
            connection_statuses = self.websocket_manager.get_connection_status()
            connected_count = sum(1 for status in connection_statuses.values() if status.value == "connected")
            websocket_status = f"{connected_count}/{len(connection_statuses)} connected"
        
        risk_metrics = self.risk_manager.get_risk_metrics() if self.risk_manager else {}
        
        uptime = str(datetime.now() - self.start_time) if self.start_time else "Unknown"
        
        return {
            'is_running': self.is_running,
            'uptime': uptime,
            'signals_generated_today': self.signals_generated_today,
            'trades_executed_today': self.trades_executed_today,
            'active_positions': len(self.active_signals),
            'total_pnl': risk_metrics.get('total_pnl', 0),
            'available_capital': risk_metrics.get('available_capital', 0),
            'symbols_tracked': len(self.market_data_cache),
            'websocket_status': websocket_status,
            'enabled_strategies': [s.value for s in self.config.enabled_strategies],
            'enabled_exchanges': [e.value for e in self.config.enabled_exchanges],
            'integrations_status': self.integrations_status,
            'paper_trading': self.config.paper_trading
        }
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get enhanced performance metrics"""
        processor_stats = self.data_processor.get_performance_stats() if self.data_processor else {}
        risk_metrics = self.risk_manager.get_risk_metrics() if self.risk_manager else {}
        
        strategy_stats = {}
        for strategy_type, strategy in self.strategies.items():
            if hasattr(strategy, 'get_strategy_stats'):
                strategy_stats[strategy_type.value] = strategy.get_strategy_stats()
        
        return {
            'trading_engine': self.get_enhanced_status(),
            'data_processor': processor_stats,
            'risk_management': risk_metrics,
            'strategies': strategy_stats,
            'signal_history_count': len(self.signal_history),
            'integrations_status': self.integrations_status
        }
