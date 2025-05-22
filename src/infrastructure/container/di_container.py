"""
Dependency Injection Container
Sistema avanzado de inyección de dependencias para arquitectura limpia
"""

import asyncio
import logging
from typing import Dict, Any, Type, TypeVar, Callable, Optional, Union, List
from dataclasses import dataclass
import inspect
from enum import Enum


T = TypeVar('T')


class ServiceLifetime(Enum):
    """Tipos de ciclo de vida de servicios."""
    SINGLETON = "singleton"
    TRANSIENT = "transient" 
    SCOPED = "scoped"


@dataclass
class ServiceDescriptor:
    """Descriptor de un servicio registrado."""
    service_type: Type
    implementation_type: Optional[Type] = None
    factory: Optional[Callable] = None
    instance: Optional[Any] = None
    lifetime: ServiceLifetime = ServiceLifetime.TRANSIENT
    dependencies: List[Type] = None
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []


class DIContainer:
    """Contenedor de inyección de dependencias."""
    
    def __init__(self):
        self.logger = logging.getLogger("DIContainer")
        self._services: Dict[Type, ServiceDescriptor] = {}
        self._singletons: Dict[Type, Any] = {}
        self._scoped_instances: Dict[Type, Any] = {}
        self._building_stack: List[Type] = []
        
        # Registrar el contenedor como singleton
        self.register_instance(DIContainer, self)
        
        self.logger.info("DIContainer initialized")
    
    def register_singleton(self, service_type: Type[T], implementation_type: Optional[Type] = None) -> 'DIContainer':
        """Registra un servicio como singleton."""
        return self._register_service(service_type, implementation_type, ServiceLifetime.SINGLETON)
    
    def register_transient(self, service_type: Type[T], implementation_type: Optional[Type] = None) -> 'DIContainer':
        """Registra un servicio como transient."""
        return self._register_service(service_type, implementation_type, ServiceLifetime.TRANSIENT)
    
    def register_scoped(self, service_type: Type[T], implementation_type: Optional[Type] = None) -> 'DIContainer':
        """Registra un servicio como scoped."""
        return self._register_service(service_type, implementation_type, ServiceLifetime.SCOPED)
    
    def register_factory(self, service_type: Type[T], factory: Callable[[], T], lifetime: ServiceLifetime = ServiceLifetime.TRANSIENT) -> 'DIContainer':
        """Registra un factory para crear instancias."""
        descriptor = ServiceDescriptor(
            service_type=service_type,
            factory=factory,
            lifetime=lifetime
        )
        
        self._services[service_type] = descriptor
        self.logger.info(f"Registered factory for {service_type.__name__} as {lifetime.value}")
        
        return self
    
    def register_instance(self, service_type: Type[T], instance: T) -> 'DIContainer':
        """Registra una instancia específica como singleton."""
        descriptor = ServiceDescriptor(
            service_type=service_type,
            instance=instance,
            lifetime=ServiceLifetime.SINGLETON
        )
        
        self._services[service_type] = descriptor
        self._singletons[service_type] = instance
        
        self.logger.info(f"Registered instance for {service_type.__name__}")
        
        return self
    
    def _register_service(self, service_type: Type[T], implementation_type: Optional[Type], lifetime: ServiceLifetime) -> 'DIContainer':
        """Registra un servicio con el tipo de ciclo de vida especificado."""
        impl_type = implementation_type or service_type
        
        # Analizar dependencias del constructor
        dependencies = self._analyze_dependencies(impl_type)
        
        descriptor = ServiceDescriptor(
            service_type=service_type,
            implementation_type=impl_type,
            lifetime=lifetime,
            dependencies=dependencies
        )
        
        self._services[service_type] = descriptor
        
        self.logger.info(
            f"Registered {service_type.__name__} -> {impl_type.__name__} "
            f"as {lifetime.value} with {len(dependencies)} dependencies"
        )
        
        return self
    
    def resolve(self, service_type: Type[T]) -> T:
        """Resuelve una instancia del tipo especificado."""
        if service_type not in self._services:
            raise ValueError(f"Service {service_type.__name__} is not registered")
        
        # Detectar dependencias circulares
        if service_type in self._building_stack:
            circular_deps = " -> ".join([t.__name__ for t in self._building_stack] + [service_type.__name__])
            raise ValueError(f"Circular dependency detected: {circular_deps}")
        
        descriptor = self._services[service_type]
        
        # Singleton: retornar instancia existente
        if descriptor.lifetime == ServiceLifetime.SINGLETON:
            if service_type in self._singletons:
                return self._singletons[service_type]
        
        # Scoped: retornar instancia del scope actual
        elif descriptor.lifetime == ServiceLifetime.SCOPED:
            if service_type in self._scoped_instances:
                return self._scoped_instances[service_type]
        
        # Crear nueva instancia
        self._building_stack.append(service_type)
        
        try:
            instance = self._create_instance(descriptor)
            
            # Almacenar según el ciclo de vida
            if descriptor.lifetime == ServiceLifetime.SINGLETON:
                self._singletons[service_type] = instance
            elif descriptor.lifetime == ServiceLifetime.SCOPED:
                self._scoped_instances[service_type] = instance
            
            return instance
            
        finally:
            self._building_stack.pop()
    
    def resolve_optional(self, service_type: Type[T]) -> Optional[T]:
        """Resuelve una instancia si está registrada, sino retorna None."""
        try:
            return self.resolve(service_type)
        except ValueError:
            return None
    
    def resolve_all(self, service_type: Type[T]) -> List[T]:
        """Resuelve todas las implementaciones de un tipo."""
        implementations = []
        
        for registered_type, descriptor in self._services.items():
            if (issubclass(descriptor.implementation_type or descriptor.service_type, service_type) 
                and registered_type != service_type):
                implementations.append(self.resolve(registered_type))
        
        return implementations
    
    def _create_instance(self, descriptor: ServiceDescriptor) -> Any:
        """Crea una instancia basada en el descriptor."""
        # Si ya hay una instancia registrada
        if descriptor.instance is not None:
            return descriptor.instance
        
        # Si hay un factory
        if descriptor.factory is not None:
            return descriptor.factory()
        
        # Crear usando el constructor
        impl_type = descriptor.implementation_type
        
        if not impl_type:
            raise ValueError(f"No implementation type for {descriptor.service_type.__name__}")
        
        # Resolver dependencias
        dependencies = []
        for dep_type in descriptor.dependencies:
            dependency = self.resolve(dep_type)
            dependencies.append(dependency)
        
        # Crear instancia
        try:
            instance = impl_type(*dependencies)
            self.logger.debug(f"Created instance of {impl_type.__name__}")
            return instance
            
        except Exception as e:
            self.logger.error(f"Error creating instance of {impl_type.__name__}: {e}")
            raise
    
    def _analyze_dependencies(self, impl_type: Type) -> List[Type]:
        """Analiza las dependencias del constructor."""
        try:
            signature = inspect.signature(impl_type.__init__)
            dependencies = []
            
            for param_name, param in signature.parameters.items():
                if param_name == 'self':
                    continue
                
                if param.annotation != inspect.Parameter.empty:
                    dependencies.append(param.annotation)
                else:
                    self.logger.warning(
                        f"Parameter '{param_name}' in {impl_type.__name__}.__init__ "
                        f"has no type annotation"
                    )
            
            return dependencies
            
        except Exception as e:
            self.logger.error(f"Error analyzing dependencies for {impl_type.__name__}: {e}")
            return []
    
    def create_scope(self) -> 'DIScope':
        """Crea un nuevo scope para servicios scoped."""
        return DIScope(self)
    
    def clear_scoped(self):
        """Limpia todas las instancias scoped."""
        self._scoped_instances.clear()
        self.logger.debug("Cleared scoped instances")
    
    def is_registered(self, service_type: Type) -> bool:
        """Verifica si un tipo está registrado."""
        return service_type in self._services
    
    def get_registration_info(self) -> Dict[str, Dict[str, Any]]:
        """Obtiene información de todos los servicios registrados."""
        info = {}
        
        for service_type, descriptor in self._services.items():
            info[service_type.__name__] = {
                "service_type": service_type.__name__,
                "implementation_type": descriptor.implementation_type.__name__ if descriptor.implementation_type else None,
                "lifetime": descriptor.lifetime.value,
                "has_factory": descriptor.factory is not None,
                "has_instance": descriptor.instance is not None,
                "dependencies": [dep.__name__ for dep in descriptor.dependencies],
                "is_singleton_created": service_type in self._singletons,
                "is_scoped_created": service_type in self._scoped_instances
            }
        
        return info


