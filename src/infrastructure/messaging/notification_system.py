"""
Intelligent Notification System
Multi-channel notifications with priority-based routing and smart filtering
"""

import asyncio
import logging
import smtplib
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from decimal import Decimal
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
from typing import Dict, List, Any, Optional
from enum import Enum
import json

try:
    import telegram
    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False


class NotificationLevel(Enum):
    """Notification priority levels"""
    DEBUG = 1
    INFO = 2
    WARNING = 3
    ERROR = 4
    CRITICAL = 5


class NotificationChannel(Enum):
    """Available notification channels"""
    LOG = "log"
    EMAIL = "email"
    TELEGRAM = "telegram"
    WEBHOOK = "webhook"
    FILE = "file"


class Notification:
    """Notification data structure"""
    
    def __init__(
        self,
        title: str,
        message: str,
        level: NotificationLevel,
        category: str = "general",
        data: Optional[Dict[str, Any]] = None
    ):
        self.id = f"notif_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        self.timestamp = datetime.now()
        self.title = title
        self.message = message
        self.level = level
        self.category = category
        self.data = data or {}
        self.sent_channels: List[NotificationChannel] = []
        self.retry_count = 0


class NotificationHandler(ABC):
    """Abstract base class for notification handlers"""
    
    @abstractmethod
    async def send_notification(self, notification: Notification) -> bool:
        """Send notification through this channel"""
        pass
    
    @abstractmethod
    def is_configured(self) -> bool:
        """Check if handler is properly configured"""
        pass


class LogNotificationHandler(NotificationHandler):
    """Log-based notification handler"""
    
    def __init__(self):
        self.logger = logging.getLogger("notifications.log")
    
    async def send_notification(self, notification: Notification) -> bool:
        """Send notification to logs"""
        try:
            log_message = f"[{notification.category.upper()}] {notification.title}: {notification.message}"
            
            if notification.level == NotificationLevel.DEBUG:
                self.logger.debug(log_message)
            elif notification.level == NotificationLevel.INFO:
                self.logger.info(log_message)
            elif notification.level == NotificationLevel.WARNING:
                self.logger.warning(log_message)
            elif notification.level == NotificationLevel.ERROR:
                self.logger.error(log_message)
            elif notification.level == NotificationLevel.CRITICAL:
                self.logger.critical(log_message)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send log notification: {e}")
            return False
    
    def is_configured(self) -> bool:
        """Logs are always available"""
        return True


