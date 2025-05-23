"""
Servicio para interactuar con los informes de IA almacenados en Supabase.
"""

from typing import Any, Dict, List, Optional

from src.apis.supabase_client import SupabaseClient
from src.utils.logger import get_logger

logger = get_logger("ai_report_service")

class AIReportService:
    """
    Servicio para obtener y procesar informes de IA desde Supabase.
    """
    def __init__(self, supabase_client: SupabaseClient):
        """
        Inicializa el servicio con una instancia del cliente Supabase.
        
        Args:
            supabase_client: Instancia del cliente Supabase.
        """
        self.supabase_client = supabase_client
        logger.info("AIReportService initialized")

    def get_ai_reports(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Obtiene los informes de IA más recientes desde Supabase.
        
        Args:
            limit: Número máximo de informes a obtener.
            
        Returns:
            Lista de diccionarios, cada uno representando un informe.
        """
        try:
            # Assuming 'informes_ia' table exists and has 'generated_at' column
            reports = self.supabase_client.client.table("informes_ia").select("*").order("generated_at", desc=True).limit(limit).execute()
            logger.info(f"Fetched {len(reports.data if reports.data else [])} AI reports")
            return reports.data if reports.data else []
        except Exception as e:
            logger.error(f"Error fetching AI reports from Supabase: {e}", exc_info=e)
            return []
