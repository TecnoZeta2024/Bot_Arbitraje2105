import logging
from typing import Dict, Any, List
from .base_adapter import BaseMCPAdapter
from src.mcp_server.schemas import Tool, Resource, ToolParameter, CryptoSentimentRequest, CryptoSentimentResponse, ResourceSchema

logger = logging.getLogger(__name__)

class CryptoSentimentAdapter(BaseMCPAdapter):
    def __init__(self, config: Dict[str, Any]):
        super().__init__("crypto-sentiment", "Adaptador para análisis de sentimiento criptográfico", config)

    def get_tools(self) -> List[Tool]:
        return [
            Tool(
                name="get_sentiment",
                description="Obtiene el sentimiento criptográfico para una moneda específica.",
                parameters=[
                    ToolParameter(name="symbol", type="string", description="Símbolo de la criptomoneda (ej. 'BTC', 'ETH').", optional=False)
                ],
                output_schema=CryptoSentimentResponse.schema()
            )
        ]

    def get_resources(self) -> List[Resource]:
        return []

    async def handle_tool_request(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        logger.info(f"Manejando solicitud de herramienta CryptoSentiment: {tool_name} con parámetros {parameters}")
        if tool_name == "get_sentiment":
            request = CryptoSentimentRequest(**parameters)
            response = await self._get_sentiment(request)
            return response.dict() # Convertir a diccionario
        else:
            raise ValueError(f"Herramienta CryptoSentiment no soportada: {tool_name}")

    async def handle_resource_request(self, uri: str, query_params: Dict[str, Any]) -> Any:
        raise NotImplementedError("Este adaptador no proporciona recursos.")

    async def _get_sentiment(self, request: CryptoSentimentRequest) -> CryptoSentimentResponse:
        """
        Simula la obtención del sentimiento criptográfico para una moneda específica.
        En una implementación real, esto interactuaría con una API de análisis de sentimiento.
        """
        # Lógica simulada para obtener el sentimiento
        sentiment_score = 0.75  # Ejemplo: 0.75 para sentimiento positivo
        sentiment_label = "positive"

        if request.symbol == "BTC":
            sentiment_score = 0.85
            sentiment_label = "very_positive"
        elif request.symbol == "ETH":
            sentiment_score = 0.70
            sentiment_label = "positive"
        elif request.symbol == "XRP":
            sentiment_score = 0.40
            sentiment_label = "neutral"
        elif request.symbol == "DOGE":
            sentiment_score = 0.20
            sentiment_label = "negative"

        return CryptoSentimentResponse(
            symbol=request.symbol,
            sentiment_score=sentiment_score,
            sentiment_label=sentiment_label,
            source="simulated_news_and_social_media"
        )
