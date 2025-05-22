"""
Inicialización del paquete de repositorios.
"""

from src.core.dashboard.repositories.repository_interface import Repository
from src.core.dashboard.repositories.specific_repositories import TokenRepository, OperationRepository, ConfigRepository
from src.core.dashboard.repositories.supabase_repositories import (
    SupabaseTokenRepository, 
    SupabaseOperationRepository, 
    SupabaseConfigRepository
)
from src.core.dashboard.repositories.file_system_repositories import FileSystemLogRepository

# Exportar todas las interfaces e implementaciones
__all__ = [
    # Interfaces
    'Repository',
    'TokenRepository',
    'OperationRepository',
    'ConfigRepository',
    
    # Implementaciones concretas
    'SupabaseTokenRepository',
    'SupabaseOperationRepository',
    'SupabaseConfigRepository',
    'FileSystemLogRepository'
]
