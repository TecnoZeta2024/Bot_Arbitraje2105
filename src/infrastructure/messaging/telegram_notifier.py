"""
Telegram Notification System
Sends intelligent trading alerts and status updates via Telegram
"""

import os
import logging
import asyncio
import aiohttp
from typing import Dict, Any, Optional
from datetime import datetime
from decimal import Decimal

from ...domain.trading_signals.trading_signal import TradingSignal
from ...domain.risk_management.advanced_risk_manager import RiskEvent


class TelegramNotifier:
    """
    Telegram notification system for trading alerts
    
    Features:
    - Trade execution alerts
    - Risk management notifications
    - Performance summaries
    - System status updates
    """
    
    def __init__(self):
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.chat_id = os.getenv('TELEGRAM_CHAT_ID')
        self.logger = logging.getLogger("notifications.telegram")
        
        if not self.bot_token or not self.chat_id:
            self.logger.warning("Telegram credentials not configured")
            self.enabled = False
        else:
            self.enabled = True
            self.base_url = f"https://api.telegram.org/bot{self.bot_token}"
            self.logger.info("Telegram notifier initialized")
    
    async def send_message(self, message: str, parse_mode: str = "Markdown"):
        """Send a message to Telegram"""
        
        if not self.enabled:
            self.logger.debug(f"Telegram disabled - would send: {message[:100]}")
            return False
        
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    'chat_id': self.chat_id,
                    'text': message,
                    'parse_mode': parse_mode
                }
                
                async with session.post(f"{self.base_url}/sendMessage", json=payload) as response:
                    if response.status == 200:
                        self.logger.debug("Telegram message sent successfully")
                        return True
                    else:
                        error_text = await response.text()
                        self.logger.error(f"Telegram API error: {response.status} - {error_text}")
                        return False
                        
        except Exception as e:
            self.logger.error(f"Failed to send Telegram message: {e}")
            return False
    
    async def send_trade_execution_alert(self, signal: TradingSignal, position_size: float):
        """Send trade execution alert"""
        
        # Emojis for different strategies
        strategy_emojis = {
            'scalping': '⚡',
            'day_trading': '📈',
            'triangular_arbitrage': '🔺'
        }
        
        action_emojis = {
            'BUY': '🟢',
            'SELL': '🔴',
            'HOLD': '🟡'
        }
        
        strategy_emoji = strategy_emojis.get(signal.strategy_name.value, '🎯')
        action_emoji = action_emojis.get(signal.action.value, '❓')
        
        message = f"""
🚀 *TRADE EJECUTADO* {strategy_emoji}

{action_emoji} *Acción:* {signal.action.value}
💰 *Símbolo:* {signal.symbol}
📊 *Estrategia:* {signal.strategy_name.value.title()}
💵 *Precio:* ${signal.entry_price:.6f}
📏 *Tamaño:* {position_size:.4f}
🎯 *Ganancia Esperada:* {signal.expected_profit:.2%}
🔮 *Confianza IA:* {signal.confidence:.1%}
⚠️ *Nivel de Riesgo:* {signal.risk_level.value}
⏱️ *Timeframe:* {signal.timeframe}

🧠 *Análisis IA:* {signal.ai_analysis.get('ai_reasoning', 'N/A')[:100] if signal.ai_analysis else 'N/A'}...

⏰ {datetime.now().strftime('%H:%M:%S %d/%m/%Y')}
        """
        
        await self.send_message(message)
    
    async def send_position_closed_alert(self, symbol: str, strategy: str, pnl: Decimal, 
                                       reason: str, entry_price: float, exit_price: float):
        """Send position closed alert"""
        
        pnl_emoji = '💚' if pnl > 0 else '❌' if pnl < 0 else '➖'
        reason_emojis = {
            'TAKE_PROFIT': '🎯',
            'STOP_LOSS': '🛑',
            'TIME_LIMIT': '⏰',
            'MANUAL': '👤'
        }
        
        reason_emoji = reason_emojis.get(reason, '📝')
        
        message = f"""
📊 *POSICIÓN CERRADA* {pnl_emoji}

💰 *Símbolo:* {symbol}
📈 *Estrategia:* {strategy.title()}
{reason_emoji} *Razón:* {reason.replace('_', ' ').title()}

💵 *Precio Entrada:* ${entry_price:.6f}
💸 *Precio Salida:* ${exit_price:.6f}
{pnl_emoji} *P&L:* ${float(pnl):.2f} ({((exit_price/entry_price-1)*100):.2f}%)

⏰ {datetime.now().strftime('%H:%M:%S %d/%m/%Y')}
        """
        
        await self.send_message(message)
    
    async def send_risk_alert(self, risk_event: RiskEvent):
        """Send risk management alert"""
        
        severity_emojis = {
            'LOW': '🟡',
            'MEDIUM': '🟠', 
            'HIGH': '🔴',
            'CRITICAL': '🚨'
        }
        
        severity_emoji = severity_emojis.get(risk_event.severity, '⚠️')
        
        message = f"""
{severity_emoji} *ALERTA DE RIESGO* {severity_emoji}

🎯 *Tipo:* {risk_event.event_type.value.replace('_', ' ').title()}
⚠️ *Severidad:* {risk_event.severity}
💰 *Símbolo:* {risk_event.symbol or 'GLOBAL'}

📝 *Descripción:* {risk_event.description}
🔧 *Acción Tomada:* {risk_event.action_taken}

⏰ {risk_event.timestamp.strftime('%H:%M:%S %d/%m/%Y')}
        """
        
        await self.send_message(message)
    
    async def send_daily_summary(self, performance_data: Dict[str, Any]):
        """Send daily performance summary"""
        
        summary = performance_data.get('summary', {})
        
        total_trades = summary.get('total_trades', 0)
        winning_trades = summary.get('winning_trades', 0)
        total_pnl = summary.get('total_pnl', 0)
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        
        pnl_emoji = '💚' if total_pnl > 0 else '❌' if total_pnl < 0 else '➖'
        
        message = f"""
📊 *RESUMEN DIARIO* 📊

💼 *Operaciones Total:* {total_trades}
✅ *Operaciones Ganadoras:* {winning_trades}
❌ *Operaciones Perdedoras:* {summary.get('losing_trades', 0)}
🎯 *Win Rate:* {win_rate:.1f}%

{pnl_emoji} *P&L Total:* ${float(total_pnl):.2f}
📈 *P&L Promedio:* ${float(summary.get('avg_pnl', 0)):.2f}
🥇 *Mejor Trade:* ${float(summary.get('best_trade', 0)):.2f}
📉 *Peor Trade:* ${float(summary.get('worst_trade', 0)):.2f}

🔮 *Confianza IA Promedio:* {float(summary.get('avg_confidence', 0)):.1%}
⏱️ *Tiempo Promedio Hold:* {float(summary.get('avg_hold_time_seconds', 0))/60:.1f} min

📅 *Fecha:* {datetime.now().strftime('%d/%m/%Y')}
        """
        
        # Add strategy breakdown
        strategy_data = performance_data.get('by_strategy', [])
        if strategy_data:
            message += "\n\n📊 *POR ESTRATEGIA:*\n"
            for strategy in strategy_data:
                strategy_pnl = float(strategy.get('pnl', 0))
                strategy_emoji = '💚' if strategy_pnl > 0 else '❌' if strategy_pnl < 0 else '➖'
                message += f"{strategy_emoji} *{strategy['strategy_name'].title()}:* ${strategy_pnl:.2f} ({strategy['trades']} trades)\n"
        
        await self.send_message(message)
    
    async def send_system_status(self, status_data: Dict[str, Any]):
        """Send system status update"""
        
        is_running = status_data.get('is_running', False)
        status_emoji = '🟢' if is_running else '🔴'
        
        websocket_status = status_data.get('websocket_status', 'UNKNOWN')
        ws_emoji = '🟢' if 'connected' in websocket_status else '🟡' if 'connecting' in websocket_status else '🔴'
        
        message = f"""
🤖 *ESTADO DEL SISTEMA* {status_emoji}

{status_emoji} *Estado:* {'ACTIVO' if is_running else 'INACTIVO'}
{ws_emoji} *WebSockets:* {websocket_status}
📡 *Símbolos Monitoreados:* {status_data.get('symbols_tracked', 0)}
📊 *Señales Hoy:* {status_data.get('signals_generated_today', 0)}
💼 *Posiciones Activas:* {status_data.get('active_positions', 0)}
💰 *Capital Disponible:* ${float(status_data.get('available_capital', 0)):.2f}
📈 *P&L Total:* ${float(status_data.get('total_pnl', 0)):.2f}

🎯 *Estrategias Activas:*
{chr(10).join(['• ' + s.title() for s in status_data.get('enabled_strategies', [])])}

🏦 *Exchanges Conectados:*
{chr(10).join(['• ' + e.title() for e in status_data.get('enabled_exchanges', [])])}

⏰ {datetime.now().strftime('%H:%M:%S %d/%m/%Y')}
        """
        
        await self.send_message(message)
    
    async def send_ai_insight(self, symbol: str, ai_analysis: Dict[str, Any]):
        """Send AI analysis insight"""
        
        sentiment_score = ai_analysis.get('sentiment_score', 50)
        confidence = ai_analysis.get('confidence_level', 0.5)
        recommendation = ai_analysis.get('recommended_action', 'HOLD')
        
        sentiment_emoji = '📈' if sentiment_score > 70 else '📉' if sentiment_score < 30 else '➖'
        
        message = f"""
🧠 *INSIGHT DE IA* {sentiment_emoji}

💰 *Símbolo:* {symbol}
{sentiment_emoji} *Sentiment Score:* {sentiment_score}/100
🔮 *Confianza:* {confidence:.1%}
🎯 *Recomendación:* {recommendation}

📝 *Análisis:* {ai_analysis.get('reasoning', 'N/A')[:200]}...

⏰ {datetime.now().strftime('%H:%M:%S %d/%m/%Y')}
        """
        
        await self.send_message(message)
    
    async def send_startup_message(self):
        """Send system startup notification"""
        
        message = f"""
🚀 *SISTEMA INICIADO* 🚀

✅ Trading Engine iniciado correctamente
🔮 IA Google Gemini conectada
📡 WebSockets configurados
🛡️ Sistema de riesgos activo

🎯 *Listo para operar!*

⏰ {datetime.now().strftime('%H:%M:%S %d/%m/%Y')}
        """
        
        await self.send_message(message)
    
    async def send_shutdown_message(self):
        """Send system shutdown notification"""
        
        message = f"""
🛑 *SISTEMA DETENIDO* 🛑

❌ Trading Engine detenido
📊 Posiciones cerradas
💾 Datos guardados

⏰ {datetime.now().strftime('%H:%M:%S %d/%m/%Y')}
        """
        
        await self.send_message(message)
    
    async def send_error_alert(self, error_type: str, error_message: str, component: str = None):
        """Send error alert"""
        
        message = f"""
🚨 *ERROR DEL SISTEMA* 🚨

⚠️ *Tipo:* {error_type}
🔧 *Componente:* {component or 'GENERAL'}
📝 *Mensaje:* {error_message[:300]}

⏰ {datetime.now().strftime('%H:%M:%S %d/%m/%Y')}
        """
        
        await self.send_message(message)


# Global instance
telegram_notifier = TelegramNotifier()
