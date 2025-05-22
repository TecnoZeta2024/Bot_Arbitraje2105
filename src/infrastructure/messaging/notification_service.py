"""
Sistema de Messaging - Telegram, Email, SMS y otras notificaciones
"""

import asyncio
import logging
from typing import Dict, List, Optional, Union
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import json
import aiohttp
from abc import ABC, abstractmethod


class MessageType(Enum):
    """Tipos de mensajes."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"
    TRADE_SIGNAL = "trade_signal"
    PROFIT_LOSS = "profit_loss"
    SYSTEM_STATUS = "system_status"


class MessagePriority(Enum):
    """Prioridades de mensajes."""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class Message:
    """Mensaje a enviar."""
    id: str
    type: MessageType
    priority: MessagePriority
    title: str
    content: str
    timestamp: datetime
    recipient: str
    tags: Dict[str, str]
    retry_count: int = 0
    max_retries: int = 3
    sent: bool = False
    sent_at: Optional[datetime] = None
    error: Optional[str] = None


class MessageChannel(ABC):
    """Canal abstracto de mensajería."""
    
    def __init__(self, name: str):
        self.name = name
        self.logger = logging.getLogger(f"MessageChannel.{name}")
        self.is_enabled = True
        self.rate_limit_delay = 1.0  # segundos entre mensajes
        self.last_message_time = None
    
    @abstractmethod
    async def send_message(self, message: Message) -> bool:
        """Envía un mensaje a través del canal."""
        pass
    
    @abstractmethod
    async def test_connection(self) -> bool:
        """Prueba la conexión del canal."""
        pass
    
    async def _rate_limit_check(self):
        """Verifica rate limiting."""
        if self.last_message_time:
            elapsed = (datetime.now() - self.last_message_time).total_seconds()
            if elapsed < self.rate_limit_delay:
                await asyncio.sleep(self.rate_limit_delay - elapsed)
        
        self.last_message_time = datetime.now()


class TelegramChannel(MessageChannel):
    """Canal de Telegram."""
    
    def __init__(self, bot_token: str, chat_id: str):
        super().__init__("Telegram")
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.api_url = f"https://api.telegram.org/bot{bot_token}"
        self.rate_limit_delay = 1.0  # Telegram permite ~30 mensajes por segundo
    
    async def send_message(self, message: Message) -> bool:
        """Envía mensaje por Telegram."""
        try:
            await self._rate_limit_check()
            
            # Formatear mensaje para Telegram
            formatted_message = self._format_telegram_message(message)
            
            async with aiohttp.ClientSession() as session:
                payload = {
                    "chat_id": self.chat_id,
                    "text": formatted_message,
                    "parse_mode": "Markdown",
                    "disable_web_page_preview": True
                }
                
                async with session.post(
                    f"{self.api_url}/sendMessage",
                    json=payload
                ) as response:
                    
                    if response.status == 200:
                        self.logger.info(f"Telegram message sent: {message.id}")
                        return True
                    else:
                        error_text = await response.text()
                        self.logger.error(f"Telegram send failed: {error_text}")
                        return False
        
        except Exception as e:
            self.logger.error(f"Error sending Telegram message: {e}")
            return False
    
    async def test_connection(self) -> bool:
        """Prueba la conexión con Telegram."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.api_url}/getMe") as response:
                    return response.status == 200
        except Exception:
            return False
    
    def _format_telegram_message(self, message: Message) -> str:
        """Formatea mensaje para Telegram."""
        # Emojis según el tipo
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
        
        formatted = f"{emoji} *{message.title}*\n\n"
        formatted += f"{message.content}\n\n"
        formatted += f"🕐 {message.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
        
        # Agregar tags si existen
        if message.tags:
            formatted += "\n\n*Tags:*"
            for key, value in message.tags.items():
                formatted += f"\n• {key}: `{value}`"
        
        return formatted


