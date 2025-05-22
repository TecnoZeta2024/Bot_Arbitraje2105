import unittest
from unittest.mock import patch, MagicMock
import requests # Import requests to mock exceptions

from src.apis.mobula_client import MobulaClient

# Mock de las dependencias externas
@patch('src.apis.mobula_client.get_mobula_config')
@patch('src.apis.mobula_client.requests')
class TestMobulaClient(unittest.TestCase):

    def setUp(self):
        """Configuración común para los tests."""
        # Reset mocks before each test
        self.mock_get_mobula_config.reset_mock()
        self.mock_requests.reset_mock()

        # Configure default mock settings
        self.mock_get_mobula_config.return_value = {
            "base_url": "https://api.mobula.io/api/v1/",
            "api_key": "test_mobula_key",
            "timeout": 10
        }

    @patch('src.apis.mobula_client.get_logger') # Mock logger to prevent output during tests
    def test_init(self, mock_get_logger, mock_requests, mock_get_mobula_config):
        """
        Test para la inicialización del cliente Mobula.
        """
        client = MobulaClient()

        # Verify config was used
        mock_get_mobula_config.assert_called_once()

        # Verify attributes
        self.assertEqual(client.base_url, "https://api.mobula.io/api/v1/")
        self.assertEqual(client.api_key, "test_mobula_key")
        self.assertEqual(client.timeout, 10)
        self.assertIn("Authorization", client.headers)
        self.assertEqual(client.headers["Authorization"], "Bearer test_mobula_key")

    # Add tests for MobulaClient methods here
    # For example: test_get_market_data_success, test_get_market_data_failure, etc.

    def test_obtener_tokens_top_success(self, mock_requests, mock_get_mobula_config):
        """
        Test para obtener_tokens_top (exitoso).
        Verifica que obtiene los tokens principales por capitalización.
        """
        client = MobulaClient()
        limit = 50
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": [{"id": "bitcoin", "symbol": "btc"}, {"id": "ethereum", "symbol": "eth"}]}
        mock_requests.get.return_value = mock_response

        tokens = client.obtener_tokens_top(limit)

        # Verify requests.get was called with correct parameters
        expected_params = {
            "limit": limit,
            "sort": "market_cap",
            "order": "desc"
        }
        mock_requests.get.assert_called_once_with(
            "https://api.mobula.io/api/v1/market/multi-data",
            headers=client.headers,
            params=expected_params,
            timeout=10
        )
        self.assertEqual(tokens, [{"id": "bitcoin", "symbol": "btc"}, {"id": "ethereum", "symbol": "eth"}])

    def test_obtener_tokens_top_failure(self, mock_requests, mock_get_mobula_config):
        """
        Test para obtener_tokens_top (fallo).
        Verifica que retorna una lista vacía si la solicitud falla.
        """
        client = MobulaClient()
        limit = 50
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"
        mock_requests.get.return_value = mock_response

        tokens = client.obtener_tokens_top(limit)

        # Verify requests.get was called
        mock_requests.get.assert_called_once_with(
            "https://api.mobula.io/api/v1/market/multi-data",
            headers=client.headers,
            params={
                "limit": limit,
                "sort": "market_cap",
                "order": "desc"
            },
            timeout=10
        )
        self.assertEqual(tokens, [])

    def test_obtener_tokens_top_exception(self, mock_requests, mock_get_mobula_config):
        """
        Test para obtener_tokens_top (excepción).
        Verifica que retorna una lista vacía si ocurre una excepción.
        """
        client = MobulaClient()
        limit = 50
        mock_requests.get.side_effect = requests.exceptions.RequestException("Connection Error")

        tokens = client.obtener_tokens_top(limit)

        # Verify requests.get was called
        mock_requests.get.assert_called_once_with(
            "https://api.mobula.io/api/v1/market/multi-data",
            headers=client.headers,
            params={
                "limit": limit,
                "sort": "market_cap",
                "order": "desc"
            },
            timeout=10
        )
        self.assertEqual(tokens, [])

    def test_obtener_datos_token_success(self, mock_requests, mock_get_mobula_config):
        """
        Test para obtener_datos_token (exitoso).
        Verifica que obtiene datos detallados de un token.
        """
        client = MobulaClient()
        token_id = "bitcoin"
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": {"id": "bitcoin", "symbol": "btc"}}
        mock_requests.get.return_value = mock_response

        token_data = client.obtener_datos_token(token_id)

        # Verify requests.get was called with correct parameters
        mock_requests.get.assert_called_once_with(
            f"https://api.mobula.io/api/v1/metadata/{token_id}",
            headers=client.headers,
            timeout=10
        )
        self.assertEqual(token_data, {"id": "bitcoin", "symbol": "btc"})

    def test_obtener_datos_token_failure(self, mock_requests, mock_get_mobula_config):
        """
        Test para obtener_datos_token (fallo).
        Verifica que retorna None si la solicitud falla.
        """
        client = MobulaClient()
        token_id = "nonexistent"
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.text = "Not Found"
        mock_requests.get.return_value = mock_response

        token_data = client.obtener_datos_token(token_id)

        # Verify requests.get was called
        mock_requests.get.assert_called_once_with(
            f"https://api.mobula.io/api/v1/metadata/{token_id}",
            headers=client.headers,
            timeout=10
        )
        self.assertIsNone(token_data)

    def test_obtener_datos_token_exception(self, mock_requests, mock_get_mobula_config):
        """
        Test para obtener_datos_token (excepción).
        Verifica que retorna None si ocurre una excepción.
        """
        client = MobulaClient()
        token_id = "bitcoin"
        mock_requests.get.side_effect = requests.exceptions.RequestException("Connection Error")

        token_data = client.obtener_datos_token(token_id)

        # Verify requests.get was called
        mock_requests.get.assert_called_once_with(
            f"https://api.mobula.io/api/v1/metadata/{token_id}",
            headers=client.headers,
            timeout=10
        )
        self.assertIsNone(token_data)

    @patch('src.apis.mobula_client.time.time') # Mock time.time()
    def test_obtener_precios_historicos_success(self, mock_time, mock_requests, mock_get_mobula_config):
        """
        Test para obtener_precios_historicos (exitoso).
        Verifica que obtiene precios históricos para un token.
        """
        client = MobulaClient()
        token_id = "bitcoin"
        dias = 7
        mock_time.return_value = 1678886400 # Mock current time (example timestamp)
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": [{"timestamp": 1678281600, "price": 20000}, {"timestamp": 1678886400, "price": 22000}]}
        mock_requests.get.return_value = mock_response

        historical_data = client.obtener_precios_historicos(token_id, dias)

        # Verify requests.get was called with correct parameters
        expected_from_timestamp = int(mock_time.return_value - (dias * 24 * 60 * 60))
        expected_to_timestamp = int(mock_time.return_value)
        expected_params = {
            "from": expected_from_timestamp,
            "to": expected_to_timestamp
        }
        mock_requests.get.assert_called_once_with(
            f"https://api.mobula.io/api/v1/market/history/{token_id}",
            headers=client.headers,
            params=expected_params,
            timeout=10
        )
        self.assertEqual(historical_data, [{"timestamp": 1678281600, "price": 20000}, {"timestamp": 1678886400, "price": 22000}])

    @patch('src.apis.mobula_client.time.time') # Mock time.time()
    def test_obtener_precios_historicos_failure(self, mock_time, mock_requests, mock_get_mobula_config):
        """
        Test para obtener_precios_historicos (fallo).
        Verifica que retorna una lista vacía si la solicitud falla.
        """
        client = MobulaClient()
        token_id = "nonexistent"
        dias = 7
        mock_time.return_value = 1678886400 # Mock current time (example timestamp)
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"
        mock_requests.get.return_value = mock_response

        historical_data = client.obtener_precios_historicos(token_id, dias)

        # Verify requests.get was called
        expected_from_timestamp = int(mock_time.return_value - (dias * 24 * 60 * 60))
        expected_to_timestamp = int(mock_time.return_value)
        mock_requests.get.assert_called_once_with(
            f"https://api.mobula.io/api/v1/market/history/{token_id}",
            headers=client.headers,
            params={
                "from": expected_from_timestamp,
                "to": expected_to_timestamp
            },
            timeout=10
        )
        self.assertEqual(historical_data, [])

    @patch('src.apis.mobula_client.time.time') # Mock time.time()
    def test_obtener_precios_historicos_exception(self, mock_time, mock_requests, mock_get_mobula_config):
        """
        Test para obtener_precios_historicos (excepción).
        Verifica que retorna una lista vacía si ocurre una excepción.
        """
        client = MobulaClient()
        token_id = "bitcoin"
        dias = 7
        mock_time.return_value = 1678886400 # Mock current time (example timestamp)
        mock_requests.get.side_effect = requests.exceptions.RequestException("Connection Error")

        historical_data = client.obtener_precios_historicos(token_id, dias)

        # Verify requests.get was called
        expected_from_timestamp = int(mock_time.return_value - (dias * 24 * 60 * 60))
        expected_to_timestamp = int(mock_time.return_value)
        mock_requests.get.assert_called_once_with(
            f"https://api.mobula.io/api/v1/market/history/{token_id}",
            headers=client.headers,
            params={
                "from": expected_from_timestamp,
                "to": expected_to_timestamp
            },
            timeout=10
        )
        self.assertEqual(historical_data, [])

    @patch.object(MobulaClient, 'obtener_precios_historicos')
    def test_calcular_metricas_rendimiento_success(self, mock_obtener_precios_historicos, mock_requests, mock_get_mobula_config):
        """
        Test para calcular_metricas_rendimiento (exitoso).
        Verifica que calcula métricas de rendimiento correctamente.
        """
        client = MobulaClient()
        token_id = "bitcoin"

        # Mock historical data for 1h, 24h, and 7d
        mock_obtener_precios_historicos.side_effect = [
            [{"timestamp": 1, "price": 100}, {"timestamp": 2, "price": 101}], # 1h data
            [{"timestamp": 10, "price": 95}, {"timestamp": 20, "price": 101}], # 24h data
            [{"timestamp": 100, "price": 90}, {"timestamp": 110, "price": 92}, {"timestamp": 120, "price": 98}, {"timestamp": 130, "price": 101}] # 7d data
        ]

        metrics = client.calcular_metricas_rendimiento(token_id)

        # Verify obtener_precios_historicos was called with correct parameters
        mock_obtener_precios_historicos.assert_any_call(token_id, dias=1)
        mock_obtener_precios_historicos.assert_any_call(token_id, dias=7)
        self.assertEqual(mock_obtener_precios_historicos.call_count, 3) # Called for 1h, 24h, and 7d

        # Expected calculations (approximate based on mock data)
        # 1h: ((101 - 100) / 100) * 100 = 1.0
        # 24h: ((101 - 95) / 95) * 100 = 6.31
        # 7d: ((101 - 90) / 90) * 100 = 12.22
        # Volatility: Daily returns from 7d data:
        # (92-90)/90 * 100 = 2.22
        # (98-92)/92 * 100 = 6.52
        # (101-98)/98 * 100 = 3.06
        # Volatility = (|2.22| + |6.52| + |3.06|) / 3 = 11.8 / 3 = 3.93 (approx)

        # Note: The actual calculation in the method uses the last price from the 1h data for 24h and 7d calculations if those lists are not empty.
        # Let's re-calculate based on the actual method logic:
        # precio_actual = 101 (from 1h data)
        # precio_1h = 100 (from 1h data) -> rendimiento_1h = ((101 - 100) / 100) * 100 = 1.0
        # precio_24h = 95 (from 24h data) -> rendimiento_24h = ((101 - 95) / 95) * 100 = 6.315... -> 6.32
        # precio_7d = 90 (from 7d data) -> rendimiento_7d = ((101 - 90) / 90) * 100 = 12.222... -> 12.22
        # Volatility: Daily returns from 7d data:
        # (92-90)/90 * 100 = 2.22
        # (98-92)/92 * 100 = 6.52
        # (101-98)/98 * 100 = 3.06
        # Volatility = (|2.22| + |6.52| + |3.06|) / 3 = 11.8 / 3 = 3.93 (approx)

        self.assertAlmostEqual(metrics["rendimiento_1h"], 1.0, places=2)
        self.assertAlmostEqual(metrics["rendimiento_24h"], 6.32, places=2)
        self.assertAlmostEqual(metrics["rendimiento_7d"], 12.22, places=2)
        self.assertAlmostEqual(metrics["volatilidad"], 3.93, places=2)


    @patch.object(MobulaClient, 'obtener_precios_historicos')
    def test_calcular_metricas_rendimiento_empty_data(self, mock_obtener_precios_historicos, mock_requests, mock_get_mobula_config):
        """
        Test para calcular_metricas_rendimiento (datos vacíos).
        Verifica que retorna métricas cero si los datos históricos están vacíos.
        """
        client = MobulaClient()
        token_id = "token_without_data"

        # Mock historical data to be empty
        mock_obtener_precios_historicos.return_value = []

        metrics = client.calcular_metricas_rendimiento(token_id)

        # Verify obtener_precios_historicos was called
        mock_obtener_precios_historicos.assert_any_call(token_id, dias=1)
        mock_obtener_precios_historicos.assert_any_call(token_id, dias=7)
        self.assertEqual(mock_obtener_precios_historicos.call_count, 3) # Called for 1h, 24h, and 7d

        # Verify metrics are zero
        self.assertEqual(metrics, {
            "rendimiento_1h": 0.0,
            "rendimiento_24h": 0.0,
            "rendimiento_7d": 0.0,
            "volatilidad": 0.0
        })

    @patch.object(MobulaClient, 'obtener_precios_historicos')
    def test_calcular_metricas_rendimiento_exception(self, mock_obtener_precios_historicos, mock_requests, mock_get_mobula_config):
        """
        Test para calcular_metricas_rendimiento (excepción).
        Verifica que retorna métricas cero si ocurre una excepción.
        """
        client = MobulaClient()
        token_id = "bitcoin"

        # Simulate an exception when getting historical data
        mock_obtener_precios_historicos.side_effect = Exception("Calculation Error")

        metrics = client.calcular_metricas_rendimiento(token_id)

        # Verify obtener_precios_historicos was called
        mock_obtener_precios_historicos.assert_any_call(token_id, dias=1)
        # Note: The method might not call for 7d data if 1h or 24h calls fail first.
        # We just need to ensure it returns zero metrics on exception.

        # Verify metrics are zero
        self.assertEqual(metrics, {
            "rendimiento_1h": 0.0,
            "rendimiento_24h": 0.0,
            "rendimiento_7d": 0.0,
            "volatilidad": 0.0
        })


if __name__ == '__main__':
    unittest.main()
