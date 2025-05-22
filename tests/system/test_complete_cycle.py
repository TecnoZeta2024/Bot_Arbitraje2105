#!/usr/bin/env python
"""
Prueba completa del ciclo de arbitraje triangular.

Este script ejecuta una prueba completa del ciclo de arbitraje triangular, incluyendo:
1. Detección de oportunidades
2. Envío a n8n (webhook)
3. Recepción de solicitud de ejecución
4. Ejecución de operaciones (en testnet)
5. Envío de resultados a n8n
6. Verificación del registro en la base de datos

Uso:
    python tests/system/test_complete_cycle.py

Nota: Este script requiere que el servidor API esté en ejecución.
"""

import sys
import os
import time
import json
import logging
import requests
from datetime import datetime
from pathlib import Path

# Añadir el directorio raíz del proyecto al path para importar módulos
project_root = Path(__file__).parents[2].absolute()
sys.path.append(str(project_root))

# Importar módulos del proyecto
from src.utils.config import settings
from src.utils.logger import setup_logger
from src.apis.supabase_client import SupabaseClient
from src.core.detectar_oportunidades import ejecutar_deteccion
from src.core.ejecutar_ciclo import ejecutar_arbitraje

# Configurar logger para esta prueba
logger = setup_logger("test_complete_cycle", log_level=logging.INFO)

