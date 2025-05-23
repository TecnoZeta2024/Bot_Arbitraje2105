"""
Modelos de datos para usuarios y autenticación.
Implementa patrones basados en SOLID para mantener la responsabilidad única y extensibilidad.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class User(BaseModel):
    """Modelo para un usuario del sistema"""
    id: str = Field(..., description="ID único del usuario")
    email: str = Field(..., description="Email del usuario")
    role: str = Field(default="user", description="Rol del usuario (admin, user)")
    name: Optional[str] = Field(default=None, description="Nombre del usuario")
    created_at: Optional[datetime] = Field(default=None, description="Fecha de creación del usuario")
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'User':
        """
        Crea una instancia de User a partir de un diccionario
        
        Args:
            data: Diccionario con datos del usuario
            
        Returns:
            Instancia de User
        """
        return cls(
            id=data.get("id") or data.get("user_id"),
            email=data.get("email") or "",
            role=data.get("role", "user"),
            name=data.get("name"),
            created_at=data.get("created_at")
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convierte el usuario a un diccionario
        
        Returns:
            Dict[str, Any]: Diccionario con datos del usuario
        """
        result = {
            "id": self.id,
            "email": self.email,
            "role": self.role
        }
        
        if self.name:
            result["name"] = self.name
            
        if self.created_at:
            result["created_at"] = self.created_at.isoformat()
            
        return result
    
    def has_permission(self, required_role: str) -> bool:
        """
        Verifica si el usuario tiene el rol requerido
        
        Args:
            required_role: Rol requerido para la acción
            
        Returns:
            bool: True si el usuario tiene permiso, False en caso contrario
        """
        if required_role == "user":
            return True
        elif required_role == "admin":
            return self.role == "admin"
        return False

class UserCredentials(BaseModel):
    """Modelo para credenciales de usuario"""
    email: str = Field(..., description="Email del usuario")
    password: str = Field(..., description="Contraseña del usuario")
