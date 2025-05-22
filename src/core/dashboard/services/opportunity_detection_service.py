import streamlit as st
import pandas as pd
from typing import List, Dict, Any

from src.core.detectar_oportunidades import (
    fetch_market_data, 
    find_opportunities, 
    send_opportunities_to_webhook,
    load_specific_cache_file,
    list_available_cache_files
)
from src.utils.config import settings
from src.apis.binance_client import BinanceClient
from src.apis.mobula_client import MobulaClient
from src.utils.logger import get_logger

logger = get_logger("opportunity_service")

class OpportunityDetectionService:
    def __init__(self, binance_client: BinanceClient, mobula_client: MobulaClient, settings):
        self.binance_client = binance_client
        self.mobula_client = mobula_client
        self.settings = settings

    def fetch_and_store_market_data(self, token_search_limit: int, use_cache: bool = False, cache_dir: str = "./cache"):
        """
        Fetches market data and stores it in the Streamlit session state.
        
        Args:
            token_search_limit (int): Maximum number of tokens to fetch from Mobula API.
            use_cache (bool): Whether to use cached data if available.
            cache_dir (str): Directory for cache files.
            
        Returns:
            bool: True if market data was successfully fetched, False otherwise.
        """
        if 'symbols' not in st.session_state or 'tickers' not in st.session_state:
            with st.spinner("Obteniendo datos del mercado..."):
                symbols, tickers = fetch_market_data(
                    self.binance_client, 
                    self.mobula_client, 
                    token_search_limit,
                    use_cache=use_cache,
                    cache_dir=cache_dir
                )
                if symbols and tickers:
                    st.session_state['symbols'] = symbols
                    st.session_state['tickers'] = tickers
                    st.success(f"Datos del mercado obtenidos: {len(symbols)} símbolos y {len(tickers)} tickers.")
                    st.write("Puede proceder a la búsqueda de oportunidades.")
                    return True
                else:
                    st.error("No se pudieron obtener los datos del mercado.")
                    return False
        else:
            st.info("Datos del mercado ya cargados. Puede proceder a la búsqueda de oportunidades.")
            return True
    
    def load_market_data_from_cache_file(self, cache_filepath: str):
        """
        Loads market data from a specific cache file and stores it in the Streamlit session state.
        
        Args:
            cache_filepath (str): Path to the cache file.
            
        Returns:
            bool: True if data was successfully loaded, False otherwise.
        """
        with st.spinner(f"Cargando datos de caché: {cache_filepath}"):
            symbols, tickers = load_specific_cache_file(cache_filepath)
            if symbols and tickers:
                st.session_state['symbols'] = symbols
                st.session_state['tickers'] = tickers
                st.success(f"Datos cargados desde caché: {len(symbols)} símbolos y {len(tickers)} tickers.")
                return True
            else:
                st.error("No se pudieron cargar los datos del archivo de caché.")
                return False

    def find_and_store_opportunities(
        self, 
        umbral_rentabilidad: float, 
        capital_inicial: float, 
        fees_percentage: List[float] = None,
        use_cache: bool = False,
        cache_filepath: str = None,
        cache_dir: str = "./cache"
    ):
        """
        Finds triangular arbitrage opportunities and stores them in the Streamlit session state.
        
        Args:
            umbral_rentabilidad (float): Minimum profitability threshold in percentage.
            capital_inicial (float): Initial capital suggested for operation.
            fees_percentage (List[float], optional): List of fee percentages for each step.
            use_cache (bool): Whether to use cached market data.
            cache_filepath (str): Specific cache file to use if provided.
            cache_dir (str): Directory for cache files.
        
        Returns:
            List[Dict[str, Any]]: List of found opportunities.
        """
        logger.info("OpportunityDetectionService.find_and_store_opportunities called.")
        
        # Si se proporcionó un archivo de caché específico, cargarlo
        if cache_filepath:
            logger.info(f"Using specific cache file: {cache_filepath}")
            self.load_market_data_from_cache_file(cache_filepath)
        
        # Si no hay datos en session_state o si se solicita uso de caché, intentar obtener datos
        if 'symbols' not in st.session_state or 'tickers' not in st.session_state:
            success = self.fetch_and_store_market_data(
                token_search_limit=400,  # Default value
                use_cache=use_cache,
                cache_dir=cache_dir
            )
            if not success:
                logger.warning("Failed to fetch market data.")
                return []
        
        # Ahora que tenemos datos, buscar oportunidades
        if 'symbols' in st.session_state and 'tickers' in st.session_state:
            symbols = st.session_state['symbols']
            tickers = st.session_state['tickers']

            with st.spinner("Buscando oportunidades..."):
                # Apply filters from session state if available
                params = st.session_state.get('detection_params', {})
                
                # Filter symbols if include_base_coins is specified
                filtered_symbols = symbols
                if params.get('include_base_coins'):
                    base_coins = params.get('include_base_coins')
                    filtered_symbols = [
                        symbol for symbol in symbols 
                        if any(symbol.startswith(coin) or symbol.endswith(coin) for coin in base_coins)
                    ]
                    st.info(f"Filtrados {len(filtered_symbols)} de {len(symbols)} símbolos basados en monedas base seleccionadas.")
                
                # Limit max pairs to check if specified
                if params.get('max_pairs') and params.get('max_pairs') < 1000000:
                    # Simple approach: just limit the number of symbols
                    max_symbols = int((params.get('max_pairs') * 3) ** (1/3)) + 1
                    if max_symbols < len(filtered_symbols):
                        filtered_symbols = filtered_symbols[:max_symbols]
                        st.info(f"Limitando a {max_symbols} símbolos para respetar el límite de combinaciones.")
                
                # Use fees from parameters
                if fees_percentage is None:
                    fees_percentage = [0.1, 0.1, 0.1]  # Default
                
                opportunities = find_opportunities(
                    filtered_symbols, 
                    tickers, 
                    umbral_rentabilidad, 
                    capital_inicial,
                    fees_percentage
                )

                logger.info(f"find_opportunities returned {len(opportunities)} opportunities.")

                if opportunities:
                    # Sort by net profitability
                    opportunities = sorted(
                        opportunities, 
                        key=lambda x: x.get('profit_percentage_net', 0), 
                        reverse=True
                    )
                    
                    # Apply limit if specified
                    if params.get('limit_results', True) and params.get('top_results'):
                        top_n = min(params.get('top_results'), len(opportunities))
                        opportunities = opportunities[:top_n]
                    
                    st.session_state['opportunities'] = opportunities
                    logger.info(f"Stored {len(st.session_state.get('opportunities', []))} opportunities in session state.")
                    st.success(f"Se encontraron {len(opportunities)} oportunidades.")
                    return opportunities
                else:
                    st.info("No se encontraron oportunidades con los parámetros especificados.")
                    st.session_state['opportunities'] = []
                    logger.info("No opportunities found, session state['opportunities'] set to empty list.")
                    return []
        else:
            st.warning("Por favor, realice la 'Búsqueda de Tokens' primero.")
            logger.warning("Symbols or tickers not found in session state.")
            return []

    def get_available_cache_files(self, cache_dir: str = "./cache"):
        """
        Gets a list of available cache files with their information.
        
        Args:
            cache_dir (str): Directory for cache files.
            
        Returns:
            List[Dict[str, Any]]: Information about available cache files.
        """
        return list_available_cache_files(cache_dir)

    def send_found_opportunities_to_webhook(self):
        """
        Sends the found opportunities to the configured webhook URL.
        
        Returns:
            bool: True if sending was successful, False otherwise.
        """
        if 'opportunities' in st.session_state and st.session_state['opportunities']:
            st.info("Enviando oportunidades a webhook...")

            webhook_url = self.settings.n8n_webhook_oportunidad

            if webhook_url:
                success = send_opportunities_to_webhook(st.session_state['opportunities'], webhook_url)
                if success:
                    st.success("Oportunidades enviadas al webhook correctamente.")
                    return True
                else:
                    st.error("Error al enviar oportunidades al webhook.")
                    return False
            else:
                st.warning("Webhook URL no configurado en settings.")
                return False
        else:
            st.warning("No hay oportunidades para enviar al webhook.")
            return False