class DIScope:
    """Scope para servicios scoped."""
    
    def __init__(self, container: DIContainer):
        self.container = container
        self._previous_scoped = container._scoped_instances.copy()
        self.logger = logging.getLogger("DIScope")
    
    def __enter__(self):
        self.logger.debug("Entering DI scope")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Restaurar instancias scoped previas
        self.container._scoped_instances = self._previous_scoped
        self.logger.debug("Exiting DI scope")
    
    def resolve(self, service_type: Type[T]) -> T:
        """Resuelve un servicio en este scope."""
        return self.container.resolve(service_type)


class ServiceLocator:
    """Service Locator pattern para acceso global al contenedor."""
    
    _container: Optional[DIContainer] = None
    
    @classmethod
    def set_container(cls, container: DIContainer):
        """Establece el contenedor global."""
        cls._container = container
    
    @classmethod
    def get_container(cls) -> DIContainer:
        """Obtiene el contenedor global."""
        if cls._container is None:
            raise ValueError("No DI container has been set")
        return cls._container
    
    @classmethod
    def resolve(cls, service_type: Type[T]) -> T:
        """Resuelve un servicio usando el contenedor global."""
        return cls.get_container().resolve(service_type)
    
    @classmethod
    def resolve_optional(cls, service_type: Type[T]) -> Optional[T]:
        """Resuelve un servicio opcionalmente."""
        return cls.get_container().resolve_optional(service_type)


