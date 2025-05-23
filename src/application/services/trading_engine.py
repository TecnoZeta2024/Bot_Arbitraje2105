"""
Trading Engine Application Service
Main orchestrator that integrates all components: WebSockets, AI, Strategies, Risk Management
"""

import asyncio
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional

from ...domain.entities.market_data import MarketData
from ...domain.risk_management.advanced_risk_manager import (
    AdvancedRiskManager,
    RiskParameters,
)
from ...domain.strategies.base_strategy import TradingStrategy
from ...domain.strategies.day_trading_strategy import DayTradingStrategy
from ...domain.strategies.scalping_strategy import ScalpingStrategy
from ...domain.trading_signals.trading_signal import StrategyType, TradingSignal
from ...infrastructure.ai_analysis.gemini_analyzer import GeminiMarketAnalyzer
from ...infrastructure.real_time_data.stream_processor import RealTimeDataProcessor
from ...infrastructure.websockets.binance_websocket import BinanceWebSocketClient
from ...infrastructure.websockets.websocket_manager import (
    ExchangeType,
    ExchangeWebSocketManager,
)


class TradingEngineConfig:
    """Configuration for the trading engine"""
    
    def __init__(self):
        # Capital configuration
        self.initial_capital = Decimal('10000')  # $10,000 initial capital
        
        # Symbols to trade
        self.trading_symbols = [
            'BTCUSDT', 'ETHUSDT', 'ADAUSDT', 'DOTUSDT', 'LINKUSDT',
            'BNBUSDT', 'XRPUSDT', 'LTCUSDT', 'BCHUSDT', 'EOSUSDT'
        ]
        
        # Strategy configuration
        self.enabled_strategies = [StrategyType.SCALPING, StrategyType.DAY_TRADING]
        self.strategy_weights = {
            StrategyType.SCALPING: 0.4,      # 40% weight
            StrategyType.DAY_TRADING: 0.6    # 60% weight
        }
        
        # Exchange configuration
        self.enabled_exchanges = [ExchangeType.BINANCE]  # Start with Binance
        
        # AI configuration
        self.gemini_api_key = ""  # Set this from environment
        self.ai_enabled = True
        
        # Risk management
        self.risk_params = RiskParameters(
            max_daily_loss=Decimal('0.02'),      # 2% max daily loss
            max_position_size=Decimal('0.05'),   # 5% max per position
            max_concurrent_positions=8,
            require_ai_validation=True
        )
        
        # Performance settings
        self.max_signals_per_minute = 10
        self.signal_cooldown_seconds = 30