class EmailChannel(MessageChannel):
    """Canal de Email."""
    
    def __init__(self, smtp_host: str, smtp_port: int, username: str, password: str, from_email: str):
        super().__init__("Email")
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.from_email = from_email
        self.rate_limit_delay = 5.0  # 5 segundos entre emails
    
    async def send_message(self, message: Message) -> bool:
        """Envía mensaje por Email."""
        try:
            await self._rate_limit_check()
            
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            
            # Crear mensaje
            msg = MIMEMultipart()
            msg['From'] = self.from_email
            msg['To'] = message.recipient
            msg['Subject'] = f"[{message.type.value.upper()}] {message.title}"
            
            # Cuerpo del mensaje
            body = self._format_email_message(message)
            msg.attach(MIMEText(body, 'html'))
            
            # Enviar email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.username, self.password)
                server.send_message(msg)
            
            self.logger.info(f"Email sent: {message.id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error sending email: {e}")
            return False
    
    async def test_connection(self) -> bool:
        """Prueba la conexión SMTP."""
        try:
            import smtplib
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.username, self.password)
            return True
        except Exception:
            return False
    
    def _format_email_message(self, message: Message) -> str:
        """Formatea mensaje para Email."""
        html = f"""
        <html>
        <body>
            <h2>{message.title}</h2>
            <p><strong>Tipo:</strong> {message.type.value}</p>
            <p><strong>Prioridad:</strong> {message.priority.name}</p>
            <p><strong>Timestamp:</strong> {message.timestamp.strftime('%Y-%m-%d %H:%M:%S')}</p>
            
            <div style="margin: 20px 0; padding: 15px; background-color: #f5f5f5; border-radius: 5px;">
                {message.content.replace('\n', '<br>')}
            </div>
            
            {self._format_tags_html(message.tags) if message.tags else ''}
            
            <hr>
            <p style="font-size: 12px; color: #666;">
                Enviado por Bot de Trading - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            </p>
        </body>
        </html>
        """
        return html
    
    def _format_tags_html(self, tags: Dict[str, str]) -> str:
        """Formatea tags como HTML."""
        html = "<h3>Tags:</h3><ul>"
        for key, value in tags.items():
            html += f"<li><strong>{key}:</strong> {value}</li>"
        html += "</ul>"
        return html


class ConsoleChannel(MessageChannel):
    """Canal de consola (para desarrollo/debug)."""
    
    def __init__(self):
        super().__init__("Console")
        self.rate_limit_delay = 0.1
    
    async def send_message(self, message: Message) -> bool:
        """Imprime mensaje en consola."""
        try:
            await self._rate_limit_check()
            
            print(f"\n{'='*60}")
            print(f"[{message.type.value.upper()}] {message.title}")
            print(f"Timestamp: {message.timestamp}")
            print(f"Priority: {message.priority.name}")
            print(f"{'='*60}")
            print(message.content)
            
            if message.tags:
                print(f"\nTags: {message.tags}")
            
            print(f"{'='*60}\n")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error sending console message: {e}")
            return False
    
    async def test_connection(self) -> bool:
        """La consola siempre está disponible."""
        return True


