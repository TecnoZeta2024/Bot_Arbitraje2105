import unittest
from unittest.mock import patch, MagicMock
import requests # Import requests
import json # Import json
from src.core.detectar_oportunidades import (
    obtener_tokens_desde_supabase,
    obtener_pares_disponibles,
    obtener_precios_actuales,
    construir_grafo_mercado,
    encontrar_rutas_triangulares,
    calcular_rentabilidad_ruta,
    formatear_ruta_legible,
    guardar_oportunidad_en_supabase,
    enviar_oportunidad_a_n8n,
    ejecutar_deteccion
)

# Mock de las dependencias externas
@patch('src.core.detectar_oportunidades.supabase_client')
@patch('src.core.detectar_oportunidades.binance_data_client')
@patch('src.core.detectar_oportunidades.settings')
@patch('src.core.detectar_oportunidades.requests')
@patch('src.core.detectar_oportunidades.calcular_rentabilidad_triangular')
@patch('src.core.detectar_oportunidades.normalizar_precios')
class TestDetectarOportunidades(unittest.TestCase):

    def test_obtener_tokens_desde_supabase(self, mock_normalizar_precios, mock_calcular_rentabilidad, mock_requests, mock_settings, mock_binance_client, mock_supabase_client):
        """
        Test para la función obtener_tokens_desde_supabase.
        Verifica que obtiene tokens desde Supabase con el límite correcto.
        """
        mock_settings.max_tokens_considerados = 50
        mock_supabase_client.obtener_tokens.return_value = [{"simbolo": "BTC"}, {"simbolo": "ETH"}]

        tokens = obtener_tokens_desde_supabase()

        # Verificar que se llamó al cliente Supabase con el límite correcto
        mock_supabase_client.obtener_tokens.assert_called_once_with(limit=50)

        # Verificar que retorna los tokens obtenidos
        self.assertEqual(tokens, [{"simbolo": "BTC"}, {"simbolo": "ETH"}])

    def test_obtener_pares_disponibles(self, mock_normalizar_precios, mock_calcular_rentabilidad, mock_requests, mock_settings, mock_binance_client, mock_supabase_client):
        """
        Test para la función obtener_pares_disponibles.
        Verifica que obtiene y parsea correctamente la información de pares de Binance.
        """
        # Mock exchange info response
        mock_exchange_info = {
            "symbols": [
                {
                    "symbol": "BTCUSDT",
                    "status": "TRADING",
                    "baseAsset": "BTC",
                    "quoteAsset": "USDT",
                    "filters": [
                        {"filterType": "MIN_NOTIONAL", "minNotional": "10.0"},
                        {"filterType": "LOT_SIZE", "stepSize": "0.000001"}
                    ]
                },
                {
                    "symbol": "ETHBTC",
                    "status": "TRADING",
                    "baseAsset": "ETH",
                    "quoteAsset": "BTC",
                    "filters": [
                        {"filterType": "MIN_NOTIONAL", "minNotional": "0.001"},
                        {"filterType": "LOT_SIZE", "stepSize": "0.0001"}
                    ]
                },
                {
                    "symbol": "XRPETH",
                    "status": "TRADING",
                    "baseAsset": "XRP",
                    "quoteAsset": "ETH",
                    "filters": [
                        {"filterType": "MIN_NOTIONAL", "minNotional": "5"},
                        {"filterType": "LOT_SIZE", "stepSize": "1"}
                    ]
                },
                 {
                    "symbol": "LTCUSDT",
                    "status": "BREAK", # Should be ignored
                    "baseAsset": "LTC",
                    "quoteAsset": "USDT",
                    "filters": []
                }
            ]
        }
        mock_binance_client.obtener_info_exchange.return_value = mock_exchange_info

        pares = obtener_pares_disponibles()

        # Verificar que se llamó al cliente Binance
        mock_binance_client.obtener_info_exchange.assert_called_once()

        # Verificar que se parsearon correctamente los pares en estado TRADING
        self.assertEqual(len(pares), 3)
        self.assertIn("BTCUSDT", pares)
        self.assertIn("ETHBTC", pares)
        self.assertIn("XRPETH", pares)
        self.assertNotIn("LTCUSDT", pares)

        # Verificar la estructura y los valores de los pares parseados
        self.assertEqual(pares["BTCUSDT"]["base"], "BTC")
        self.assertEqual(pares["BTCUSDT"]["quote"], "USDT")
        self.assertEqual(pares["BTCUSDT"]["min_notional"], 10.0)
        self.assertEqual(pares["BTCUSDT"]["step_size"], 0.000001)

        self.assertEqual(pares["ETHBTC"]["base"], "ETH")
        self.assertEqual(pares["ETHBTC"]["quote"], "BTC")
        self.assertEqual(pares["ETHBTC"]["min_notional"], 0.001)
        self.assertEqual(pares["ETHBTC"]["step_size"], 0.0001)

        self.assertEqual(pares["XRPETH"]["base"], "XRP")
        self.assertEqual(pares["XRPETH"]["quote"], "ETH")
        self.assertEqual(pares["XRPETH"]["min_notional"], 5.0)
        self.assertEqual(pares["XRPETH"]["step_size"], 1.0)

    def test_obtener_precios_actuales(self, mock_normalizar_precios, mock_calcular_rentabilidad, mock_requests, mock_settings, mock_binance_client, mock_supabase_client):
        """
        Test para la función obtener_precios_actuales.
        Verifica que obtiene los precios actuales de Binance.
        """
        mock_prices = {"BTCUSDT": 60000.0, "ETHBTC": 0.05}
        mock_binance_client.obtener_precios_todos.return_value = mock_prices

        precios = obtener_precios_actuales()

        # Verificar que se llamó al cliente Binance
        mock_binance_client.obtener_precios_todos.assert_called_once()

        # Verificar que retorna los precios obtenidos
        self.assertEqual(precios, mock_prices)

    def test_construir_grafo_mercado(self, mock_normalizar_precios, mock_calcular_rentabilidad, mock_requests, mock_settings, mock_binance_client, mock_supabase_client):
        """
        Test para la función construir_grafo_mercado.
        Verifica que construye correctamente el grafo de mercado.
        """
        pares_input = {
            "BTCUSDT": {"base": "BTC", "quote": "USDT"},
            "ETHBTC": {"base": "ETH", "quote": "BTC"},
            "XRPETH": {"base": "XRP", "quote": "ETH"},
            "LTCUSDT": {"base": "LTC", "quote": "USDT"}
        }

        grafo = construir_grafo_mercado(pares_input)

        # Verificar que los nodos (monedas) existen en el grafo
        self.assertIn("BTC", grafo)
        self.assertIn("USDT", grafo)
        self.assertIn("ETH", grafo)
        self.assertIn("XRP", grafo)
        self.assertIn("LTC", grafo)

        # Verificar las aristas (pares) y sus inversas
        self.assertIn(("USDT", "BTCUSDT"), grafo["BTC"])
        self.assertIn(("BTC", "BTCUSDT_INV"), grafo["USDT"])

        self.assertIn(("BTC", "ETHBTC"), grafo["ETH"])
        self.assertIn(("ETH", "ETHBTC_INV"), grafo["BTC"])

        self.assertIn(("ETH", "XRPETH"), grafo["XRP"])
        self.assertIn(("XRP", "XRPETH_INV"), grafo["ETH"])

        self.assertIn(("USDT", "LTCUSDT"), grafo["LTC"])
        self.assertIn(("LTC", "LTCUSDT_INV"), grafo["USDT"])

    def test_encontrar_rutas_triangulares(self, mock_normalizar_precios, mock_calcular_rentabilidad, mock_requests, mock_settings, mock_binance_client, mock_supabase_client):
        """
        Test para la función encontrar_rutas_triangulares.
        Verifica que encuentra rutas triangulares correctas.
        """
        # Grafo de mercado simulado
        grafo_input = {
            "USDT": [("BTC", "BTCUSDT_INV"), ("ETH", "ETHUSDT_INV")],
            "BTC": [("USDT", "BTCUSDT"), ("ETH", "ETHBTC_INV")],
            "ETH": [("USDT", "ETHUSDT"), ("BTC", "ETHBTC"), ("XRP", "XRPETH")],
            "XRP": [("ETH", "XRPETH_INV")]
        }

        # Encontrar rutas triangulares empezando por USDT
        rutas = encontrar_rutas_triangulares(grafo_input, start_token="USDT")

        # Verificar que se encontraron las rutas triangulares esperadas
        # Posibles rutas: USDT -> BTC -> ETH -> USDT (BTCUSDT, ETHBTC_INV, ETHUSDT_INV)
        #                 USDT -> ETH -> BTC -> USDT (ETHUSDT, ETHBTC, BTCUSDT_INV)
        #                 USDT -> ETH -> XRP -> ETH (No es triangular)
        #                 USDT -> BTC -> USDT (No es triangular)
        #                 USDT -> ETH -> USDT (No es triangular)

        # Note: The order of pairs in the route might vary depending on graph traversal.
        # We check for the presence of the expected pairs in the route.
        expected_routes_sets = [
            {("BTCUSDT_INV", "USDT", "BTC"), ("ETHBTC_INV", "BTC", "ETH"), ("ETHUSDT", "ETH", "USDT")}, # Corrected ETH -> USDT pair name
            {("ETHUSDT_INV", "USDT", "ETH"), ("ETHBTC", "ETH", "BTC"), ("BTCUSDT", "BTC", "USDT")} # Corrected BTC -> USDT pair name
        ]

        self.assertEqual(len(rutas), 2)

        # Convertir rutas encontradas a conjuntos para comparación de contenido
        found_routes_sets = [{tuple(item) for item in r} for r in rutas]

        # Check if each expected route set is present in the found routes sets
        for expected_set in expected_routes_sets:
            self.assertIn(expected_set, found_routes_sets)

    def test_calcular_rentabilidad_ruta_success(self, mock_normalizar_precios, mock_calcular_rentabilidad, mock_requests, mock_settings, mock_binance_client, mock_supabase_client):
        """
        Test para la función calcular_rentabilidad_ruta en caso de éxito.
        Verifica que calcula la rentabilidad correctamente.
        """
        ruta_input = [
            ("BTCUSDT_INV", "USDT", "BTC"),
            ("ETHBTC_INV", "BTC", "ETH"),
            ("ETHUSDT_INV", "ETH", "USDT")
        ]
        pares_input = {
            "BTCUSDT": {"base": "BTC", "quote": "USDT"},
            "ETHBTC": {"base": "ETH", "quote": "BTC"},
            "ETHUSDT": {"base": "ETH", "quote": "USDT"}
        }
        precios_input = {
            "BTCUSDT": 60000.0,
            "ETHBTC": 0.05,
            "ETHUSDT": 3000.0
        }

        # Mock helper functions
        mock_normalizar_precios.return_value = [1/60000.0, 1/0.05, 1/3000.0] # Example normalized prices
        mock_calcular_rentabilidad.return_value = {
            "rentabilidad_bruta": 1.01,
            "rentabilidad_neta": 0.008, # 0.8%
            "monto_comisiones": 0.002
        }

        resultado = calcular_rentabilidad_ruta(ruta_input, pares_input, precios_input)

        # Verificar que se llamaron a las funciones helper
        mock_normalizar_precios.assert_called_once_with([1/60000.0, 1/0.05, 1/3000.0])
        mock_calcular_rentabilidad.assert_called_once_with(mock_normalizar_precios.return_value, [1000000, 1000000, 1000000], [0.1, 0.1, 0.1])

        # Verificar la estructura y los valores del resultado
        self.assertIn("rentabilidad_bruta", resultado)
        self.assertIn("rentabilidad_neta", resultado)
        self.assertIn("comisiones", resultado)
        self.assertIn("pares", resultado)
        self.assertIn("precios", resultado)

        self.assertEqual(resultado["rentabilidad_bruta"], 1.01)
        self.assertEqual(resultado["rentabilidad_neta"], 0.008)
        self.assertEqual(resultado["comisiones"], 0.002)
        self.assertEqual(resultado["pares"], ["BTCUSDT (INV)", "ETHBTC (INV)", "ETHUSDT (INV)"])
        self.assertEqual(resultado["precios"], mock_normalizar_precios.return_value)

    def test_calcular_rentabilidad_ruta_missing_price(self, mock_normalizar_precios, mock_calcular_rentabilidad, mock_requests, mock_settings, mock_binance_client, mock_supabase_client):
        """
        Test para la función calcular_rentabilidad_ruta cuando falta un precio.
        Verifica que retorna un error y rentabilidad negativa.
        """
        ruta_input = [
            ("BTCUSDT_INV", "USDT", "BTC"),
            ("ETHBTC_INV", "BTC", "ETH"),
            ("ETHUSDT_INV", "ETH", "USDT")
        ]
        pares_input = {
            "BTCUSDT": {"base": "BTC", "quote": "USDT"},
            "ETHBTC": {"base": "ETH", "quote": "BTC"}
            # Missing ETHUSDT
        }
        precios_input = {
            "BTCUSDT": 60000.0,
            "ETHBTC": 0.05
            # Missing ETHUSDT price
        }

        resultado = calcular_rentabilidad_ruta(ruta_input, pares_input, precios_input)

        # Verificar que retorna un error y rentabilidad negativa
        self.assertIn("error", resultado)
        self.assertEqual(resultado["rentabilidad_bruta"], -100.0)
        self.assertIn("Precio no disponible para ETHUSDT", resultado["error"])

        # Verificar que las funciones helper no fueron llamadas
        mock_normalizar_precios.assert_not_called()
        mock_calcular_rentabilidad.assert_not_called()

    def test_formatear_ruta_legible(self, mock_normalizar_precios, mock_calcular_rentabilidad, mock_requests, mock_settings, mock_binance_client, mock_supabase_client):
        """
        Test para la función formatear_ruta_legible.
        Verifica que formatea la ruta correctamente.
        """
        ruta_input = [
            ("BTCUSDT_INV", "USDT", "BTC"),
            ("ETHBTC_INV", "BTC", "ETH"),
            ("ETHUSDT_INV", "ETH", "USDT")
        ]

        ruta_formateada = formatear_ruta_legible(ruta_input)

        # Verificar que la ruta se formateó como se espera
        self.assertEqual(ruta_formateada, "USDT → BTC → ETH → USDT")

    @patch('src.core.detectar_oportunidades.settings') # Move settings patch to method level
    @patch('src.core.detectar_oportunidades.time') # Mock time to control the timestamp
    def test_guardar_oportunidad_en_supabase_success(self, mock_settings, mock_time, mock_supabase_client, mock_binance_client, mock_requests, mock_calcular_rentabilidad, mock_normalizar_precios): # Corrected argument order
        """
        Test para la función guardar_oportunidad_en_supabase en caso de éxito.
        Verifica que guarda la oportunidad en Supabase correctamente.
        """
        oportunidad_input = {
            "ruta": "USDT → BTC → ETH → USDT",
            "rentabilidad_bruta": 1.01,
            "rentabilidad_neta": 0.008,
            "comisiones": 0.002,
            "pares": ["BTCUSDT (INV)", "ETHBTC (INV)", "ETHUSDT (INV)"],
            "precios": [1/60000.0, 1/0.05, 1/3000.0],
            "pares_info": [{"symbol": "BTCUSDT", "step": 1}, {"symbol": "ETHBTC", "step": 2}, {"symbol": "ETHUSDT", "step": 3}]
        }
        mock_settings.capital_inicial = 1000
        mock_supabase_client.insertar_oportunidad.return_value = {"id": "test-uuid"} # Simulate successful insertion

        # Mock time.strftime to return a fixed timestamp
        mock_time.strftime.return_value = "2025-05-13 12:00:00"

        oportunidad_guardada = guardar_oportunidad_en_supabase(oportunidad_input)

        # Verify that the insert method was called with the correct data
        expected_data = {
            "ruta": "USDT → BTC → ETH → USDT",
            "pares_comercio": json.dumps([{"symbol": "BTCUSDT", "step": 1}, {"symbol": "ETHBTC", "step": 2}, {"symbol": "ETHUSDT", "step": 3}]),
            "rentabilidad_teorica": 0.008,
            "capital_inicial": 1000,
            "fecha_deteccion": "2025-05-13 12:00:00"
        }
        mock_supabase_client.insertar_oportunidad.assert_called_once_with(expected_data)

        # Verify that the returned opportunity includes the ID from Supabase
        self.assertIsNotNone(oportunidad_guardada)
        self.assertIn("oportunidad_id", oportunidad_guardada)
        self.assertEqual(oportunidad_guardada["oportunidad_id"], "test-uuid")

    @patch('src.core.detectar_oportunidades.time') # Mock time to control the timestamp
    def test_guardar_oportunidad_en_supabase_error(self, mock_time, mock_normalizar_precios, mock_calcular_rentabilidad, mock_requests, mock_settings, mock_binance_client, mock_supabase_client):
        """
        Test para la función guardar_oportunidad_en_supabase en caso de error.
        Verifica que maneja excepciones y retorna None.
        """
        oportunidad_input = {
            "ruta": "USDT → BTC → ETH → USDT",
            "rentabilidad_neta": 0.008,
            "pares_info": []
        }
        mock_settings.capital_inicial = 1000
        mock_supabase_client.insertar_oportunidad.side_effect = Exception("Supabase Error") # Simulate insertion error

        # Mock time.strftime to return a fixed timestamp
        mock_time.strftime.return_value = "2025-05-13 12:00:00"

        oportunidad_guardada = guardar_oportunidad_en_supabase(oportunidad_input)

        # Verify that the insert method was called
        mock_supabase_client.insertar_oportunidad.assert_called_once()

        # Verify that None is returned on error
        self.assertIsNone(oportunidad_guardada)

    def test_enviar_oportunidad_a_n8n_success(self, mock_normalizar_precios, mock_calcular_rentabilidad, mock_requests, mock_settings, mock_binance_client, mock_supabase_client):
        """
        Test para la función enviar_oportunidad_a_n8n en caso de éxito.
        Verifica que envía la oportunidad a n8n correctamente.
        """
        oportunidad_input = {
            "ruta": "USDT → BTC → ETH → USDT",
            "rentabilidad_neta": 0.008,
            "pares": ["BTCUSDT (INV)", "ETHBTC (INV)", "ETHUSDT (INV)"],
            "oportunidad_id": "test-uuid"
        }
        mock_settings.n8n_webhook_oportunidad = "https://bea5-177-222-98-63.ngrok-free.app/webhook-test/arbitraje-oportunidad"
        mock_settings.capital_inicial = 1000

        # Mock the requests.post method
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_requests.post.return_value = mock_response

        enviado = enviar_oportunidad_a_n8n(oportunidad_input)

        # Verify that requests.post was called with the correct URL and data
        expected_data = {
            "body": {
                "oportunidad": {
                    "ruta": "USDT → BTC → ETH → USDT",
                    "pares": ["BTCUSDT (INV)", "ETHBTC (INV)", "ETHUSDT (INV)"],
                    "rentabilidad": 0.008,
                    "capital": 1000,
                    "oportunidad_id": "test-uuid"
                }
            }
        }
        mock_requests.post.assert_called_once_with(
            "https://bea5-177-222-98-63.ngrok-free.app/webhook-test/arbitraje-oportunidad",
            json=expected_data,
            headers={"Content-Type": "application/json"}
        )

        # Verify that True is returned on success
        self.assertTrue(enviado)

    def test_enviar_oportunidad_a_n8n_failure(self, mock_normalizar_precios, mock_calcular_rentabilidad, mock_requests, mock_settings, mock_binance_client, mock_supabase_client):
        """
        Test para la función enviar_oportunidad_a_n8n en caso de fallo.
        Verifica que maneja errores de respuesta HTTP.
        """
        oportunidad_input = {
            "ruta": "USDT → BTC → ETH → USDT",
            "rentabilidad_neta": 0.008,
            "pares": ["BTCUSDT (INV)", "ETHBTC (INV)", "ETHUSDT (INV)"],
            "oportunidad_id": "test-uuid"
        }
        mock_settings.n8n_webhook_oportunidad = "https://bea5-177-222-98-63.ngrok-free.app/webhook-test/arbitraje-oportunidad"
        mock_settings.capital_inicial = 1000

        # Mock the requests.post method to return an error status code
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"
        mock_requests.post.return_value = mock_response

        enviado = enviar_oportunidad_a_n8n(oportunidad_input)

        # Verify that requests.post was called
        mock_requests.post.assert_called_once()

        # Verify that False is returned on failure
        self.assertFalse(enviado)

    def test_enviar_oportunidad_a_n8n_exception(self, mock_normalizar_precios, mock_calcular_rentabilidad, mock_requests, mock_settings, mock_binance_client, mock_supabase_client):
        """
        Test para la función enviar_oportunidad_a_n8n en caso de excepción.
        Verifica que maneja excepciones durante la solicitud.
        """
        oportunidad_input = {
            "ruta": "USDT → BTC → ETH → USDT",
            "rentabilidad_neta": 0.008,
            "pares": ["BTCUSDT (INV)", "ETHBTC (INV)", "ETHUSDT (INV)"],
            "oportunidad_id": "test-uuid"
        }
        mock_settings.n8n_webhook_oportunidad = "https://bea5-177-222-98-63.ngrok-free.app/webhook-test/arbitraje-oportunidad"
        mock_settings.capital_inicial = 1000

        # Mock requests.post to raise an exception
        mock_requests.post.side_effect = requests.exceptions.RequestException("Connection Error")

        enviado = enviar_oportunidad_a_n8n(oportunidad_input)

        # Verify that requests.post was called
        mock_requests.post.assert_called_once()

        # Verify that False is returned on exception
        self.assertFalse(enviado)

    @patch('src.core.detectar_oportunidades.obtener_tokens_desde_supabase')
    @patch('src.core.detectar_oportunidades.obtener_pares_disponibles')
    @patch('src.core.detectar_oportunidades.obtener_precios_actuales')
    @patch('src.core.detectar_oportunidades.construir_grafo_mercado')
    @patch('src.core.detectar_oportunidades.encontrar_rutas_triangulares')
    @patch('src.core.detectar_oportunidades.calcular_rentabilidad_ruta')
    @patch('src.core.detectar_oportunidades.formatear_ruta_legible')
    @patch('src.core.detectar_oportunidades.guardar_oportunidad_en_supabase')
    @patch('src.core.detectar_oportunidades.enviar_oportunidad_a_n8n') # Corrected typo
    @patch('src.core.detectar_oportunidades.time.time') # Mock time.time for execution time calculation
    def test_ejecutar_deteccion_success(self, mock_time_time, mock_enviar_oportunidad, mock_guardar_oportunidad, mock_formatear_ruta, mock_calcular_rentabilidad, mock_encontrar_rutas, mock_construir_grafo, mock_obtener_precios, mock_obtener_pares, mock_obtener_tokens, mock_normalizar_precios, mock_calcular_rentabilidad_helper, mock_requests, mock_settings, mock_binance_client, mock_supabase_client):
        """
        Test para la función ejecutar_deteccion en caso de éxito.
        Verifica que el flujo completo se ejecuta correctamente.
        """
        # Configure mocks to return specific values and track calls
        mock_obtener_tokens.return_value = [{"simbolo": "USDT"}]
        mock_obtener_pares.return_value = {"BTCUSDT": {}, "ETHBTC": {}, "ETHUSDT": {}}
        mock_obtener_precios.return_value = {"BTCUSDT": 60000, "ETHBTC": 0.05, "ETHUSDT": 3000}
        mock_construir_grafo.return_value = {
             "USDT": [("BTC", "BTCUSDT_INV"), ("ETH", "ETHUSDT_INV")],
             "BTC": [("USDT", "BTCUSDT"), ("ETH", "ETHBTC_INV")],
             "ETH": [("USDT", "ETHUSDT"), ("BTC", "ETHBTC")]
        }
        mock_encontrar_rutas.return_value = [
            [("BTCUSDT_INV", "USDT", "BTC"), ("ETHBTC_INV", "BTC", "ETH"), ("ETHUSDT_INV", "ETH", "USDT")], # Profitable
            [("ETHUSDT_INV", "USDT", "ETH"), ("ETHBTC", "ETH", "BTC"), ("BTCUSDT_INV", "BTC", "USDT")], # Profitable
            [("USDT", "BTCUSDT"), ("BTC", "BTCUSDT_INV"), ("USDT", "USDT")] # Not triangular, should be filtered by encontrar_rutas_triangulares
        ]
        # Mock calcular_rentabilidad_ruta to return different profitabilities
        mock_calcular_rentabilidad.side_effect = [
            {"rentabilidad_bruta": 1.01, "rentabilidad_neta": 0.01, "comisiones": 0.001, "pares": ["BTCUSDT (INV)", "ETHBTC (INV)", "ETHUSDT (INV)"], "precios": [1/60000.0, 1/0.05, 1/3000.0], "pares_info": []}, # Profitable
            {"rentabilidad_bruta": 1.005, "rentabilidad_neta": 0.0051, "comisiones": 0.0005, "pares": ["ETHUSDT (INV)", "ETHBTC", "BTCUSDT_INV"], "precios": [1/3000.0, 0.05, 60000.0], "pares_info": []}, # Profitable (adjusted rentabilidad_neta)
            {"rentabilidad_bruta": -0.001, "rentabilidad_neta": -0.001, "comisiones": 0.0, "pares": [], "precios": [], "pares_info": []} # Not profitable
        ]
        mock_formatear_ruta.side_effect = ["USDT → BTC → ETH → USDT (1)", "USDT → ETH → BTC → USDT (2)"]
        mock_guardar_oportunidad.side_effect = lambda opp: {**opp, "oportunidad_id": "test-id"} # Simulate saving and adding ID
        mock_enviar_oportunidad.return_value = True # Simulate successful sending

        mock_settings.umbral_rentabilidad = 0.005 # 0.5%
        mock_settings.capital_inicial = 1000

        # Mock time.time to control execution time
        mock_time_time.side_effect = [0, 10] # Start time 0, End time 10

        result = ejecutar_deteccion()

        # Verify that functions were called in the correct order
        mock_obtener_tokens.assert_called_once()
        mock_obtener_pares.assert_called_once()
        mock_obtener_precios.assert_called_once()
        mock_construir_grafo.assert_called_once_with(mock_obtener_pares.return_value)
        mock_encontrar_rutas.assert_called_once() # Changed to assert_called_once()

        # Verify that calcular_rentabilidad_ruta was called for each potential triangular route
        self.assertEqual(mock_calcular_rentabilidad.call_count, 3)

        # Verify that formatear_ruta_legible was called only for profitable routes
        self.assertEqual(mock_formatear_ruta.call_count, 2)

        # Verify that guardar_oportunidad_en_supabase and enviar_oportunidad_a_n8n were called for the top 2 profitable opportunities
        self.assertEqual(mock_guardar_oportunidad.call_count, 2)
        self.assertEqual(mock_enviar_oportunidad.call_count, 2)

        # Verify the returned result structure and values
        self.assertIn("rutas_analizadas", result)
        self.assertIn("oportunidades_detectadas", result)
        self.assertIn("oportunidades_procesadas", result)
        self.assertIn("tiempo_ejecucion", result)

        self.assertEqual(result["rutas_analizadas"], 3) # Total routes found by encontrar_rutas_triangulares
        self.assertEqual(result["oportunidades_detectadas"], 2) # Profitable opportunities
        self.assertEqual(result["oportunidades_procesadas"], 2) # Opportunities saved and sent
        self.assertEqual(result["tiempo_ejecucion"], 10.0)

    @patch('src.core.detectar_oportunidades.obtener_tokens_desde_supabase')
    @patch('src.core.detectar_oportunidades.time.time') # Mock time.time for execution time calculation
    def test_ejecutar_deteccion_error(self, mock_time_time, mock_obtener_tokens, mock_normalizar_precios, mock_calcular_rentabilidad, mock_requests, mock_settings, mock_binance_client, mock_supabase_client):
        """
        Test para la función ejecutar_deteccion en caso de error.
        Verifica que maneja excepciones y retorna un resultado con error.
        """
        # Configure mock to raise an exception
        mock_obtener_tokens.side_effect = Exception("Supabase Error")

        # Mock time.time to control execution time
        mock_time_time.side_effect = [0, 3] # Start time 0, End time 3

        result = ejecutar_deteccion()

        # Verify that the error was caught and reported
        self.assertIn("error", result)
        self.assertEqual(result["error"], "Supabase Error")
        self.assertEqual(result["rutas_analizadas"], 0)
        self.assertEqual(result["oportunidades_detectadas"], 0)
        self.assertEqual(result["oportunidades_procesadas"], 0)
        self.assertEqual(result["tiempo_ejecucion"], 3.0)

    # Aquí se añadirán más tests para las otras funciones

if __name__ == '__main__':
    unittest.main()