class TradingEngine:
    """
    Main trading engine that orchestrates all components
    
    Architecture:
    WebSockets -> RealTimeProcessor -> Strategies -> AI Validation -> Risk Management -> Execution
    """
    
    def __init__(self, config: TradingEngineConfig):
        self.config = config
        self.logger = logging.getLogger("trading.engine")
        
        # Core components
        self.websocket_manager: Optional[ExchangeWebSocketManager] = None
        self.data_processor: Optional[RealTimeDataProcessor] = None
        self.ai_analyzer: Optional[GeminiMarketAnalyzer] = None
        self.risk_manager: Optional[AdvancedRiskManager] = None
        self.strategies: Dict[StrategyType, TradingStrategy] = {}
        
        # State management
        self.is_running = False
        self.market_data_cache: Dict[str, MarketData] = {}
        self.active_signals: List[TradingSignal] = []
        self.signal_history: List[TradingSignal] = []
        
        # Performance tracking
        self.signals_generated_today = 0
        self.trades_executed_today = 0
        self.last_signal_time = datetime.now()
        
        self.logger.info("Trading engine initialized")
    
    async def initialize(self):
        """Initialize all components"""
        try:
            self.logger.info("Initializing trading engine components...")
            
            # Initialize AI analyzer
            if self.config.ai_enabled and self.config.gemini_api_key:
                self.ai_analyzer = GeminiMarketAnalyzer(self.config.gemini_api_key)
                self.logger.info("AI analyzer initialized")
            else:
                self.logger.warning("AI analyzer not initialized - missing API key")
            
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
            
            self.logger.info("Trading engine initialization complete")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize trading engine: {e}")
            raise
    
    async def _initialize_strategies(self):
        """Initialize trading strategies"""
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
        """Initialize WebSocket connections"""
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
    
    async def _on_websocket_ticker_data(self, data: Dict[str, Any]):
        """Handle incoming ticker data from WebSocket"""
        try:
            # Forward to real-time data processor
            await self.data_processor.process_websocket_message(data)
        except Exception as e:
            self.logger.error(f"Error processing ticker data: {e}")
    
    async def _on_websocket_orderbook_data(self, data: Dict[str, Any]):
        """Handle incoming order book data from WebSocket"""
        try:
            # Forward to real-time data processor
            await self.data_processor.process_websocket_message(data)
        except Exception as e:
            self.logger.error(f"Error processing order book data: {e}")
    
    async def _on_market_data_update(self, symbol: str, market_data: MarketData):
        """Handle processed market data updates"""
        try:
            # Update cache
            self.market_data_cache[symbol] = market_data
            
            # Trigger strategy analysis if enough data
            if len(self.market_data_cache) >= 3:  # Wait for at least 3 symbols
                await self._analyze_trading_opportunities()
                
        except Exception as e:
            self.logger.error(f"Error handling market data update for {symbol}: {e}")
    
    async def _analyze_trading_opportunities(self):
        """Analyze market data with all strategies to find trading opportunities"""
        
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
            
            # Process signals through risk management
            if all_signals:
                await self._process_trading_signals(all_signals)
                
        except Exception as e:
            self.logger.error(f"Error analyzing trading opportunities: {e}")
    
    def _can_generate_signal(self) -> bool:
        """Check if we can generate new signals (rate limiting)"""
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
    
    async def _process_trading_signals(self, signals: List[TradingSignal]):
        """Process trading signals through risk management"""
        
        approved_signals = []
        
        for signal in signals:
            try:
                # Get market data for the signal
                market_data = self.market_data_cache.get(signal.symbol)
                if not market_data:
                    continue
                
                # Risk assessment
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
        
        # Execute approved signals
        if approved_signals:
            await self._execute_trading_signals(approved_signals)
    
    async def _execute_trading_signals(self, signals: List[TradingSignal]):
        """Execute approved trading signals"""
        
        for signal in signals:
            try:
                # For now, just log the signal (execution would integrate with exchange API)
                self._log_signal_execution(signal)
                
                # Add to active signals
                self.active_signals.append(signal)
                self.signal_history.append(signal)
                
                # Update statistics
                self.signals_generated_today += 1
                self.last_signal_time = datetime.now()
                
                # Add position to risk manager (simulated)
                position_size = self._calculate_position_size(signal)
                entry_price = signal.entry_price or 0
                
                self.risk_manager.add_position(signal, Decimal(str(position_size)), Decimal(str(entry_price)))
                
                self.logger.info(f"EXECUTED: {signal.symbol} {signal.action.value} - Size: {position_size:.6f}")
                
            except Exception as e:
                self.logger.error(f"Error executing signal for {signal.symbol}: {e}")
    
    def _log_signal_execution(self, signal: TradingSignal):
        """Log signal execution details"""
        self.logger.info(f"""
        === TRADING SIGNAL EXECUTED ===
        Symbol: {signal.symbol}
        Strategy: {signal.strategy_name.value}
        Action: {signal.action.value}
        Confidence: {signal.confidence:.2%}
        Expected Profit: {signal.expected_profit:.2%}
        Entry Price: {signal.entry_price}
        Stop Loss: {signal.stop_loss}
        Take Profit: {signal.take_profit}
        Risk Level: {signal.risk_level.value}
        Timeframe: {signal.timeframe}
        AI Analysis: {signal.ai_analysis.get('ai_reasoning', 'N/A') if signal.ai_analysis else 'N/A'}
        ==============================
        """)
    
    def _calculate_position_size(self, signal: TradingSignal) -> float:
        """Calculate position size for signal"""
        # Get risk parameters from strategy
        strategy = self.strategies.get(signal.strategy_name)
        if strategy:
            risk_params = strategy.get_risk_parameters()
            max_position = risk_params.get('max_position_size', 0.02)
        else:
            max_position = 0.02  # Default 2%
        
        # Adjust based on confidence
        position_size = max_position * signal.confidence
        
        return position_size
    
    async def start_trading(self):
        """Start the trading engine"""
        if self.is_running:
            self.logger.warning("Trading engine already running")
            return
        
        try:
            await self.initialize()
            
            self.is_running = True
            self.logger.info("🚀 TRADING ENGINE STARTED 🚀")
            
            # Start monitoring tasks
            asyncio.create_task(self._monitor_positions())
            asyncio.create_task(self._periodic_status_report())
            
            # Keep the engine running
            while self.is_running:
                await asyncio.sleep(1)
                
        except Exception as e:
            self.logger.error(f"Trading engine error: {e}")
            await self.stop_trading()
    
    async def stop_trading(self):
        """Stop the trading engine"""
        self.logger.info("Stopping trading engine...")
        
        self.is_running = False
        
        # Disconnect WebSockets
        if self.websocket_manager:
            await self.websocket_manager.disconnect_all()
        
        # Close any open positions (would implement position closing logic)
        
        self.logger.info("Trading engine stopped")
    
    async def _monitor_positions(self):
        """Monitor open positions for risk management"""
        while self.is_running:
            try:
                # Get current prices for all symbols
                current_prices = {
                    symbol: data.current_price 
                    for symbol, data in self.market_data_cache.items()
                }
                
                # Monitor positions
                positions_to_close = await self.risk_manager.monitor_positions(current_prices)
                
                # Close positions if needed
                for position_id, reason in positions_to_close:
                    symbol = position_id.split('_')[0]  # Extract symbol from position_id
                    current_price = current_prices.get(symbol, Decimal('0'))
                    
                    if current_price > 0:
                        self.risk_manager.close_position(position_id, current_price, reason)
                        self.logger.info(f"Position closed: {position_id} - Reason: {reason}")
                
                await asyncio.sleep(5)  # Check every 5 seconds
                
            except Exception as e:
                self.logger.error(f"Error monitoring positions: {e}")
                await asyncio.sleep(10)
    
    async def _periodic_status_report(self):
        """Generate periodic status reports"""
        while self.is_running:
            try:
                await asyncio.sleep(300)  # Every 5 minutes
                
                # Generate status report
                status = self.get_status()
                self.logger.info(f"""
                === TRADING ENGINE STATUS ===
                Uptime: {status['uptime']}
                Signals Today: {status['signals_generated_today']}
                Active Positions: {status['active_positions']}
                Total P&L: ${status['total_pnl']:.2f}
                Available Capital: ${status['available_capital']:.2f}
                Symbols Tracked: {status['symbols_tracked']}
                WebSocket Status: {status['websocket_status']}
                =============================
                """)
                
            except Exception as e:
                self.logger.error(f"Error generating status report: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current engine status"""
        websocket_status = "DISCONNECTED"
        if self.websocket_manager:
            connection_statuses = self.websocket_manager.get_connection_status()
            connected_count = sum(1 for status in connection_statuses.values() if status.value == "connected")
            websocket_status = f"{connected_count}/{len(connection_statuses)} connected"
        
        risk_metrics = self.risk_manager.get_risk_metrics() if self.risk_manager else {}
        
        return {
            'is_running': self.is_running,
            'uptime': str(datetime.now() - self.last_signal_time) if hasattr(self, 'start_time') else "Unknown",
            'signals_generated_today': self.signals_generated_today,
            'active_positions': len(self.active_signals),
            'total_pnl': risk_metrics.get('total_pnl', 0),
            'available_capital': risk_metrics.get('available_capital', 0),
            'symbols_tracked': len(self.market_data_cache),
            'websocket_status': websocket_status,
            'enabled_strategies': [s.value for s in self.config.enabled_strategies],
            'enabled_exchanges': [e.value for e in self.config.enabled_exchanges]
        }
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get detailed performance metrics"""
        processor_stats = self.data_processor.get_performance_stats() if self.data_processor else {}
        risk_metrics = self.risk_manager.get_risk_metrics() if self.risk_manager else {}
        
        strategy_stats = {}
        for strategy_type, strategy in self.strategies.items():
            if hasattr(strategy, 'get_strategy_stats'):
                strategy_stats[strategy_type.value] = strategy.get_strategy_stats()
        
        return {
            'trading_engine': self.get_status(),
            'data_processor': processor_stats,
            'risk_management': risk_metrics,
            'strategies': strategy_stats,
            'signal_history_count': len(self.signal_history)
        }
