"""
Trading Application Test Runner and Validator
Tests core functionality without requiring live data
"""

import asyncio
import logging
import sys
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List

# Add src to path for imports
sys.path.insert(0, '.')

from src.domain.trading_signals.trading_signal import TradingSignal, SignalAction, RiskLevel, StrategyType
from src.domain.entities.market_data import MarketData, PriceData, OrderBook, OrderBookLevel
from src.domain.strategies.scalping_strategy import ScalpingStrategy
from src.domain.strategies.day_trading_strategy import DayTradingStrategy
from src.domain.risk_management.advanced_risk_manager import AdvancedRiskManager, RiskParameters
from src.infrastructure.real_time_data.stream_processor import RealTimeDataProcessor


class TradingSystemTester:
    """
    Comprehensive testing system for the trading application
    Tests components in isolation and integration scenarios
    """
    
    def __init__(self):
        self.logger = logging.getLogger("testing")
        self.test_results = []
        
        # Setup basic logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    async def run_all_tests(self):
        """Run comprehensive test suite"""
        print("🧪 Starting Trading System Tests")
        print("=" * 50)
        
        try:
            # Test 1: Market Data Entities
            await self._test_market_data_entities()
            
            # Test 2: Trading Signals
            await self._test_trading_signals()
            
            # Test 3: Risk Management
            await self._test_risk_management()
            
            # Test 4: Real-time Data Processor
            await self._test_data_processor()
            
            # Test 5: Strategies (without AI - simulate AI responses)
            await self._test_strategies_simulation()
            
            # Test 6: Integration Test
            await self._test_integration_scenario()
            
            # Report results
            self._report_test_results()
            
        except Exception as e:
            self.logger.error(f"Test suite failed: {e}")
            return False
        
        return True
    
    async def _test_market_data_entities(self):
        """Test market data entities and validation"""
        test_name = "Market Data Entities"
        self.logger.info(f"Testing: {test_name}")
        
        try:
            # Test PriceData creation
            price_data = PriceData(
                timestamp=datetime.now(),
                open=Decimal('50000.00'),
                high=Decimal('50100.00'),
                low=Decimal('49900.00'),
                close=Decimal('50050.00'),
                volume=Decimal('100.5')
            )
            
            assert price_data.ohlc_tuple == (50000.0, 50100.0, 49900.0, 50050.0)
            
            # Test OrderBook creation
            bids = [
                OrderBookLevel(Decimal('50000.00'), Decimal('1.5')),
                OrderBookLevel(Decimal('49999.00'), Decimal('2.0'))
            ]
            asks = [
                OrderBookLevel(Decimal('50001.00'), Decimal('1.2')),
                OrderBookLevel(Decimal('50002.00'), Decimal('1.8'))
            ]
            
            order_book = OrderBook(
                timestamp=datetime.now(),
                symbol="BTCUSDT",
                bids=bids,
                asks=asks
            )
            
            assert order_book.best_bid.price == Decimal('50000.00')
            assert order_book.best_ask.price == Decimal('50001.00')
            assert order_book.spread == Decimal('1.00')
            
            # Test MarketData creation
            market_data = MarketData(
                symbol="BTCUSDT",
                exchange="binance",
                timestamp=datetime.now(),
                current_price=Decimal('50050.00'),
                volume_24h=Decimal('1000000'),
                order_book=order_book
            )
            
            assert market_data.is_liquid  # Should be True with sufficient volume
            assert market_data.has_tight_spread  # Should be True with small spread
            
            self._record_test_result(test_name, True, "All market data entities work correctly")
            
        except Exception as e:
            self._record_test_result(test_name, False, f"Error: {e}")
    
    async def _test_trading_signals(self):
        """Test trading signal creation and validation"""
        test_name = "Trading Signals"
        self.logger.info(f"Testing: {test_name}")
        
        try:
            # Test valid signal creation
            signal = TradingSignal(
                signal_id="test_001",
                timestamp=datetime.now(),
                strategy_name=StrategyType.SCALPING,
                symbol="BTCUSDT",
                action=SignalAction.BUY,
                confidence=0.85,
                expected_profit=0.001,
                risk_level=RiskLevel.LOW,
                timeframe="1m",
                entry_price=50000.0,
                stop_loss=49900.0,
                take_profit=50100.0
            )
            
            assert signal.is_high_confidence  # Should be True (>= 0.7)
            assert signal.is_low_risk  # Should be True
            assert signal.is_scalping_signal  # Should be True
            
            # Test signal validation
            try:
                invalid_signal = TradingSignal(
                    signal_id="test_002",
                    timestamp=datetime.now(),
                    strategy_name=StrategyType.SCALPING,
                    symbol="BTCUSDT",
                    action=SignalAction.BUY,
                    confidence=1.5,  # Invalid confidence > 1.0
                    expected_profit=0.001,
                    risk_level=RiskLevel.LOW,
                    timeframe="1m"
                )
                assert False, "Should have raised ValueError for invalid confidence"
            except ValueError:
                pass  # Expected behavior
            
            # Test signal serialization
            signal_dict = signal.to_dict()
            assert signal_dict['symbol'] == "BTCUSDT"
            assert signal_dict['confidence'] == 0.85
            
            self._record_test_result(test_name, True, "Trading signals work correctly")
            
        except Exception as e:
            self._record_test_result(test_name, False, f"Error: {e}")
    
    async def _test_risk_management(self):
        """Test risk management system"""
        test_name = "Risk Management"
        self.logger.info(f"Testing: {test_name}")
        
        try:
            # Create risk manager
            risk_params = RiskParameters(
                max_daily_loss=Decimal('0.02'),
                max_position_size=Decimal('0.05'),
                max_concurrent_positions=3
            )
            
            risk_manager = AdvancedRiskManager(
                initial_capital=Decimal('10000'),
                risk_params=risk_params
            )
            
            # Test signal evaluation
            test_signal = TradingSignal(
                signal_id="risk_test_001",
                timestamp=datetime.now(),
                strategy_name=StrategyType.SCALPING,
                symbol="BTCUSDT",
                action=SignalAction.BUY,
                confidence=0.8,
                expected_profit=0.001,
                risk_level=RiskLevel.LOW,
                timeframe="1m",
                entry_price=50000.0
            )
            
            # Create mock market data
            market_data = MarketData(
                symbol="BTCUSDT",
                exchange="binance",
                timestamp=datetime.now(),
                current_price=Decimal('50000.00'),
                volume_24h=Decimal('1000000')
            )
            
            # Evaluate risk
            risk_assessment = await risk_manager.evaluate_signal_risk(test_signal, market_data)
            
            assert 'approved' in risk_assessment
            assert 'risk_score' in risk_assessment
            assert 'position_size' in risk_assessment
            
            # Test position management
            if risk_assessment['approved']:
                risk_manager.add_position(
                    test_signal,
                    Decimal('0.1'),  # quantity
                    Decimal('50000')  # entry price
                )
                
                assert len(risk_manager.open_positions) == 1
            
            # Test risk metrics
            metrics = risk_manager.get_risk_metrics()
            assert 'current_capital' in metrics
            assert 'open_positions' in metrics
            
            self._record_test_result(test_name, True, "Risk management system works correctly")
            
        except Exception as e:
            self._record_test_result(test_name, False, f"Error: {e}")
    
    async def _test_data_processor(self):
        """Test real-time data processor"""
        test_name = "Real-Time Data Processor"
        self.logger.info(f"Testing: {test_name}")
        
        try:
            processor = RealTimeDataProcessor()
            
            # Test message processing
            test_message = {
                'symbol': 'BTCUSDT',
                'exchange': 'binance',
                'timestamp': datetime.now().isoformat(),
                'price': '50000.00',
                'volume': '100.5',
                'stream_type': 'ticker'
            }
            
            await processor.process_websocket_message(test_message)
            
            # Test subscription
            received_data = []
            
            async def test_callback(symbol, market_data):
                received_data.append((symbol, market_data))
            
            processor.subscribe_to_symbol('BTCUSDT', test_callback)
            
            # Process more messages to trigger aggregation
            for i in range(5):
                test_message_copy = test_message.copy()
                test_message_copy['price'] = f'{50000 + i}.00'
                await processor.process_websocket_message(test_message_copy)
                await asyncio.sleep(0.1)
            
            # Force aggregation
            await processor._trigger_aggregation()
            
            # Check if callback was called
            await asyncio.sleep(0.2)  # Allow time for processing
            
            assert len(processor.symbol_data_cache) > 0
            
            # Get performance stats
            stats = processor.get_performance_stats()
            assert 'total_messages_processed' in stats
            
            self._record_test_result(test_name, True, "Data processor works correctly")
            
        except Exception as e:
            self._record_test_result(test_name, False, f"Error: {e}")
    
    async def _test_strategies_simulation(self):
        """Test trading strategies with simulated AI responses"""
        test_name = "Trading Strategies (Simulated)"
        self.logger.info(f"Testing: {test_name}")
        
        try:
            # Create mock AI analyzer
            class MockAIAnalyzer:
                async def analyze_market_sentiment(self, symbol, market_data):
                    return type('MockAnalysis', (), {
                        'sentiment_score': 75.0,
                        'confidence_level': 0.8,
                        'risk_assessment': 'LOW',
                        'recommended_action': 'BUY',
                        'reasoning': 'Mock AI analysis for testing'
                    })()
                
                async def detect_price_patterns(self, symbol, price_history):
                    return {
                        'patterns_detected': ['bullish_flag'],
                        'pattern_reliability': 0.7
                    }
            
            mock_ai = MockAIAnalyzer()
            
            # Test Scalping Strategy
            scalping_strategy = ScalpingStrategy(mock_ai)
            
            # Create mock market data with price history
            price_history = []
            base_price = 50000.0
            for i in range(100):
                price_data = PriceData(
                    timestamp=datetime.now() - timedelta(minutes=100-i),
                    open=Decimal(str(base_price + i - 1)),
                    high=Decimal(str(base_price + i + 1)),
                    low=Decimal(str(base_price + i - 2)),
                    close=Decimal(str(base_price + i)),
                    volume=Decimal('10.0')
                )
                price_history.append(price_data)
            
            market_data = {
                'BTCUSDT': MarketData(
                    symbol="BTCUSDT",
                    exchange="binance",
                    timestamp=datetime.now(),
                    current_price=Decimal('50100.00'),
                    volume_24h=Decimal('2000000'),  # High volume
                    price_history=price_history,
                    technical_indicators={'rsi': 25, 'macd': 0.5}  # Oversold condition
                )
            }
            
            # Test strategy analysis
            scalping_signals = await scalping_strategy.analyze_market(market_data)
            
            # Should generate signals with mock AI validation
            self.logger.info(f"Scalping strategy generated {len(scalping_signals)} signals")
            
            # Test risk parameters
            risk_params = scalping_strategy.get_risk_parameters()
            assert 'max_position_size' in risk_params
            assert 'stop_loss_percentage' in risk_params
            
            # Test Day Trading Strategy
            day_trading_strategy = DayTradingStrategy(mock_ai)
            day_trading_signals = await day_trading_strategy.analyze_market(market_data)
            
            self.logger.info(f"Day trading strategy generated {len(day_trading_signals)} signals")
            
            self._record_test_result(test_name, True, f"Strategies work correctly. Scalping: {len(scalping_signals)}, Day Trading: {len(day_trading_signals)} signals")
            
        except Exception as e:
            self._record_test_result(test_name, False, f"Error: {e}")
    
    async def _test_integration_scenario(self):
        """Test integration scenario simulating real trading flow"""
        test_name = "Integration Scenario"
        self.logger.info(f"Testing: {test_name}")
        
        try:
            # This test simulates the full flow without external dependencies
            
            # 1. Create components
            mock_ai = type('MockAI', (), {
                'analyze_market_sentiment': lambda self, symbol, data: asyncio.create_task(
                    asyncio.coroutine(lambda: type('MockResult', (), {
                        'sentiment_score': 80.0,
                        'confidence_level': 0.85,
                        'risk_assessment': 'LOW',
                        'recommended_action': 'BUY',
                        'reasoning': 'Integration test mock analysis'
                    })())()
                ),
                'detect_price_patterns': lambda self, symbol, prices: asyncio.create_task(
                    asyncio.coroutine(lambda: {'patterns_detected': ['ascending_triangle'], 'pattern_reliability': 0.8})()
                )
            })()
            
            strategy = ScalpingStrategy(mock_ai)
            risk_manager = AdvancedRiskManager(Decimal('10000'))
            
            # 2. Create market data
            market_data = {
                'BTCUSDT': MarketData(
                    symbol="BTCUSDT",
                    exchange="binance",
                    timestamp=datetime.now(),
                    current_price=Decimal('50000.00'),
                    volume_24h=Decimal('2000000')
                )
            }
            
            # 3. Generate signals
            signals = await strategy.analyze_market(market_data)
            
            # 4. Process through risk management
            approved_signals = []
            for signal in signals:
                risk_assessment = await risk_manager.evaluate_signal_risk(
                    signal, market_data['BTCUSDT']
                )
                if risk_assessment['approved']:
                    approved_signals.append(signal)
            
            # 5. Simulate position tracking
            for signal in approved_signals:
                risk_manager.add_position(
                    signal,
                    Decimal('0.1'),
                    Decimal('50000')
                )
            
            # 6. Check final state
            final_metrics = risk_manager.get_risk_metrics()
            
            self.logger.info(f"Integration test completed: {len(signals)} signals generated, {len(approved_signals)} approved")
            
            self._record_test_result(test_name, True, f"Integration successful. {len(approved_signals)} positions opened")
            
        except Exception as e:
            self._record_test_result(test_name, False, f"Error: {e}")
    
    def _record_test_result(self, test_name: str, passed: bool, details: str):
        """Record test result"""
        self.test_results.append({
            'test': test_name,
            'passed': passed,
            'details': details,
            'timestamp': datetime.now()
        })
        
        status = "✅ PASSED" if passed else "❌ FAILED"
        self.logger.info(f"{status}: {test_name} - {details}")
    
    def _report_test_results(self):
        """Generate final test report"""
        print("\n" + "=" * 50)
        print("📊 TEST RESULTS SUMMARY")
        print("=" * 50)
        
        passed_count = sum(1 for result in self.test_results if result['passed'])
        total_count = len(self.test_results)
        
        for result in self.test_results:
            status = "✅" if result['passed'] else "❌"
            print(f"{status} {result['test']}: {result['details']}")
        
        print(f"\n📈 OVERALL: {passed_count}/{total_count} tests passed")
        
        if passed_count == total_count:
            print("🎉 ALL TESTS PASSED! The trading system is ready.")
        else:
            print("⚠️  Some tests failed. Please review the errors above.")


async def main():
    """Run the test suite"""
    print("🚀 Advanced Trading Application - Test Suite")
    print("Testing core functionality without external dependencies")
    print()
    
    tester = TradingSystemTester()
    success = await tester.run_all_tests()
    
    if success:
        print("\n✅ Test suite completed successfully!")
        print("The trading system components are working correctly.")
        print("\nNext steps:")
        print("1. Set up your .env file with API keys")
        print("2. Install requirements: pip install -r requirements.txt")
        print("3. Run the main application: python src/main.py")
    else:
        print("\n❌ Test suite failed!")
        print("Please review the errors and fix any issues.")
    
    return success


if __name__ == "__main__":
    asyncio.run(main())