def dependency(service_type: Type[T]) -> T:
    """Decorator/función para inyección de dependencias."""
    return ServiceLocator.resolve(service_type)


class AutowiredMixin:
    """Mixin para auto-inyección de dependencias."""
    
    def __post_init__(self):
        """Auto-inyecta dependencias después de la inicialización."""
        container = ServiceLocator.get_container()
        
        # Buscar atributos que necesitan inyección
        for attr_name in dir(self):
            if attr_name.startswith('_autowired_'):
                service_type = getattr(self, attr_name)
                if isinstance(service_type, type):
                    instance = container.resolve_optional(service_type)
                    if instance:
                        setattr(self, attr_name.replace('_autowired_', ''), instance)


# Decoradores de conveniencia

def singleton(cls: Type[T]) -> Type[T]:
    """Decorator para marcar una clase como singleton."""
    if not hasattr(cls, '_di_lifetime'):
        cls._di_lifetime = ServiceLifetime.SINGLETON
    return cls


def transient(cls: Type[T]) -> Type[T]:
    """Decorator para marcar una clase como transient."""
    if not hasattr(cls, '_di_lifetime'):
        cls._di_lifetime = ServiceLifetime.TRANSIENT
    return cls


def scoped(cls: Type[T]) -> Type[T]:
    """Decorator para marcar una clase como scoped."""
    if not hasattr(cls, '_di_lifetime'):
        cls._di_lifetime = ServiceLifetime.SCOPED
    return cls


def auto_register(container: DIContainer, module_or_classes: Union[Any, List[Type]]):
    """Auto-registra clases basándose en decoradores."""
    import types
    
    classes_to_register = []
    
    if isinstance(module_or_classes, types.ModuleType):
        # Obtener todas las clases del módulo
        for name in dir(module_or_classes):
            obj = getattr(module_or_classes, name)
            if isinstance(obj, type) and hasattr(obj, '_di_lifetime'):
                classes_to_register.append(obj)
    elif isinstance(module_or_classes, list):
        classes_to_register = module_or_classes
    else:
        classes_to_register = [module_or_classes]
    
    for cls in classes_to_register:
        if hasattr(cls, '_di_lifetime'):
            lifetime = cls._di_lifetime
            
            if lifetime == ServiceLifetime.SINGLETON:
                container.register_singleton(cls)
            elif lifetime == ServiceLifetime.TRANSIENT:
                container.register_transient(cls)
            elif lifetime == ServiceLifetime.SCOPED:
                container.register_scoped(cls)
            
            logging.getLogger("auto_register").info(f"Auto-registered {cls.__name__} as {lifetime.value}")
