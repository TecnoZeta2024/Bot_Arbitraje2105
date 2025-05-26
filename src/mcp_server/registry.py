import json
import threading
import time
from collections import deque


class MCPRegistry:
    def __init__(self):
        self._mcps = {}  # Stores registered MCPs: {mcp_id: {'config': config, 'status': 'active', 'last_check': time.time(), 'metadata': {}, 'load_balancer': deque()}}
        self._lock = threading.Lock()
        self._health_check_thread = None
        self._running = False

    def register(self, mcp_id, config, metadata=None):
        with self._lock:
            if mcp_id in self._mcps:
                print(f"MCP {mcp_id} already registered. Updating configuration.")
            
            self._mcps[mcp_id] = {
                'config': config,
                'status': 'active',
                'last_check': time.time(),
                'metadata': metadata if metadata is not None else {},
                'load_balancer': deque() # For round-robin if multiple instances of same MCP_ID
            }
            print(f"MCP {mcp_id} registered/updated with config: {config} and metadata: {metadata}")
            self._update_load_balancer(mcp_id)

    def unregister(self, mcp_id):
        with self._lock:
            if mcp_id in self._mcps:
                del self._mcps[mcp_id]
                print(f"MCP {mcp_id} unregistered.")
            else:
                print(f"MCP {mcp_id} not found in registry.")

    def get_mcp(self, mcp_id):
        with self._lock:
            mcp_info = self._mcps.get(mcp_id)
            if mcp_info and mcp_info['status'] == 'active':
                # Simple round-robin load balancing if multiple instances
                if mcp_info['load_balancer']:
                    instance = mcp_info['load_balancer'].popleft()
                    mcp_info['load_balancer'].append(instance)
                    return instance
                else:
                    # If no specific instances for load balancing, return the main config
                    return mcp_info['config']
            return None

    def list_mcps(self, status=None):
        with self._lock:
            if status:
                return {mcp_id: info for mcp_id, info in self._mcps.items() if info['status'] == status}
            return self._mcps.copy()

    def _update_load_balancer(self, mcp_id):
        # This is a placeholder. In a real scenario, this would involve
        # discovering actual instances of the MCP (e.g., via network scan, K8s API)
        # For now, we'll just use the main config as the "instance"
        mcp_info = self._mcps.get(mcp_id)
        if mcp_info:
            mcp_info['load_balancer'] = deque([mcp_info['config']]) # Only one instance for now

    def _perform_health_check(self, mcp_id, config):
        # Placeholder for actual health check logic
        # In a real system, this would involve sending a request to the MCP's health endpoint
        try:
            # Simulate network request
            # For now, assume it's always healthy
            is_healthy = True
            # print(f"Performing health check for {mcp_id} at {config.get('url', 'N/A')}: {'Healthy' if is_healthy else 'Unhealthy'}")
            return is_healthy
        except Exception as e:
            print(f"Health check for {mcp_id} failed: {e}")
            return False

    def health_check_loop(self, interval=10):
        self._running = True
        while self._running:
            with self._lock:
                for mcp_id, info in self._mcps.items():
                    if self._perform_health_check(mcp_id, info['config']):
                        info['status'] = 'active'
                    else:
                        info['status'] = 'inactive'
                    info['last_check'] = time.time()
            time.sleep(interval)

    def start_health_checks(self, interval=10):
        if self._health_check_thread is None or not self._health_check_thread.is_alive():
            self._health_check_thread = threading.Thread(target=self.health_check_loop, args=(interval,))
            self._health_check_thread.daemon = True
            self._health_check_thread.start()
            print("Health check thread started.")
        else:
            print("Health check thread is already running.")

    def stop_health_checks(self):
        self._running = False
        if self._health_check_thread and self._health_check_thread.is_alive():
            self._health_check_thread.join(timeout=5)
            print("Health check thread stopped.")

    def hot_reload_config(self, mcp_id, new_config):
        with self._lock:
            if mcp_id in self._mcps:
                self._mcps[mcp_id]['config'] = new_config
                print(f"Configuration for MCP {mcp_id} hot-reloaded.")
                # Potentially re-initialize parts of the MCP if needed
                self._update_load_balancer(mcp_id)
            else:
                print(f"MCP {mcp_id} not found for hot-reload.")

# Example Usage (for testing purposes)
if __name__ == "__main__":
    registry = MCPRegistry()

    # Register some dummy MCPs
    registry.register("mcp_crypto_indicators", {"url": "http://localhost:8001/crypto", "version": "1.0"}, {"type": "data_source", "data_format": "JSON"})
    registry.register("mcp_sentiment_analysis", {"url": "http://localhost:8002/sentiment", "version": "1.1"}, {"type": "analysis", "model": "BERT"})

    # Start health checks
    registry.start_health_checks(interval=5)

    print("\nRegistered MCPs:")
    print(registry.list_mcps())

    # Simulate some time passing
    time.sleep(7)

    print("\nMCPs after some health checks:")
    print(registry.list_mcps())

    # Get an MCP
    mcp_config = registry.get_mcp("mcp_crypto_indicators")
    print(f"\nRetrieved MCP config for mcp_crypto_indicators: {mcp_config}")

    # Hot-reload config
    registry.hot_reload_config("mcp_crypto_indicators", {"url": "http://localhost:8001/crypto_new", "version": "1.0.1"})
    print("\nMCPs after hot-reload:")
    print(registry.list_mcps())

    # Unregister an MCP
    registry.unregister("mcp_sentiment_analysis")
    print("\nMCPs after unregistering one:")
    print(registry.list_mcps())

    # Stop health checks
    registry.stop_health_checks()
