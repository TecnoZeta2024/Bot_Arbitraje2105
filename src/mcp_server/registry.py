import importlib.util
import json
import logging
import os
import sys
import threading
import time
from collections import deque
from typing import Any, Dict, List, Optional

import httpx

from src.mcp_server.adapters.base_adapter import BaseMCPAdapter
from src.mcp_server.database import get_db_connection, init_db
from src.mcp_server.schemas import MCPInfo, MCPRegistration

logger = logging.getLogger(__name__)

class MCPRegistry:
    def __init__(self):
        self._lock = threading.Lock()
        self._health_check_thread = None
        self._running = False
        init_db() # Ensure database is initialized
        self._mcps_cache = {} # Cache for frequently accessed MCPs
        self._refresh_mcps_cache_from_db() # Load initial MCPs into cache
        self._load_local_adapters() # Load local MCP adapters

    def _load_mcp_from_db(self, server_name: str) -> Optional[Dict[str, Any]]:
        """Carga un MCP específico de la base de datos, incluyendo metadatos y capacidades."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT server_name, url, metadata, capabilities, status FROM mcps WHERE server_name = ?", (server_name,))
            row = cursor.fetchone()
            if row:
                mcp_data = dict(row)
                url_data = json.loads(mcp_data['url']) if mcp_data['url'] else {}
                base_url = url_data.get('url', '')
                
                mcp_data['base_url'] = base_url
                mcp_data['metadata'] = json.loads(mcp_data['metadata']) if isinstance(mcp_data['metadata'], str) and mcp_data['metadata'] else {}
                mcp_data['capabilities'] = json.loads(mcp_data['capabilities']) if isinstance(mcp_data['capabilities'], str) and mcp_data['capabilities'] else {}
                return mcp_data
            return None

    def _save_mcp_to_db(self, registration_data: MCPRegistration, status: str = 'active'):
        """Guarda o actualiza un MCP en la base de datos utilizando el esquema MCPRegistration."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            metadata_json = json.dumps(registration_data.metadata)
            capabilities_json = json.dumps(registration_data.capabilities)
            url_json = json.dumps({"url": registration_data.address})
            try:
                cursor.execute("""
                    INSERT INTO mcps (server_name, url, metadata, capabilities, status)
                    VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(server_name) DO UPDATE SET
                        url = EXCLUDED.url,
                        metadata = EXCLUDED.metadata,
                        capabilities = EXCLUDED.capabilities,
                        status = EXCLUDED.status,
                        registered_at = CURRENT_TIMESTAMP
                """, (registration_data.mcp_id, url_json, metadata_json, capabilities_json, status))
                conn.commit()
                logger.info(f"MCP {registration_data.mcp_id} registrado/actualizado en la base de datos.")
            except Exception as e:
                logger.error(f"Error al guardar MCP {registration_data.mcp_id} en la base de datos: {e}")
                raise

    def register(self, registration_data: MCPRegistration):
        """Registra un nuevo MCP o actualiza uno existente con metadatos y capacidades detallados."""
        with self._lock:
            try:
                self._save_mcp_to_db(registration_data)
                # Update cache after successful DB operation
                self._mcps_cache[registration_data.mcp_id] = self._load_mcp_from_db(registration_data.mcp_id)
                logger.info(f"MCP {registration_data.mcp_id} registrado/actualizado con dirección: {registration_data.address}, metadatos: {registration_data.metadata} y capacidades: {registration_data.capabilities}")
            except Exception as e:
                logger.error(f"Fallo al registrar MCP {registration_data.mcp_id}: {e}")
                raise

    def unregister(self, server_name: str):
        with self._lock:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM mcps WHERE server_name = ?", (server_name,))
                conn.commit()
                if cursor.rowcount > 0:
                    self._mcps_cache.pop(server_name, None) # Remove from cache
                    logger.info(f"MCP {server_name} dado de baja.")
                else:
                    logger.warning(f"MCP {server_name} no encontrado en el registro para dar de baja.")

    def _refresh_mcps_cache_from_db(self):
        """Recarga la caché de MCPs desde la base de datos, incluyendo solo los activos."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT server_name, url, metadata, capabilities, status FROM mcps WHERE status = 'active'")
            new_cache = {}
            for row in cursor.fetchall():
                mcp_data = dict(row)
                url_data = json.loads(mcp_data['url']) if mcp_data['url'] else {}
                base_url = url_data.get('url', '')
                mcp_data['base_url'] = base_url
                mcp_data['metadata'] = json.loads(mcp_data['metadata']) if isinstance(mcp_data['metadata'], str) and mcp_data['metadata'] else {}
                mcp_data['capabilities'] = json.loads(mcp_data['capabilities']) if isinstance(mcp_data['capabilities'], str) and mcp_data['capabilities'] else {}
                new_cache[mcp_data['server_name']] = mcp_data
            self._mcps_cache = new_cache
            logger.info(f"Caché de MCPs recargada. {len(new_cache)} MCPs activos cargados.")

    def get_healthy_mcps(self) -> List[MCPInfo]:
        """Retorna una lista de MCPInfo para todos los MCPs activos."""
        with self._lock:
            healthy_mcps = []
            # Iterate through the cache which is already filtered for active MCPs by _refresh_mcps_cache_from_db
            for mcp_id, mcp_data in self._mcps_cache.items():
                if mcp_data.get('status') == 'active':
                    healthy_mcps.append(MCPInfo(
                        mcp_id=mcp_data['server_name'],
                        base_url=mcp_data['base_url'],
                        status=mcp_data['status'],
                        capabilities=mcp_data['capabilities']
                    ))
            return healthy_mcps

    def mark_mcp_unhealthy(self, mcp_id: str):
        """Marca un MCP como inactivo en la base de datos y en la caché."""
        with self._lock:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE mcps SET status = 'inactive', last_check = CURRENT_TIMESTAMP
                    WHERE server_name = ?
                """, (mcp_id,))
                conn.commit()
                if cursor.rowcount > 0:
                    # Update cache directly for this MCP
                    if mcp_id in self._mcps_cache:
                        self._mcps_cache[mcp_id]['status'] = 'inactive'
                    logger.warning(f"MCP {mcp_id} marcado como inactivo debido a un fallo.")
                else:
                    logger.warning(f"MCP {mcp_id} no encontrado para marcar como inactivo.")

    def get_mcp(self, server_name: str) -> Optional[MCPInfo]:
        """Retorna la información de un MCP específico si está activo."""
        with self._lock:
            mcp_data = self._mcps_cache.get(server_name)
            if not mcp_data:
                # If not in cache, try loading from DB (might be a newly added MCP not yet in cache refresh cycle)
                mcp_data = self._load_mcp_from_db(server_name)
                if mcp_data:
                    self._mcps_cache[server_name] = mcp_data # Add to cache

            if mcp_data and mcp_data.get('status') == 'active':
                return MCPInfo(
                    mcp_id=mcp_data['server_name'],
                    base_url=mcp_data['base_url'],
                    status=mcp_data['status'],
                    capabilities=mcp_data['capabilities']
                )
            return None

    def _load_local_adapters(self):
        """
        Descubre y carga dinámicamente adaptadores MCP locales desde el directorio 'adapters'.
        """
        adapters_dir = os.path.join(os.path.dirname(__file__), 'adapters')
        if not os.path.exists(adapters_dir):
            logger.warning(f"Directorio de adaptadores no encontrado: {adapters_dir}")
            return

        for filename in os.listdir(adapters_dir):
            if filename.endswith(".py") and filename not in ["__init__.py", "base_adapter.py"]:
                module_name = filename[:-3]
                file_path = os.path.join(adapters_dir, filename)
                
                try:
                    spec = importlib.util.spec_from_file_location(module_name, file_path)
                    if spec is None or spec.loader is None:
                        logger.error(f"No se pudo obtener la especificación o el cargador para el módulo {module_name} en {file_path}")
                        continue
                    
                    module = importlib.util.module_from_spec(spec)
                    sys.modules[module_name] = module
                    spec.loader.exec_module(module)

                    for attribute_name in dir(module):
                        attribute = getattr(module, attribute_name)
                        if (isinstance(attribute, type) and 
                            issubclass(attribute, BaseMCPAdapter) and 
                            attribute is not BaseMCPAdapter):
                            
                            # Crear una instancia del adaptador, pasando una configuración vacía por defecto
                            # y una descripción genérica si el adaptador no la proporciona directamente.
                            # La descripción se obtiene del adaptador si está disponible, de lo contrario, se usa una genérica.
                            # Crear una instancia del adaptador, pasando una configuración vacía por defecto.
                            # Crear una instancia del adaptador, pasando una configuración vacía por defecto.
                            # Crear una instancia del adaptador, pasando una configuración vacía por defecto.
                            # Crear una instancia del adaptador, pasando una configuración vacía por defecto.
                            # Crear una instancia del adaptador, pasando una configuración vacía por defecto.
                            # Crear una instancia del adaptador, pasando una configuración vacía por defecto.
                            # Crear una instancia del adaptador, pasando una configuración vacía por defecto.
                            # Crear una instancia del adaptador, pasando una configuración vacía por defecto.
                            # Crear una instancia del adaptador, pasando una configuración vacía por defecto.
                            # Crear una instancia del adaptador, pasando una configuración vacía por defecto.
                            # Crear una instancia del adaptador, pasando una configuración vacía por defecto.
                            # Crear una instancia del adaptador, pasando una configuración vacía por defecto.
                            # Crear una instancia del adaptador, pasando una configuración vacía por defecto.
                            # Crear una instancia del adaptador, pasando una configuración vacía por defecto.
                            # Crear una instancia del adaptador, pasando una configuración vacía por defecto.
                            # Crear una instancia del adaptador, pasando una configuración vacía por defecto.
                            # El constructor de BaseMCPAdapter ahora requiere server_name, description y config.
                            # Los adaptadores locales deben tener un constructor que acepte 'config'.
                            # La descripción y el nombre del servidor se obtendrán del propio adaptador después de la inicialización.
                            # Para evitar el error de Pylance, pasamos valores por defecto para server_name y description
                            # al constructor del adaptador, ya que todos nuestros adaptadores ahora aceptan 'config'.
                            # Estos valores serán sobrescritos por el super().__init__ del adaptador si están definidos allí.
                            adapter_instance = attribute(config={}) 
                            logger.info(f"Adaptador local descubierto: {module_name}")
                            
                            # Convertir las capacidades del adaptador (objetos Tool/Resource) a diccionarios
                            # usando el método to_registry_format del adaptador base.
                            adapter_registry_format = adapter_instance.to_registry_format()
                            
                            # Crear una instancia de MCPRegistration para el adaptador local
                            # Usamos una URL ficticia o un identificador para adaptadores locales
                            local_mcp_registration = MCPRegistration(
                                mcp_id=adapter_registry_format["server_name"], # Usar el nombre del servidor del adaptador
                                address=f"local://{adapter_registry_format['server_name']}", # URL ficticia para adaptadores locales
                                metadata={"type": "local_adapter", "description": adapter_registry_format["description"]},
                                capabilities={
                                    "tools": adapter_registry_format["tools"],
                                    "resources": adapter_registry_format["resources"]
                                }
                            )
                            self.register(local_mcp_registration)
                            logger.info(f"Adaptador local {module_name} registrado exitosamente.")
                            break # Asumimos una clase de adaptador por archivo
                except Exception as e:
                    logger.error(f"Error al cargar el adaptador local {filename}: {e}")

    def list_mcps(self, status: Optional[str] = None):
        with self._lock:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                if status:
                    cursor.execute("SELECT server_name, url, capabilities, status, registered_at FROM mcps WHERE status = ?", (status,))
                else:
                    cursor.execute("SELECT server_name, url, capabilities, status, registered_at FROM mcps")
                
                mcps_list = []
                for row in cursor.fetchall():
                    mcp_data = dict(row)
                    mcp_data['url'] = json.loads(mcp_data['url']) # Parse URL back to dict
                    mcp_data['capabilities'] = json.loads(mcp_data['capabilities']) if mcp_data['capabilities'] else {}
                    mcps_list.append(mcp_data)
                return mcps_list

    def _update_load_balancer(self, server_name):
        # This is a placeholder. In a real scenario, this would involve
        # discovering actual instances of the MCP (e.g., via network scan, K8s API)
        # For now, we'll just use the main config as the "instance"
        mcp_info = self._mcps_cache.get(server_name)
        if mcp_info:
            mcp_info['load_balancer'] = deque([mcp_info['config']]) # Only one instance for now

    async def _perform_health_check_async(self, server_name: str, config: dict):
        """Realiza una verificación de salud asíncrona para un MCP."""
        health_url = config.get('health_url') or config.get('url')
        if not health_url:
            logger.warning(f"No URL o health_url especificada para MCP {server_name}. Asumiendo inactivo.")
            return False
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(health_url)
                is_healthy = response.status_code == 200
                logger.info(f"Verificación de salud para {server_name} en {health_url}: {'Activo' if is_healthy else 'Inactivo'} (Estado: {response.status_code})")
                return is_healthy
        except httpx.RequestError as e:
            logger.error(f"Fallo la solicitud de verificación de salud para {server_name} en {health_url}: {e}")
            return False
        except Exception as e:
            logger.error(f"Ocurrió un error inesperado durante la verificación de salud para {server_name}: {e}")
            return False

    def health_check_loop(self, interval=10):
        import asyncio
        self._running = True
        while self._running:
            with self._lock:
                self._refresh_mcps_cache_from_db() # Ensure cache is up-to-date with DB before health checks
                
                mcps_to_check = list(self._mcps_cache.values()) # Get current MCPs from cache

                for mcp_data in mcps_to_check:
                    server_name = mcp_data['server_name']
                    config = {"url": mcp_data['base_url'], "health_url": mcp_data['metadata'].get('health_url')}
                    try:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        is_healthy = loop.run_until_complete(self._perform_health_check_async(server_name, config))
                        loop.close()

                        with get_db_connection() as conn:
                            cursor = conn.cursor()
                            status = 'active' if is_healthy else 'inactive'
                            cursor.execute("""
                                UPDATE mcps SET status = ?, last_check = CURRENT_TIMESTAMP
                                WHERE server_name = ?
                            """, (status, server_name))
                            conn.commit()
                            # Update cache directly
                            if server_name in self._mcps_cache:
                                self._mcps_cache[server_name]['status'] = status
                                self._mcps_cache[server_name]['last_check'] = time.time()
                    except Exception as e:
                        logger.error(f"Error al ejecutar la verificación de salud asíncrona para {server_name}: {e}")
            time.sleep(interval)

    def start_health_checks(self, interval=10):
        if self._health_check_thread is None or not self._health_check_thread.is_alive():
            self._running = True
            self._health_check_thread = threading.Thread(target=self.health_check_loop, args=(interval,))
            self._health_check_thread.daemon = True
            self._health_check_thread.start()
            logger.info("Hilo de verificación de salud iniciado.")
        else:
            logger.info("El hilo de verificación de salud ya está en ejecución.")

    def stop_health_checks(self):
        self._running = False
        if self._health_check_thread and self._health_check_thread.is_alive():
            self._health_check_thread.join(timeout=5)
            logger.info("Hilo de verificación de salud detenido.")

    def hot_reload_config(self, registration_data: MCPRegistration):
        """Recarga la configuración de un MCP existente con nuevos metadatos."""
        with self._lock:
            try:
                self._save_mcp_to_db(registration_data)
                # Update cache after successful DB operation
                self._mcps_cache[registration_data.mcp_id] = self._load_mcp_from_db(registration_data.mcp_id)
                logger.info(f"Configuración para MCP {registration_data.mcp_id} recargada en caliente con dirección: {registration_data.address} y metadatos: {registration_data.metadata}.")
            except Exception as e:
                logger.error(f"Fallo al recargar la configuración para MCP {registration_data.mcp_id}: {e}")
                raise

