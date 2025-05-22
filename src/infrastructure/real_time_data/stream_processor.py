"""
Real-Time Data Stream Processor
Procesamiento eficiente de datos en tiempo real con patrones de suscripción
"""

import asyncio
from typing import Dict, List, Callable, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
import logging
from collections import defaultdict, deque
import statistics

from ..domain.entities.market_data import MarketData


@dataclass
class PerformanceMetrics:
    """Métricas de rendimiento del procesador de datos."""
    messages_processed: int = 0
    processing_time_avg: float = 0.0
    processing_times: deque = field(default_factory=lambda: deque(maxlen=1000))
    errors_count: int = 0
    last_update: datetime = field(default_factory=datetime.now)


class SpecializedProcessor:
    """Procesador especializado para tipos específicos de datos."""
    
    def __init__(self, name: str):
        self.name = name
        self.logger = logging.getLogger(f"SpecializedProcessor.{name}")
    
    async def process(self, data: Dict[str, Any]) -> Optional[MarketData]:
        """Procesa datos específicos del tipo."""
        raise NotImplementedError


class PriceProcessor(SpecializedProcessor):
    """Procesador especializado para datos de precios."""
    
    def __init__(self):
        super().__init__("Price")
        self.price_history = defaultdict(deque)
    
    async def process(self, data: Dict[str, Any]) -> Optional[MarketData]:
        """Procesa datos de precio en tiempo real."""
        try:
            symbol = data.get('symbol', '').upper()
            price = float(data.get('price', 0))
            
            if not symbol or price <= 0:
                return None
            
            # Mantener historial de precios
            self.price_history[symbol].append(price)
            if len(self.price_history[symbol]) > 100:
                self.price_history[symbol].popleft()
            
            # Calcular estadísticas básicas
            prices = list(self.price_history[symbol])
            price_change_24h = 0.0
            if len(prices) > 1:
                price_change_24h = ((price - prices[0]) / prices[0]) * 100
            
            market_data = MarketData(
                symbol=symbol,
                price=price,
                volume=data.get('volume', 0.0),
                timestamp=datetime.now(),
                bid_price=data.get('bid', price),
                ask_price=data.get('ask', price),
                high_24h=max(prices) if prices else price,
                low_24h=min(prices) if prices else price,
                price_change_24h=price_change_24h
            )
            
            self.logger.debug(f"Processed price data for {symbol}: ${price}")
            return market_data
            
        except Exception as e:
            self.logger.error(f"Error processing price data: {e}")
            return None


class OrderBookProcessor(SpecializedProcessor):
    """Procesador especializado para datos de order book."""
    
    def __init__(self):
        super().__init__("OrderBook")
        self.order_books = defaultdict(dict)
    
    async def process(self, data: Dict[str, Any]) -> Optional[MarketData]:
        """Procesa datos del order book."""
        try:
            symbol = data.get('symbol', '').upper()
            
            if not symbol:
                return None
            
            # Procesar bids y asks
            bids = data.get('bids', [])
            asks = data.get('asks', [])
            
            if not bids or not asks:
                return None
            
            # Obtener mejores precios
            best_bid = float(bids[0][0]) if bids else 0.0
            best_ask = float(asks[0][0]) if asks else 0.0
            
            # Calcular spread
            spread = best_ask - best_bid if best_ask > best_bid else 0.0
            spread_pct = (spread / best_ask * 100) if best_ask > 0 else 0.0
            
            # Calcular liquidez total (primeros 10 niveles)
            bid_liquidity = sum(float(bid[1]) for bid in bids[:10])
            ask_liquidity = sum(float(ask[1]) for ask in asks[:10])
            
            market_data = MarketData(
                symbol=symbol,
                price=(best_bid + best_ask) / 2,
                volume=bid_liquidity + ask_liquidity,
                timestamp=datetime.now(),
                bid_price=best_bid,
                ask_price=best_ask,
                spread=spread,
                spread_percentage=spread_pct
            )
            
            self.logger.debug(f"Processed order book for {symbol}: spread {spread_pct:.4f}%")
            return market_data
            
        except Exception as e:
            self.logger.error(f"Error processing order book data: {e}")
            return None


class VolumeProcessor(SpecializedProcessor):
    """Procesador especializado para datos de volumen."""
    
    def __init__(self):
        super().__init__("Volume")
        self.volume_history = defaultdict(deque)
    
    async def process(self, data: Dict[str, Any]) -> Optional[MarketData]:
        """Procesa datos de volumen."""
        try:
            symbol = data.get('symbol', '').upper()
            volume = float(data.get('volume', 0))
            
            if not symbol or volume < 0:
                return None
            
            # Mantener historial de volumen
            self.volume_history[symbol].append(volume)
            if len(self.volume_history[symbol]) > 100:
                self.volume_history[symbol].popleft()
            
            # Calcular volumen promedio
            volumes = list(self.volume_history[symbol])
            avg_volume = statistics.mean(volumes) if volumes else volume
            volume_ratio = volume / avg_volume if avg_volume > 0 else 1.0
            
            market_data = MarketData(
                symbol=symbol,
                price=data.get('price', 0.0),
                volume=volume,
                timestamp=datetime.now(),
                volume_ratio=volume_ratio
            )
            
            self.logger.debug(f"Processed volume data for {symbol}: {volume:.2f} (ratio: {volume_ratio:.2f})")
            return market_data
            
        except Exception as e:
            self.logger.error(f"Error processing volume data: {e}")
            return None


