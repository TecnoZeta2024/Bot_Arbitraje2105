"""
Manejador de respuestas de Telegram para el Bot de Arbitraje Triangular.
Procesa mensajes recibidos del bot de Telegram y los reenvía a n8n.
"""

import asyncio
import json
import logging
import time
from typing import Any, Callable, Dict, List, Optional

import requests
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from ...apis.supabase_client import SupabaseClient
from ...utils.config import settings
from ...utils.logger import get_logger

# from ...core.ejecutar_ciclo import execute_trade_cycle # Removed to break circular dependency

# Obtener logger específico
telegram_logger = get_logger("telegram_handler")

class TelegramHandler:
    """
    Clase para gestionar la comunicación con Telegram.
    Facilita el procesamiento de respuestas del usuario.
    """
    
    def __init__(self):
        """Inicializa el manejador de Telegram con la configuración global."""
        self.token = settings.telegram_bot_token
        self.chat_id = settings.telegram_chat_id
        self.operaciones_pendientes = {}  # Diccionario para seguimiento de operaciones pendientes
        self.bot = None
        self.app = None
        self.trade_execution_function: Optional[Callable] = None # To inject execute_trade_cycle
        telegram_logger.info("Manejador de Telegram inicializado")

    def set_trade_execution_function(self, func: Callable):
        """Sets the function to be called for trade execution."""
        self.trade_execution_function = func
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Maneja el comando /start.
        
        Args:
            update: Objeto Update de Telegram.
            context: Contexto del manejador.
        """
        await update.message.reply_text(
            "Bot de Arbitraje Triangular activo. Usa /status para ver el estado actual."
        )
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Maneja el comando /status.
        
        Args:
            update: Objeto Update de Telegram.
            context: Contexto del manejador.
        """
        # Contar operaciones pendientes
        num_pendientes = len(self.operaciones_pendientes)
        
        # Preparar mensaje de estado
        if num_pendientes > 0:
            mensaje = f"🤖 Bot activo con {num_pendientes} operación(es) pendiente(s):"
            
            for op_id, op_info in self.operaciones_pendientes.items():
                mensaje += f"\n- {op_id}: {op_info.get('ruta', 'N/A')} (exp: {op_info.get('expiracion', 'N/A')})"
        else:
            mensaje = "🤖 Bot activo sin operaciones pendientes."
        
        await update.message.reply_text(mensaje)
    
    async def si_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Maneja el comando /Si (confirmación).
        
        Args:
            update: Objeto Update de Telegram.
            context: Contexto del manejador.
        """
        # Buscar operación pendiente para este chat
        operacion_id = None
        for op_id, op_info in self.operaciones_pendientes.items():
            if op_info.get("chat_id") == update.effective_chat.id:
                operacion_id = op_id
                break
        
        if not operacion_id:
            await update.message.reply_text("No hay operaciones pendientes de confirmación.")
            return
        
        # Extraer datos de la operación
        operacion = self.operaciones_pendientes[operacion_id]

        supabase_client = SupabaseClient() # Instantiate SupabaseClient

        try:
            # Update status to confirmed in Supabase
            await supabase_client.update_opportunity_status(operacion_id, "confirmed")
            telegram_logger.info(f"Opportunity {operacion_id} status updated to confirmed in Supabase.")

            # Trigger trade execution
            if self.trade_execution_function:
                await self.trade_execution_function(operacion_id, operacion, operacion.get("analisis_ia", {})) # Pass required args
                await update.message.reply_text("✅ Confirmación recibida. Iniciando ejecución...")
                telegram_logger.info(f"Trade execution triggered for opportunity: {operacion_id}")
            else:
                telegram_logger.error("Trade execution function not set in TelegramHandler.")
                await update.message.reply_text("❌ Error: La función de ejecución de operaciones no está configurada.")

            # Send decision to n8n (optional, depending on n8n workflow)
            # exito_n8n = self.enviar_decision_n8n(operacion_id, "Si")
            # if not exito_n8n:
            #     telegram_logger.error(f"Failed to send decision to n8n for operation: {operacion_id}")

        except Exception as e:
            telegram_logger.error(f"Error processing 'Si' command for operation {operacion_id}: {str(e)}", exc_info=e)
            await update.message.reply_text(f"❌ Error al procesar la confirmación: {str(e)}")
        finally:
            # Always remove from pending operations
            if operacion_id in self.operaciones_pendientes:
                del self.operaciones_pendientes[operacion_id]
                telegram_logger.info(f"Removed operation {operacion_id} from pending list.")

    async def no_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Maneja el comando /No (cancelación).
        
        Args:
            update: Objeto Update de Telegram.
            context: Contexto del manejador.
        """
        # Buscar operación pendiente para este chat
        operacion_id = None
        for op_id, op_info in self.operaciones_pendientes.items():
            if op_info.get("chat_id") == update.effective_chat.id:
                operacion_id = op_id
                break
        
        if not operacion_id:
            await update.message.reply_text("No hay operaciones pendientes de cancelación.")
            return
        
        # Extraer datos de la operación
        operacion = self.operaciones_pendientes[operacion_id]

        supabase_client = SupabaseClient() # Instantiate SupabaseClient

        try:
            # Update status to discarded in Supabase
            await supabase_client.update_opportunity_status(operacion_id, "discarded")
            await update.message.reply_text("❌ Operación cancelada.")
            telegram_logger.info(f"Opportunity {operacion_id} status updated to discarded in Supabase.")

            # Send Telegram notification for discarded opportunity
            await self.send_trade_result_notification({
                "opportunity_id": operacion_id,
                "status": "DESCARTADA",
                "profit_loss": "N/A",
                "details": "Oportunidad descartada por el usuario."
            })

            # Send decision to n8n (optional, depending on n8n workflow)
            # exito_n8n = self.enviar_decision_n8n(operacion_id, "No")
            # if not exito_n8n:
            #     telegram_logger.error(f"Failed to send decision to n8n for operation: {operacion_id}")

        except Exception as e:
            telegram_logger.error(f"Error processing 'No' command for operation {operacion_id}: {str(e)}", exc_info=e)
            await update.message.reply_text(f"❌ Error al procesar la cancelación: {str(e)}")
        finally:
            # Always remove from pending operations
            if operacion_id in self.operaciones_pendientes:
                del self.operaciones_pendientes[operacion_id]
                telegram_logger.info(f"Removed operation {operacion_id} from pending list.")

    async def notify_opportunity_for_confirmation(self, opportunity_details: Dict[str, Any]) -> bool:
        """
        Envía una notificación de oportunidad de arbitraje y solicita confirmación.
        
        Args:
            opportunity_details: Diccionario con los detalles de la oportunidad.
            
        Returns:
            True si el mensaje se envía correctamente, False en caso contrario.
        """
        try:
            opportunity_id = opportunity_details.get("opportunity_id", "N/A")
            cycle = opportunity_details.get("cycle", "N/A")
            profit_net = opportunity_details.get("profit_percentage_net", "N/A")
            capital_sugerido = opportunity_details.get("capital_sugerido", "N/A")
            
            message_text = (
                f"✨ *Nueva Oportunidad de Arbitraje Detectada* ✨\n\n"
                f"*ID de Oportunidad*: `{opportunity_id}`\n"
                f"*Ruta*: `{cycle}`\n"
                f"*Rentabilidad Neta Estimada*: `{profit_net:.6f}%`\n"
                f"*Capital Sugerido*: `{capital_sugerido}`\n\n"
                f"¿Deseas ejecutar esta operación?\n"
            )
            
            # Create inline keyboard
            keyboard = [
                [
                    InlineKeyboardButton("✅ Sí", callback_data="Si"),
                    InlineKeyboardButton("❌ No", callback_data="No")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            if self.bot is None:
                self.bot = Bot(token=self.token)
                
            # Send message with inline keyboard
            sent_message = await self.bot.send_message(
                chat_id=self.chat_id,
                text=message_text,
                parse_mode="Markdown",
                reply_markup=reply_markup
            )
            
            # Register the pending operation
            self.registrar_operacion_pendiente(opportunity_id, opportunity_details)
            
            telegram_logger.info(f"Notificación de oportunidad enviada para ID: {opportunity_id}")
            return True
            
        except Exception as e:
            telegram_logger.error(f"Error al enviar notificación de oportunidad: {str(e)}", exc_info=e)
            return False
    
    def enviar_decision_n8n(self, operacion_id: str, decision: str) -> bool:
        """
        Envía la decisión del usuario a n8n.
        
        Args:
            operacion_id: ID único de la operación.
            decision: Decisión del usuario ('Si' o 'No').
            
        Returns:
            True si se envía correctamente, False en caso contrario.
        """
        try:
            # Obtener información de la operación
            if operacion_id not in self.operaciones_pendientes:
                telegram_logger.error(f"No se encontró la operación {operacion_id} en operaciones pendientes")
                return False
            
            # URL del webhook en n8n (endpoint de decisión)
            # Esto asume que hay un webhook configurado en n8n para recibir decisiones
            webhook_url = f"http://localhost:5678/webhook/9028c049-7a92-4a41-a0c8-c2b96b0b8872/decision"
            
            # Formatear datos para n8n
            datos = {
                "body": {
                    "operacion_id": operacion_id,
                    "decision": decision,
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                }
            }
            
            # Enviar POST request
            response = requests.post(
                webhook_url,
                json=datos,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code >= 200 and response.status_code < 300:
                telegram_logger.info(f"Decisión {decision} enviada correctamente a n8n para operación: {operacion_id}")
                return True
            else:
                telegram_logger.error(f"Error al enviar decisión a n8n. Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            telegram_logger.error(f"Error al enviar decisión a n8n: {str(e)}", exc_info=e)
            return False
    
    def registrar_operacion_pendiente(self, operacion_id: str, datos: Dict[str, Any]) -> None:
        """
        Registra una operación pendiente de confirmación.
        
        Args:
            operacion_id: ID único de la operación.
            datos: Datos adicionales de la operación.
        """
        # Añadir timestamp de expiración (5 minutos)
        datos["expiracion"] = time.time() + 300  # 300 segundos = 5 minutos
        
        # Registrar chat_id
        datos["chat_id"] = self.chat_id
        
        # Almacenar en diccionario
        self.operaciones_pendientes[operacion_id] = datos
        telegram_logger.info(f"Registrada operación pendiente: {operacion_id}")
    
    def limpiar_operaciones_expiradas(self) -> None:
        """Elimina operaciones que han expirado."""
        tiempo_actual = time.time()
        operaciones_expiradas = []
        
        for op_id, op_info in self.operaciones_pendientes.items():
            if op_info.get("expiracion", 0) < tiempo_actual:
                operaciones_expiradas.append(op_id)
        
        for op_id in operaciones_expiradas:
            del self.operaciones_pendientes[op_id]
            telegram_logger.info(f"Eliminada operación expirada: {op_id}")
    
    async def enviar_mensaje(self, texto: str) -> bool:
        """
        Envía un mensaje a través del bot de Telegram.
        
        Args:
            texto: Texto del mensaje a enviar.
            
        Returns:
            True si se envía correctamente, False en caso contrario.
        """
        try:
            if self.bot is None:
                # Crear bot si no existe
                self.bot = Bot(token=self.token)
            
            # Enviar mensaje
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=texto,
                parse_mode="Markdown"
            )
            
            return True
        except Exception as e:
            telegram_logger.error(f"Error al enviar mensaje a Telegram: {str(e)}", exc_info=e)
            return False
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Maneja los callbacks de botones inline.
        
        Args:
            update: Objeto Update de Telegram.
            context: Contexto del manejador.
        """
        query = update.callback_query
        await query.answer()  # Responder al callback para quitar el "reloj de carga"
        
        # Extraer decisión del callback data
        decision = query.data  # 'Si' o 'No'
        chat_id = update.effective_chat.id
        
        # Buscar operación pendiente para este chat
        operacion_id = None
        for op_id, op_info in self.operaciones_pendientes.items():
            if op_info.get("chat_id") == chat_id:
                operacion_id = op_id
                break
        
        if not operacion_id:
            await query.edit_message_text("No hay operaciones pendientes de confirmación.")
            return
        
        # Extraer datos de la operación
        operacion = self.operaciones_pendientes[operacion_id]

        supabase_client = SupabaseClient() # Instantiate SupabaseClient

        try:
            if decision == "Si":
                # Update status to confirmed in Supabase
                await supabase_client.update_opportunity_status(operacion_id, "confirmed")
                telegram_logger.info(f"Opportunity {operacion_id} status updated to confirmed in Supabase.")

                # Trigger trade execution
                if self.trade_execution_function:
                    await self.trade_execution_function(operacion_id, operacion, operacion.get("analisis_ia", {})) # Pass required args
                    await query.edit_message_text("✅ Confirmación recibida. Iniciando ejecución...")
                    telegram_logger.info(f"Trade execution triggered for opportunity: {operacion_id}")
                else:
                    telegram_logger.error("Trade execution function not set in TelegramHandler.")
                    await query.edit_message_text("❌ Error: La función de ejecución de operaciones no está configurada.")

            else: # decision == "No"
                # Update status to discarded in Supabase
                await supabase_client.update_opportunity_status(operacion_id, "discarded")
                await query.edit_message_text("❌ Operación cancelada.")
                telegram_logger.info(f"Opportunity {operacion_id} status updated to discarded in Supabase.")

                # Send Telegram notification for discarded opportunity
                await self.send_trade_result_notification({
                    "opportunity_id": operacion_id,
                    "status": "DESCARTADA",
                    "profit_loss": "N/A",
                    "details": "Oportunidad descartada por el usuario."
                })

            # Send decision to n8n (optional, depending on n8n workflow)
            # exito_n8n = self.enviar_decision_n8n(operacion_id, decision)
            # if not exito_n8n:
            #     telegram_logger.error(f"Failed to send decision to n8n for operation: {operacion_id}")

        except Exception as e:
            telegram_logger.error(f"Error processing decision for operation {operacion_id}: {str(e)}", exc_info=e)
            await query.edit_message_text(f"❌ Error al procesar la operación: {str(e)}")
        finally:
            # Always remove from pending operations
            if operacion_id in self.operaciones_pendientes:
                del self.operaciones_pendientes[operacion_id]
                telegram_logger.info(f"Removed operation {operacion_id} from pending list.")

    async def enviar_mensaje_recordatorio(self, operacion_id: str, tiempo_restante: int):
        """
        Envía un mensaje recordatorio cuando está por expirar una operación.
        
        Args:
            operacion_id: ID de la operación.
            tiempo_restante: Tiempo restante en segundos.
        """
        try:
            if operacion_id not in self.operaciones_pendientes:
                return
            
            operacion = self.operaciones_pendientes[operacion_id]
            chat_id = operacion.get("chat_id")
            
            mensaje = f"⏰ *RECORDATORIO*\n\nLa oportunidad de arbitraje expirará en {tiempo_restante} segundos.\n\n"
            mensaje += f"*Ruta*: {operacion.get('ruta', 'N/A')}\n"
            mensaje += f"*Rentabilidad*: {operacion.get('rentabilidad', 'N/A')}%\n\n"
            mensaje += "Por favor, confirma o cancela la operación:\n/Si - Confirmar\n/No - Cancelar"
            
            if self.bot is None:
                self.bot = Bot(token=self.token)
            
            await self.bot.send_message(
                chat_id=chat_id,
                text=mensaje,
                parse_mode="Markdown"
            )
            
            telegram_logger.info(f"Enviado recordatorio para operación: {operacion_id}")
        except Exception as e:
            telegram_logger.error(f"Error al enviar recordatorio: {str(e)}", exc_info=e)
    
    async def send_trade_result_notification(self, trade_result: Dict[str, Any]) -> bool:
        """
        Envía una notificación del resultado de la operación a Telegram.
        
        Args:
            trade_result: Diccionario con los detalles del resultado de la operación.
            
        Returns:
            True si el mensaje se envía correctamente, False en caso contrario.
        """
        try:
            opportunity_id = trade_result.get("opportunity_id", "N/A")
            status = trade_result.get("status", "N/A")
            profit_loss = trade_result.get("profit_loss", "N/A")
            details = trade_result.get("details", "No hay detalles adicionales.")

            message_text = (
                f"📊 *Resultado de Operación de Arbitraje* 📊\n\n"
                f"*ID de Oportunidad*: `{opportunity_id}`\n"
                f"*Estado*: `{status}`\n"
                f"*Ganancia/Pérdida*: `{profit_loss}`\n"
                f"*Detalles*: {details}\n\n"
                f"¡Revisa el dashboard para más información!"
            )

            if self.bot is None:
                self.bot = Bot(token=self.token)
            
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message_text,
                parse_mode="Markdown"
            )
            
            telegram_logger.info(f"Notificación de resultado de operación enviada para ID: {opportunity_id}")
            return True
            
        except Exception as e:
            telegram_logger.error(f"Error al enviar notificación de resultado de operación: {str(e)}", exc_info=e)
            return False

    async def iniciar_bot(self):
        """Inicia el bot de Telegram para recibir comandos."""
        try:
            # Crear aplicación
            self.app = Application.builder().token(self.token).build()
            
            # Registrar handlers
            self.app.add_handler(CommandHandler("start", self.start_command))
            self.app.add_handler(CommandHandler("status", self.status_command))
            self.app.add_handler(CommandHandler("Si", self.si_command))
            self.app.add_handler(CommandHandler("No", self.no_command))
            self.app.add_handler(CallbackQueryHandler(self.handle_callback))  # Para botones inline
            
            # Iniciar bot
            telegram_logger.info("Iniciando bot de Telegram...")
            await self.app.initialize()
            await self.app.start()
            await self.app.updater.start_polling()
            
            # Enviar mensaje de inicio
            await self.enviar_mensaje("🤖 *Bot de Arbitraje Triangular iniciado*\nListo para procesar operaciones.")
            
            telegram_logger.info("Bot de Telegram iniciado correctamente")
            
            # Loop para limpiar operaciones expiradas y enviar recordatorios
            while True:
                tiempo_actual = time.time()
                
                # Comprobar recordatorios
                for op_id, op_info in self.operaciones_pendientes.items():
                    tiempo_expiracion = op_info.get("expiracion", 0)
                    tiempo_restante = tiempo_expiracion - tiempo_actual
                    
                    # Enviar recordatorio cuando queden 60 segundos
                    if 55 <= tiempo_restante <= 65:
                        await self.enviar_mensaje_recordatorio(op_id, int(tiempo_restante))
                
                # Limpiar operaciones expiradas
                self.limpiar_operaciones_expiradas()
                
                # Esperar antes de siguiente comprobación
                await asyncio.sleep(30)  # Comprobar cada 30 segundos
                
        except Exception as e:
            telegram_logger.error(f"Error al iniciar bot de Telegram: {str(e)}", exc_info=e)
            raise

# Instancia global
telegram_handler = TelegramHandler()

def start_telegram_bot():
    """Inicia el bot de Telegram en un hilo separado."""
    asyncio.run(telegram_handler.iniciar_bot())

if __name__ == "__main__":
    # Para pruebas directas
    start_telegram_bot()
