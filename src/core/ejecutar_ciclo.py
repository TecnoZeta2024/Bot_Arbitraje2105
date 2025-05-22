import ccxt
import json
import requests
import time # Import time for timestamps
from typing import Dict, Any, List, Optional, Tuple # Add typing imports

from src.apis.binance_client import BinanceClient, binance_trade_client # Import both clients
from src.apis.supabase_client import SupabaseClient
from src.utils.config import get_config_value # Import get_config_value
from src.utils.logger import get_logger
from src.core.telegram.telegram_handler import telegram_handler # Re-added for use within function

import ccxt
import json
import requests
import time # Import time for timestamps
from typing import Dict, Any, List, Optional, Tuple # Add typing imports

from src.apis.binance_client import BinanceClient, binance_trade_client # Import both clients
from src.apis.supabase_client import SupabaseClient
from src.utils.config import get_config_value # Import get_config_value
from src.utils.logger import get_logger

"""
Función de verificación para el módulo de ejecución de ciclo.
Esta función se utiliza para validar que el módulo está correctamente configurado.
"""

def verificar_modulo_ejecucion():
    """
    Verifica que el módulo de ejecución de operaciones esté correctamente configurado.
    
    Returns:
        dict: Resultado de la verificación
            {
                "success": bool,
                "message": str,
                "details": dict
            }
    """
    try:
        from src.apis.binance_client import BinanceClient
        from src.apis.supabase_client import SupabaseClient
        from src.utils.config import get_config_value # Import get_config_value
        import ccxt
        import json
        import requests
        import time # Import time for timestamps

        from src.apis.binance_client import binance_trade_client # Import the trade client instance
        from src.utils.logger import get_logger

        logger = get_logger("ejecutar_ciclo") # Use a specific logger for this module
        
        # Verificar la conexión con Binance
        binance_client = BinanceClient()
        testnet_mode = binance_client.testnet
        
        # Verificar que se puede obtener la información de la cuenta
        account_info = binance_client.get_account_info()
        
        if not account_info:
            return {
                "success": False,
                "message": "No se pudo obtener la información de la cuenta de Binance",
                "details": {
                    "testnet_mode": testnet_mode
                }
            }
        
        # Verificar los balances
        balances = binance_client.get_balances()
        
        if balances is None:
            return {
                "success": False,
                "message": "No se pudieron obtener los balances de la cuenta",
                "details": {
                    "testnet_mode": testnet_mode,
                    "account_info": "OK"
                }
            }
        
        # Verificar si hay saldo USDT suficiente para operar
        usdt_balance = next((b["free"] for b in balances if b["asset"] == "USDT"), 0)
        min_usdt = 10.0  # Mínimo 10 USDT para operar
        
        has_sufficient_balance = usdt_balance >= min_usdt
        
        # Verificar la conexión con Supabase
        supabase_client = SupabaseClient()
        connection_result = supabase_client.check_connection()
        
        if not connection_result:
            return {
                "success": False,
                "message": "No se pudo conectar con Supabase",
                "details": {
                    "testnet_mode": testnet_mode,
                    "account_info": "OK",
                    "usdt_balance": usdt_balance,
                    "has_sufficient_balance": has_sufficient_balance
                }
            }
        
        # Verificar que existe la tabla para registrar operaciones
        try:
            response = supabase_client.client.table("arbitraje_operaciones").select("count").execute()
            table_exists = True
        except Exception as e:
            table_exists = False
        
        # Verificar que se puede enviar un resultado de ejecución a n8n
        webhook_url_resultado = get_config_value("n8n_webhook_resultado") # Use get_config_value
        webhook_url_configured = bool(webhook_url_resultado)
        
        # Verificar con una prueba de mercado que se pueden consultar precios
        market_test = binance_client.get_ticker("BTCUSDT")
        market_working = market_test is not None and "lastPrice" in market_test
        
        # Todo correcto
        return {
            "success": True,
            "message": "Módulo de ejecución correctamente configurado",
            "details": {
                "testnet_mode": testnet_mode,
                "account_info": "OK",
                "usdt_balance": usdt_balance,
                "has_sufficient_balance": has_sufficient_balance,
                "supabase_connection": "OK",
                "operations_table_exists": table_exists,
                "n8n_webhook_resultado": webhook_url_configured,
                "market_test": "OK" if market_working else "ERROR"
            }
        }
    
    except Exception as e:
        return {
            "success": False,
            "message": f"Error al verificar el módulo de ejecución: {str(e)}",
            "details": {
                "error": str(e)
            }
        }