class EmailNotificationHandler(NotificationHandler):
    """Email notification handler"""
    
    def __init__(self, smtp_server: str, smtp_port: int, username: str, 
                 password: str, from_email: str, to_emails: List[str]):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.from_email = from_email
        self.to_emails = to_emails
        self.logger = logging.getLogger("notifications.email")
    
    async def send_notification(self, notification: Notification) -> bool:
        """Send email notification"""
        try:
            # Create message
            msg = MimeMultipart()
            msg['From'] = self.from_email
            msg['To'] = ', '.join(self.to_emails)
            msg['Subject'] = f"[TRADING ALERT] {notification.title}"
            
            # Create HTML body
            html_body = self._create_email_body(notification)
            msg.attach(MimeText(html_body, 'html'))
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.username, self.password)
                text = msg.as_string()
                server.sendmail(self.from_email, self.to_emails, text)
            
            self.logger.info(f"Email notification sent: {notification.title}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send email notification: {e}")
            return False
    
    def _create_email_body(self, notification: Notification) -> str:
        """Create HTML email body"""
        level_colors = {
            NotificationLevel.DEBUG: "#6c757d",
            NotificationLevel.INFO: "#17a2b8",
            NotificationLevel.WARNING: "#ffc107",
            NotificationLevel.ERROR: "#dc3545",
            NotificationLevel.CRITICAL: "#721c24"
        }
        
        color = level_colors.get(notification.level, "#17a2b8")
        
        html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; margin: 20px;">
            <div style="border-left: 4px solid {color}; padding-left: 20px;">
                <h2 style="color: {color}; margin-top: 0;">
                    {notification.title}
                </h2>
                <p><strong>Level:</strong> {notification.level.name}</p>
                <p><strong>Category:</strong> {notification.category}</p>
                <p><strong>Time:</strong> {notification.timestamp.strftime('%Y-%m-%d %H:%M:%S')}</p>
                <hr>
                <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px;">
                    <pre style="white-space: pre-wrap; margin: 0;">{notification.message}</pre>
                </div>
        """
        
        if notification.data:
            html += """
                <hr>
                <h3>Additional Data:</h3>
                <div style="background-color: #e9ecef; padding: 10px; border-radius: 5px;">
                    <pre style="white-space: pre-wrap; margin: 0; font-size: 12px;">
            """
            html += json.dumps(notification.data, indent=2, default=str)
            html += """
                    </pre>
                </div>
            """
        
        html += """
            </div>
            <hr>
            <p style="color: #6c757d; font-size: 12px;">
                This is an automated notification from your Advanced Trading System.
            </p>
        </body>
        </html>
        """
        
        return html
    
    def is_configured(self) -> bool:
        """Check if email is properly configured"""
        return all([
            self.smtp_server,
            self.smtp_port,
            self.username,
            self.password,
            self.from_email,
            self.to_emails
        ])


class TelegramNotificationHandler(NotificationHandler):
    """Telegram notification handler"""
    
    def __init__(self, bot_token: str, chat_ids: List[str]):
        self.bot_token = bot_token
        self.chat_ids = chat_ids
        self.bot = None
        self.logger = logging.getLogger("notifications.telegram")
        
        if TELEGRAM_AVAILABLE and self.bot_token:
            try:
                self.bot = telegram.Bot(token=self.bot_token)
            except Exception as e:
                self.logger.error(f"Failed to initialize Telegram bot: {e}")
    
    async def send_notification(self, notification: Notification) -> bool:
        """Send Telegram notification"""
        if not self.bot:
            return False
        
        try:
            # Create message
            message = self._create_telegram_message(notification)
            
            # Send to all chat IDs
            for chat_id in self.chat_ids:
                await self.bot.send_message(
                    chat_id=chat_id,
                    text=message,
                    parse_mode='HTML'
                )
            
            self.logger.info(f"Telegram notification sent: {notification.title}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send Telegram notification: {e}")
            return False
    
    def _create_telegram_message(self, notification: Notification) -> str:
        """Create Telegram message"""
        # Emoji mapping for levels
        level_emojis = {
            NotificationLevel.DEBUG: "🔍",
            NotificationLevel.INFO: "ℹ️",
            NotificationLevel.WARNING: "⚠️",
            NotificationLevel.ERROR: "❌",
            NotificationLevel.CRITICAL: "🚨"
        }
        
        emoji = level_emojis.get(notification.level, "📢")
        
        message = f"""
{emoji} <b>{notification.title}</b>

<b>Level:</b> {notification.level.name}
<b>Category:</b> {notification.category}
<b>Time:</b> {notification.timestamp.strftime('%Y-%m-%d %H:%M:%S')}