class RealTimeDataProcessor:
    """
    Motor principal de procesamiento de datos en tiempo real.
    Implementa patrones de suscripción y agregación inteligente.
    """
    
    def __init__(self):
        self.logger = logging.getLogger("RealTimeDataProcessor")
        
        # Suscriptores por símbolo
        self.subscribers = defaultdict(list)
        
        # Procesadores especializados
        self.processors = {
            'price': PriceProcessor(),
            'orderbook': OrderBookProcessor(),
            'volume': VolumeProcessor()
        }
        
        # Agregación de datos por símbolo
        self.aggregated_data = defaultdict(dict)
        
        # Métricas de rendimiento
        self.metrics = PerformanceMetrics()
        
        # Control de flujo
        self.is_running = False
        self.processing_queue = asyncio.Queue()
        
        self.logger.info("RealTimeDataProcessor initialized")
    
    async def start(self):
        """Inicia el procesador de datos."""
        if self.is_running:
            return
        
        self.is_running = True
        self.logger.info("Starting real-time data processor")
        
        # Iniciar tareas de procesamiento
        asyncio.create_task(self._process_data_loop())
        asyncio.create_task(self._metrics_reporter_loop())
    
    async def stop(self):
        """Detiene el procesador de datos."""
        self.is_running = False
        self.logger.info("Stopping real-time data processor")
    
    def subscribe(self, symbol: str, callback: Callable[[MarketData], None]):
        """Suscribe un callback para recibir datos de un símbolo."""
        symbol = symbol.upper()
        self.subscribers[symbol].append(callback)
        self.logger.info(f"New subscriber for {symbol}, total: {len(self.subscribers[symbol])}")
    
    def unsubscribe(self, symbol: str, callback: Callable[[MarketData], None]):
        """Desuscribe un callback."""
        symbol = symbol.upper()
        if callback in self.subscribers[symbol]:
            self.subscribers[symbol].remove(callback)
            self.logger.info(f"Unsubscribed from {symbol}, remaining: {len(self.subscribers[symbol])}")
    
    async def process_raw_data(self, data_type: str, raw_data: Dict[str, Any]):
        """Procesa datos en bruto y los pone en cola."""
        await self.processing_queue.put((data_type, raw_data))
    
    async def _process_data_loop(self):
        """Loop principal de procesamiento de datos."""
        while self.is_running:
            try:
                # Obtener datos de la cola con timeout
                data_type, raw_data = await asyncio.wait_for(
                    self.processing_queue.get(), timeout=1.0
                )
                
                start_time = datetime.now()
                
                # Procesar con el procesador especializado
                if data_type in self.processors:
                    market_data = await self.processors[data_type].process(raw_data)
                    
                    if market_data:
                        await self._aggregate_and_notify(market_data)
                        
                        # Actualizar métricas
                        processing_time = (datetime.now() - start_time).total_seconds()
                        self._update_metrics(processing_time)
                
            except asyncio.TimeoutError:
                # Timeout normal, continuar
                continue
            except Exception as e:
                self.logger.error(f"Error in processing loop: {e}")
                self.metrics.errors_count += 1
    
    async def _aggregate_and_notify(self, market_data: MarketData):
        """Agrega datos y notifica a suscriptores."""
        symbol = market_data.symbol
        
        # Agregar datos por símbolo
        self.aggregated_data[symbol].update({
            'last_update': market_data.timestamp,
            'price': market_data.price,
            'volume': market_data.volume,
            'bid_price': market_data.bid_price,
            'ask_price': market_data.ask_price,
            'spread': getattr(market_data, 'spread', None),
            'volume_ratio': getattr(market_data, 'volume_ratio', None)
        })
        
        # Notificar a suscriptores
        for callback in self.subscribers[symbol]:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(market_data)
                else:
                    callback(market_data)
            except Exception as e:
                self.logger.error(f"Error notifying subscriber for {symbol}: {e}")
    
    def _update_metrics(self, processing_time: float):
        """Actualiza métricas de rendimiento."""
        self.metrics.messages_processed += 1
        self.metrics.processing_times.append(processing_time)
        
        # Calcular tiempo promedio
        if self.metrics.processing_times:
            self.metrics.processing_time_avg = statistics.mean(self.metrics.processing_times)
        
        self.metrics.last_update = datetime.now()
    
    async def _metrics_reporter_loop(self):
        """Reporta métricas periódicamente."""
        while self.is_running:
            try:
                await asyncio.sleep(60)  # Reportar cada minuto
                
                self.logger.info(
                    f"Data Processor Metrics - "
                    f"Messages: {self.metrics.messages_processed}, "
                    f"Avg Processing Time: {self.metrics.processing_time_avg:.4f}s, "
                    f"Errors: {self.metrics.errors_count}, "
                    f"Active Subscriptions: {sum(len(subs) for subs in self.subscribers.values())}"
                )
                
            except Exception as e:
                self.logger.error(f"Error in metrics reporter: {e}")
    
    def get_aggregated_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Obtiene datos agregados para un símbolo."""
        return self.aggregated_data.get(symbol.upper())
    
    def get_metrics(self) -> PerformanceMetrics:
        """Obtiene métricas de rendimiento."""
        return self.metrics
    
    def get_active_symbols(self) -> List[str]:
        """Obtiene lista de símbolos activos."""
        return list(self.aggregated_data.keys())
