"""
Sistema de Telegram mejorado para el trading bot
Basado en código probado y funcional
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime
import aiohttp
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode

from infrastructure.messaging.notification_service import MessageChannel, Message, MessageType


class AdvancedTelegramChannel(MessageChannel):
    """Canal de Telegram avanzado basado en código probado."""
    
    def __init__(self, bot_token: str, chat_id: str):
        super().__init__("TelegramAdvanced")
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.bot = None
        self.rate_limit_delay = 1.0
        
    async def send_message(self, message: Message) -> bool:
        """Envía mensaje por Telegram usando la librería telegram."""
        try:
            await self._rate_limit_check()
            
            if self.bot is None:
                self.bot = Bot(token=self.bot_token)
            
            # Formatear mensaje
            formatted_message = self._format_message_safe(message)
            
            # Enviar mensaje
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=formatted_message,
                parse_mode=ParseMode.MARKDOWN,
                disable_web_page_preview=True
            )
            
            self.logger.info(f"Telegram message sent successfully: {message.id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error sending Telegram message: {e}")
            # Fallback: enviar como texto plano
            try:
                return await self._send_plain_text_fallback(message)
            except:
                return False
    
    async def _send_plain_text_fallback(self, message: Message) -> bool:
        """Fallback para enviar como texto plano."""
        try:
            if self.bot is None:
                self.bot = Bot(token=self.bot_token)
            
            plain_text = self._format_plain_text(message)
            
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=plain_text,
                disable_web_page_preview=True
            )
            
            self.logger.info(f"Telegram fallback message sent: {message.id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Telegram fallback failed: {e}")
            return False
    
    async def test_connection(self) -> bool:
        """Prueba la conexión con Telegram."""
        try:
            if self.bot is None:
                self.bot = Bot(token=self.bot_token)
            
            # Test con getMe
            bot_info = await self.bot.get_me()
            self.logger.info(f"Connected to Telegram bot: {bot_info.username}")
            return True
            
        except Exception as e:
            self.logger.error(f"Telegram connection test failed: {e}")
            return False
    
    def _format_message_safe(self, message: Message) -> str:
        """Formatea mensaje de manera segura para Telegram."""
        # Mapeo de emojis seguro
        emoji_map = {
            MessageType.INFO: "ℹ️",
            MessageType.WARNING: "⚠️", 
            MessageType.ERROR: "❌",
            MessageType.CRITICAL: "🚨",
            MessageType.TRADE_SIGNAL: "📈",
            MessageType.PROFIT_LOSS: "💰",
            MessageType.SYSTEM_STATUS: "🔧"
        }
        
        emoji = emoji_map.get(message.type, "📄")
        
        # Limpiar contenido de caracteres problemáticos
        clean_title = self._clean_text_for_markdown(str(message.title))
        clean_content = self._clean_text_for_markdown(str(message.content))
        
        # Formato básico sin caracteres problemáticos
        formatted = f"{emoji} *{clean_title}*\n\n"
        formatted += f"{clean_content}\n\n"
        formatted += f"🕐 {message.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
        
        # Agregar tags de manera segura
        if message.tags:
            formatted += "\n\n*Tags:*"
            for key, value in message.tags.items():
                clean_key = self._clean_text_for_markdown(str(key))
                clean_value = self._clean_text_for_markdown(str(value))
                formatted += f"\n• {clean_key}: {clean_value}"
        
        return formatted
    
    def _format_plain_text(self, message: Message) -> str:
        """Formatea como texto plano sin Markdown."""
        type_labels = {
            MessageType.INFO: "[INFO]",
            MessageType.WARNING: "[WARNING]",
            MessageType.ERROR: "[ERROR]", 
            MessageType.CRITICAL: "[CRITICAL]",
            MessageType.TRADE_SIGNAL: "[TRADE_SIGNAL]",
            MessageType.PROFIT_LOSS: "[PROFIT_LOSS]",
            MessageType.SYSTEM_STATUS: "[SYSTEM_STATUS]"
        }
        
        label = type_labels.get(message.type, "[MESSAGE]")
        
        formatted = f"{label} {message.title}\n\n"
        formatted += f"{message.content}\n\n"
        formatted += f"Time: {message.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
        
        if message.tags:
            formatted += "\n\nTags:"
            for key, value in message.tags.items():
                formatted += f"\n- {key}: {value}"
        
        return formatted
    
    def _clean_text_for_markdown(self, text: str) -> str:
        """Limpia texto para evitar problemas con Markdown."""
        # Reemplazar caracteres problemáticos
        replacements = {
            '_': ' ',
            '*': ' ',
            '[': '(',
            ']': ')',
            '`': "'",
            '\\': '/',
        }
        
        cleaned = str(text)
        for old, new in replacements.items():
            cleaned = cleaned.replace(old, new)
        
        # Remover caracteres no ASCII problemáticos excepto emojis básicos
        cleaned = ''.join(char for char in cleaned if ord(char) < 127 or char in '📈📉💰🚨⚠️ℹ️❌✅🔧📄🕐')
        
        return cleaned
    
    async def send_trading_notification(self, 
                                      title: str, 
                                      symbol: str, 
                                      action: str, 
                                      price: float, 
                                      confidence: float,
                                      additional_info: Dict[str, Any] = None) -> bool:
        """Envía notificación específica de trading."""
        try:
            if self.bot is None:
                self.bot = Bot(token=self.bot_token)
            
            # Formatear mensaje de trading
            message_text = f"📈 *Nueva Señal de Trading*\n\n"
            message_text += f"*Símbolo*: {symbol}\n"
            message_text += f"*Acción*: {action}\n"
            message_text += f"*Precio*: ${price:.6f}\n"
            message_text += f"*Confianza*: {confidence:.1%}\n"
            
            if additional_info:
                message_text += f"\n*Información adicional*:\n"
                for key, value in additional_info.items():
                    clean_key = self._clean_text_for_markdown(str(key))
                    clean_value = self._clean_text_for_markdown(str(value))
                    message_text += f"• {clean_key}: {clean_value}\n"
            
            message_text += f"\n🕐 {datetime.now().strftime('%H:%M:%S')}"
            
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message_text,
                parse_mode=ParseMode.MARKDOWN,
                disable_web_page_preview=True
            )
            
            self.logger.info(f"Trading notification sent for {symbol}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error sending trading notification: {e}")
            return False
    
    async def send_pnl_notification(self, 
                                   symbol: str, 
                                   pnl: float, 
                                   pnl_pct: float, 
                                   position_size: float) -> bool:
        """Envía notificación de P&L."""
        try:
            if self.bot is None:
                self.bot = Bot(token=self.bot_token)
            
            # Emoji según el resultado
            emoji = "📈" if pnl > 0 else "📉"
            status = "GANANCIA" if pnl > 0 else "PERDIDA"
            
            message_text = f"{emoji} *{status} - {symbol}*\n\n"
            message_text += f"*P&L*: ${pnl:.2f} ({pnl_pct:+.2f}%)\n"
            message_text += f"*Tamaño*: ${position_size:.2f}\n"
            message_text += f"\n🕐 {datetime.now().strftime('%H:%M:%S')}"
            
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message_text,
                parse_mode=ParseMode.MARKDOWN,
                disable_web_page_preview=True
            )
            
            self.logger.info(f"P&L notification sent for {symbol}: ${pnl:.2f}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error sending P&L notification: {e}")
            return False


# Función para reemplazar el canal de Telegram en NotificationService
def upgrade_telegram_channel(notification_service, bot_token: str, chat_id: str):
    """Actualiza el canal de Telegram con la versión mejorada."""
    try:
        # Crear nuevo canal avanzado
        advanced_channel = AdvancedTelegramChannel(bot_token, chat_id)
        
        # Reemplazar en el router
        notification_service.router.channels["telegram"] = advanced_channel
        
        logging.getLogger("TelegramUpgrade").info("Telegram channel upgraded successfully")
        return advanced_channel
        
    except Exception as e:
        logging.getLogger("TelegramUpgrade").error(f"Failed to upgrade Telegram channel: {e}")
        return None
