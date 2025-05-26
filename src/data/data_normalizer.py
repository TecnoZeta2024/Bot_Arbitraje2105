import logging
from decimal import ROUND_HALF_UP, Decimal, getcontext
from datetime import datetime
from typing import Optional, Any, Dict, List, Union
from src.domain.data_models import MarketDataUnified, OpportunityUnified, OpportunityStep
from src.application.services.data_validator import DataValidator

# Configurar la precisión decimal global
getcontext().prec = 28 # Precisión estándar para operaciones financieras

class DataNormalizer:
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.data_validator = DataValidator() # Instanciar el servicio de validación

    def normalize_ticker(self, raw_ticker_data: Dict[str, Any], source: str) -> Optional[MarketDataUnified]:
        """
        Normaliza los datos de un ticker de una fuente específica a un esquema unificado.

        Args:
            raw_ticker_data (dict): Datos brutos del ticker de la fuente.
            source (str): Nombre de la fuente (ej. 'binance', 'mobula').

        Returns:
            Optional[MarketDataUnified]: Datos del ticker normalizados y validados, o None si falla.
        """
        try:
            if source == 'binance':
                symbol = raw_ticker_data.get('s', '')
                timestamp_ms = raw_ticker_data.get('E')
                price = self._to_decimal(raw_ticker_data.get('c'))
                volume = self._to_decimal(raw_ticker_data.get('v'))
                close_price = self._to_decimal(raw_ticker_data.get('c'))

                if not all([symbol, price, volume, close_price]): # timestamp_ms puede ser None si se usa datetime.now()
                    self.logger.error(f"Datos obligatorios faltantes o inválidos para Binance MarketDataUnified: {raw_ticker_data}")
                    return None

                timestamp_dt = datetime.fromtimestamp(timestamp_ms / 1000) if timestamp_ms is not None else datetime.now()

                market_data = MarketDataUnified(
                    symbol=symbol,
                    timestamp=timestamp_dt,
                    price=price,
                    volume=volume,
                    quote_volume=self._to_decimal(raw_ticker_data.get('q')),
                    high_price=self._to_decimal(raw_ticker_data.get('h')),
                    low_price=self._to_decimal(raw_ticker_data.get('l')),
                    open_price=self._to_decimal(raw_ticker_data.get('o')),
                    close_price=close_price,
                    bid_price=self._to_decimal(raw_ticker_data.get('b')),
                    bid_qty=self._to_decimal(raw_ticker_data.get('B')),
                    ask_price=self._to_decimal(raw_ticker_data.get('a')),
                    ask_qty=self._to_decimal(raw_ticker_data.get('A')),
                    source=source,
                    price_change_24h=self._to_decimal(raw_ticker_data.get('p')),
                    price_change_percentage_24h=self._to_decimal(raw_ticker_data.get('P')),
                    market_cap=self._to_decimal(raw_ticker_data.get('mkCap', '0')), # Asumiendo un campo para market_cap si existe
                    rank=raw_ticker_data.get('rank', None), # Asumiendo un campo para rank si existe
                    number_of_trades=raw_ticker_data.get('n')
                )
            
            elif source == 'mobula':
                symbol = raw_ticker_data.get('symbol', '')
                timestamp_raw = raw_ticker_data.get('timestamp')
                price = self._to_decimal(raw_ticker_data.get('lastPrice'))
                volume = self._to_decimal(raw_ticker_data.get('volume24h'))
                close_price = self._to_decimal(raw_ticker_data.get('lastPrice'))

                if not all([symbol, price, volume, close_price]): # timestamp_raw puede ser None si se usa datetime.now()
                    self.logger.error(f"Datos obligatorios faltantes o inválidos para Mobula MarketDataUnified: {raw_ticker_data}")
                    return None

                timestamp_dt = None
                if timestamp_raw is not None:
                    if len(str(timestamp_raw)) == 13:
                        timestamp_dt = datetime.fromtimestamp(timestamp_raw / 1000)
                    else:
                        timestamp_dt = datetime.fromtimestamp(timestamp_raw)
                else:
                    timestamp_dt = datetime.now()

                market_data = MarketDataUnified(
                    symbol=symbol,
                    timestamp=timestamp_dt,
                    price=price,
                    volume=volume,
                    quote_volume=self._to_decimal(raw_ticker_data.get('quoteVolume24h')),
                    high_price=self._to_decimal(raw_ticker_data.get('highPrice')),
                    low_price=self._to_decimal(raw_ticker_data.get('lowPrice')),
                    open_price=self._to_decimal(raw_ticker_data.get('openPrice')),
                    close_price=close_price,
                    bid_price=self._to_decimal(raw_ticker_data.get('bidPrice')),
                    bid_qty=self._to_decimal(raw_ticker_data.get('bidQty')),
                    ask_price=self._to_decimal(raw_ticker_data.get('askPrice')),
                    ask_qty=self._to_decimal(raw_ticker_data.get('askQty')),
                    source=source,
                    price_change_24h=self._to_decimal(raw_ticker_data.get('priceChange24h', '0')), # Asumiendo un campo para price_change_24h
                    price_change_percentage_24h=self._to_decimal(raw_ticker_data.get('priceChangePercent24h', '0')), # Asumiendo un campo para price_change_percentage_24h
                    market_cap=self._to_decimal(raw_ticker_data.get('marketCap')),
                    rank=raw_ticker_data.get('rank'),
                    number_of_trades=raw_ticker_data.get('numberOfTrades', None) # Asumiendo un campo para number_of_trades
                )
            else:
                self.logger.warning(f"Fuente de datos desconocida: {source}")
                return None

            validated_data = self.data_validator.validate_market_data(market_data)
            return validated_data
        except Exception as e:
            self.logger.error(f"Error al normalizar o validar datos de mercado de {source}: {e}, Datos: {raw_ticker_data}")
            return None

    def normalize_opportunity(self, raw_opportunity_data: Dict[str, Any]) -> Optional[OpportunityUnified]:
        """
        Normaliza los datos de una oportunidad de arbitraje a un esquema unificado.
        """
        try:
            opportunity_id = raw_opportunity_data.get('opportunity_id', '')
            cycle = raw_opportunity_data.get('cycle', '')
            profit_percentage_gross = self._to_decimal(raw_opportunity_data.get('profit_percentage_gross'))
            profit_percentage_net = self._to_decimal(raw_opportunity_data.get('profit_percentage_net'))
            capital_inicial = self._to_decimal(raw_opportunity_data.get('capital_inicial'))
            capital_sugerido = self._to_decimal(raw_opportunity_data.get('capital_sugerido'))
            timestamp_detected_raw = raw_opportunity_data.get('timestamp_detected')
            
            if not all([opportunity_id, cycle, profit_percentage_gross, profit_percentage_net,
                        capital_inicial, capital_sugerido, timestamp_detected_raw is not None]):
                self.logger.error(f"Datos de oportunidad incompletos o inválidos: {raw_opportunity_data}")
                return None

            timestamp_detected = datetime.fromisoformat(str(timestamp_detected_raw))

            steps_data = raw_opportunity_data.get('steps', [])
            parsed_steps = []
            for step in steps_data:
                try:
                    # Asegurar que los valores numéricos en los pasos también sean Decimal
                    step['price'] = self._to_decimal(step.get('price'))
                    step['amount'] = self._to_decimal(step.get('amount'))
                    step['fee'] = self._to_decimal(step.get('fee'))
                    parsed_steps.append(OpportunityStep(**step))
                except Exception as step_e:
                    self.logger.error(f"Error al parsear paso de oportunidad: {step_e}, Paso: {step}")
                    return None # Fallar si un paso es inválido

            opportunity_data = OpportunityUnified(
                opportunity_id=opportunity_id,
                cycle=cycle,
                profit_percentage_gross=profit_percentage_gross,
                profit_percentage_net=profit_percentage_net,
                steps=parsed_steps,
                capital_inicial=capital_inicial,
                capital_sugerido=capital_sugerido,
                timestamp_detected=timestamp_detected
            )
            validated_opportunity = self.data_validator.validate_opportunity_data(opportunity_data)
            return validated_opportunity
        except Exception as e:
            self.logger.error(f"Error al normalizar o validar datos de oportunidad: {e}, Datos: {raw_opportunity_data}")
            return None

    def _to_decimal(self, value: Any) -> Decimal:
        """
        Convierte un valor a Decimal, manejando None o errores de conversión.
        Siempre retorna un Decimal, usando Decimal('0') como valor por defecto.
        """
        if value is None or str(value).strip() == '':
            return Decimal('0')
        try:
            return Decimal(str(value))
        except Exception as e:
            self.logger.error(f"Error al convertir a Decimal: {value}, Error: {e}. Retornando Decimal('0').")
            return Decimal('0')

    # La función validate_data ya no es necesaria si usamos DataValidator
    # def validate_data(self, unified_data: dict) -> bool:
    #     """
    #     Valida la integridad de los datos unificados.
    #     """
    #     pass # Esta función será reemplazada por el uso de DataValidator

    def detect_anomalies(self, data_stream: List[Any], threshold_multiplier: float = 3.0) -> List[Any]:
        """
        Detecta anomalías en un flujo de datos (ej. precios, volúmenes).
        Este es un ejemplo simple basado en la desviación estándar.

        Args:
            data_stream (list): Lista de valores numéricos (ej. precios de cierre).
            threshold_multiplier (float): Multiplicador para la desviación estándar para definir el umbral.

        Returns:
            list: Lista de tuplas (índice, valor) de las anomalías detectadas.
        """
        if not data_stream or len(data_stream) < 2:
            return []

        decimal_stream = [val for val in (self._to_decimal(x) for x in data_stream) if val is not None]
        if not decimal_stream or len(decimal_stream) < 2:
            return []

        mean = sum(decimal_stream) / Decimal(len(decimal_stream))
        
        variance = sum([(x - mean) ** 2 for x in decimal_stream]) / Decimal(len(decimal_stream))
        if variance < 0:
            variance = Decimal(0)
        
        std_dev = variance.sqrt()

        anomalies = []
        for i, value in enumerate(data_stream):
            dec_value = self._to_decimal(value)
            if dec_value is None:
                continue

            threshold_decimal = self._to_decimal(threshold_multiplier)
            if threshold_decimal is None:
                self.logger.error(f"Error: threshold_multiplier ({threshold_multiplier}) no pudo ser convertido a Decimal.")
                continue

            if abs(dec_value - mean) > threshold_decimal * std_dev:
                anomalies.append((i, dec_value))
                self.logger.warning(f"Anomalía detectada en el índice {i}: {dec_value} (fuera de {threshold_multiplier} * std_dev)")
        return anomalies

    def handle_decimal_precision(self, value: Any, precision: int = 8) -> Optional[Decimal]:
        """
        Asegura la precisión decimal de un valor.

        Args:
            value: El valor a ajustar.
            precision (int): Número de decimales deseados.

        Returns:
            Decimal: El valor ajustado a la precisión especificada.
        """
        if value is None:
            return None
        try:
            dec_value = self._to_decimal(value)
            if dec_value is None:
                return None
            
            local_context = getcontext().copy()
            local_context.prec = precision + 4
            
            quantize_pattern = Decimal('1e-' + str(precision))
            return dec_value.quantize(quantize_pattern, rounding=ROUND_HALF_UP, context=local_context)
        except Exception as e:
            self.logger.error(f"Error al manejar la precisión decimal para {value} con precisión {precision}: {e}")
            return None
