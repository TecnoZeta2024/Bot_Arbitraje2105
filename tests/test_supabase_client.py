import unittest
from unittest.mock import patch, MagicMock

from src.apis.supabase_client import SupabaseClient

# Mock de las dependencias externas
@patch('src.apis.supabase_client.create_client')
@patch('src.apis.supabase_client.get_supabase_config')
class TestSupabaseClient(unittest.TestCase):

    def setUp(self):
        """Configuración común para los tests."""
        # Reset mocks before each test
        self.mock_create_client.reset_mock()
        self.mock_get_supabase_config.reset_mock()

        # Configure default mock settings
        self.mock_get_supabase_config.return_value = {
            "url": "https://test.supabase.co",
            "key": "test_supabase_key"
        }
        self.mock_supabase_instance = MagicMock()
        self.mock_create_client.return_value = self.mock_supabase_instance

    @patch('src.apis.supabase_client.get_logger') # Mock logger to prevent output during tests
    def test_init(self, mock_get_logger, mock_create_client, mock_get_supabase_config):
        """
        Test para la inicialización del cliente Supabase.
        """
        client = SupabaseClient()

        # Verify config and create_client were used
        mock_get_supabase_config.assert_called_once()
        mock_create_client.assert_called_once_with(
            "https://test.supabase.co",
            "test_supabase_key"
        )

        # Verify attribute
        self.assertEqual(client.client, self.mock_supabase_instance)

    # Add tests for SupabaseClient methods here
    # For example: test_insert_data_success, test_insert_data_failure, etc.

    def test_insertar_token_success(self, mock_create_client, mock_get_supabase_config):
        """
        Test para insertar_token (exitoso).
        Verifica que inserta un token candidato.
        """
        client = SupabaseClient()
        token_data = {"simbolo": "BTC", "nombre": "Bitcoin"}
        mock_execute = MagicMock()
        mock_execute.execute.return_value = MagicMock(data=[token_data])
        client.supabase.table.return_value.insert.return_value = mock_execute

        inserted_token = client.insertar_token(token_data)

        # Verify Supabase client methods were called
        client.supabase.table.assert_called_once_with("token_candidatos")
        client.supabase.table.return_value.insert.assert_called_once_with(token_data)
        mock_execute.execute.assert_called_once()
        self.assertEqual(inserted_token, token_data)

    def test_insertar_token_exception(self, mock_create_client, mock_get_supabase_config):
        """
        Test para insertar_token (excepción).
        Verifica que lanza una excepción si ocurre un error.
        """
        client = SupabaseClient()
        token_data = {"simbolo": "BTC", "nombre": "Bitcoin"}
        client.supabase.table.side_effect = Exception("DB Error")

        with self.assertRaises(Exception):
            client.insertar_token(token_data)

        # Verify Supabase client methods were called
        client.supabase.table.assert_called_once_with("token_candidatos")

    def test_insertar_tokens_success(self, mock_create_client, mock_get_supabase_config):
        """
        Test para insertar_tokens (exitoso).
        Verifica que inserta múltiples tokens candidatos.
        """
        client = SupabaseClient()
        tokens_data = [{"simbolo": "BTC", "nombre": "Bitcoin"}, {"simbolo": "ETH", "nombre": "Ethereum"}]
        mock_execute = MagicMock()
        mock_execute.execute.return_value = MagicMock(data=tokens_data)
        client.supabase.table.return_value.insert.return_value = mock_execute

        inserted_tokens = client.insertar_tokens(tokens_data)

        # Verify Supabase client methods were called
        client.supabase.table.assert_called_once_with("token_candidatos")
        client.supabase.table.return_value.insert.assert_called_once_with(tokens_data)
        mock_execute.execute.assert_called_once()
        self.assertEqual(inserted_tokens, tokens_data)

    def test_insertar_tokens_exception(self, mock_create_client, mock_get_supabase_config):
        """
        Test para insertar_tokens (excepción).
        Verifica que lanza una excepción si ocurre un error.
        """
        client = SupabaseClient()
        tokens_data = [{"simbolo": "BTC", "nombre": "Bitcoin"}, {"simbolo": "ETH", "nombre": "Ethereum"}]
        client.supabase.table.side_effect = Exception("DB Error")

        with self.assertRaises(Exception):
            client.insertar_tokens(tokens_data)

        # Verify Supabase client methods were called
        client.supabase.table.assert_called_once_with("token_candidatos")

    def test_obtener_tokens_success(self, mock_create_client, mock_get_supabase_config):
        """
        Test para obtener_tokens (exitoso).
        Verifica que obtiene la lista de tokens candidatos.
        """
        client = SupabaseClient()
        limit = 10
        mock_execute = MagicMock()
        mock_execute.execute.return_value = MagicMock(data=[{"simbolo": "BTC"}, {"simbolo": "ETH"}])
        client.supabase.table.return_value.select.return_value.limit.return_value = mock_execute

        tokens = client.obtener_tokens(limit)

        # Verify Supabase client methods were called
        client.supabase.table.assert_called_once_with("token_candidatos")
        client.supabase.table.return_value.select.assert_called_once_with("*")
        client.supabase.table.return_value.select.return_value.limit.assert_called_once_with(limit)
        mock_execute.execute.assert_called_once()
        self.assertEqual(tokens, [{"simbolo": "BTC"}, {"simbolo": "ETH"}])

    def test_obtener_tokens_exception(self, mock_create_client, mock_get_supabase_config):
        """
        Test para obtener_tokens (excepción).
        Verifica que retorna una lista vacía si ocurre un error.
        """
        client = SupabaseClient()
        limit = 10
        client.supabase.table.side_effect = Exception("DB Error")

        tokens = client.obtener_tokens(limit)

        # Verify Supabase client methods were called
        client.supabase.table.assert_called_once_with("token_candidatos")
        self.assertEqual(tokens, [])

    def test_obtener_token_por_simbolo_success_found(self, mock_create_client, mock_get_supabase_config):
        """
        Test para obtener_token_por_simbolo (exitoso - encontrado).
        Verifica que obtiene un token por su símbolo.
        """
        client = SupabaseClient()
        simbolo = "BTC"
        token_data = {"simbolo": "BTC", "nombre": "Bitcoin"}
        mock_execute = MagicMock()
        mock_execute.execute.return_value = MagicMock(data=[token_data])
        client.supabase.table.return_value.select.return_value.eq.return_value = mock_execute

        token = client.obtener_token_por_simbolo(simbolo)

        # Verify Supabase client methods were called
        client.supabase.table.assert_called_once_with("token_candidatos")
        client.supabase.table.return_value.select.assert_called_once_with("*")
        client.supabase.table.return_value.select.return_value.eq.assert_called_once_with("simbolo", simbolo)
        mock_execute.execute.assert_called_once()
        self.assertEqual(token, token_data)

    def test_obtener_token_por_simbolo_success_not_found(self, mock_create_client, mock_get_supabase_config):
        """
        Test para obtener_token_por_simbolo (exitoso - no encontrado).
        Verifica que retorna None si el token no existe.
        """
        client = SupabaseClient()
        simbolo = "NONEXISTENT"
        mock_execute = MagicMock()
        mock_execute.execute.return_value = MagicMock(data=[]) # Empty data list
        client.supabase.table.return_value.select.return_value.eq.return_value = mock_execute

        token = client.obtener_token_por_simbolo(simbolo)

        # Verify Supabase client methods were called
        client.supabase.table.assert_called_once_with("token_candidatos")
        client.supabase.table.return_value.select.assert_called_once_with("*")
        client.supabase.table.return_value.select.return_value.eq.assert_called_once_with("simbolo", simbolo)
        mock_execute.execute.assert_called_once()
        self.assertIsNone(token)

    def test_obtener_token_por_simbolo_exception(self, mock_create_client, mock_get_supabase_config):
        """
        Test para obtener_token_por_simbolo (excepción).
        Verifica que retorna None si ocurre un error.
        """
        client = SupabaseClient()
        simbolo = "BTC"
        client.supabase.table.side_effect = Exception("DB Error")

        token = client.obtener_token_por_simbolo(simbolo)

        # Verify Supabase client methods were called
        client.supabase.table.assert_called_once_with("token_candidatos")
        self.assertIsNone(token)

    def test_actualizar_token_success(self, mock_create_client, mock_get_supabase_config):
        """
        Test para actualizar_token (exitoso).
        Verifica que actualiza los datos de un token candidato.
        """
        client = SupabaseClient()
        simbolo = "BTC"
        actualizacion_data = {"nombre": "Bitcoin Updated"}
        updated_token_data = {"simbolo": "BTC", "nombre": "Bitcoin Updated"}
        mock_execute = MagicMock()
        mock_execute.execute.return_value = MagicMock(data=[updated_token_data])
        client.supabase.table.return_value.update.return_value.eq.return_value = mock_execute

        updated_token = client.actualizar_token(simbolo, actualizacion_data)

        # Verify Supabase client methods were called
        client.supabase.table.assert_called_once_with("token_candidatos")
        client.supabase.table.return_value.update.assert_called_once_with(actualizacion_data)
        client.supabase.table.return_value.update.return_value.eq.assert_called_once_with("simbolo", simbolo)
        mock_execute.execute.assert_called_once()
        self.assertEqual(updated_token, updated_token_data)

    def test_actualizar_token_exception(self, mock_create_client, mock_get_supabase_config):
        """
        Test para actualizar_token (excepción).
        Verifica que lanza una excepción si ocurre un error.
        """
        client = SupabaseClient()
        simbolo = "BTC"
        actualizacion_data = {"nombre": "Bitcoin Updated"}
        client.supabase.table.side_effect = Exception("DB Error")

        with self.assertRaises(Exception):
            client.actualizar_token(simbolo, actualizacion_data)

        # Verify Supabase client methods were called
        client.supabase.table.assert_called_once_with("token_candidatos")

    def test_eliminar_token_success(self, mock_create_client, mock_get_supabase_config):
        """
        Test para eliminar_token (exitoso).
        Verifica que elimina un token candidato.
        """
        client = SupabaseClient()
        simbolo = "BTC"
        deleted_token_data = {"simbolo": "BTC", "nombre": "Bitcoin"}
        mock_execute = MagicMock()
        mock_execute.execute.return_value = MagicMock(data=[deleted_token_data])
        client.supabase.table.return_value.delete.return_value.eq.return_value = mock_execute

        deleted_token = client.eliminar_token(simbolo)

        # Verify Supabase client methods were called
        client.supabase.table.assert_called_once_with("token_candidatos")
        client.supabase.table.return_value.delete.assert_called_once()
        client.supabase.table.return_value.delete.return_value.eq.assert_called_once_with("simbolo", simbolo)
        mock_execute.execute.assert_called_once()
        self.assertEqual(deleted_token, deleted_token_data)

    def test_eliminar_token_exception(self, mock_create_client, mock_get_supabase_config):
        """
        Test para eliminar_token (excepción).
        Verifica que lanza una excepción si ocurre un error.
        """
        client = SupabaseClient()
        simbolo = "BTC"
        client.supabase.table.side_effect = Exception("DB Error")

        with self.assertRaises(Exception):
            client.eliminar_token(simbolo)

        # Verify Supabase client methods were called
        client.supabase.table.assert_called_once_with("token_candidatos")

    def test_insertar_oportunidad_success(self, mock_create_client, mock_get_supabase_config):
        """
        Test para insertar_oportunidad (exitoso).
        Verifica que inserta una oportunidad detectada, manejando campos JSON.
        """
        client = SupabaseClient()
        oportunidad_data = {"ruta": "BTC->ETH->BTC", "pares_comercio": ["BTC/ETH", "ETH/BTC"], "rentabilidad_teorica": 0.01}
        expected_insert_data = {"ruta": "BTC->ETH->BTC", "pares_comercio": '["BTC/ETH", "ETH/BTC"]', "rentabilidad_teorica": 0.01}
        mock_execute = MagicMock()
        mock_execute.execute.return_value = MagicMock(data=[expected_insert_data])
        client.supabase.table.return_value.insert.return_value = mock_execute

        inserted_oportunidad = client.insertar_oportunidad(oportunidad_data)

        # Verify Supabase client methods were called
        client.supabase.table.assert_called_once_with("oportunidades_detectadas")
        client.supabase.table.return_value.insert.assert_called_once_with(expected_insert_data)
        mock_execute.execute.assert_called_once()
        self.assertEqual(inserted_oportunidad, expected_insert_data)

    def test_insertar_oportunidad_exception(self, mock_create_client, mock_get_supabase_config):
        """
        Test para insertar_oportunidad (excepción).
        Verifica que lanza una excepción si ocurre un error.
        """
        client = SupabaseClient()
        oportunidad_data = {"ruta": "BTC->ETH->BTC", "pares_comercio": ["BTC/ETH", "ETH/BTC"], "rentabilidad_teorica": 0.01}
        client.supabase.table.side_effect = Exception("DB Error")

        with self.assertRaises(Exception):
            client.insertar_oportunidad(oportunidad_data)

        # Verify Supabase client methods were called
        client.supabase.table.assert_called_once_with("oportunidades_detectadas")

    def test_obtener_oportunidades_success(self, mock_create_client, mock_get_supabase_config):
        """
        Test para obtener_oportunidades (exitoso).
        Verifica que obtiene la lista de oportunidades detectadas.
        """
        client = SupabaseClient()
        limit = 10
        oportunidades_data = [{"id": "1", "ruta": "BTC->ETH->BTC"}, {"id": "2", "ruta": "ETH->BTC->ETH"}]
        mock_execute = MagicMock()
        mock_execute.execute.return_value = MagicMock(data=oportunidades_data)
        client.supabase.table.return_value.select.return_value.order.return_value.limit.return_value = mock_execute

        oportunidades = client.obtener_oportunidades(limit)

        # Verify Supabase client methods were called
        client.supabase.table.assert_called_once_with("oportunidades_detectadas")
        client.supabase.table.return_value.select.assert_called_once_with("*")
        client.supabase.table.return_value.select.return_value.order.assert_called_once_with("fecha_deteccion", desc=True)
        client.supabase.table.return_value.select.return_value.order.return_value.limit.assert_called_once_with(limit)
        mock_execute.execute.assert_called_once()
        self.assertEqual(oportunidades, oportunidades_data)

    def test_obtener_oportunidades_exception(self, mock_create_client, mock_get_supabase_config):
        """
        Test para obtener_oportunidades (excepción).
        Verifica que retorna una lista vacía si ocurre un error.
        """
        client = SupabaseClient()
        limit = 10
        client.supabase.table.side_effect = Exception("DB Error")

        oportunidades = client.obtener_oportunidades(limit)

        # Verify Supabase client methods were called
        client.supabase.table.assert_called_once_with("oportunidades_detectadas")
        self.assertEqual(oportunidades, [])

    def test_actualizar_oportunidad_success(self, mock_create_client, mock_get_supabase_config):
        """
        Test para actualizar_oportunidad (exitoso).
        Verifica que actualiza los datos de una oportunidad, manejando campos JSON.
        """
        client = SupabaseClient()
        oportunidad_id = "123"
        actualizacion_data = {"estado": "ejecutada", "pares_comercio": ["BTC/ETH", "ETH/BTC"]}
        expected_update_data = {"estado": "ejecutada", "pares_comercio": '["BTC/ETH", "ETH/BTC"]'}
        updated_oportunidad_data = {"id": oportunidad_id, "estado": "ejecutada", "pares_comercio": '["BTC/ETH", "ETH/BTC"]'}
        mock_execute = MagicMock()
        mock_execute.execute.return_value = MagicMock(data=[updated_oportunidad_data])
        client.supabase.table.return_value.update.return_value.eq.return_value = mock_execute

        updated_oportunidad = client.actualizar_oportunidad(oportunidad_id, actualizacion_data)

        # Verify Supabase client methods were called
        client.supabase.table.assert_called_once_with("oportunidades_detectadas")
        client.supabase.table.return_value.update.assert_called_once_with(expected_update_data)
        client.supabase.table.return_value.update.return_value.eq.assert_called_once_with("id", oportunidad_id)
        mock_execute.execute.assert_called_once()
        self.assertEqual(updated_oportunidad, updated_oportunidad_data)

    def test_actualizar_oportunidad_exception(self, mock_create_client, mock_get_supabase_config):
        """
        Test para actualizar_oportunidad (excepción).
        Verifica que lanza una excepción si ocurre un error.
        """
        client = SupabaseClient()
        oportunidad_id = "123"
        actualizacion_data = {"estado": "ejecutada"}
        client.supabase.table.side_effect = Exception("DB Error")

        with self.assertRaises(Exception):
            client.actualizar_oportunidad(oportunidad_id, actualizacion_data)

        # Verify Supabase client methods were called
        client.supabase.table.assert_called_once_with("oportunidades_detectadas")

    def test_eliminar_oportunidad_success(self, mock_create_client, mock_get_supabase_config):
        """
        Test para eliminar_oportunidad (exitoso).
        Verifica que elimina una oportunidad detectada.
        """
        client = SupabaseClient()
        oportunidad_id = "123"
        deleted_oportunidad_data = {"id": oportunidad_id, "ruta": "BTC->ETH->BTC"}
        mock_execute = MagicMock()
        mock_execute.execute.return_value = MagicMock(data=[deleted_oportunidad_data])
        client.supabase.table.return_value.delete.return_value.eq.return_value = mock_execute

        deleted_oportunidad = client.eliminar_oportunidad(oportunidad_id)

        # Verify Supabase client methods were called
        client.supabase.table.assert_called_once_with("oportunidades_detectadas")
        client.supabase.table.return_value.delete.assert_called_once()
        client.supabase.table.return_value.delete.return_value.eq.assert_called_once_with("id", oportunidad_id)
        mock_execute.execute.assert_called_once()
        self.assertEqual(deleted_oportunidad, deleted_oportunidad_data)

    def test_eliminar_oportunidad_exception(self, mock_create_client, mock_get_supabase_config):
        """
        Test para eliminar_oportunidad (excepción).
        Verifica que lanza una excepción si ocurre un error.
        """
        client = SupabaseClient()
        oportunidad_id = "123"
        client.supabase.table.side_effect = Exception("DB Error")

        with self.assertRaises(Exception):
            client.eliminar_oportunidad(oportunidad_id)

        # Verify Supabase client methods were called
        client.supabase.table.assert_called_once_with("oportunidades_detectadas")

    def test_insertar_operacion_success(self, mock_create_client, mock_get_supabase_config):
        """
        Test para insertar_operacion (exitoso).
        Verifica que inserta una operación de arbitraje, manejando campos JSON.
        """
        client = SupabaseClient()
        operacion_data = {
            "operacion_id": "op123",
            "ruta": "BTC->ETH->BTC",
            "analisis_ia": {"recomendacion": "PROCEDER"},
            "pares_ejecutados": ["BTC/ETH", "ETH/BTC"],
            "precios_reales": {"BTC/ETH": 0.05, "ETH/BTC": 20}
        }
        expected_insert_data = {
            "operacion_id": "op123",
            "ruta": "BTC->ETH->BTC",
            "analisis_ia": '{"recomendacion": "PROCEDER"}',
            "pares_ejecutados": '["BTC/ETH", "ETH/BTC"]',
            "precios_reales": '{"BTC/ETH": 0.05, "ETH/BTC": 20}'
        }
        mock_execute = MagicMock()
        mock_execute.execute.return_value = MagicMock(data=[expected_insert_data])
        client.supabase.table.return_value.insert.return_value = mock_execute

        inserted_operacion = client.insertar_operacion(operacion_data)

        # Verify Supabase client methods were called
        client.supabase.table.assert_called_once_with("arbitraje_operaciones")
        client.supabase.table.return_value.insert.assert_called_once_with(expected_insert_data)
        mock_execute.execute.assert_called_once()
        self.assertEqual(inserted_operacion, expected_insert_data)

    def test_insertar_operacion_exception(self, mock_create_client, mock_get_supabase_config):
        """
        Test para insertar_operacion (excepción).
        Verifica que lanza una excepción si ocurre un error.
        """
        client = SupabaseClient()
        operacion_data = {
            "operacion_id": "op123",
            "ruta": "BTC->ETH->BTC",
            "analisis_ia": {"recomendacion": "PROCEDER"},
            "pares_ejecutados": ["BTC/ETH", "ETH/BTC"],
            "precios_reales": {"BTC/ETH": 0.05, "ETH/BTC": 20}
        }
        client.supabase.table.side_effect = Exception("DB Error")

        with self.assertRaises(Exception):
            client.insertar_operacion(operacion_data)

        # Verify Supabase client methods were called
        client.supabase.table.assert_called_once_with("arbitraje_operaciones")

    def test_actualizar_operacion_success(self, mock_create_client, mock_get_supabase_config):
        """
        Test para actualizar_operacion (exitoso).
        Verifica que actualiza los datos de una operación, manejando campos JSON.
        """
        client = SupabaseClient()
        operacion_id = "op123"
        actualizacion_data = {
            "estado": "completada",
            "pares_ejecutados": ["BTC/ETH", "ETH/BTC"],
            "precios_reales": {"BTC/ETH": 0.05, "ETH/BTC": 20}
        }
        expected_update_data = {
            "estado": "completada",
            "pares_ejecutados": '["BTC/ETH", "ETH/BTC"]',
            "precios_reales": '{"BTC/ETH": 0.05, "ETH/BTC": 20}'
        }
        updated_operacion_data = {
            "operacion_id": operacion_id,
            "estado": "completada",
            "pares_ejecutados": '["BTC/ETH", "ETH/BTC"]',
            "precios_reales": '{"BTC/ETH": 0.05, "ETH/BTC": 20}'
        }
        mock_execute = MagicMock()
        mock_execute.execute.return_value = MagicMock(data=[updated_operacion_data])
        client.supabase.table.return_value.update.return_value.eq.return_value = mock_execute

        updated_operacion = client.actualizar_operacion(operacion_id, actualizacion_data)

        # Verify Supabase client methods were called
        client.supabase.table.assert_called_once_with("arbitraje_operaciones")
        client.supabase.table.return_value.update.assert_called_once_with(expected_update_data)
        client.supabase.table.return_value.update.return_value.eq.assert_called_once_with("operacion_id", operacion_id)
        mock_execute.execute.assert_called_once()
        self.assertEqual(updated_operacion, updated_operacion_data)

    def test_actualizar_operacion_exception(self, mock_create_client, mock_get_supabase_config):
        """
        Test para actualizar_operacion (excepción).
        Verifica que lanza una excepción si ocurre un error.
        """
        client = SupabaseClient()
        operacion_id = "op123"
        actualizacion_data = {"estado": "completada"}
        client.supabase.table.side_effect = Exception("DB Error")

        with self.assertRaises(Exception):
            client.actualizar_operacion(operacion_id, actualizacion_data)

        # Verify Supabase client methods were called
        client.supabase.table.assert_called_once_with("arbitraje_operaciones")

    def test_obtener_operacion_success_found(self, mock_create_client, mock_get_supabase_config):
        """
        Test para obtener_operacion (exitoso - encontrado).
        Verifica que obtiene una operación por su ID.
        """
        client = SupabaseClient()
        operacion_id = "op123"
        operacion_data = {"operacion_id": operacion_id, "ruta": "BTC->ETH->BTC"}
        mock_execute = MagicMock()
        mock_execute.execute.return_value = MagicMock(data=[operacion_data])
        client.supabase.table.return_value.select.return_value.eq.return_value = mock_execute

        operacion = client.obtener_operacion(operacion_id)

        # Verify Supabase client methods were called
        client.supabase.table.assert_called_once_with("arbitraje_operaciones")
        client.supabase.table.return_value.select.assert_called_once_with("*")
        client.supabase.table.return_value.select.return_value.eq.assert_called_once_with("operacion_id", operacion_id)
        mock_execute.execute.assert_called_once()
        self.assertEqual(operacion, operacion_data)

    def test_obtener_operacion_success_not_found(self, mock_create_client, mock_get_supabase_config):
        """
        Test para obtener_operacion (exitoso - no encontrado).
        Verifica que retorna None si la operación no existe.
        """
        client = SupabaseClient()
        operacion_id = "nonexistent_op"
        mock_execute = MagicMock()
        mock_execute.execute.return_value = MagicMock(data=[]) # Empty data list
        client.supabase.table.return_value.select.return_value.eq.return_value = mock_execute

        operacion = client.obtener_operacion(operacion_id)

        # Verify Supabase client methods were called
        client.supabase.table.assert_called_once_with("arbitraje_operaciones")
        client.supabase.table.return_value.select.assert_called_once_with("*")
        client.supabase.table.return_value.select.return_value.eq.assert_called_once_with("operacion_id", operacion_id)
        mock_execute.execute.assert_called_once()
        self.assertIsNone(operacion)

    def test_obtener_operacion_exception(self, mock_create_client, mock_get_supabase_config):
        """
        Test para obtener_operacion (excepción).
        Verifica que retorna None si ocurre un error.
        """
        client = SupabaseClient()
        operacion_id = "op123"
        client.supabase.table.side_effect = Exception("DB Error")

        operacion = client.obtener_operacion(operacion_id)

        # Verify Supabase client methods were called
        client.supabase.table.assert_called_once_with("arbitraje_operaciones")
        self.assertIsNone(operacion)

    def test_obtener_operaciones_recientes_success(self, mock_create_client, mock_get_supabase_config):
        """
        Test para obtener_operaciones_recientes (exitoso).
        Verifica que obtiene la lista de operaciones recientes.
        """
        client = SupabaseClient()
        limit = 5
        operaciones_data = [{"operacion_id": "op1"}, {"operacion_id": "op2"}]
        mock_execute = MagicMock()
        mock_execute.execute.return_value = MagicMock(data=operaciones_data)
        client.supabase.table.return_value.select.return_value.order.return_value.limit.return_value = mock_execute

        operaciones = client.obtener_operaciones_recientes(limit)

        # Verify Supabase client methods were called
        client.supabase.table.assert_called_once_with("arbitraje_operaciones")
        client.supabase.table.return_value.select.assert_called_once_with("*")
        client.supabase.table.return_value.select.return_value.order.assert_called_once_with("fecha_completado", desc=True)
        client.supabase.table.return_value.select.return_value.order.return_value.limit.assert_called_once_with(limit)
        mock_execute.execute.assert_called_once()
        self.assertEqual(operaciones, operaciones_data)

    def test_obtener_operaciones_recientes_exception(self, mock_create_client, mock_get_supabase_config):
        """
        Test para obtener_operaciones_recientes (excepción).
        Verifica que retorna una lista vacía si ocurre un error.
        """
        client = SupabaseClient()
        limit = 5
        client.supabase.table.side_effect = Exception("DB Error")

        operaciones = client.obtener_operaciones_recientes(limit)

        # Verify Supabase client methods were called
        client.supabase.table.assert_called_once_with("arbitraje_operaciones")
        self.assertEqual(operaciones, [])

    def test_eliminar_operacion_success(self, mock_create_client, mock_get_supabase_config):
        """
        Test para eliminar_operacion (exitoso).
        Verifica que elimina una operación de arbitraje.
        """
        client = SupabaseClient()
        operacion_id = "op123"
        deleted_operacion_data = {"operacion_id": operacion_id, "ruta": "BTC->ETH->BTC"}
        mock_execute = MagicMock()
        mock_execute.execute.return_value = MagicMock(data=[deleted_operacion_data])
        client.supabase.table.return_value.delete.return_value.eq.return_value = mock_execute

        deleted_operacion = client.eliminar_operacion(operacion_id)

        # Verify Supabase client methods were called
        client.supabase.table.assert_called_once_with("arbitraje_operaciones")
        client.supabase.table.return_value.delete.assert_called_once()
        client.supabase.table.return_value.delete.return_value.eq.assert_called_once_with("operacion_id", operacion_id)
        mock_execute.execute.assert_called_once()
        self.assertEqual(deleted_operacion, deleted_operacion_data)

    def test_eliminar_operacion_exception(self, mock_create_client, mock_get_supabase_config):
        """
        Test para eliminar_operacion (excepción).
        Verifica que lanza una excepción si ocurre un error.
        """
        client = SupabaseClient()
        operacion_id = "op123"
        client.supabase.table.side_effect = Exception("DB Error")

        with self.assertRaises(Exception):
            client.eliminar_operacion(operacion_id)

        # Verify Supabase client methods were called
        client.supabase.table.assert_called_once_with("arbitraje_operaciones")

    def test_obtener_configuracion_success_found(self, mock_create_client, mock_get_supabase_config):
        """
        Test para obtener_configuracion (exitoso - encontrado).
        Verifica que obtiene la configuración del sistema.
        """
        client = SupabaseClient()
        config_data = {"id": "sys_config", "param1": "value1"}
        mock_execute = MagicMock()
        mock_execute.execute.return_value = MagicMock(data=[config_data])
        client.supabase.table.return_value.select.return_value.limit.return_value = mock_execute

        config = client.obtener_configuracion()

        # Verify Supabase client methods were called
        client.supabase.table.assert_called_once_with("configuracion_sistema")
        client.supabase.table.return_value.select.assert_called_once_with("*")
        client.supabase.table.return_value.select.return_value.limit.assert_called_once_with(1)
        mock_execute.execute.assert_called_once()
        self.assertEqual(config, config_data)

    def test_obtener_configuracion_success_not_found(self, mock_create_client, mock_get_supabase_config):
        """
        Test para obtener_configuracion (exitoso - no encontrado).
        Verifica que retorna None si la configuración no existe.
        """
        client = SupabaseClient()
        mock_execute = MagicMock()
        mock_execute.execute.return_value = MagicMock(data=[]) # Empty data list
        client.supabase.table.return_value.select.return_value.limit.return_value = mock_execute

        config = client.obtener_configuracion()

        # Verify Supabase client methods were called
        client.supabase.table.assert_called_once_with("configuracion_sistema")
        client.supabase.table.return_value.select.assert_called_once_with("*")
        client.supabase.table.return_value.select.return_value.limit.assert_called_once_with(1)
        mock_execute.execute.assert_called_once()
        self.assertIsNone(config)

    def test_obtener_configuracion_exception(self, mock_create_client, mock_get_supabase_config):
        """
        Test para obtener_configuracion (excepción).
        Verifica que retorna None si ocurre un error.
        """
        client = SupabaseClient()
        client.supabase.table.side_effect = Exception("DB Error")

        config = client.obtener_configuracion()

        # Verify Supabase client methods were called
        client.supabase.table.assert_called_once_with("configuracion_sistema")
        self.assertIsNone(config)

    @patch.object(SupabaseClient, 'obtener_configuracion')
    def test_actualizar_configuracion_success(self, mock_obtener_configuracion, mock_create_client, mock_get_supabase_config):
        """
        Test para actualizar_configuracion (exitoso).
        Verifica que actualiza la configuración del sistema.
        """
        client = SupabaseClient()
        actualizacion_data = {"param1": "updated_value"}
        current_config = {"id": "sys_config", "param1": "value1"}
        updated_config_data = {"id": "sys_config", "param1": "updated_value"}

        mock_obtener_configuracion.return_value = current_config # Mock getting current config

        mock_execute = MagicMock()
        mock_execute.execute.return_value = MagicMock(data=[updated_config_data])
        client.supabase.table.return_value.update.return_value.eq.return_value = mock_execute

        updated_config = client.actualizar_configuracion(actualizacion_data)

        # Verify Supabase client methods were called
        mock_obtener_configuracion.assert_called_once()
        client.supabase.table.assert_called_once_with("configuracion_sistema")
        client.supabase.table.return_value.update.assert_called_once_with(actualizacion_data)
        client.supabase.table.return_value.update.return_value.eq.assert_called_once_with("id", current_config['id'])
        mock_execute.execute.assert_called_once()
        self.assertEqual(updated_config, updated_config_data)

    @patch.object(SupabaseClient, 'obtener_configuracion')
    def test_actualizar_configuracion_no_existing_config(self, mock_obtener_configuracion, mock_create_client, mock_get_supabase_config):
        """
        Test para actualizar_configuracion (no existe configuración).
        Verifica que retorna un diccionario vacío si no hay configuración existente.
        """
        client = SupabaseClient()
        actualizacion_data = {"param1": "updated_value"}

        mock_obtener_configuracion.return_value = None # Mock no existing config

        updated_config = client.actualizar_configuracion(actualizacion_data)

        # Verify obtener_configuracion was called
        mock_obtener_configuracion.assert_called_once()
        # Verify that update was NOT called
        client.supabase.table.return_value.update.assert_not_called()
        self.assertEqual(updated_config, {})

    @patch.object(SupabaseClient, 'obtener_configuracion')
    def test_actualizar_configuracion_exception(self, mock_obtener_configuracion, mock_create_client, mock_get_supabase_config):
        """
        Test para actualizar_configuracion (excepción).
        Verifica que lanza una excepción si ocurre un error.
        """
        client = SupabaseClient()
        actualizacion_data = {"param1": "updated_value"}
        current_config = {"id": "sys_config", "param1": "value1"}

        mock_obtener_configuracion.return_value = current_config # Mock getting current config
        client.supabase.table.side_effect = Exception("DB Error")

        with self.assertRaises(Exception):
            client.actualizar_configuracion(actualizacion_data)

        # Verify Supabase client methods were called
        mock_obtener_configuracion.assert_called_once()
        client.supabase.table.assert_called_once_with("configuracion_sistema")

    def test_insertar_metrica_success(self, mock_create_client, mock_get_supabase_config):
        """
        Test para insertar_metrica (exitoso).
        Verifica que inserta una métrica de rendimiento.
        """
        client = SupabaseClient()
        metrica_data = {"token_simbolo": "BTC", "rendimiento_24h": 5.0}
        mock_execute = MagicMock()
        mock_execute.execute.return_value = MagicMock(data=[metrica_data])
        client.supabase.table.return_value.insert.return_value = mock_execute

        inserted_metrica = client.insertar_metrica(metrica_data)

        # Verify Supabase client methods were called
        client.supabase.table.assert_called_once_with("metricas_rendimiento")
        client.supabase.table.return_value.insert.assert_called_once_with(metrica_data)
        mock_execute.execute.assert_called_once()
        self.assertEqual(inserted_metrica, metrica_data)

    def test_insertar_metrica_exception(self, mock_create_client, mock_get_supabase_config):
        """
        Test para insertar_metrica (excepción).
        Verifica que lanza una excepción si ocurre un error.
        """
        client = SupabaseClient()
        metrica_data = {"token_simbolo": "BTC", "rendimiento_24h": 5.0}
        client.supabase.table.side_effect = Exception("DB Error")

        with self.assertRaises(Exception):
            client.insertar_metrica(metrica_data)

        # Verify Supabase client methods were called
        client.supabase.table.assert_called_once_with("metricas_rendimiento")

    def test_obtener_metricas_success(self, mock_create_client, mock_get_supabase_config):
        """
        Test para obtener_metricas (exitoso).
        Verifica que obtiene la lista de métricas de rendimiento.
        """
        client = SupabaseClient()
        limit = 10
        metricas_data = [{"id": "1", "token_simbolo": "BTC"}, {"id": "2", "token_simbolo": "ETH"}]
        mock_execute = MagicMock()
        mock_execute.execute.return_value = MagicMock(data=metricas_data)
        client.supabase.table.return_value.select.return_value.order.return_value.limit.return_value = mock_execute

        metricas = client.obtener_metricas(limit)

        # Verify Supabase client methods were called
        client.supabase.table.assert_called_once_with("metricas_rendimiento")
        client.supabase.table.return_value.select.assert_called_once_with("*")
        client.supabase.table.return_value.select.return_value.order.assert_called_once_with("fecha", desc=True)
        client.supabase.table.return_value.select.return_value.order.return_value.limit.assert_called_once_with(limit)
        mock_execute.execute.assert_called_once()
        self.assertEqual(metricas, metricas_data)

    def test_obtener_metricas_exception(self, mock_create_client, mock_get_supabase_config):
        """
        Test para obtener_metricas (excepción).
        Verifica que retorna una lista vacía si ocurre un error.
        """
        client = SupabaseClient()
        limit = 10
        client.supabase.table.side_effect = Exception("DB Error")

        metricas = client.obtener_metricas(limit)

        # Verify Supabase client methods were called
        client.supabase.table.assert_called_once_with("metricas_rendimiento")
        self.assertEqual(metricas, [])

    def test_eliminar_metrica_success(self, mock_create_client, mock_get_supabase_config):
        """
        Test para eliminar_metrica (exitoso).
        Verifica que elimina una métrica de rendimiento.
        """
        client = SupabaseClient()
        metrica_id = "metrica123"
        deleted_metrica_data = {"id": metrica_id, "token_simbolo": "BTC"}
        mock_execute = MagicMock()
        mock_execute.execute.return_value = MagicMock(data=[deleted_metrica_data])
        client.supabase.table.return_value.delete.return_value.eq.return_value = mock_execute

        deleted_metrica = client.eliminar_metrica(metrica_id)

        # Verify Supabase client methods were called
        client.supabase.table.assert_called_once_with("metricas_rendimiento")
        client.supabase.table.return_value.delete.assert_called_once()
        client.supabase.table.return_value.delete.return_value.eq.assert_called_once_with("id", metrica_id)
        mock_execute.execute.assert_called_once()
        self.assertEqual(deleted_metrica, deleted_metrica_data)

    def test_eliminar_metrica_exception(self, mock_create_client, mock_get_supabase_config):
        """
        Test para eliminar_metrica (excepción).
        Verifica que lanza una excepción si ocurre un error.
        """
        client = SupabaseClient()
        metrica_id = "metrica123"
        client.supabase.table.side_effect = Exception("DB Error")

        with self.assertRaises(Exception):
            client.eliminar_metrica(metrica_id)

        # Verify Supabase client methods were called
        client.supabase.table.assert_called_once_with("metricas_rendimiento")

    def test_actualizar_metrica_success(self, mock_create_client, mock_get_supabase_config):
        """
        Test para actualizar_metrica (exitoso).
        Verifica que actualiza los datos de una métrica de rendimiento.
        """
        client = SupabaseClient()
        metrica_id = "metrica123"
        actualizacion_data = {"rendimiento_24h": 6.0}
        updated_metrica_data = {"id": metrica_id, "token_simbolo": "BTC", "rendimiento_24h": 6.0}
        mock_execute = MagicMock()
        mock_execute.execute.return_value = MagicMock(data=[updated_metrica_data])
        client.supabase.table.return_value.update.return_value.eq.return_value = mock_execute

        updated_metrica = client.actualizar_metrica(metrica_id, actualizacion_data)

        # Verify Supabase client methods were called
        client.supabase.table.assert_called_once_with("metricas_rendimiento")
        client.supabase.table.return_value.update.assert_called_once_with(actualizacion_data)
        client.supabase.table.return_value.update.return_value.eq.assert_called_once_with("id", metrica_id)
        mock_execute.execute.assert_called_once()
        self.assertEqual(updated_metrica, updated_metrica_data)

    def test_actualizar_metrica_exception(self, mock_create_client, mock_get_supabase_config):
        """
        Test para actualizar_metrica (excepción).
        Verifica que lanza una excepción si ocurre un error.
        """
        client = SupabaseClient()
        metrica_id = "metrica123"
        actualizacion_data = {"rendimiento_24h": 6.0}
        client.supabase.table.side_effect = Exception("DB Error")

        with self.assertRaises(Exception):
            client.actualizar_metrica(metrica_id, actualizacion_data)

        # Verify Supabase client methods were called
        client.supabase.table.assert_called_once_with("metricas_rendimiento")

    def test_obtener_historial_operaciones_success(self, mock_create_client, mock_get_supabase_config):
        """
        Test para obtener_historial_operaciones (exitoso).
        Verifica que obtiene el historial de operaciones, incluyendo ordenamiento.
        """
        client = SupabaseClient()
        limit = 20
        order_by = "fecha_completado"
        ascending = False
        historial_data = [{"operacion_id": "op1", "fecha_completado": "date2"}, {"operacion_id": "op2", "fecha_completado": "date1"}]
        mock_execute = MagicMock()
        mock_execute.execute.return_value = MagicMock(data=historial_data)
        client.supabase.table.return_value.select.return_value.order.return_value.limit.return_value = mock_execute

        historial = client.obtener_historial_operaciones(limit, order_by, ascending)

        # Verify Supabase client methods were called
        client.supabase.table.assert_called_once_with("arbitraje_operaciones")
        client.supabase.table.return_value.select.assert_called_once_with("*")
        client.supabase.table.return_value.select.return_value.order.assert_called_once_with(order_by, desc=not ascending)
        client.supabase.table.return_value.select.return_value.order.return_value.limit.assert_called_once_with(limit)
        mock_execute.execute.assert_called_once()
        self.assertEqual(historial, historial_data)

    def test_obtener_historial_operaciones_exception(self, mock_create_client, mock_get_supabase_config):
        """
        Test para obtener_historial_operaciones (excepción).
        Verifica que retorna una lista vacía si ocurre un error.
        """
        client = SupabaseClient()
        limit = 20
        order_by = "fecha_completado"
        ascending = False
        client.supabase.table.side_effect = Exception("DB Error")

        historial = client.obtener_historial_operaciones(limit, order_by, ascending)

        # Verify Supabase client methods were called
        client.supabase.table.assert_called_once_with("arbitraje_operaciones")
        self.assertEqual(historial, [])


if __name__ == '__main__':
    unittest.main()
