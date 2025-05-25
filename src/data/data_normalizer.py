import logging
from decimal import Decimal, getcontext, ROUND_HALF_UP

# Configurar la precisión decimal global
getcontext().prec = 28 # Precisión estándar para operaciones financieras

class DataNormalizer:
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    def normalize_ticker(self, raw_ticker_data: dict, source: str) -> dict:
        """
        Normaliza los datos de un ticker de una fuente específica a un esquema unificado.

        Args:
            raw_ticker_data (dict): Datos brutos del ticker de la fuente.
            source (str): Nombre de la fuente (ej. 'binance', 'mobula').

        Returns:
            dict: Datos del ticker normalizados.
        """
        normalized_data = {
            "symbol": None,
            "bid_price": None,
            "ask_price": None,
            "last_price": None,
            "volume_24h": None,
            "timestamp": None,
            "source": source
        }

        if source == 'binance':
            normalized_data["symbol"] = raw_ticker_data.get('s')
            normalized_data["bid_price"] = self._to_decimal(raw_ticker_data.get('b'))
            normalized_data["ask_price"] = self._to_decimal(raw_ticker_data.get('a'))
            normalized_data["last_price"] = self._to_decimal(raw_ticker_data.get('c'))
            normalized_data["volume_24h"] = self._to_decimal(raw_ticker_data.get('v'))
            normalized_data["timestamp"] = raw_ticker_data.get('E') # Event time in milliseconds
        elif source == 'mobula':
            normalized_data["symbol"] = raw_ticker_data.get('symbol')
            normalized_data["bid_price"] = self._to_decimal(raw_ticker_data.get('bidPrice'))
            normalized_data["ask_price"] = self._to_decimal(raw_ticker_data.get('askPrice'))
            normalized_data["last_price"] = self._to_decimal(raw_ticker_data.get('lastPrice'))
            normalized_data["volume_24h"] = self._to_decimal(raw_ticker_data.get('volume24h'))
            normalized_data["timestamp"] = raw_ticker_data.get('timestamp') # Unix timestamp in seconds or milliseconds
        else:
            self.logger.warning(f"Fuente de datos desconocida: {source}")
            return {}

        # Validar y limpiar datos nulos o inválidos
        for key, value in normalized_data.items():
            if value is None and key not in ["bid_price", "ask_price", "last_price", "volume_24h"]:
                self.logger.warning(f"Dato faltante para {key} en {source} ticker: {raw_ticker_data}")
            elif isinstance(value, Decimal) and value < 0:
                self.logger.warning(f"Valor negativo para {key} en {source} ticker: {raw_ticker_data}")
                normalized_data[key] = None # O manejar de otra forma, ej. abs(value)

        return normalized_data

    def _to_decimal(self, value):
        """Convierte un valor a Decimal, manejando None o errores de conversión."""
        if value is None:
            return None
        try:
            return Decimal(str(value))
        except Exception as e:
            self.logger.error(f"Error al convertir a Decimal: {value}, Error: {e}")
            return None

    def validate_data(self, unified_data: dict) -> bool:
        """
        Valida la integridad de los datos unificados.

        Args:
            unified_data (dict): Datos normalizados a validar.

        Returns:
            bool: True si los datos son válidos, False en caso contrario.
        """
        if not unified_data:
            self.logger.error("Datos vacíos para validación.")
            return False

        required_fields = ["symbol", "timestamp", "source"]
        for field in required_fields:
            if unified_data.get(field) is None:
                self.logger.error(f"Campo requerido '{field}' faltante en datos unificados: {unified_data}")
                return False

        # Validar que los precios y volúmenes sean números positivos si existen
        numeric_fields = ["bid_price", "ask_price", "last_price", "volume_24h"]
        for field in numeric_fields:
            value = unified_data.get(field)
            if value is not None:
                if not isinstance(value, Decimal):
                    self.logger.error(f"Campo '{field}' no es Decimal: {value} en {unified_data}")
                    return False
                if value < 0:
                    self.logger.error(f"Campo '{field}' es negativo: {value} en {unified_data}")
                    return False
        
        # Ejemplo de validación de consistencia: bid_price <= ask_price
        bid = unified_data.get("bid_price")
        ask = unified_data.get("ask_price")
        if bid is not None and ask is not None and bid > ask:
            self.logger.error(f"Bid price ({bid}) es mayor que Ask price ({ask}) en {unified_data}")
            return False

        return True

    def detect_anomalies(self, data_stream: list, threshold_multiplier: float = 3.0) -> list:
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

        # Convertir a Decimal para cálculos precisos y filtrar None
        decimal_stream = [val for val in (self._to_decimal(x) for x in data_stream) if val is not None]
        if not decimal_stream or len(decimal_stream) < 2: # Asegurar al menos 2 puntos para std_dev
            return []

        # Calcular la media
        mean = sum(decimal_stream) / Decimal(len(decimal_stream))
        
        # Calcular la varianza y la desviación estándar
        # Asegurarse de que la varianza no sea negativa debido a errores de punto flotante
        variance = sum([(x - mean) ** 2 for x in decimal_stream]) / Decimal(len(decimal_stream))
        if variance < 0:
            variance = Decimal(0) # Evitar sqrt de números negativos
        
        std_dev = variance.sqrt()

        anomalies = []
        for i, value in enumerate(data_stream): # Iterar sobre el stream original para mantener el índice
            dec_value = self._to_decimal(value)
            if dec_value is None:
                continue # Saltar valores no numéricos

            threshold_decimal = self._to_decimal(threshold_multiplier)
            if threshold_decimal is None:
                self.logger.error(f"Error: threshold_multiplier ({threshold_multiplier}) no pudo ser convertido a Decimal.")
                continue # Saltar esta iteración si el umbral es inválido

            if abs(dec_value - mean) > threshold_decimal * std_dev:
                anomalies.append((i, dec_value))
                self.logger.warning(f"Anomalía detectada en el índice {i}: {dec_value} (fuera de {threshold_multiplier} * std_dev)")
        return anomalies

    def handle_decimal_precision(self, value, precision: int = 8):
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
            # Convertir a Decimal si no lo es
            dec_value = self._to_decimal(value)
            if dec_value is None:
                return None
            
            # Crear un contexto local para la precisión si es diferente de la global
            local_context = getcontext().copy()
            local_context.prec = precision + 4 # Un poco más de precisión para el redondeo
            
            # Redondear al número de decimales especificado
            # Usar ROUND_HALF_UP para el redondeo estándar
            quantize_pattern = Decimal('1e-' + str(precision))
            return dec_value.quantize(quantize_pattern, rounding=ROUND_HALF_UP, context=local_context)
        except Exception as e:
            self.logger.error(f"Error al manejar la precisión decimal para {value} con precisión {precision}: {e}")
            return None