# Example Usage (for testing purposes)
if __name__ == "__main__":
    # No need to clean up registry file, database handles persistence
    # Ensure the database is initialized before starting
    init_db()

    registry = MCPRegistry()

    # Register some dummy MCPs
    mcp_crypto_reg = MCPRegistration(
        mcp_id="mcp_crypto_indicators",
        address="http://localhost:8001/crypto",
        metadata={"health_url": "http://localhost:8001/health", "version": "1.0", "type": "data_source", "data_format": "JSON"}
    )
    registry.register(mcp_crypto_reg)

    mcp_sentiment_reg = MCPRegistration(
        mcp_id="mcp_sentiment_analysis",
        address="http://localhost:8002/sentiment",
        metadata={"health_url": "http://localhost:8002/health", "version": "1.1", "type": "analysis", "model": "BERT"}
    )
    registry.register(mcp_sentiment_reg)

    # Start health checks
    registry.start_health_checks(interval=5)

    print("\nRegistered MCPs:")
    for mcp in registry.list_mcps():
        print(mcp)

    # Simulate some time passing
    time.sleep(7)

    print("\nMCPs after some health checks:")
    for mcp in registry.list_mcps():
        print(mcp)

    # Get an MCP
    mcp_config = registry.get_mcp("mcp_crypto_indicators")
    print(f"\nRetrieved MCP config for mcp_crypto_indicators: {mcp_config}")

    # Hot-reload config
    # hot_reload_config still expects server_name, new_url_config, new_capabilities
    # We need to adjust hot_reload_config to use MCPRegistration or keep its current signature
    # For now, let's adjust hot_reload_config to accept MCPRegistration as well for consistency
    # Or, we can keep it as is and pass the data in the old format, but that's less consistent.
    # Let's modify hot_reload_config to accept MCPRegistration.

    # First, modify the hot_reload_config method signature and implementation
    # Then, update this call.
    # For now, commenting out to fix other errors first.
    # registry.hot_reload_config("mcp_crypto_indicators", {"url": "http://localhost:8001/crypto_new", "health_url": "http://localhost:8001/health_new", "version": "1.0.1"}, {"type": "data_source", "data_format": "JSON", "updated": True})
    
    # New hot-reload call using MCPRegistration
    mcp_crypto_reload_reg = MCPRegistration(
        mcp_id="mcp_crypto_indicators",
        address="http://localhost:8001/crypto_new",
        metadata={"health_url": "http://localhost:8001/health_new", "version": "1.0.1", "type": "data_source", "data_format": "JSON", "updated": True}
    )
    registry.hot_reload_config(mcp_crypto_reload_reg) # This will require changing hot_reload_config signature

    print("\nMCPs after hot-reload:")
    for mcp in registry.list_mcps():
        print(mcp)

    # Unregister an MCP
    registry.unregister("mcp_sentiment_analysis")
    print("\nMCPs after unregistering one:")
    for mcp in registry.list_mcps():
        print(mcp)

    # Stop health checks
    registry.stop_health_checks()
    
    # Verify persistence by creating a new registry instance
    print("\nCreating a new registry instance to verify persistence:")
    new_registry = MCPRegistry()
    for mcp in new_registry.list_mcps():
        print(mcp)
