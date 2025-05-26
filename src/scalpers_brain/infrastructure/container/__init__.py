"""
Contenedor de inyección de dependencias para Scalper's Brain
"""

from .di_container import (
    DIContainer, 
    DIScope,
    ServiceLocator,
    ServiceLifetime,
    singleton,
    transient,
    scoped,
    dependency,
    auto_register
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