class CompleteCycleTest:
    """
    Clase para ejecutar y verificar una prueba completa del ciclo de arbitraje.
    
    Esta clase sigue el patrón Single Responsibility Principle (SRP) al tener
    una única responsabilidad: gestionar la prueba del ciclo completo.
    """
    
    def __init__(self):
        """Inicializa la prueba del ciclo completo."""
        self.start_time = datetime.now()
        self.test_id = f"test_{int(time.time())}"
        self.supabase = SupabaseClient()
        self.api_server_url = settings.api_server_url
        self.n8n_webhook_url = settings.n8n_webhook_resultado
        
        logger.info(f"Iniciando prueba completa del ciclo con ID: {self.test_id}")
        logger.info(f"API Server URL: {self.api_server_url}")
        logger.info(f"n8n Webhook URL (resultado): {self.n8n_webhook_url}")
    
    def run_detection_phase(self):
        """
        Ejecuta la fase de detección de oportunidades.
        
        Returns:
            dict: Resultado de la detección o None si no se detectan oportunidades.
        """
        logger.info("1. Iniciando fase de detección de oportunidades...")
        
        try:
            # Intentar ejecutar detección de oportunidades
            result = ejecutar_deteccion()
            
            if not result or 'oportunidades' not in result or not result['oportunidades']:
                logger.warning("No se detectaron oportunidades de arbitraje.")
                return None
            
            # Tomar la primera oportunidad detectada
            oportunidad = result['oportunidades'][0]
            logger.info(f"Oportunidad detectada: {oportunidad['ruta']} - Rentabilidad: {oportunidad['rentabilidad_bruta']}%")
            
            return oportunidad
        
        except Exception as e:
            logger.error(f"Error en fase de detección: {str(e)}", exc_info=True)
            return None
    
    def simulate_n8n_execution_request(self, oportunidad):
        """
        Simula una solicitud de ejecución desde n8n.
        
        Args:
            oportunidad (dict): Datos de la oportunidad detectada.
            
        Returns:
            dict: Resultado de la simulación o None si falla.
        """
        logger.info("2. Simulando solicitud de ejecución desde n8n...")
        
        try:
            # Crear solicitud de ejecución simulada (como si viniera de n8n)
            operacion_id = f"{self.test_id}_{int(time.time())}"
            
            # Simular análisis de IA
            analisis_ia = {
                "recomendacion": "PROCEDER",
                "confianza": 85,
                "rentabilidad_neta_estimada": oportunidad['rentabilidad_bruta'] * 0.9,  # Estimación ajustada con comisiones
                "riesgos_identificados": [
                    "Posible slippage en pares con menor liquidez",
                    "Volatilidad reciente en el mercado"
                ],
                "explicacion": "Oportunidad de arbitraje viable con buena rentabilidad estimada después de comisiones."
            }
            
            # Crear payload para la solicitud de ejecución
            payload = {
                "operacion_id": operacion_id,
                "oportunidad": oportunidad,
                "analisis_ia": analisis_ia,
                "confirmacion_usuario": {
                    "timestamp": datetime.now().isoformat(),
                    "decision": "Ejecutar"
                }
            }
            
            # Hacer la solicitud al servidor API para ejecutar el arbitraje
            response = requests.post(
                f"{self.api_server_url}/api/ejecutar-arbitraje",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                logger.info("Solicitud de ejecución enviada correctamente.")
                return {
                    "operacion_id": operacion_id,
                    "payload": payload,
                    "response": response.json()
                }
            else:
                logger.error(f"Error al enviar solicitud: {response.status_code} - {response.text}")
                return None
        
        except Exception as e:
            logger.error(f"Error al simular solicitud de ejecución: {str(e)}", exc_info=True)
            return None
    
    def execute_arbitrage(self, execution_data):
        """
        Ejecuta directamente el arbitraje sin pasar por el servidor API.
        
        Esta alternativa es útil si el servidor API no está disponible o se quiere
        probar la ejecución de forma aislada.
        
        Args:
            execution_data (dict): Datos de la solicitud de ejecución.
            
        Returns:
            dict: Resultado de la ejecución o None si falla.
        """
        logger.info("3. Ejecutando operación de arbitraje (directamente)...")
        
        try:
            # Extraer datos relevantes
            operacion_id = execution_data["operacion_id"]
            oportunidad = execution_data["payload"]["oportunidad"]
            analisis_ia = execution_data["payload"]["analisis_ia"]
            
            # Ejecutar arbitraje (en modo simulación/testnet)
            resultado = ejecutar_arbitraje(
                operacion_id=operacion_id,
                oportunidad=oportunidad,
                analisis_ia=analisis_ia,
                test_mode=True  # Usar modo de prueba (sin ejecutar órdenes reales)
            )
            
            if resultado:
                logger.info(f"Ejecución completada: {resultado['estado']}")
                logger.info(f"Ganancia neta: {resultado['ganancia_neta']} USDT")
                logger.info(f"Rentabilidad real: {resultado['rentabilidad_real']}%")
                return resultado
            else:
                logger.error("No se pudo completar la ejecución del arbitraje.")
                return None
        
        except Exception as e:
            logger.error(f"Error al ejecutar arbitraje: {str(e)}", exc_info=True)
            return None
    
    def send_result_to_n8n(self, resultado):
        """
        Envía el resultado de la ejecución a n8n vía webhook.
        
        Args:
            resultado (dict): Resultado de la ejecución.
            
        Returns:
            bool: True si se envió correctamente, False en caso contrario.
        """
        logger.info("4. Enviando resultado a n8n...")
        
        try:
            # Preparar payload para el webhook
            payload = {
                "body": resultado
            }
            
            # Enviar resultado a n8n
            response = requests.post(
                self.n8n_webhook_url,
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                logger.info("Resultado enviado correctamente a n8n.")
                return True
            else:
                logger.error(f"Error al enviar resultado a n8n: {response.status_code} - {response.text}")
                return False
        
        except Exception as e:
            logger.error(f"Error al enviar resultado a n8n: {str(e)}", exc_info=True)
            return False
    
    def verify_database_record(self, operacion_id):
        """
        Verifica que la operación se haya registrado correctamente en la base de datos.
        
        Args:
            operacion_id (str): ID de la operación a verificar.
            
        Returns:
            bool: True si se encuentra el registro, False en caso contrario.
        """
        logger.info("5. Verificando registro en base de datos...")
        
        try:
            # Esperar un momento para que n8n procese y actualice la base de datos
            time.sleep(3)
            
            # Consultar la tabla de operaciones
            response = self.supabase.client.table("arbitraje_operaciones").select("*").eq("operacion_id", operacion_id).execute()
            
            if response.data and len(response.data) > 0:
                logger.info(f"Registro encontrado en base de datos: {response.data[0]}")
                return True
            else:
                logger.warning(f"No se encontró registro para la operación {operacion_id}")
                return False
        
        except Exception as e:
            logger.error(f"Error al verificar registro en base de datos: {str(e)}", exc_info=True)
            return False
    
    def run(self):
        """
        Ejecuta la prueba completa del ciclo.
        
        Returns:
            dict: Resultado de la prueba con todas las fases.
        """
        result = {
            "test_id": self.test_id,
            "start_time": self.start_time.isoformat(),
            "end_time": None,
            "success": False,
            "phases": {}
        }
        
        try:
            # Fase 1: Detección de oportunidades
            oportunidad = self.run_detection_phase()
            result["phases"]["detection"] = {
                "success": oportunidad is not None,
                "data": oportunidad
            }
            
            if not oportunidad:
                logger.error("La prueba no puede continuar sin una oportunidad detectada.")
                result["end_time"] = datetime.now().isoformat()
                return result
            
            # Fase 2: Simulación de solicitud desde n8n
            execution_data = self.simulate_n8n_execution_request(oportunidad)
            result["phases"]["execution_request"] = {
                "success": execution_data is not None,
                "data": execution_data
            }
            
            if not execution_data:
                logger.error("La prueba no puede continuar sin una solicitud de ejecución válida.")
                result["end_time"] = datetime.now().isoformat()
                return result
            
            # Fase 3: Ejecución del arbitraje
            execution_result = self.execute_arbitrage(execution_data)
            result["phases"]["execution"] = {
                "success": execution_result is not None,
                "data": execution_result
            }
            
            if not execution_result:
                logger.error("La prueba no puede continuar sin un resultado de ejecución válido.")
                result["end_time"] = datetime.now().isoformat()
                return result
            
            # Fase 4: Envío de resultado a n8n
            n8n_result = self.send_result_to_n8n(execution_result)
            result["phases"]["n8n_result"] = {
                "success": n8n_result,
                "webhook_url": self.n8n_webhook_url
            }
            
            # Fase 5: Verificación de registro en base de datos
            db_verification = False
            if n8n_result:
                db_verification = self.verify_database_record(execution_data["operacion_id"])
            
            result["phases"]["db_verification"] = {
                "success": db_verification,
                "operacion_id": execution_data["operacion_id"]
            }
            
            # Resultado general
            result["success"] = all([
                result["phases"]["detection"]["success"],
                result["phases"]["execution_request"]["success"],
                result["phases"]["execution"]["success"],
                result["phases"]["n8n_result"]["success"],
                result["phases"]["db_verification"]["success"]
            ])
            
        except Exception as e:
            logger.error(f"Error durante la prueba completa: {str(e)}", exc_info=True)
            result["error"] = str(e)
        
        # Finalizar prueba
        result["end_time"] = datetime.now().isoformat()
        result["duration_seconds"] = (datetime.now() - self.start_time).total_seconds()
        
        # Guardar resultado en archivo
        self.save_result(result)
        
        return result
    
    def save_result(self, result):
        """
        Guarda el resultado de la prueba en un archivo JSON.
        
        Args:
            result (dict): Resultado de la prueba.
        """
        try:
            # Crear directorio para resultados si no existe
            result_dir = project_root / "tests" / "system" / "results"
            result_dir.mkdir(parents=True, exist_ok=True)
            
            # Crear nombre de archivo con timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"test_result_{timestamp}.json"
            filepath = result_dir / filename
            
            # Guardar resultado en formato JSON
            with open(filepath, 'w') as f:
                json.dump(result, f, indent=2)
                
            logger.info(f"Resultado guardado en: {filepath}")
            
        except Exception as e:
            logger.error(f"Error al guardar resultado: {str(e)}", exc_info=True)

def run_test():
    """
    Ejecuta la prueba completa del ciclo e imprime resultados.
    """
    logger.info("=" * 80)
    logger.info("INICIANDO PRUEBA COMPLETA DEL CICLO DE ARBITRAJE TRIANGULAR")
    logger.info("=" * 80)
    
    # Verificar que el servidor API esté en ejecución
    try:
        response = requests.get(f"{settings.api_server_url}/api/health")
        if response.status_code != 200:
            logger.error(f"El servidor API no está en ejecución o no responde: {response.status_code}")
            sys.exit(1)
    except Exception as e:
        logger.error(f"No se puede conectar al servidor API: {str(e)}")
        logger.info("Asegúrate de que el servidor API esté en ejecución antes de iniciar la prueba.")
        logger.info("Puedes iniciarlo con: python src/core/api_server.py")
        sys.exit(1)
    
    # Ejecutar prueba completa
    test = CompleteCycleTest()
    result = test.run()
    
    # Mostrar resultado final
    logger.info("=" * 80)
    logger.info(f"RESULTADO DE LA PRUEBA: {'ÉXITO' if result['success'] else 'FALLO'}")
    logger.info(f"Duración total: {result['duration_seconds']:.2f} segundos")
    logger.info("=" * 80)
    
    # Mostrar resultados por fase
    for phase, phase_result in result["phases"].items():
        status = "✅" if phase_result["success"] else "❌"
        logger.info(f"{status} Fase: {phase}")
    
    logger.info("=" * 80)
    logger.info("Para más detalles, revisa el archivo de resultado generado.")
    
    return result["success"]

if __name__ == "__main__":
    success = run_test()
    sys.exit(0 if success else 1)
