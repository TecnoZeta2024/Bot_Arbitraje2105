import unittest
from unittest.mock import patch, MagicMock
from src.core.filtrar_tokens import (
    obtener_tokens_candidatos,
    filtrar_por_market_cap,
    filtrar_por_disponibilidad_binance,
    obtener_metricas_token,
    filtrar_por_rendimiento,
    filtrar_por_volumen,
    guardar_tokens_en_supabase,
    ejecutar_filtrado
)

# Mock de las dependencias externas
@patch('src.core.filtrar_tokens.mobula_client')
@patch('src.core.filtrar_tokens.coingecko_client')
@patch('src.core.filtrar_tokens.binance_data_client')
@patch('src.core.filtrar_tokens.supabase_client')
@patch('src.core.filtrar_tokens.settings')
class TestFiltrarTokens(unittest.TestCase):

    def test_obtener_tokens_candidatos(self, mock_settings, mock_supabase_client, mock_binance_client, mock_coingecko_client, mock_mobula_client):
        """
        Test para la función obtener_tokens_candidatos.
        Verifica que combina correctamente los resultados de Mobula y CoinGecko.
        """
        mock_settings.max_tokens_considerados = 100

        # Configurar mocks para devolver datos simulados
        mock_mobula_client.obtener_tokens_top.return_value = [
            {"symbol": "BTC", "name": "Bitcoin", "market_cap": 1000000000000},
            {"symbol": "ETH", "name": "Ethereum", "market_cap": 500000000000},
            {"symbol": "XRP", "name": "Ripple", "market_cap": 50000000000} # Token que se repetirá en CoinGecko
        ]
        mock_coingecko_client.obtener_tokens_top.return_value = [
            {"symbol": "eth", "name": "Ethereum", "market_cap": 500000000000}, # Token que se repetirá en Mobula (diferente capitalización, debería usar la primera)
            {"symbol": "ada", "name": "Cardano", "market_cap": 20000000000},
            {"symbol": "xrp", "name": "Ripple", "market_cap": 55000000000} # Token que se repetirá en Mobula
        ]

        tokens = obtener_tokens_candidatos()

        # Verificar que se llamaron a los clientes API
        mock_mobula_client.obtener_tokens_top.assert_called_once_with(limit=100)
        mock_coingecko_client.obtener_tokens_top.assert_called_once_with(limit=100)

        # Verificar el número total de tokens (debería evitar duplicados por símbolo)
        self.assertEqual(len(tokens), 4) # BTC, ETH, XRP, ADA

        # Verificar que los tokens tienen la estructura esperada y los símbolos están en mayúsculas
        symbols = {token["simbolo"] for token in tokens}
        self.assertIn("BTC", symbols)
        self.assertIn("ETH", symbols)
        self.assertIn("XRP", symbols)
        self.assertIn("ADA", symbols)

        # Verificar que se usó la primera capitalización de mercado encontrada para duplicados
        eth_token = next(t for t in tokens if t["simbolo"] == "ETH")
        self.assertEqual(eth_token["market_cap"], 500000000000) # Debería ser la de Mobula

        xrp_token = next(t for t in tokens if t["simbolo"] == "XRP")
        self.assertEqual(xrp_token["market_cap"], 50000000000) # Debería ser la de Mobula

    def test_filtrar_por_market_cap(self, mock_settings, mock_supabase_client, mock_binance_client, mock_coingecko_client, mock_mobula_client):
        """
        Test para la función filtrar_por_market_cap.
        Verifica que filtra correctamente por capitalización de mercado mínima.
        """
        tokens_input = [
            {"simbolo": "BTC", "nombre": "Bitcoin", "market_cap": 1000000000000}, # Should pass
            {"simbolo": "ETH", "nombre": "Ethereum", "market_cap": 500000000000},  # Should pass
            {"simbolo": "XRP", "nombre": "Ripple", "market_cap": 50000000000},   # Should pass
            {"simbolo": "ADA", "nombre": "Cardano", "market_cap": 20000000000},   # Should fail
            {"simbolo": "DOGE", "nombre": "Dogecoin", "market_cap": 10000000000}, # Should fail
            {"simbolo": "SHIB", "nombre": "Shiba Inu", "market_cap": 5000000000},  # Should fail
            {"simbolo": "LOWCAP", "nombre": "Low Cap Coin", "market_cap": 1000000} # Should fail
        ]
        min_market_cap = 50000000000 # 50 Billion USD

        filtered_tokens = filtrar_por_market_cap(tokens_input, min_market_cap)

        # Verificar que solo los tokens con market cap >= min_market_cap están presentes
        self.assertEqual(len(filtered_tokens), 3)
        symbols = {token["simbolo"] for token in filtered_tokens}
        self.assertIn("BTC", symbols)
        self.assertIn("ETH", symbols)
        self.assertIn("XRP", symbols)
        self.assertNotIn("ADA", symbols)
        self.assertNotIn("DOGE", symbols)
        self.assertNotIn("SHIB", symbols)
        self.assertNotIn("LOWCAP", symbols)

    def test_filtrar_por_disponibilidad_binance(self, mock_settings, mock_supabase_client, mock_binance_client, mock_coingecko_client, mock_mobula_client):
        """
        Test para la función filtrar_por_disponibilidad_binance.
        Verifica que filtra tokens disponibles en Binance como base assets.
        """
        tokens_input = [
            {"simbolo": "BTC", "nombre": "Bitcoin"}, # Should pass (BTCUSDT, BTCETH, etc.)
            {"simbolo": "ETH", "nombre": "Ethereum"}, # Should pass (ETHUSDT, ETHBTC, etc.)
            {"simbolo": "XRP", "nombre": "Ripple"}, # Should pass (XRPUSDT, XRPBTC, etc.)
            {"simbolo": "ADA", "nombre": "Cardano"}, # Should pass (ADAUSDT, ADABTC, etc.)
            {"simbolo": "DOT", "nombre": "Polkadot"}, # Should pass (DOTUSDT, DOTBTC, etc.)
            {"simbolo": "SOL", "nombre": "Solana"}, # Should pass (SOLUSDT, SOLBTC, etc.)
            {"simbolo": "NONEXIST", "nombre": "Non Existent Coin"}, # Should fail
            {"simbolo": "TEST", "nombre": "Test Coin"} # Should fail
        ]

        # Configurar mock para devolver símbolos de trading de Binance
        mock_binance_client.obtener_simbolos_trading.return_value = [
            "BTCUSDT", "ETHUSDT", "XRPUSDT", "ADAUSDT", "DOTBTC", "SOLETH",
            "BNBUSDT", "BUSDUSDT", "BTCBUSD" # Otros pares para asegurar que la lógica de base/quote funciona
        ]

        filtered_tokens = filtrar_por_disponibilidad_binance(tokens_input)

        # Verificar que solo los tokens disponibles en Binance como base assets están presentes
        self.assertEqual(len(filtered_tokens), 6)
        symbols = {token["simbolo"] for token in filtered_tokens}
        self.assertIn("BTC", symbols)
        self.assertIn("ETH", symbols)
        self.assertIn("XRP", symbols)
        self.assertIn("ADA", symbols)
        self.assertIn("DOT", symbols)
        self.assertIn("SOL", symbols)
        self.assertNotIn("NONEXIST", symbols)
        self.assertNotIn("TEST", symbols)

    def test_obtener_metricas_token(self, mock_settings, mock_supabase_client, mock_binance_client, mock_coingecko_client, mock_mobula_client):
        """
        Test para la función obtener_metricas_token.
        Verifica que obtiene y añade métricas de rendimiento y volumen de Binance.
        """
        token_input = {"simbolo": "BTC", "nombre": "Bitcoin", "market_cap": 1000000000000}

        # Configurar mocks para devolver métricas y volumen simulados
        mock_mobula_client.calcular_metricas_rendimiento.return_value = {
            "rendimiento_1h": 1.5,
            "rendimiento_24h": 5.0,
            "rendimiento_7d": 15.0,
            "volatilidad": 0.02
        }
        mock_binance_client.obtener_volumen_24h.side_effect = [
            None, # BTCETH
            1000000000 # BTCUSDT
        ] # Simula que busca en varios pares hasta encontrar uno

        token_with_metrics = obtener_metricas_token(token_input)

        # Verificar que se llamaron a los clientes API con el símbolo correcto
        mock_mobula_client.calcular_metricas_rendimiento.assert_called_once_with("BTC")
        # Verificar que se intentó obtener volumen para pares comunes
        mock_binance_client.obtener_volumen_24h.assert_any_call("BTCUSDT")
        mock_binance_client.obtener_volumen_24h.assert_any_call("BTCETH")


        # Verificar que las métricas y el volumen se añadieron al token
        self.assertIn("rendimiento_1h", token_with_metrics)
        self.assertIn("rendimiento_24h", token_with_metrics)
        self.assertIn("rendimiento_7d", token_with_metrics)
        self.assertIn("volatilidad", token_with_metrics)
        self.assertIn("volumen_binance_24h", token_with_metrics)

        self.assertEqual(token_with_metrics["rendimiento_1h"], 1.5)
        self.assertEqual(token_with_metrics["volumen_binance_24h"], 1000000000)

    def test_filtrar_por_rendimiento(self, mock_settings, mock_supabase_client, mock_binance_client, mock_coingecko_client, mock_mobula_client):
        """
        Test para la función filtrar_por_rendimiento.
        Verifica que filtra correctamente por rendimiento mínimo.
        """
        tokens_input = [
            {"simbolo": "A", "rendimiento_1h": 1.0, "rendimiento_24h": 2.0, "rendimiento_7d": 5.0},   # Pass (1h)
            {"simbolo": "B", "rendimiento_1h": 0.1, "rendimiento_24h": 4.0, "rendimiento_7d": 8.0},   # Pass (24h)
            {"simbolo": "C", "rendimiento_1h": 0.2, "rendimiento_24h": 1.0, "rendimiento_7d": 12.0},  # Pass (7d)
            {"simbolo": "D", "rendimiento_1h": 0.1, "rendimiento_24h": 1.0, "rendimiento_7d": 5.0},   # Fail
            {"simbolo": "E", "rendimiento_1h": 0.6, "rendimiento_24h": 3.5, "rendimiento_7d": 11.0},  # Pass (all)
            {"simbolo": "F", "rendimiento_1h": -0.5, "rendimiento_24h": -2.0, "rendimiento_7d": -5.0} # Fail
        ]
        min_rendimiento_1h = 0.5
        min_rendimiento_24h = 3.0
        min_rendimiento_7d = 10.0

        filtered_tokens = filtrar_por_rendimiento(tokens_input, min_rendimiento_1h, min_rendimiento_24h, min_rendimiento_7d)

        # Verificar que solo los tokens que cumplen al menos un criterio de rendimiento están presentes
        self.assertEqual(len(filtered_tokens), 4)
        symbols = {token["simbolo"] for token in filtered_tokens}
        self.assertIn("A", symbols)
        self.assertIn("B", symbols)
        self.assertIn("C", symbols)
        self.assertIn("E", symbols)
        self.assertNotIn("D", symbols)
        self.assertNotIn("F", symbols)

    def test_filtrar_por_volumen(self, mock_settings, mock_supabase_client, mock_binance_client, mock_coingecko_client, mock_mobula_client):
        """
        Test para la función filtrar_por_volumen.
        Verifica que filtra correctamente por volumen mínimo en Binance.
        """
        tokens_input = [
            {"simbolo": "A", "volumen_binance_24h": 1500000}, # Pass
            {"simbolo": "B", "volumen_binance_24h": 1000000}, # Pass
            {"simbolo": "C", "volumen_binance_24h": 500000},  # Fail
            {"simbolo": "D", "volumen_binance_24h": 0}       # Fail
        ]
        min_volumen = 1000000 # 1 Million USD

        filtered_tokens = filtrar_por_volumen(tokens_input, min_volumen)

        # Verificar que solo los tokens con volumen >= min_volumen están presentes
        self.assertEqual(len(filtered_tokens), 2)
        symbols = {token["simbolo"] for token in filtered_tokens}
        self.assertIn("A", symbols)
        self.assertIn("B", symbols)
        self.assertNotIn("C", symbols)
        self.assertNotIn("D", symbols)

    @patch('src.core.filtrar_tokens.time') # Mock time to control the timestamp
    def test_guardar_tokens_en_supabase(self, mock_time, mock_settings, mock_supabase_client, mock_binance_client, mock_coingecko_client, mock_mobula_client):
        """
        Test para la función guardar_tokens_en_supabase.
        Verifica que guarda los tokens en Supabase correctamente.
        """
        tokens_input = [
            {"simbolo": "A", "nombre": "Token A", "market_cap": 1e9, "rendimiento_1h": 1.0, "rendimiento_24h": 5.0, "rendimiento_7d": 10.0, "volumen_binance_24h": 1e6},
            {"simbolo": "B", "nombre": "Token B", "market_cap": 2e9, "rendimiento_1h": 0.5, "rendimiento_24h": 3.0, "rendimiento_7d": 8.0, "volumen_binance_24h": 2e6},
            # Add more tokens to test batching if needed, e.g., 51 tokens
        ]

        # Mock time.strftime to return a fixed timestamp
        mock_time.strftime.return_value = "2025-05-13 12:00:00"

        # Mock the insert method to track calls
        mock_supabase_client.insertar_tokens.return_value = [] # Assuming insert returns empty list on success

        tokens_saved_count = guardar_tokens_en_supabase(tokens_input)

        # Verify that the insert method was called with the correct data
        expected_data = [
            {
                "simbolo": "A",
                "nombre": "Token A",
                "market_cap": 1e9,
                "rendimiento_1h": 1.0,
                "rendimiento_24h": 5.0,
                "rendimiento_7d": 10.0,
                "volumen_binance_24h": 1e6,
                "fecha_actualizacion": "2025-05-13 12:00:00"
            },
            {
                "simbolo": "B",
                "nombre": "Token B",
                "market_cap": 2e9,
                "rendimiento_1h": 0.5,
                "rendimiento_24h": 3.0,
                "rendimiento_7d": 8.0,
                "volumen_binance_24h": 2e6,
                "fecha_actualizacion": "2025-05-13 12:00:00"
            }
        ]
        mock_supabase_client.insertar_tokens.assert_called_once_with(expected_data)

        # Verify the number of tokens reported as saved
        self.assertEqual(tokens_saved_count, len(tokens_input))

    @patch('src.core.filtrar_tokens.obtener_tokens_candidatos')
    @patch('src.core.filtrar_tokens.filtrar_por_market_cap')
    @patch('src.core.filtrar_tokens.filtrar_por_disponibilidad_binance')
    @patch('src.core.filtrar_tokens.obtener_metricas_token')
    @patch('src.core.filtrar_tokens.filtrar_por_rendimiento')
    @patch('src.core.filtrar_tokens.filtrar_por_volumen')
    @patch('src.core.filtrar_tokens.guardar_tokens_en_supabase')
    @patch('src.core.filtrar_tokens.time.time') # Mock time.time for execution time calculation
    def test_ejecutar_filtrado_success(self, mock_time_time, mock_guardar_tokens, mock_filtrar_volumen, mock_filtrar_rendimiento, mock_obtener_metricas, mock_filtrar_binance, mock_filtrar_market_cap, mock_obtener_candidatos, mock_settings, mock_supabase_client, mock_binance_client, mock_coingecko_client, mock_mobula_client):
        """
        Test para la función ejecutar_filtrado en caso de éxito.
        Verifica que el flujo completo se ejecuta correctamente.
        """
        # Configure mocks to return specific values and track calls
        mock_obtener_candidatos.return_value = [{"simbolo": "A"}, {"simbolo": "B"}, {"simbolo": "C"}]
        mock_filtrar_market_cap.return_value = [{"simbolo": "A"}, {"simbolo": "B"}]
        mock_filtrar_binance.return_value = [{"simbolo": "A"}]
        mock_obtener_metricas.side_effect = lambda token: {**token, "metrics": True} # Add a dummy metric
        mock_filtrar_rendimiento.return_value = [{"simbolo": "A"}]
        mock_filtrar_volumen.return_value = [{"simbolo": "A"}]
        mock_guardar_tokens.return_value = 1 # Number of tokens saved

        # Mock time.time to control execution time
        mock_time_time.side_effect = [0, 5] # Start time 0, End time 5

        result = ejecutar_filtrado()

        # Verify that functions were called in the correct order
        mock_obtener_candidatos.assert_called_once()
        mock_filtrar_market_cap.assert_called_once_with([{"simbolo": "A"}, {"simbolo": "B"}, {"simbolo": "C"}])
        mock_filtrar_binance.assert_called_once_with([{"simbolo": "A"}, {"simbolo": "B"}])
        # obtener_metricas_token is called in a loop, check calls for each token
        mock_obtener_metricas.assert_any_call({"simbolo": "A"})
        # Check that it was called for all tokens that passed the previous filter
        self.assertEqual(mock_obtener_metricas.call_count, 1) # Only 'A' passed filtrar_por_disponibilidad_binance
        mock_filtrar_rendimiento.assert_called_once_with([{"simbolo": "A", "metrics": True}])
        mock_filtrar_volumen.assert_called_once_with([{"simbolo": "A"}])
        mock_guardar_tokens.assert_called_once_with([{"simbolo": "A"}])

        # Verify the returned result structure and values
        self.assertIn("tokens_iniciales", result)
        self.assertIn("tokens_filtrados", result)
        self.assertIn("tokens_guardados", result)
        self.assertIn("tiempo_ejecucion", result)

        self.assertEqual(result["tokens_iniciales"], 3)
        self.assertEqual(result["tokens_filtrados"], 1)
        self.assertEqual(result["tokens_guardados"], 1)
        self.assertEqual(result["tiempo_ejecucion"], 5.0)

    @patch('src.core.filtrar_tokens.obtener_tokens_candidatos')
    @patch('src.core.filtrar_tokens.time.time') # Mock time.time for execution time calculation
    def test_ejecutar_filtrado_error(self, mock_time_time, mock_obtener_candidatos, mock_settings, mock_supabase_client, mock_binance_client, mock_coingecko_client, mock_mobula_client):
        """
        Test para la función ejecutar_filtrado en caso de error.
        Verifica que maneja excepciones y retorna un resultado con error.
        """
        # Configure mock to raise an exception
        mock_obtener_candidatos.side_effect = Exception("API Error")

        # Mock time.time to control execution time
        mock_time_time.side_effect = [0, 2] # Start time 0, End time 2

        result = ejecutar_filtrado()

        # Verify that the error was caught and reported
        self.assertIn("error", result)
        self.assertEqual(result["error"], "API Error")
        self.assertEqual(result["tokens_filtrados"], 0)
        self.assertEqual(result["tokens_guardados"], 0)
        self.assertEqual(result["tiempo_ejecucion"], 2.0)

    # Aquí se añadirán más tests para las otras funciones

if __name__ == '__main__':
    unittest.main()