class MessageRouter:
    """Router de mensajes que maneja el envío a múltiples canales."""
    
    def __init__(self):
        self.logger = logging.getLogger("MessageRouter")
        self.channels = {}
        self.routing_rules = {}
        self.message_queue = asyncio.Queue()
        self.is_running = False
        
        # Registrar canal de consola por defecto
        self.register_channel("console", ConsoleChannel())
    
    def register_channel(self, name: str, channel: MessageChannel):
        """Registra un canal de mensajería."""
        self.channels[name] = channel
        self.logger.info(f"Registered message channel: {name}")
    
    def add_routing_rule(self, message_type: MessageType, channels: List[str], priority_filter: Optional[MessagePriority] = None):
        """Agrega regla de routing."""
        rule = {
            "channels": channels,
            "priority_filter": priority_filter
        }
        self.routing_rules[message_type] = rule
        self.logger.info(f"Added routing rule for {message_type.value} -> {channels}")
    
    async def send_message(
        self,
        message_type: MessageType,
        title: str,
        content: str,
        priority: MessagePriority = MessagePriority.NORMAL,
        recipient: str = "",
        tags: Dict[str, str] = None
    ) -> str:
        """Envía un mensaje."""
        message = Message(
            id=f"msg_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}",
            type=message_type,
            priority=priority,
            title=title,
            content=content,
            timestamp=datetime.now(),
            recipient=recipient,
            tags=tags or {}
        )
        
        await self.message_queue.put(message)
        self.logger.info(f"Message queued: {message.id}")
        
        return message.id
    
    async def start(self):
        """Inicia el router de mensajes."""
        if self.is_running:
            return
        
        self.is_running = True
        self.logger.info("Starting message router")
        
        # Probar conexiones de canales
        await self._test_channels()
        
        # Iniciar procesamiento de mensajes
        asyncio.create_task(self._process_messages())
    
    async def stop(self):
        """Detiene el router de mensajes."""
        self.is_running = False
        self.logger.info("Stopping message router")
    
    async def _test_channels(self):
        """Prueba conexiones de todos los canales."""
        for name, channel in self.channels.items():
            try:
                is_connected = await channel.test_connection()
                status = "✓" if is_connected else "✗"
                self.logger.info(f"Channel {name}: {status}")
                
                if not is_connected:
                    channel.is_enabled = False
                    
            except Exception as e:
                self.logger.error(f"Error testing channel {name}: {e}")
                channel.is_enabled = False
    
    async def _process_messages(self):
        """Procesa la cola de mensajes."""
        while self.is_running:
            try:
                # Obtener mensaje de la cola
                message = await asyncio.wait_for(self.message_queue.get(), timeout=1.0)
                
                # Determinar canales de destino
                target_channels = self._get_target_channels(message)
                
                # Enviar a cada canal
                for channel_name in target_channels:
                    if channel_name in self.channels:
                        channel = self.channels[channel_name]
                        
                        if channel.is_enabled:
                            success = await self._send_with_retry(channel, message)
                            
                            if success:
                                message.sent = True
                                message.sent_at = datetime.now()
                            else:
                                self.logger.warning(f"Failed to send message {message.id} via {channel_name}")
                        else:
                            self.logger.warning(f"Channel {channel_name} is disabled")
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                self.logger.error(f"Error processing message: {e}")
    
    def _get_target_channels(self, message: Message) -> List[str]:
        """Determina los canales de destino para un mensaje."""
        # Buscar regla específica para el tipo de mensaje
        if message.type in self.routing_rules:
            rule = self.routing_rules[message.type]
            
            # Verificar filtro de prioridad
            if rule["priority_filter"] and message.priority.value < rule["priority_filter"].value:
                return []
            
            return rule["channels"]
        
        # Si no hay regla específica, usar consola para mensajes críticos
        if message.priority == MessagePriority.CRITICAL:
            return ["console"]
        
        return []
    
    async def _send_with_retry(self, channel: MessageChannel, message: Message) -> bool:
        """Envía mensaje con reintentos."""
        while message.retry_count < message.max_retries:
            try:
                success = await channel.send_message(message)
                if success:
                    return True
                
                message.retry_count += 1
                if message.retry_count < message.max_retries:
                    await asyncio.sleep(2 ** message.retry_count)  # Backoff exponencial
                
            except Exception as e:
                message.error = str(e)
                message.retry_count += 1
                
                if message.retry_count < message.max_retries:
                    await asyncio.sleep(2 ** message.retry_count)
        
        return False


