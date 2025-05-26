import asyncio
import re
from typing import Any, Dict, Optional, Protocol

from src.ai.llm_factory import LLMFactory
from src.ai.llm_providers import ILLMProvider, LLMAbstraction
from src.mcp_server.adapters import IMCPAdapter


class MultimodalAnalyzer:
    def __init__(self, llm_factory: LLMFactory, mcp_orchestrator: IMCPAdapter):
        self.llm_provider = llm_factory.get_llm_abstraction(primary_llm="gemini") # Use LLMAbstraction
        self.mcp_orchestrator = mcp_orchestrator

    async def analyze_opportunity(self, market_data: dict, news_data: str, sentiment_data: dict) -> dict:
        """
        Analiza una oportunidad de trading combinando análisis técnico, de sentimiento y de noticias.

        Args:
            market_data (dict): Datos de mercado para análisis técnico.
            news_data (str): Datos de noticias para análisis de texto.
            sentiment_data (dict): Datos de sentimiento para análisis de sentimiento.

        Returns:
            dict: Un diccionario con el scoring unificado de la oportunidad.
        """
        # Análisis técnico usando MCP
        technical_result = await self.mcp_orchestrator.call("crypto-indicators", market_data)
        technical_score = float(technical_result.get("data", 0.0)) if isinstance(technical_result, dict) and "data" in technical_result else 0.0
        # Asumiendo que el MCP devuelve un diccionario con una clave 'data' que contiene el score.
        # Si el MCP devuelve directamente el score, se ajustaría a:
        # technical_score = float(technical_result) if isinstance(technical_result, (int, float)) else 0.0


        # Análisis de sentimiento usando MCP
        sentiment_result = await self.mcp_orchestrator.call("crypto-sentiment", sentiment_data)
        sentiment_score = float(sentiment_result.get("data", 0.0)) if isinstance(sentiment_result, dict) and "data" in sentiment_result else 0.0
        # Si el MCP devuelve directamente el score, se ajustaría a:
        # sentiment_score = float(sentiment_result) if isinstance(sentiment_result, (int, float)) else 0.0

        # Análisis de noticias usando LLM
        news_analysis_prompt = f"Analiza las siguientes noticias y proporciona un score de impacto en el mercado (0-100) y un resumen conciso: {news_data}"
        news_llm_response = await self.llm_provider.generate_text(news_analysis_prompt, config={}) # Pasar config vacío
        
        # Parsear la respuesta del LLM para obtener el score de noticias.
        # Esto es un placeholder y necesitaría una lógica de parsing más robusta.
        news_score = self._parse_news_score(news_llm_response)

        # Combinar scores en un scoring unificado.
        # Esta es una lógica de combinación simple y puede ser más compleja.
        unified_score = self._combine_scores(technical_score, sentiment_score, news_score)

        return {
            "unified_score": unified_score,
            "technical_score": technical_score,
            "sentiment_score": sentiment_score,
            "news_score": news_score,
            "news_analysis_summary": news_llm_response # Incluir la respuesta completa del LLM para depuración/auditoría
        }

    def _parse_news_score(self, llm_response: str) -> float:
        """
        Parsea la respuesta del LLM para extraer el score de noticias.
        Esta es una implementación básica y debería ser mejorada para robustez.
        """
        try:
            # Buscar un patrón como "score: XX" o "Score: XX"
            import re
            match = re.search(r'[Ss]core:\s*(\d+)', llm_response)
            if match:
                return float(match.group(1))
            return 50.0 # Valor por defecto si no se encuentra el score
        except Exception as e:
            print(f"Error al parsear el score de noticias del LLM: {e}")
            return 50.0 # Valor por defecto en caso de error

    def _combine_scores(self, technical: float, sentiment: float, news: float) -> float:
        """
        Combina los scores individuales en un score unificado.
        Esta es una lógica de combinación simple y puede ser ajustada.
        """
        # Ponderaciones de ejemplo, pueden ser ajustadas o configurables
        weight_technical = 0.4
        weight_sentiment = 0.3
        weight_news = 0.3
        
        unified = (technical * weight_technical +
                   sentiment * weight_sentiment +
                   news * weight_news)
        return unified

# Ejemplo de uso (para pruebas, no parte del código de producción)
async def main():
    # Mock de LLMFactory y MCPOrchestrator para demostración
    class MockLLMProvider(ILLMProvider): # Heredar de ILLMProvider
        async def generate_text(self, prompt: str, config: Dict[str, Any]) -> str: # Añadir config
            if "Analyze news" in prompt:
                return "Análisis de noticias completado. Score: 75. Resumen: Las noticias son mayormente positivas para el mercado."
            return "Respuesta LLM genérica."

    class MockLLMFactory(LLMFactory): # Heredar de LLMFactory
        def get_llm_abstraction(self, primary_llm: str, fallback_llm: Optional[str] = None) -> LLMAbstraction:
            # Retornar una instancia de LLMAbstraction con el mock provider
            return LLMAbstraction(primary_provider=MockLLMProvider())

    class MockMCPOrchestrator(IMCPAdapter): # Heredar de IMCPAdapter
        async def call(self, tool_name: str, args: dict): # Cambiar a 'call'
            if tool_name == "crypto-indicators":
                return 80.0 # Score técnico de ejemplo
            elif tool_name == "crypto-sentiment":
                return 65.0 # Score de sentimiento de ejemplo
            return 0.0

    llm_factory_mock = MockLLMFactory()
    mcp_orchestrator_mock = MockMCPOrchestrator()

    analyzer = MultimodalAnalyzer(llm_factory_mock, mcp_orchestrator_mock)

    market_data_example = {"price": 100, "volume": 1000}
    news_data_example = "La empresa X anuncia nuevas asociaciones y un aumento en sus ingresos."
    sentiment_data_example = {"positive": 0.7, "negative": 0.1, "neutral": 0.2}

    result = await analyzer.analyze_opportunity(market_data_example, news_data_example, sentiment_data_example)
    print(f"Resultado del análisis multimodal: {result}")

if __name__ == "__main__":
    asyncio.run(main())