<code>{notification.message}</code>
        """.strip()
        
        # Add data if present and not too long
        if notification.data and len(str(notification.data)) < 500:
            data_str = json.dumps(notification.data, indent=2, default=str)
            message += f"\n\n<b>Data:</b>\n<pre>{data_str}</pre>"
        
        return message
    
    def is_configured(self) -> bool:
        """Check if Telegram is properly configured"""
        return TELEGRAM_AVAILABLE and self.bot is not None and len(self.chat_ids) > 0


class FileNotificationHandler(NotificationHandler):
    """File-based notification handler"""
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.logger = logging.getLogger("notifications.file")
    
    async def send_notification(self, notification: Notification) -> bool:
        """Write notification to file"""
        try:
            with open(self.file_path, 'a', encoding='utf-8') as f:
                notification_data = {
                    'id': notification.id,
                    'timestamp': notification.timestamp.isoformat(),
                    'level': notification.level.name,
                    'category': notification.category,
                    'title': notification.title,
                    'message': notification.message,
                    'data': notification.data
                }
                
                f.write(json.dumps(notification_data) + '\n')
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to write notification to file: {e}")
            return False
    
    def is_configured(self) -> bool:
        """Check if file path is accessible"""
        try:
            # Test write access
            with open(self.file_path, 'a') as f:
                pass
            return True
        except Exception:
            return False


class IntelligentNotificationSystem:
    """
    Intelligent notification system with smart routing and filtering
    
    Features:
    - Multi-channel delivery
    - Priority-based routing
    - Rate limiting and deduplication
    - Smart filtering
    - Retry logic
    - Performance monitoring
    """
    
    def __init__(self):
        self.handlers: Dict[NotificationChannel, NotificationHandler] = {}
        self.routing_rules: Dict[str, Dict] = {}
        self.sent_notifications: List[Notification] = []
        self.rate_limits: Dict[str, List[datetime]] = {}
        self.deduplication_cache: Dict[str, datetime] = {}
        
        self.logger = logging.getLogger("notifications.system")
        
        # Default routing rules
        self._setup_default_routing()
    
    def add_handler(self, channel: NotificationChannel, handler: NotificationHandler):
        """Add notification handler"""
        if handler.is_configured():
            self.handlers[channel] = handler
            self.logger.info(f"Added {channel.value} notification handler")
        else:
            self.logger.warning(f"Handler for {channel.value} is not properly configured")
    
    def _setup_default_routing(self):
        """Setup default routing rules"""
        self.routing_rules = {
            'trading_signal': {
                'channels': [NotificationChannel.LOG, NotificationChannel.TELEGRAM],
                'min_level': NotificationLevel.INFO,
                'rate_limit_minutes': 1
            },
            'risk_alert': {
                'channels': [NotificationChannel.LOG, NotificationChannel.EMAIL, NotificationChannel.TELEGRAM],
                'min_level': NotificationLevel.WARNING,
                'rate_limit_minutes': 0  # No rate limiting for risk alerts
            },
            'system_error': {
                'channels': [NotificationChannel.LOG, NotificationChannel.EMAIL],
                'min_level': NotificationLevel.ERROR,
                'rate_limit_minutes': 5
            },
            'performance': {
                'channels': [NotificationChannel.LOG, NotificationChannel.FILE],
                'min_level': NotificationLevel.INFO,
                'rate_limit_minutes': 30
            },
            'general': {
                'channels': [NotificationChannel.LOG],
                'min_level': NotificationLevel.INFO,
                'rate_limit_minutes': 10
            }
        }
    
    async def send_notification(
        self,
        title: str,
        message: str,
        level: NotificationLevel = NotificationLevel.INFO,
        category: str = "general",
        data: Optional[Dict[str, Any]] = None,
        force_send: bool = False
    ) -> bool:
        """Send notification through appropriate channels"""
        
        notification = Notification(title, message, level, category, data)
        
        try:
            # Check if should send based on rules
            if not force_send and not self._should_send_notification(notification):
                return False
            
            # Get routing rule
            rule = self.routing_rules.get(category, self.routing_rules['general'])
            
            # Check minimum level
            if notification.level.value < rule['min_level'].value:
                return False
            
            # Send through configured channels
            success_count = 0
            total_channels = 0
            
            for channel in rule['channels']:
                if channel in self.handlers:
                    total_channels += 1
                    try:
                        success = await self.handlers[channel].send_notification(notification)
                        if success:
                            notification.sent_channels.append(channel)
                            success_count += 1
                    except Exception as e:
                        self.logger.error(f"Error sending notification via {channel.value}: {e}")
            
            # Record notification
            self.sent_notifications.append(notification)
            
            # Update rate limiting
            self._update_rate_limiting(category)
            
            # Update deduplication cache
            self._update_deduplication_cache(notification)
            
            self.logger.debug(f"Notification sent via {success_count}/{total_channels} channels")
            
            return success_count > 0
            
        except Exception as e:
            self.logger.error(f"Failed to send notification: {e}")
            return False
    
    def _should_send_notification(self, notification: Notification) -> bool:
        """Check if notification should be sent based on rules"""
        
        # Check rate limiting
        if self._is_rate_limited(notification.category):
            return False
        
        # Check deduplication
        if self._is_duplicate(notification):
            return False
        
        return True
    
    def _is_rate_limited(self, category: str) -> bool:
        """Check if category is rate limited"""
        rule = self.routing_rules.get(category, self.routing_rules['general'])
        rate_limit_minutes = rule.get('rate_limit_minutes', 10)
        
        if rate_limit_minutes <= 0:
            return False
        
        now = datetime.now()
        cutoff = now - timedelta(minutes=rate_limit_minutes)
        
        # Clean old entries
        if category in self.rate_limits:
            self.rate_limits[category] = [
                timestamp for timestamp in self.rate_limits[category]
                if timestamp > cutoff
            ]
            
            # Check if we have recent notifications
            return len(self.rate_limits[category]) > 0
        
        return False
    
    def _update_rate_limiting(self, category: str):
        """Update rate limiting tracking"""
        if category not in self.rate_limits:
            self.rate_limits[category] = []
        
        self.rate_limits[category].append(datetime.now())
    
    def _is_duplicate(self, notification: Notification) -> bool:
        """Check if notification is a duplicate"""
        # Create deduplication key
        dedupe_key = f"{notification.category}:{notification.title}:{notification.message[:100]}"
        
        if dedupe_key in self.deduplication_cache:
            last_sent = self.deduplication_cache[dedupe_key]
            if datetime.now() - last_sent < timedelta(minutes=5):
                return True
        
        return False
    
    def _update_deduplication_cache(self, notification: Notification):
        """Update deduplication cache"""
        dedupe_key = f"{notification.category}:{notification.title}:{notification.message[:100]}"
        self.deduplication_cache[dedupe_key] = datetime.now()
        
        # Clean old entries (keep only last hour)
        cutoff = datetime.now() - timedelta(hours=1)
        self.deduplication_cache = {
            key: timestamp for key, timestamp in self.deduplication_cache.items()
            if timestamp > cutoff
        }
    
    async def send_trading_signal_notification(self, signal_data: Dict[str, Any]):
        """Send trading signal notification"""
        await self.send_notification(
            title=f"🚀 Trading Signal: {signal_data.get('symbol', 'Unknown')}",
            message=f"""