async def ejecutar_arbitraje(operacion_id: str, oportunidad: dict, analisis_ia: dict) -> dict:
    """
    Ejecuta un ciclo de arbitraje triangular en Binance.

    Args:
        operacion_id: ID único de la operación.
        oportunidad: Diccionario con los detalles de la oportunidad de arbitraje.
        analisis_ia: Diccionario con el análisis y recomendación de la IA.

    Returns:
        dict: Resultado de la ejecución de la operación.
    """
    logger.info(f"Iniciando ejecución de arbitraje para operación ID: {operacion_id}")
    logger.debug(f"Oportunidad recibida: {oportunidad}")
    logger.debug(f"Análisis IA recibido: {analisis_ia}")

    resultados = {
        "operacion_id": operacion_id,
        "estado": "PENDIENTE", # Initial state
        "resultado_real": 0.0,
        "pares_ejecutados": [],
        "precios_reales": {},
        "comisiones_totales": 0.0,
        "slippage_real": 0.0,
        "ganancia_neta": 0.0,
        "fecha_completado": None,
        "rentabilidad_real": 0.0,
        "rentabilidad_estimada": analisis_ia.get("rentabilidad_neta_estimada", 0.0),
        "log_ejecucion": ""
    }

    # Instantiate SupabaseClient
    supabase_client = SupabaseClient()

    pares_comercio = oportunidad.get("pares_comercio", [])
    ruta_arbitraje = oportunidad.get("ruta", [])
    capital_inicial = oportunidad.get("capital_inicial", 0.0)

    if not pares_comercio or not ruta_arbitraje or capital_inicial <= 0:
        error_msg = f"Datos de oportunidad incompletos para operación {operacion_id}. Pares: {pares_comercio}, Ruta: {ruta_arbitraje}, Capital: {capital_inicial}"
        logger.error(error_msg)
        resultados["estado"] = "FALLIDO"
        resultados["log_ejecucion"] += f"Error: {error_msg}\n"
        return resultados

    # Ensure we have a trading client instance
    if not binance_trade_client.trading_enabled:
         error_msg = "Binance trade client no inicializado para trading."
         logger.critical(error_msg) # Use critical for this severe error
         resultados["estado"] = "FALLIDO"
         resultados["log_ejecucion"] += f"Error: {error_msg}\n"
         return resultados

    try:
        current_capital = capital_inicial
        current_asset = ruta_arbitraje[0] # Starting asset (e.g., USDT)
        executed_quantities = {}
        executed_prices = {}
        total_commissions = 0.0
        placed_order_ids = [] # To track order IDs for cancellation

        logger.info(f"Ruta de arbitraje: {' -> '.join(ruta_arbitraje)}")
        logger.info(f"Pares de comercio: {pares_comercio}")
        logger.info(f"Capital inicial: {capital_inicial} {current_asset}")

        # Execute trades in the arbitrage route sequence
        for i in range(len(pares_comercio)):
            if i + 1 >= len(ruta_arbitraje):
                 error_msg = f"Ruta de arbitraje inconsistente con pares de comercio para {operacion_id} en el paso {i+1}. Ruta: {ruta_arbitraje}, Pares: {pares_comercio}"
                 logger.error(error_msg)
                 resultados["estado"] = "FALLIDO"
                 resultados["log_ejecucion"] += f"Error: {error_msg}.\n"
                 break

            trade_pair = pares_comercio[i]
            input_asset = ruta_arbitraje[i]
            output_asset = ruta_arbitraje[i+1]

            logger.info(f"Procesando paso {i+1}/{len(pares_comercio)}: Par {trade_pair}, Entrada: {input_asset}, Salida: {output_asset}")

            # Determine order side (BUY or SELL)
            try:
                pair_info = binance_trade_client.obtener_reglas_simbolo(trade_pair)
                if not pair_info:
                     error_msg = f"No se pudo obtener información del símbolo para {trade_pair} en el paso {i+1}"
                     logger.error(error_msg)
                     resultados["estado"] = "FALLIDO"
                     resultados["log_ejecucion"] += f"Error: {error_msg}.\n"
                     break

                base_asset = pair_info.get("baseAsset")
                quote_asset = pair_info.get("quoteAsset")

                if input_asset == quote_asset and output_asset == base_asset:
                     order_side = "BUY"
                elif input_asset == base_asset and output_asset == quote_asset:
                     order_side = "SELL"
                else:
                     error_msg = f"Dirección de trading inválida para {trade_pair} con ruta {input_asset} -> {output_asset}"
                     logger.error(error_msg)
                     resultados["estado"] = "FALLIDO"
                     resultados["log_ejecucion"] += f"Error: {error_msg}.\n"
                     break
                logger.debug(f"Información del símbolo para {trade_pair}: {pair_info}")
                logger.info(f"Lado de la orden determinado: {order_side}")

            except Exception as e:
                 error_msg = f"Error al obtener información del símbolo {trade_pair} en el paso {i+1}: {str(e)}"
                 logger.error(error_msg, exc_info=e)
                 resultados["estado"] = "FALLIDO"
                 resultados["log_ejecucion"] += f"Error: {error_msg}.\n"
                 break

            logger.info(f"Ejecutando paso {i+1}: {trade_pair} {order_side} con {current_capital} de {current_asset}")

            # Get current price for calculation and slippage calculation later
            try:
                current_price_info = binance_trade_client.obtener_precio_ticker(trade_pair)
                if current_price_info is None:
                     error_msg = f"No se pudo obtener el precio para {trade_pair} en el paso {i+1}"
                     logger.error(error_msg)
                     resultados["estado"] = "FALLIDO"
                     resultados["log_ejecucion"] += f"Error: {error_msg}.\n"
                     break

                price_before_order = current_price_info # Store price before placing order
                logger.info(f"Precio antes de la orden para {trade_pair}: {price_before_order}")

            except Exception as e:
                 error_msg = f"Error al obtener el precio para {trade_pair} en el paso {i+1}: {str(e)}"
                 logger.error(error_msg, exc_info=e)
                 resultados["estado"] = "FALLIDO"
                 resultados["log_ejecucion"] += f"Error: {error_msg}.\n"
                 break

            # Calculate quantity based on current capital and price
            if order_side == "BUY":
                 # Buying base with quote: quantity of base = current_capital (quote) / price_before_order
                 quantity_to_trade = current_capital / price_before_order
            else: # SELL
                 # Selling base for quote: quantity of base = current_capital (base)
                 quantity_to_trade = current_capital

            # Round quantity according to symbol rules
            rounded_quantity = binance_trade_client.redondear_cantidad(trade_pair, quantity_to_trade)

            if rounded_quantity <= 0:
                 error_msg = f"Cantidad redondeada es cero o negativa para {trade_pair} en el paso {i+1}. Cantidad calculada: {quantity_to_trade}, Redondeada: {rounded_quantity}"
                 logger.error(error_msg)
                 resultados["estado"] = "FALLIDO"
                 resultados["log_ejecucion"] += f"Error: {error_msg}.\n"
                 break

            logger.info(f"Cantidad a tradear (redondeada): {rounded_quantity}")

            # **Balance Validation before placing order**
            try:
                balances = binance_trade_client.get_balances()
                if balances is None:
                    error_msg = f"No se pudieron obtener los balances para validar antes de la orden en el paso {i+1}"
                    logger.error(error_msg)
                    resultados["estado"] = "FALLIDO"
                    resultados["log_ejecucion"] += f"Error: {error_msg}.\n"
                    break

                available_balance = next((float(b["free"]) for b in balances if b["asset"] == input_asset), 0.0)

                # For BUY orders, check if current_capital (in quote asset) is available
                # For SELL orders, check if rounded_quantity (in base asset) is available
                if order_side == "BUY":
                    if available_balance < current_capital:
                        error_msg = f"Saldo insuficiente de {input_asset} para la orden de {trade_pair} en el paso {i+1}. Requerido: {current_capital}, Disponible: {available_balance}"
                        logger.error(error_msg)
                        resultados["estado"] = "FALLIDO"
                        resultados["log_ejecucion"] += f"Error: {error_msg}.\n"
                        break
                else: # SELL
                     if available_balance < rounded_quantity:
                        error_msg = f"Saldo insuficiente de {input_asset} para la orden de {trade_pair} en el paso {i+1}. Requerido: {rounded_quantity}, Disponible: {available_balance}"
                        logger.error(error_msg)
                        resultados["estado"] = "FALLIDO"
                        resultados["log_ejecucion"] += f"Error: {error_msg}.\n"
                        break

                logger.info(f"Validación de saldo exitosa. Disponible de {input_asset}: {available_balance}")

            except Exception as e:
                error_msg = f"Error durante la validación de saldo para {trade_pair} en el paso {i+1}: {str(e)}"
                logger.error(error_msg, exc_info=e)
                resultados["estado"] = "FALLIDO"
                resultados["log_ejecucion"] += f"Error: {error_msg}.\n"
                break


            # Place the order with improved error handling
            order_result = None
            try:
                order_result = binance_trade_client.crear_orden_mercado(trade_pair, order_side, rounded_quantity)

                if not order_result or "status" not in order_result or order_result["status"] != "FILLED":
                    error_msg = f"Orden no completada o con estado inesperado para {trade_pair} en el paso {i+1}. Resultado: {order_result}"
                    logger.error(error_msg)
                    resultados["estado"] = "FALLIDO"
                    resultados["log_ejecucion"] += f"Error: {error_msg}\n"
                    # Attempt to cancel any previously placed orders
                    for order_id, pair_sym in placed_order_ids:
                        try:
                            binance_trade_client.cancelar_orden(pair_sym, order_id)
                            logger.info(f"Orden {order_id} para {pair_sym} cancelada.")
                        except Exception as cancel_e:
                            logger.error(f"Error al cancelar orden {order_id} para {pair_sym}: {str(cancel_e)}")
                    break # Exit if order fails

                logger.info(f"Orden completada para {trade_pair} en el paso {i+1}. Resultado: {order_result}")

                # Track order ID and details
                if "orderId" in order_result:
                     placed_order_ids.append((order_result["orderId"], trade_pair))

                # Update executed quantities and prices
                executed_qty = float(order_result.get("executedQty", 0.0))
                cummulative_quote_qty = float(order_result.get("cummulativeQuoteQty", 0.0))
                executed_quantities[trade_pair] = executed_qty
                # Calculate average executed price from fills if available, otherwise use cummulativeQuoteQty / executedQty
                average_executed_price = 0.0
                if "fills" in order_result and len(order_result["fills"]) > 0:
                    total_quote_qty = sum(float(fill.get("quoteQty", 0.0)) for fill in order_result["fills"])
                    total_executed_qty = sum(float(fill.get("qty", 0.0)) for fill in order_result["fills"])
                    average_executed_price = total_quote_qty / total_executed_qty if total_executed_qty > 0 else 0.0
                elif executed_qty > 0:
                     average_executed_price = cummulative_quote_qty / executed_qty

                executed_prices[trade_pair] = average_executed_price
                logger.debug(f"Precio promedio ejecutado para {trade_pair}: {average_executed_price}")


                # Calculate commissions for this trade
                trade_commissions = 0.0
                if "fills" in order_result:
                     for fill in order_result["fills"]:
                          trade_commissions += float(fill.get("commission", 0.0)) # Assuming commission is in quote asset of the fill
                total_commissions += trade_commissions
                logger.info(f"Comisión calculada para {trade_pair}: {trade_commissions}")

                # **Calculate Slippage**
                slippage_percentage = 0.0
                if price_before_order > 0:
                    if order_side == "BUY":
                        # For BUY, slippage is (executed_price - price_before_order) / price_before_order
                        slippage_percentage = ((average_executed_price - price_before_order) / price_before_order) * 100
                    else: # SELL
                        # For SELL, slippage is (price_before_order - executed_price) / price_before_order
                        slippage_percentage = ((price_before_order - average_executed_price) / price_before_order) * 100

                resultados["slippage_real"] += slippage_percentage # Accumulate slippage across trades
                logger.info(f"Slippage calculado para {trade_pair}: {slippage_percentage:.4f}%")


                # Update current_capital and current_asset for the next trade
                if order_side == "BUY":
                     current_capital = executed_qty * average_executed_price # Use executed price for next calculation
                     current_asset = base_asset
                else: # SELL
                     current_capital = cummulative_quote_qty # cummulativeQuoteQty is already in quote asset
                     current_asset = quote_asset

                resultados["pares_ejecutados"].append({
                    "pair": trade_pair,
                    "side": order_side,
                    "executed_qty": executed_qty,
                    "executed_price": average_executed_price,
                    "commission": trade_commissions,
                    "slippage": slippage_percentage
                })
                resultados["precios_reales"][trade_pair] = average_executed_price
                logger.info(f"Capital actual después de {trade_pair}: {current_capital} {current_asset}")


            except Exception as e:
                error_msg = f"Error al crear o procesar orden para {trade_pair} en el paso {i+1}: {str(e)}"
                logger.error(error_msg, exc_info=e)
                resultados["estado"] = "FALLIDO"
                resultados["log_ejecucion"] += f"Error: {error_msg}\n"
                # Attempt to cancel any previously placed orders
                for order_id, pair_sym in placed_order_ids:
                    try:
                        binance_trade_client.cancelar_orden(pair_sym, order_id)
                        logger.info(f"Orden {order_id} para {pair_sym} cancelada en bloque de excepción.")
                    except Exception as cancel_e:
                        logger.error(f"Error al cancelar orden {order_id} para {pair_sym} en bloque de excepción: {str(cancel_e)}")
                break # Exit if order fails


        # After executing all trades (if loop completed without break)
        if resultados["estado"] == "PENDIENTE": # Check if no errors occurred during the loop
            resultados["estado"] = "COMPLETADO"
            resultados["fecha_completado"] = int(time.time() * 1000) # Use current timestamp

            # Calculate final profit/loss
            final_capital = current_capital
            ganancia_neta = final_capital - capital_inicial # Ganancia neta ya incluye comisiones y slippage a través de current_capital updates
            rentabilidad_real = (ganancia_neta / capital_inicial) * 100 if capital_inicial > 0 else 0.0

            resultados["ganancia_neta"] = ganancia_neta
            resultados["rentabilidad_real"] = rentabilidad_real
            resultados["comisiones_totales"] = total_commissions # Still track total commissions separately
            # slippage_real is already accumulated in the loop

            logger.info(f"Ejecución de arbitraje completada para {operacion_id}.")
            logger.info(f"Resultados finales: Ganancia neta: {ganancia_neta}, Rentabilidad: {rentabilidad_real}%, Comisiones: {total_commissions}, Slippage total: {resultados['slippage_real']:.4f}%")

            try:
                supabase_client.insertar_operacion(resultados)
                logger.info(f"Execution results for operation {operacion_id} logged to Supabase.")
                # Send Telegram notification for successful trade
                await telegram_handler.send_trade_result_notification({
                    "opportunity_id": operacion_id,
                    "status": "COMPLETADO",
                    "profit_loss": f"{ganancia_neta:.6f} ({rentabilidad_real:.6f}%)",
                    "details": f"Comisiones: {total_commissions:.6f}, Slippage: {resultados['slippage_real']:.4f}%"
                })
            except Exception as supabase_e:
                logger.error(f"Error logging execution results to Supabase for operation {operacion_id}: {str(supabase_e)}", exc_info=supabase_e)

    except Exception as e:
        error_msg = f"Error inesperado durante la ejecución de arbitraje para {operacion_id}: {str(e)}"
        logger.critical(error_msg, exc_info=e) # Use critical for unexpected errors
        resultados["estado"] = "FALLIDO"
        resultados["log_ejecucion"] += f"Error inesperado: {str(e)}\n"
        # Attempt to cancel any previously placed orders
        for order_id, pair_sym in placed_order_ids:
            try:
                binance_trade_client.cancelar_orden(pair_sym, order_id)
                logger.info(f"Orden {order_id} para {pair_sym} cancelada en bloque de excepción.")
            except Exception as cancel_e:
                logger.error(f"Error al cancelar orden {order_id} para {pair_sym} en bloque de excepción: {str(cancel_e)}")
        
        try:
            supabase_client.insertar_operacion(resultados)
            logger.info(f"Failed execution results for operation {operacion_id} logged to Supabase.")
            # Send Telegram notification for failed trade
            # Send Telegram notification for failed trade
            await telegram_handler.send_trade_result_notification({
                "opportunity_id": operacion_id,
                "status": "FALLIDO",
                "profit_loss": "N/A",
                "details": f"Error: {error_msg}"
            })
        except Exception as supabase_e:
            logger.error(f"Error logging failed execution results to Supabase for operation {operacion_id}: {str(supabase_e)}", exc_info=supabase_e)

    logger.info(f"Finalizando ejecución de arbitraje para operación ID: {operacion_id} con estado: {resultados['estado']}")
    return resultados

# Código para ejecutar la verificación directamente
if __name__ == "__main__":
    result = verificar_modulo_ejecucion()
    print(f"Resultado: {'✅ OK' if result['success'] else '❌ ERROR'}")
    print(f"Mensaje: {result['message']}")
    print("\nDetalles:")
    for key, value in result.get("details", {}).items():
        print(f"- {key}: {value}")
