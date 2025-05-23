"""
Servicios de integración con Telegram.
Sigue el principio SRP al tener una única responsabilidad: gestionar la comunicación con Telegram.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

import requests

from src.core.dashboard.services.service_interfaces import NotificationService
from src.utils.config import settings

logger = logging.getLogger(__name__)

class TelegramService:
    """
    Servicio para interactuar con la API de Telegram.
    """
    
    def __init__(self, token: Optional[str] = None, chat_id: Optional[str] = None):
        """
        Inicializa el servicio de Telegram.
        
        Args:
            token: Token de bot de Telegram (si no se proporciona, se usa settings.telegram_bot_token)
            chat_id: ID del chat de Telegram (si no se proporciona, se usa settings.telegram_chat_id)
        """
        self.token = token or settings.telegram_bot_token
        self.chat_id = chat_id or settings.telegram_chat_id
        self.base_url = f"https://api.telegram.org/bot{self.token}"
        
        logger.info("Servicio de Telegram inicializado")
    
    def send_message(self, message: str, parse_mode: str = "Markdown") -> Dict[str, Any]:
        """
        Envía un mensaje a Telegram.
        
        Args:
            message: Texto del mensaje
            parse_mode: Modo de formato del mensaje ("Markdown", "HTML", None)
            
        Returns:
            Dict[str, Any]: Respuesta de la API de Telegram
        """
        if not self.token or not self.chat_id:
            error_msg = "No se pudo enviar mensaje, token o chat_id no configurados"
            logger.error(error_msg)
            return {"ok": False, "error": error_msg}
        
        url = f"{self.base_url}/sendMessage"
        
        payload = {
            "chat_id": self.chat_id,
            "text": message
        }
        
        if parse_mode:
            payload["parse_mode"] = parse_mode
        
        try:
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error al enviar mensaje a Telegram: {str(e)}")
            return {"ok": False, "error": str(e)}
    
    def get_bot_info(self) -> Dict[str, Any]:
        """
        Obtiene información sobre el bot.
        
        Returns:
            Dict[str, Any]: Información del bot
        """
        if not self.token:
            error_msg = "No se pudo obtener información del bot, token no configurado"
            logger.error(error_msg)
            return {"ok": False, "error": error_msg}
        
        url = f"{self.base_url}/getMe"
        
        try:
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error al obtener información del bot: {str(e)}")
            return {"ok": False, "error": str(e)}
    
    def get_updates(self, offset: Optional[int] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Obtiene actualizaciones del bot.
        
        Args:
            offset: ID de la actualización desde la cual obtener
            limit: Número máximo de actualizaciones
            
        Returns:
            List[Dict[str, Any]]: Actualizaciones del bot
        """
        if not self.token:
            logger.error("No se pudieron obtener actualizaciones, token no configurado")
            return []
        
        url = f"{self.base_url}/getUpdates"
        
        params = {"limit": limit}
        if offset is not None:
            params["offset"] = offset
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            result = response.json()
            
            if result.get("ok", False):
                return result.get("result", [])
            else:
                logger.error(f"Error al obtener actualizaciones: {result.get('description', 'Desconocido')}")
                return []
        except requests.exceptions.RequestException as e:
            logger.error(f"Error al obtener actualizaciones: {str(e)}")
            return []
    
    def send_photo(self, photo_path: str, caption: Optional[str] = None) -> Dict[str, Any]:
        """
        Envía una imagen a Telegram.
        
        Args:
            photo_path: Ruta al archivo de imagen
            caption: Texto descriptivo de la imagen
            
        Returns:
            Dict[str, Any]: Respuesta de la API de Telegram
        """
        if not self.token or not self.chat_id:
            error_msg = "No se pudo enviar imagen, token o chat_id no configurados"
            logger.error(error_msg)
            return {"ok": False, "error": error_msg}
        
        url = f"{self.base_url}/sendPhoto"
        
        data = {
            "chat_id": self.chat_id
        }
        
        if caption:
            data["caption"] = caption
        
        try:
            with open(photo_path, "rb") as photo:
                files = {"photo": photo}
                response = requests.post(url, data=data, files=files, timeout=30)
                response.raise_for_status()
                return response.json()
        except FileNotFoundError:
            error_msg = f"No se encontró el archivo de imagen: {photo_path}"
            logger.error(error_msg)
            return {"ok": False, "error": error_msg}
        except requests.exceptions.RequestException as e:
            logger.error(f"Error al enviar imagen a Telegram: {str(e)}")
            return {"ok": False, "error": str(e)}