Action: {signal_data.get('action', 'Unknown')}
Strategy: {signal_data.get('strategy', 'Unknown')}
Confidence: {signal_data.get('confidence', 0):.1%}
Expected Profit: {signal_data.get('expected_profit', 0):.2%}
Entry Price: ${signal_data.get('entry_price', 0):.6f}
            """.strip(),
            level=NotificationLevel.INFO,
            category="trading_signal",
            data=signal_data
        )
    
    async def send_risk_alert(self, alert_type: str, details: Dict[str, Any]):
        """Send risk management alert"""
        level = NotificationLevel.CRITICAL if alert_type in ['STOP_LOSS', 'DAILY_LIMIT'] else NotificationLevel.WARNING
        
        await self.send_notification(
            title=f"⚠️ Risk Alert: {alert_type}",
            message=f"""
Alert Type: {alert_type}
Symbol: {details.get('symbol', 'N/A')}
Current P&L: ${details.get('pnl', 0):.2f}
Action Taken: {details.get('action', 'None')}
            """.strip(),
            level=level,
            category="risk_alert",
            data=details
        )
    
    async def send_system_status(self, status_data: Dict[str, Any]):
        """Send system status notification"""
        await self.send_notification(
            title="📊 System Status Update",
            message=f"""
Uptime: {status_data.get('uptime', 'Unknown')}
Active Positions: {status_data.get('active_positions', 0)}
Signals Today: {status_data.get('signals_today', 0)}
Total P&L: ${status_data.get('total_pnl', 0):.2f}
WebSocket Status: {status_data.get('websocket_status', 'Unknown')}
            """.strip(),
            level=NotificationLevel.INFO,
            category="performance",
            data=status_data
        )
    
    async def send_error_notification(self, error_type: str, error_message: str, additional_data: Optional[Dict] = None):
        """Send error notification"""
        await self.send_notification(
            title=f"❌ System Error: {error_type}",
            message=error_message,
            level=NotificationLevel.ERROR,
            category="system_error",
            data=additional_data
        )
    
    def get_notification_stats(self) -> Dict[str, Any]:
        """Get notification system statistics"""
        now = datetime.now()
        
        # Count notifications by level in last 24 hours
        recent_notifications = [
            n for n in self.sent_notifications
            if (now - n.timestamp).total_seconds() < 86400
        ]
        
        level_counts = {}
        for level in NotificationLevel:
            level_counts[level.name] = len([
                n for n in recent_notifications if n.level == level
            ])
        
        # Count by category
        category_counts = {}
        for category in self.routing_rules.keys():
            category_counts[category] = len([
                n for n in recent_notifications if n.category == category
            ])
        
        # Channel success rates
        channel_stats = {}
        for channel in NotificationChannel:
            if channel in self.handlers:
                total_sent = len([
                    n for n in recent_notifications
                    if channel in n.sent_channels
                ])
                channel_stats[channel.value] = {
                    'sent': total_sent,
                    'configured': True
                }
            else:
                channel_stats[channel.value] = {
                    'sent': 0,
                    'configured': False
                }
        
        return {
            'total_sent_24h': len(recent_notifications),
            'level_breakdown': level_counts,
            'category_breakdown': category_counts,
            'channel_stats': channel_stats,
            'configured_channels': list(self.handlers.keys()),
            'active_rate_limits': len(self.rate_limits),
            'deduplication_cache_size': len(self.deduplication_cache)
        }


# Factory function for easy setup
def create_notification_system(config: Dict[str, Any]) -> IntelligentNotificationSystem:
    """Factory function to create and configure notification system"""
    system = IntelligentNotificationSystem()
    
    # Always add log handler
    system.add_handler(NotificationChannel.LOG, LogNotificationHandler())
    
    # Add email handler if configured
    email_config = config.get('email', {})
    if all(key in email_config for key in ['smtp_server', 'username', 'password', 'from_email', 'to_emails']):
        email_handler = EmailNotificationHandler(
            smtp_server=email_config['smtp_server'],
            smtp_port=email_config.get('smtp_port', 587),
            username=email_config['username'],
            password=email_config['password'],
            from_email=email_config['from_email'],
            to_emails=email_config['to_emails']
        )
        system.add_handler(NotificationChannel.EMAIL, email_handler)
    
    # Add Telegram handler if configured
    telegram_config = config.get('telegram', {})
    if telegram_config.get('bot_token') and telegram_config.get('chat_ids'):
        telegram_handler = TelegramNotificationHandler(
            bot_token=telegram_config['bot_token'],
            chat_ids=telegram_config['chat_ids']
        )
        system.add_handler(NotificationChannel.TELEGRAM, telegram_handler)
    
    # Add file handler if configured
    file_config = config.get('file', {})
    if file_config.get('path'):
        file_handler = FileNotificationHandler(file_config['path'])
        system.add_handler(NotificationChannel.FILE, file_handler)
    
    return system