class NotificationService:
    """Servicio principal de notificaciones."""
    
    def __init__(self):
        self.logger = logging.getLogger("NotificationService")
        self.router = MessageRouter()
        self._setup_default_routing()
    
    def _setup_default_routing(self):
        """Configura routing por defecto."""
        # Todas las alertas críticas van a todos los canales disponibles
        self.router.add_routing_rule(
            MessageType.CRITICAL,
            ["console", "telegram", "email"],
            MessagePriority.HIGH
        )
        
        # Señales de trading van a Telegram
        self.router.add_routing_rule(
            MessageType.TRADE_SIGNAL,
            ["telegram", "console"]
        )
        
        # P&L va a Telegram y Email
        self.router.add_routing_rule(
            MessageType.PROFIT_LOSS,
            ["telegram", "email", "console"]
        )
        
        # Estado del sistema va a todos
        self.router.add_routing_rule(
            MessageType.SYSTEM_STATUS,
            ["console", "telegram"]
        )
    
    def configure_telegram(self, bot_token: str, chat_id: str):
        """Configura canal de Telegram."""
        telegram_channel = TelegramChannel(bot_token, chat_id)
        self.router.register_channel("telegram", telegram_channel)
        self.logger.info("Telegram channel configured")
    
    def configure_email(self, smtp_host: str, smtp_port: int, username: str, password: str, from_email: str):
        """Configura canal de Email."""
        email_channel = EmailChannel(smtp_host, smtp_port, username, password, from_email)
        self.router.register_channel("email", email_channel)
        self.logger.info("Email channel configured")
    
    async def start(self):
        """Inicia el servicio de notificaciones."""
        await self.router.start()
        self.logger.info("Notification service started")
    
    async def stop(self):
        """Detiene el servicio de notificaciones."""
        await self.router.stop()
        self.logger.info("Notification service stopped")
    
    # Métodos de conveniencia para tipos específicos de mensajes
    
    async def notify_trade_signal(self, symbol: str, action: str, price: float, confidence: float):
        """Notifica una señal de trading."""
        content = f"Símbolo: {symbol}\nAcción: {action}\nPrecio: ${price:.6f}\nConfianza: {confidence:.1%}"
        
        await self.router.send_message(
            MessageType.TRADE_SIGNAL,
            f"Señal de Trading - {symbol}",
            content,
            MessagePriority.HIGH,
            tags={
                "symbol": symbol,
                "action": action,
                "price": str(price),
                "confidence": str(confidence)
            }
        )
    
    async def notify_profit_loss(self, symbol: str, pnl: float, pnl_pct: float, position_size: float):
        """Notifica P&L de una operación."""
        status = "📈 GANANCIA" if pnl > 0 else "📉 PÉRDIDA"
        content = f"Símbolo: {symbol}\n{status}: ${pnl:.2f} ({pnl_pct:.2f}%)\nTamaño: ${position_size:.2f}"
        
        priority = MessagePriority.HIGH if abs(pnl_pct) > 5 else MessagePriority.NORMAL
        
        await self.router.send_message(
            MessageType.PROFIT_LOSS,
            f"P&L - {symbol}",
            content,
            priority,
            tags={
                "symbol": symbol,
                "pnl": str(pnl),
                "pnl_pct": str(pnl_pct),
                "position_size": str(position_size)
            }
        )
    
    async def notify_system_status(self, status: str, details: str):
        """Notifica estado del sistema."""
        await self.router.send_message(
            MessageType.SYSTEM_STATUS,
            f"Estado del Sistema: {status}",
            details,
            MessagePriority.NORMAL,
            tags={"status": status}
        )
    
    async def notify_error(self, error_type: str, error_message: str, component: str):
        """Notifica un error del sistema."""
        await self.router.send_message(
            MessageType.ERROR,
            f"Error en {component}",
            f"Tipo: {error_type}\nMensaje: {error_message}",
            MessagePriority.HIGH,
            tags={
                "error_type": error_type,
                "component": component
            }
        )
    
    async def notify_critical_alert(self, title: str, message: str, component: str):
        """Notifica una alerta crítica."""
        await self.router.send_message(
            MessageType.CRITICAL,
            title,
            message,
            MessagePriority.CRITICAL,
            tags={"component": component}
        )
