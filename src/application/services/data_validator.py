from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Union

from pydantic import ValidationError

from src.domain.data_models import MarketDataUnified, OpportunityUnified
from src.utils.logger import get_logger

# Inicializar logger para la validación de datos
data_validation_logger = get_logger('data_validation')

class DataValidator:
    """
    Servicio para validar datos unificados de mercado y oportunidades.
    Aplica reglas de negocio para asegurar la integridad y consistencia de los datos.
    """

    def validate_market_data(self, data: MarketDataUnified) -> MarketDataUnified:
        """
        Valida un objeto MarketDataUnified según las reglas de negocio.
        """
        if not isinstance(data.price, Decimal) or data.price <= 0:
            raise ValueError(f"Precio inválido: {data.price}. Debe ser un Decimal positivo.")
        if not isinstance(data.volume, Decimal) or data.volume <= 0:
            raise ValueError(f"Volumen inválido: {data.volume}. Debe ser un Decimal positivo.")
        if data.timestamp.timestamp() > datetime.now().timestamp():
            raise ValueError(f"Timestamp inválido: {data.timestamp}. No puede ser en el futuro.")
        # Integridad de datos estructurales (Pydantic ya lo maneja para campos no Optional)
        # Consistencia de tipos de datos (Pydantic ya lo maneja)
        return data

    def validate_opportunity_data(self, data: OpportunityUnified) -> OpportunityUnified:
        """
        Valida un objeto OpportunityUnified según las reglas de negocio.
        """
        if not isinstance(data.profit_percentage_net, Decimal) or data.profit_percentage_net <= 0:
            raise ValueError(f"Porcentaje de ganancia neta inválido: {data.profit_percentage_net}. Debe ser un Decimal positivo.")
        if not isinstance(data.capital_inicial, Decimal) or data.capital_inicial <= 0:
            raise ValueError(f"Capital inicial inválido: {data.capital_inicial}. Debe ser un Decimal positivo.")
        if not isinstance(data.capital_sugerido, Decimal) or data.capital_sugerido <= 0:
            raise ValueError(f"Capital sugerido inválido: {data.capital_sugerido}. Debe ser un Decimal positivo.")
        if data.timestamp_detected.timestamp() > datetime.now().timestamp():
            raise ValueError(f"Timestamp de detección inválido: {data.timestamp_detected}. No puede ser en el futuro.")
        
        for step in data.steps:
            if not isinstance(step.amount_in, Decimal) or step.amount_in <= 0:
                raise ValueError(f"Cantidad de entrada en paso {step.order} inválida: {step.amount_in}. Debe ser un Decimal positivo.")
            # Podríamos añadir más validaciones para los pasos si fuera necesario, como la consistencia de monedas.

        # Integridad de datos estructurales (Pydantic ya lo maneja para campos no Optional)
        # Consistencia de tipos de datos (Pydantic ya lo maneja)
        return data

    def validate_data_list(self, data_list: List[Union[MarketDataUnified, OpportunityUnified]]) -> List[Union[MarketDataUnified, OpportunityUnified]]:
        """
        Valida una lista de objetos MarketDataUnified o OpportunityUnified.
        Retorna solo los datos válidos.
        """
        valid_data = []
        for data in data_list:
            try:
                if isinstance(data, MarketDataUnified):
                    valid_data.append(self.validate_market_data(data))
                elif isinstance(data, OpportunityUnified):
                    valid_data.append(self.validate_opportunity_data(data))
                else:
                    data_validation_logger.warning(f"Tipo de dato desconocido para validación: {type(data)}. Dato: {data}")
                    continue # Continuar con el siguiente dato si el tipo es desconocido
            except (ValueError, ValidationError) as e:
                schema_type = type(data).__name__
                data_validation_logger.error(
                    f"Error de validación para el esquema {schema_type}. Razón: {e}. Datos originales: {data}"
                )
        return valid_data
