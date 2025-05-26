"""
Contenedor de inyección de dependencias para Scalper's Brain
"""

from .di_container import (
    DIContainer,
    DIScope,
    ServiceLifetime,
    ServiceLocator,
    auto_register,
    dependency,
    scoped,
    singleton,
    transient,
)

__all__ = [
    'DIContainer',
    'DIScope',
    'ServiceLocator',
    'ServiceLifetime',
    'singleton',
    'transient',
    'scoped',
    'dependency',
    'auto_register'
]
