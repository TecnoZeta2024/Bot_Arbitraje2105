import unittest
from unittest.mock import patch, MagicMock
import json
from src.core.ejecutar_ciclo import (
    preparar_operacion,
    verificar_saldos,
    ejecutar_paso,
    ejecutar_ciclo_completo,
    ejecutar_arbitraje
)

# Mock de las dependencias externas
@patch('src.core.ejecutar_ciclo.binance_trade_client')
@patch('src.core.ejecutar_ciclo.supabase_client')
@patch('src.core.ejecutar_ciclo.settings')
@patch('src.core.ejecutar_ciclo.time') # Mock time for timestamp formatting
class TestEjecutarCiclo(unittest.TestCase):

    def test_preparar_operacion(self, mock_time, mock_settings, mock_supabase_client, mock_binance_client):
        """
        Test para la función preparar_operacion.
        Verifica que prepara los datos de la operación correctamente.
        """
        oportunidad_input = {
            "ruta": "USDT → BTC → ETH → USDT",
            "pares": ["BTCUSDT", "ETHBTC", "ETHUSDT (INV)"],
            "capital": 1000
        }
        analisis_input = {
            "rentabilidad_neta_estimada": 1.2
        }
        mock_settings.capital_inicial = 500 # Should use capital from opportunity if provided

        # Mock binance_trade_client.obtener_reglas_simbolo
        mock_binance_client.obtener_reglas_simbolo.side_effect = [
            {"baseAsset": "BTC", "quoteAsset": "USDT"}, # BTCUSDT
            {"baseAsset": "ETH", "quoteAsset": "BTC"},  # ETHBTC
            {"baseAsset": "ETH", "quoteAsset": "USDT"}   # ETHUSDT
        ]

        operacion = preparar_operacion(oportunidad_input, analisis_input)

        # Verify that binance_trade_client.obtener_reglas_simbolo was called for each pair
        mock_binance_client.obtener_reglas_simbolo.assert_any_call("BTCUSDT")
        mock_binance_client.obtener_reglas_simbolo.assert_any_call("ETHBTC")
        mock_binance_client.obtener_reglas_simbolo.assert_any_call("ETHUSDT")
        self.assertEqual(mock_binance_client.obtener_reglas_simbolo.call_count, 3)

        # Verify the structure and values of the prepared operation
        self.assertIn("ruta", operacion)
        self.assertIn("pares", operacion)
        self.assertIn("capital_inicial", operacion)
        self.assertIn("rentabilidad_estimada", operacion)
        self.assertIn("pasos", operacion)

        self.assertEqual(operacion["ruta"], "USDT → BTC → ETH → USDT")
        self.assertEqual(operacion["capital_inicial"], 1000)
        self.assertEqual(operacion["rentabilidad_estimada"], 1.2)
        self.assertEqual(len(operacion["pasos"]), 3)

        # Verify the details of each step
        self.assertEqual(operacion["pasos"][0]["par"], "BTCUSDT")
        self.assertEqual(operacion["pasos"][0]["lado"], "BUY")
        self.assertEqual(operacion["pasos"][0]["base"], "BTC")
        self.assertEqual(operacion["pasos"][0]["quote"], "USDT")
        self.assertEqual(operacion["pasos"][0]["paso"], 1)

        self.assertEqual(operacion["pasos"][1]["par"], "ETHBTC")
        self.assertEqual(operacion["pasos"][1]["lado"], "BUY")
        self.assertEqual(operacion["pasos"][1]["base"], "ETH")
        self.assertEqual(operacion["pasos"][1]["quote"], "BTC")
        self.assertEqual(operacion["pasos"][1]["paso"], 2)

        self.assertEqual(operacion["pasos"][2]["par"], "ETHUSDT")
        self.assertEqual(operacion["pasos"][2]["lado"], "SELL") # Inverse pair
        self.assertEqual(operacion["pasos"][2]["base"], "ETH")
        self.assertEqual(operacion["pasos"][2]["quote"], "USDT")
        self.assertEqual(operacion["pasos"][2]["paso"], 3)

    def test_verificar_saldos_sufficient(self, mock_time, mock_settings, mock_supabase_client, mock_binance_client):
        """
        Test para la función verificar_saldos cuando el saldo es suficiente.
        Verifica que retorna True.
        """
        operacion_input = {
            "capital_inicial": 1000,
            "pasos": [{"par": "BTCUSDT", "lado": "BUY"}] # Need at least one step
        }
        mock_binance_client.obtener_saldo.return_value = 1500 # Sufficient balance

        result = verificar_saldos(operacion_input)

        # Verify that binance_trade_client.obtener_saldo was called with the correct asset
        mock_binance_client.obtener_saldo.assert_called_once_with("USDT")

        # Verify that True is returned
        self.assertTrue(result)

    def test_verificar_saldos_insufficient(self, mock_time, mock_settings, mock_supabase_client, mock_binance_client):
        """
        Test para la función verificar_saldos cuando el saldo es insuficiente.
        Verifica que retorna False.
        """
        operacion_input = {
            "capital_inicial": 1000,
            "pasos": [{"par": "BTCUSDT", "lado": "BUY"}] # Need at least one step
        }
        mock_binance_client.obtener_saldo.return_value = 500 # Insufficient balance

        result = verificar_saldos(operacion_input)

        # Verify that binance_trade_client.obtener_saldo was called with the correct asset
        mock_binance_client.obtener_saldo.assert_called_once_with("USDT")

        # Verify that False is returned
        self.assertFalse(result)

    def test_verificar_saldos_no_steps(self, mock_time, mock_settings, mock_supabase_client, mock_binance_client):
        """
        Test para la función verificar_saldos cuando no hay pasos definidos.
        Verifica que retorna False.
        """
        operacion_input = {
            "capital_inicial": 1000,
            "pasos": [] # No steps
        }

        result = verificar_saldos(operacion_input)

        # Verify that binance_trade_client.obtener_saldo was NOT called
        mock_binance_client.obtener_saldo.assert_not_called()

        # Verify that False is returned
        self.assertFalse(result)

    @patch('src.core.ejecutar_ciclo.binance_trade_client.redondear_cantidad')
    @patch('src.core.ejecutar_ciclo.binance_trade_client.crear_orden_mercado')
    @patch('src.core.ejecutar_ciclo.binance_trade_client.obtener_precio_ticker')
    def test_ejecutar_paso_testnet_buy_success(self, mock_obtener_precio_ticker, mock_crear_orden_mercado, mock_redondear_cantidad, mock_time, mock_settings, mock_supabase_client, mock_binance_client_helper):
        """
        Test para ejecutar_paso en testnet (BUY exitoso).
        Verifica la simulación de orden de compra.
        """
        mock_settings.binance_testnet = True
        paso_input = {"par": "BTCUSDT", "lado": "BUY"}
        cantidad_input = 0.0015

        mock_redondear_cantidad.return_value = 0.001 # Simulate rounding
        mock_obtener_precio_ticker.return_value = 60000.0 # Simulate price

        success, orden, cantidad_resultante = ejecutar_paso(paso_input, cantidad_input)

        # Verify mocks were called
        mock_redondear_cantidad.assert_called_once_with("BTCUSDT", 0.0015)
        mock_obtener_precio_ticker.assert_called_once_with("BTCUSDT")
        mock_crear_orden_mercado.assert_not_called() # Should not call real order creation in testnet

        # Verify results
        self.assertTrue(success)
        self.assertIsNotNone(orden)
        self.assertEqual(orden["symbol"], "BTCUSDT")
        self.assertEqual(orden["side"], "BUY")
        self.assertEqual(float(orden["executedQty"]), 0.001)
        self.assertEqual(float(orden["price"]), 60000.0)
        # Expected resulting quantity after simulated commission (0.1%)
        self.assertAlmostEqual(cantidad_resultante, 0.001 * (1 - 0.001))

    @patch('src.core.ejecutar_ciclo.binance_trade_client.redondear_cantidad')
    @patch('src.core.ejecutar_ciclo.binance_trade_client.crear_orden_mercado')
    @patch('src.core.ejecutar_ciclo.binance_trade_client.obtener_precio_ticker')
    def test_ejecutar_paso_testnet_sell_success(self, mock_obtener_precio_ticker, mock_crear_orden_mercado, mock_redondear_cantidad, mock_time, mock_settings, mock_supabase_client, mock_binance_client_helper):
        """
        Test para ejecutar_paso en testnet (SELL exitoso).
        Verifica la simulación de orden de venta.
        """
        mock_settings.binance_testnet = True
        paso_input = {"par": "ETHBTC", "lado": "SELL"}
        cantidad_input = 0.055

        mock_redondear_cantidad.return_value = 0.05 # Simulate rounding
        mock_obtener_precio_ticker.return_value = 0.05 # Simulate price

        success, orden, cantidad_resultante = ejecutar_paso(paso_input, cantidad_input)

        # Verify mocks were called
        mock_redondear_cantidad.assert_called_once_with("ETHBTC", 0.055)
        mock_obtener_precio_ticker.assert_called_once_with("ETHBTC")
        mock_crear_orden_mercado.assert_not_called() # Should not call real order creation in testnet

        # Verify results
        self.assertTrue(success)
        self.assertIsNotNone(orden)
        self.assertEqual(orden["symbol"], "ETHBTC")
        self.assertEqual(orden["side"], "SELL")
        self.assertEqual(float(orden["executedQty"]), 0.05)
        self.assertEqual(float(orden["price"]), 0.05)
        # Expected resulting quantity after simulated commission (0.1%)
        self.assertAlmostEqual(cantidad_resultante, (0.05 * 0.05) * (1 - 0.001)) # quantity * price * (1 - commission)

    @patch('src.core.ejecutar_ciclo.binance_trade_client.redondear_cantidad')
    @patch('src.core.ejecutar_ciclo.binance_trade_client.crear_orden_mercado')
    @patch('src.core.ejecutar_ciclo.binance_trade_client.obtener_precio_ticker')
    def test_ejecutar_paso_testnet_rounding_zero(self, mock_obtener_precio_ticker, mock_crear_orden_mercado, mock_redondear_cantidad, mock_time, mock_settings, mock_supabase_client, mock_binance_client_helper):
        """
        Test para ejecutar_paso en testnet cuando la cantidad redondeada es cero.
        Verifica que retorna fallo.
        """
        mock_settings.binance_testnet = True
        paso_input = {"par": "BTCUSDT", "lado": "BUY"}
        cantidad_input = 0.0000001

        mock_redondear_cantidad.return_value = 0.0 # Simulate rounding to zero

        success, orden, cantidad_resultante = ejecutar_paso(paso_input, cantidad_input)

        # Verify mocks were called
        mock_redondear_cantidad.assert_called_once_with("BTCUSDT", 0.0000001)
        mock_obtener_precio_ticker.assert_not_called()
        mock_crear_orden_mercado.assert_not_called()

        # Verify results
        self.assertFalse(success)
        self.assertIsNone(orden)
        self.assertEqual(cantidad_resultante, 0)

    @patch('src.core.ejecutar_ciclo.binance_trade_client.redondear_cantidad')
    @patch('src.core.ejecutar_ciclo.binance_trade_client.crear_orden_mercado')
    @patch('src.core.ejecutar_ciclo.binance_trade_client.obtener_precio_ticker')
    def test_ejecutar_paso_testnet_missing_price(self, mock_obtener_precio_ticker, mock_crear_orden_mercado, mock_redondear_cantidad, mock_time, mock_settings, mock_supabase_client, mock_binance_client_helper):
        """
        Test para ejecutar_paso en testnet cuando no se puede obtener el precio.
        Verifica que retorna fallo.
        """
        mock_settings.binance_testnet = True
        paso_input = {"par": "NONEXISTUSDT", "lado": "BUY"}
        cantidad_input = 100

        mock_redondear_cantidad.return_value = 100 # Simulate rounding
        mock_obtener_precio_ticker.return_value = None # Simulate missing price

        success, orden, cantidad_resultante = ejecutar_paso(paso_input, cantidad_input)

        # Verify mocks were called
        mock_redondear_cantidad.assert_called_once_with("NONEXISTUSDT", 100)
        mock_obtener_precio_ticker.assert_called_once_with("NONEXISTUSDT")
        mock_crear_orden_mercado.assert_not_called()

        # Verify results
        self.assertFalse(success)
        self.assertIsNone(orden)
        self.assertEqual(cantidad_resultante, 0)

    @patch('src.core.ejecutar_ciclo.binance_trade_client.redondear_cantidad')
    @patch('src.core.ejecutar_ciclo.binance_trade_client.crear_orden_mercado')
    @patch('src.core.ejecutar_ciclo.binance_trade_client.obtener_precio_ticker')
    def test_ejecutar_paso_real_success(self, mock_obtener_precio_ticker, mock_crear_orden_mercado, mock_redondear_cantidad, mock_time, mock_settings, mock_supabase_client, mock_binance_client_helper):
        """
        Test para ejecutar_paso en modo real (exitoso).
        Verifica la creación de orden real.
        """
        mock_settings.binance_testnet = False
        paso_input = {"par": "BTCUSDT", "lado": "BUY"}
        cantidad_input = 0.0015

        mock_redondear_cantidad.return_value = 0.001 # Simulate rounding
        # Mock real order creation response
        mock_crear_orden_mercado.return_value = {
            "symbol": "BTCUSDT",
            "orderId": 12345,
            "side": "BUY",
            "type": "MARKET",
            "status": "FILLED",
            "executedQty": "0.001",
            "cummulativeQuoteQty": "60.0", # Total spent (quantity * price)
            "price": "60000.0", # Avg price (not always present for MARKET)
            "time": int(time.time() * 1000)
        }

        success, orden, cantidad_resultante = ejecutar_paso(paso_input, cantidad_input)

        # Verify mocks were called
        mock_redondear_cantidad.assert_called_once_with("BTCUSDT", 0.0015)
        mock_crear_orden_mercado.assert_called_once_with("BTCUSDT", "BUY", 0.001)
        mock_obtener_precio_ticker.assert_not_called() # Should not call ticker price in real mode

        # Verify results
        self.assertTrue(success)
        self.assertIsNotNone(orden)
        self.assertEqual(orden["orderId"], 12345)
        # Expected resulting quantity after simulated commission (0.1%)
        self.assertAlmostEqual(cantidad_resultante, 0.001 * (1 - 0.001)) # For BUY, it's executedQty * (1 - commission)

    @patch('src.core.ejecutar_ciclo.binance_trade_client.redondear_cantidad')
    @patch('src.core.ejecutar_ciclo.binance_trade_client.crear_orden_mercado')
    @patch('src.core.ejecutar_ciclo.binance_trade_client.obtener_precio_ticker')
    def test_ejecutar_paso_real_sell_success(self, mock_obtener_precio_ticker, mock_crear_orden_mercado, mock_redondear_cantidad, mock_time, mock_settings, mock_supabase_client, mock_binance_client_helper):
        """
        Test para ejecutar_paso en modo real (SELL exitoso).
        Verifica la creación de orden real.
        """
        mock_settings.binance_testnet = False
        paso_input = {"par": "ETHBTC", "lado": "SELL"}
        cantidad_input = 0.055

        mock_redondear_cantidad.return_value = 0.05 # Simulate rounding
        # Mock real order creation response
        mock_crear_orden_mercado.return_value = {
            "symbol": "ETHBTC",
            "orderId": 67890,
            "side": "SELL",
            "type": "MARKET",
            "status": "FILLED",
            "executedQty": "0.05",
            "cummulativeQuoteQty": "0.0025", # Total received (quantity * price)
            "price": "0.05", # Avg price
            "time": int(time.time() * 1000)
        }

        success, orden, cantidad_resultante = ejecutar_paso(paso_input, cantidad_input)

        # Verify mocks were called
        mock_redondear_cantidad.assert_called_once_with("ETHBTC", 0.055)
        mock_crear_orden_mercado.assert_called_once_with("ETHBTC", "SELL", 0.05)
        mock_obtener_precio_ticker.assert_not_called()

        # Verify results
        self.assertTrue(success)
        self.assertIsNotNone(orden)
        self.assertEqual(orden["orderId"], 67890)
        # Expected resulting quantity after simulated commission (0.1%)
        # For SELL, it's cummulativeQuoteQty * (1 - commission)
        self.assertAlmostEqual(cantidad_resultante, 0.0025 * (1 - 0.001))

    @patch('src.core.ejecutar_ciclo.binance_trade_client.redondear_cantidad')
    @patch('src.core.ejecutar_ciclo.binance_trade_client.crear_orden_mercado')
    @patch('src.core.ejecutar_ciclo.binance_trade_client.obtener_precio_ticker')
    def test_ejecutar_paso_real_order_creation_failure(self, mock_obtener_precio_ticker, mock_crear_orden_mercado, mock_redondear_cantidad, mock_time, mock_settings, mock_supabase_client, mock_binance_client_helper):
        """
        Test para ejecutar_paso en modo real cuando falla la creación de orden.
        Verifica que retorna fallo.
        """
        mock_settings.binance_testnet = False
        paso_input = {"par": "BTCUSDT", "lado": "BUY"}
        cantidad_input = 0.001

        mock_redondear_cantidad.return_value = 0.001
        mock_crear_orden_mercado.return_value = None # Simulate order creation failure

        success, orden, cantidad_resultante = ejecutar_paso(paso_input, cantidad_input)

        # Verify mocks were called
        mock_redondear_cantidad.assert_called_once_with("BTCUSDT", 0.001)
        mock_crear_orden_mercado.assert_called_once_with("BTCUSDT", "BUY", 0.001)
        mock_obtener_precio_ticker.assert_not_called()

        # Verify results
        self.assertFalse(success)
        self.assertIsNone(orden)
        self.assertEqual(cantidad_resultante, 0)

    @patch('src.core.ejecutar_ciclo.binance_trade_client.redondear_cantidad')
    @patch('src.core.ejecutar_ciclo.binance_trade_client.crear_orden_mercado')
    @patch('src.core.ejecutar_ciclo.binance_trade_client.obtener_precio_ticker')
    def test_ejecutar_paso_real_order_not_filled(self, mock_obtener_precio_ticker, mock_crear_orden_mercado, mock_redondear_cantidad, mock_time, mock_settings, mock_supabase_client, mock_binance_client_helper):
        """
        Test para ejecutar_paso en modo real cuando la orden no se completa.
        Verifica que retorna fallo.
        """
        mock_settings.binance_testnet = False
        paso_input = {"par": "BTCUSDT", "lado": "BUY"}
        cantidad_input = 0.001

        mock_redondear_cantidad.return_value = 0.001
        # Mock real order creation response with status not FILLED
        mock_crear_orden_mercado.return_value = {
            "symbol": "BTCUSDT",
            "orderId": 12345,
            "side": "BUY",
            "type": "MARKET",
            "status": "NEW", # Not FILLED
            "executedQty": "0.0",
            "cummulativeQuoteQty": "0.0",
            "time": int(time.time() * 1000)
        }

        success, orden, cantidad_resultante = ejecutar_paso(paso_input, cantidad_input)

        # Verify mocks were called
        mock_redondear_cantidad.assert_called_once_with("BTCUSDT", 0.001)
        mock_crear_orden_mercado.assert_called_once_with("BTCUSDT", "BUY", 0.001)
        mock_obtener_precio_ticker.assert_not_called()

        # Verify results
        self.assertFalse(success)
        self.assertIsNotNone(orden)
        self.assertEqual(cantidad_resultante, 0)

    @patch('src.core.ejecutar_ciclo.binance_trade_client.redondear_cantidad')
    @patch('src.core.ejecutar_ciclo.binance_trade_client.crear_orden_mercado')
    @patch('src.core.ejecutar_ciclo.binance_trade_client.obtener_precio_ticker')
    def test_ejecutar_paso_real_exception(self, mock_obtener_precio_ticker, mock_crear_orden_mercado, mock_redondear_cantidad, mock_time, mock_settings, mock_supabase_client, mock_binance_client_helper):
        """
        Test para ejecutar_paso en modo real cuando ocurre una excepción.
        Verifica que maneja excepciones.
        """
        mock_settings.binance_testnet = False
        paso_input = {"par": "BTCUSDT", "lado": "BUY"}
        cantidad_input = 0.001

        mock_redondear_cantidad.return_value = 0.001
        mock_crear_orden_mercado.side_effect = Exception("Binance API Error") # Simulate exception

        success, orden, cantidad_resultante = ejecutar_paso(paso_input, cantidad_input)

        # Verify mocks were called
        mock_redondear_cantidad.assert_called_once_with("BTCUSDT", 0.001)
        mock_crear_orden_mercado.assert_called_once_with("BTCUSDT", "BUY", 0.001)
        mock_obtener_precio_ticker.assert_not_called()

        # Verify results
        self.assertFalse(success)
        self.assertIsNone(orden)
        self.assertEqual(cantidad_resultante, 0)

    @patch('src.core.ejecutar_ciclo.verificar_saldos')
    @patch('src.core.ejecutar_ciclo.ejecutar_paso')
    @patch('src.core.ejecutar_ciclo.time.time') # Mock time.time for execution time calculation
    def test_ejecutar_ciclo_completo_success(self, mock_time_time, mock_ejecutar_paso, mock_verificar_saldos, mock_time, mock_settings, mock_supabase_client, mock_binance_client):
        """
        Test para la función ejecutar_ciclo_completo en caso de éxito.
        Verifica que ejecuta todos los pasos y calcula el resultado final.
        """
        operacion_input = {
            "ruta": "USDT → BTC → ETH → USDT",
            "capital_inicial": 1000.0,
            "rentabilidad_estimada": 1.0, # 1%
            "pasos": [
                {"par": "BTCUSDT", "lado": "BUY", "paso": 1},
                {"par": "ETHBTC", "lado": "BUY", "paso": 2},
                {"par": "ETHUSDT", "lado": "SELL", "paso": 3}
            ]
        }

        mock_verificar_saldos.return_value = True # Simulate sufficient balance

        # Mock ejecutar_paso to simulate successful trades
        mock_ejecutar_paso.side_effect = [
            (True, {"orderId": 1}, 0.016), # Step 1: BUY BTC with 1000 USDT -> 0.016 BTC (simulated)
            (True, {"orderId": 2}, 0.32),  # Step 2: BUY ETH with 0.016 BTC -> 0.32 ETH (simulated)
            (True, {"orderId": 3}, 1010.0) # Step 3: SELL ETH -> 1010 USDT (simulated final capital)
        ]

        # Mock time.time to control execution time
        mock_time_time.side_effect = [0, 5] # Start time 0, End time 5

        resultado = ejecutar_ciclo_completo(operacion_input)

        # Verify mocks were called
        mock_verificar_saldos.assert_called_once_with(operacion_input)
        self.assertEqual(mock_ejecutar_paso.call_count, 3) # Called for each step
        mock_ejecutar_paso.assert_any_call(operacion_input["pasos"][0], 1000.0)
        mock_ejecutar_paso.assert_any_call(operacion_input["pasos"][1], 0.016)
        mock_ejecutar_paso.assert_any_call(operacion_input["pasos"][2], 0.32)

        # Verify the final result
        self.assertEqual(resultado["estado"], "COMPLETADO")
        self.assertEqual(len(resultado["pares_ejecutados"]), 3)
        self.assertEqual(len(resultado["ordenes"]), 3)
        self.assertEqual(resultado["capital_inicial"], 1000.0)
        self.assertEqual(resultado["capital_final"], 1010.0)
        self.assertEqual(resultado["ganancia_neta"], 10.0)
        self.assertAlmostEqual(resultado["rentabilidad_real"], 1.0) # (10 / 1000) * 100
        # Comisiones and slippage are simplified estimations in the actual code
        self.assertAlmostEqual(resultado["comisiones"], 1000.0 * 0.003)
        self.assertAlmostEqual(resultado["slippage"], 0.0) # Real >= Estimated

        self.assertEqual(resultado["tiempo_ejecucion"], 5.0)

    @patch('src.core.ejecutar_ciclo.verificar_saldos')
    @patch('src.core.ejecutar_ciclo.ejecutar_paso')
    @patch('src.core.ejecutar_ciclo.time.time') # Mock time.time for execution time calculation
    def test_ejecutar_ciclo_completo_insufficient_balance(self, mock_time_time, mock_ejecutar_paso, mock_verificar_saldos, mock_time, mock_settings, mock_supabase_client, mock_binance_client):
        """
        Test para ejecutar_ciclo_completo cuando el saldo es insuficiente.
        Verifica que retorna estado de error de saldo.
        """
        operacion_input = {
            "ruta": "USDT → BTC → ETH → USDT",
            "capital_inicial": 1000.0,
            "rentabilidad_estimada": 1.0,
            "pasos": [
                {"par": "BTCUSDT", "lado": "BUY", "paso": 1}
            ]
        }

        mock_verificar_saldos.return_value = False # Simulate insufficient balance

        # Mock time.time to control execution time
        mock_time_time.side_effect = [0, 2] # Start time 0, End time 2

        resultado = ejecutar_ciclo_completo(operacion_input)

        # Verify mocks were called
        mock_verificar_saldos.assert_called_once_with(operacion_input)
        mock_ejecutar_paso.assert_not_called() # Should not execute steps

        # Verify the final result
        self.assertEqual(resultado["estado"], "ERROR_SALDO")
        self.assertEqual(resultado["tiempo_ejecucion"], 2.0)

    @patch('src.core.ejecutar_ciclo.verificar_saldos')
    @patch('src.core.ejecutar_ciclo.ejecutar_paso')
    @patch('src.core.ejecutar_ciclo.time.time') # Mock time.time for execution time calculation
    def test_ejecutar_ciclo_completo_step_failure(self, mock_time_time, mock_ejecutar_paso, mock_verificar_saldos, mock_time, mock_settings, mock_supabase_client, mock_binance_client):
        """
        Test para ejecutar_ciclo_completo cuando falla un paso.
        Verifica que detiene la ejecución y retorna estado de error de ejecución.
        """
        operacion_input = {
            "ruta": "USDT → BTC → ETH → USDT",
            "capital_inicial": 1000.0,
            "rentabilidad_estimada": 1.0,
            "pasos": [
                {"par": "BTCUSDT", "lado": "BUY", "paso": 1},
                {"par": "ETHBTC", "lado": "BUY", "paso": 2}, # This step will fail
                {"par": "ETHUSDT", "lado": "SELL", "paso": 3}
            ]
        }

        mock_verificar_saldos.return_value = True # Simulate sufficient balance

        # Mock ejecutar_paso to simulate failure on the second step
        mock_ejecutar_paso.side_effect = [
            (True, {"orderId": 1}, 0.016), # Step 1 succeeds
            (False, None, 0)             # Step 2 fails
        ]

        # Mock time.time to control execution time
        mock_time_time.side_effect = [0, 7] # Start time 0, End time 7

        resultado = ejecutar_ciclo_completo(operacion_input)

        # Verify mocks were called
        mock_verificar_saldos.assert_called_once_with(operacion_input)
        self.assertEqual(mock_ejecutar_paso.call_count, 2) # Called only for the first two steps
        mock_ejecutar_paso.assert_any_call(operacion_input["pasos"][0], 1000.0)
        mock_ejecutar_paso.assert_any_call(operacion_input["pasos"][1], 0.016)

        # Verify the final result
        self.assertEqual(resultado["estado"], "ERROR_EJECUCION")
        self.assertEqual(len(resultado["pares_ejecutados"]), 1) # Only the first step was executed
        self.assertEqual(len(resultado["ordenes"]), 1)
        self.assertEqual(resultado["tiempo_ejecucion"], 7.0)

    @patch('src.core.ejecutar_ciclo.verificar_saldos')
    @patch('src.core.ejecutar_ciclo.ejecutar_paso')
    @patch('src.core.ejecutar_ciclo.time.time') # Mock time.time for execution time calculation
    def test_ejecutar_ciclo_completo_exception(self, mock_time_time, mock_ejecutar_paso, mock_verificar_saldos, mock_time, mock_settings, mock_supabase_client, mock_binance_client):
        """
        Test para ejecutar_ciclo_completo cuando ocurre una excepción inesperada.
        Verifica que maneja la excepción y retorna estado de error inesperado.
        """
        operacion_input = {
            "ruta": "USDT → BTC → ETH → USDT",
            "capital_inicial": 1000.0,
            "rentabilidad_estimada": 1.0,
            "pasos": [
                {"par": "BTCUSDT", "lado": "BUY", "paso": 1}
            ]
        }

        mock_verificar_saldos.side_effect = Exception("Unexpected Error") # Simulate unexpected exception

        # Mock time.time to control execution time
        mock_time_time.side_effect = [0, 4] # Start time 0, End time 4

        resultado = ejecutar_ciclo_completo(operacion_input)

        # Verify mocks were called
        mock_verificar_saldos.assert_called_once_with(operacion_input)
        mock_ejecutar_paso.assert_not_called() # Should not execute steps

        # Verify the final result
        self.assertEqual(resultado["estado"], "ERROR_INESPERADO")
        self.assertEqual(resultado["tiempo_ejecucion"], 4.0)

    @patch('src.core.ejecutar_ciclo.preparar_operacion')
    @patch('src.core.ejecutar_ciclo.ejecutar_ciclo_completo')
    @patch('src.core.ejecutar_ciclo.time.strftime') # Mock time.strftime for timestamp formatting
    def test_ejecutar_arbitraje_success(self, mock_strftime, mock_ejecutar_ciclo_completo, mock_preparar_operacion, mock_time, mock_settings, mock_supabase_client, mock_binance_client):
        """
        Test para la función ejecutar_arbitraje en caso de éxito.
        Verifica que ejecuta el flujo completo y actualiza Supabase.
        """
        operacion_id_input = "test-op-123"
        oportunidad_input = {"ruta": "USDT → BTC → ETH → USDT"}
        analisis_input = {"rentabilidad_neta_estimada": 1.0}

        mock_preparar_operacion.return_value = {"pasos": [...]} # Simulate prepared operation
        mock_ejecutar_ciclo_completo.return_value = {
            "estado": "COMPLETADO",
            "ganancia_neta": 10.0,
            "tiempo_ejecucion": 5.0
        }
        mock_strftime.return_value = "2025-05-13 12:00:00"

        resultado = ejecutar_arbitraje(operacion_id_input, oportunidad_input, analisis_input)

        # Verify mocks were called
        mock_preparar_operacion.assert_called_once_with(oportunidad_input, analisis_input)
        mock_supabase_client.actualizar_operacion.assert_called_once_with(
            "test-op-123",
            {
                "estado": "EJECUTANDO",
                "fecha_inicio_ejecucion": "2025-05-13 12:00:00"
            }
        )
        mock_ejecutar_ciclo_completo.assert_called_once_with(mock_preparar_operacion.return_value)

        # Verify the final result
        self.assertEqual(resultado["operacion_id"], "test-op-123")
        self.assertEqual(resultado["estado"], "COMPLETADO")
        self.assertEqual(resultado["ganancia_neta"], 10.0)
        self.assertEqual(resultado["tiempo_ejecucion"], 5.0)

    @patch('src.core.ejecutar_ciclo.preparar_operacion')
    @patch('src.core.ejecutar_ciclo.ejecutar_ciclo_completo')
    @patch('src.core.ejecutar_ciclo.time.strftime') # Mock time.strftime for timestamp formatting
    def test_ejecutar_arbitraje_cycle_failure(self, mock_strftime, mock_ejecutar_ciclo_completo, mock_preparar_operacion, mock_time, mock_settings, mock_supabase_client, mock_binance_client):
        """
        Test para la función ejecutar_arbitraje cuando falla el ciclo completo.
        Verifica que retorna el resultado de fallo del ciclo.
        """
        operacion_id_input = "test-op-456"
        oportunidad_input = {"ruta": "USDT → BTC → ETH → USDT"}
        analisis_input = {"rentabilidad_neta_estimada": 1.0}

        mock_preparar_operacion.return_value = {"pasos": [...]} # Simulate prepared operation
        mock_ejecutar_ciclo_completo.return_value = {
            "estado": "ERROR_EJECUCION",
            "pares_ejecutados": ["BTCUSDT (BUY)"],
            "tiempo_ejecucion": 7.0
        }
        mock_strftime.return_value = "2025-05-13 12:01:00"

        resultado = ejecutar_arbitraje(operacion_id_input, oportunidad_input, analisis_input)

        # Verify mocks were called
        mock_preparar_operacion.assert_called_once_with(oportunidad_input, analisis_input)
        mock_supabase_client.actualizar_operacion.assert_called_once_with(
            "test-op-456",
            {
                "estado": "EJECUTANDO",
                "fecha_inicio_ejecucion": "2025-05-13 12:01:00"
            }
        )
        mock_ejecutar_ciclo_completo.assert_called_once_with(mock_preparar_operacion.return_value)

        # Verify the final result
        self.assertEqual(resultado["operacion_id"], "test-op-456")
        self.assertEqual(resultado["estado"], "ERROR_EJECUCION")
        self.assertEqual(resultado["tiempo_ejecucion"], 7.0)

    @patch('src.core.ejecutar_ciclo.preparar_operacion')
    @patch('src.core.ejecutar_ciclo.ejecutar_ciclo_completo')
    @patch('src.core.ejecutar_ciclo.time.strftime') # Mock time.strftime for timestamp formatting
    def test_ejecutar_arbitraje_exception(self, mock_strftime, mock_ejecutar_ciclo_completo, mock_preparar_operacion, mock_time, mock_settings, mock_supabase_client, mock_binance_client):
        """
        Test para la función ejecutar_arbitraje cuando ocurre una excepción.
        Verifica que maneja la excepción y retorna un resultado de error.
        """
        operacion_id_input = "test-op-789"
        oportunidad_input = {"ruta": "USDT → BTC → ETH → USDT"}
        analisis_input = {"rentabilidad_neta_estimada": 1.0}

        mock_preparar_operacion.side_effect = Exception("Preparation Error") # Simulate exception

        mock_strftime.return_value = "2025-05-13 12:02:00"

        resultado = ejecutar_arbitraje(operacion_id_input, oportunidad_input, analisis_input)

        # Verify mocks were called
        mock_preparar_operacion.assert_called_once_with(oportunidad_input, analisis_input)
        # Supabase update should still be attempted before the exception
        mock_supabase_client.actualizar_operacion.assert_called_once_with(
            "test-op-789",
            {
                "estado": "EJECUTANDO",
                "fecha_inicio_ejecucion": "2025-05-13 12:02:00"
            }
        )
        mock_ejecutar_ciclo_completo.assert_not_called() # Should not call cycle execution

        # Verify the final result
        self.assertEqual(resultado["operacion_id"], "test-op-789")
        self.assertEqual(resultado["estado"], "ERROR")
        self.assertIn("Preparation Error", resultado["resultado"])

    # Aquí se añadirán más tests para las otras funciones

if __name__ == '__main__':
    unittest.main()
