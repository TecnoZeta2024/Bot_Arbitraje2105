import asyncio
import json
import time
from collections import OrderedDict
from typing import Any, Dict, Optional, Tuple

import redis.asyncio as redis

class CacheSystem:
    def __init__(self, redis_client: redis.Redis, l1_capacity: int = 1000, default_ttl: int = 300):
        self.l1_cache: OrderedDict[str, Tuple[Any, float]] = OrderedDict()
        self.l1_capacity = l1_capacity
        self.l2_cache = redis_client
        self.default_ttl = default_ttl
        self.metrics = {
            "l1_hits": 0,
            "l1_misses": 0,
            "l2_hits": 0,
            "l2_misses": 0,
            "sets": 0,
            "invalidations": 0,
            "l1_evictions": 0,
        }

    async def get(self, key: str) -> Optional[Any]:
        # Try L1 cache
        if key in self.l1_cache:
            value, expiry_time = self.l1_cache[key]
            if expiry_time > time.time():
                self.l1_cache.move_to_end(key)
                self.metrics["l1_hits"] += 1
                return value
            else:
                # L1 entry expired, remove it
                del self.l1_cache[key]
                self.metrics["l1_misses"] += 1 # Consider as miss if expired
        else:
            self.metrics["l1_misses"] += 1

        # Try L2 cache (Redis)
        try:
            cached_data = await self.l2_cache.get(key)
            if cached_data:
                self.metrics["l2_hits"] += 1
                value = json.loads(cached_data)
                # Populate L1 cache from L2
                self._set_l1(key, value, self.default_ttl)
                return value
            else:
                self.metrics["l2_misses"] += 1
        except Exception as e:
            # Log Redis connection errors or other issues
            print(f"Error accessing Redis L2 cache for key {key}: {e}")
            self.metrics["l2_misses"] += 1 # Treat Redis errors as misses
        
        return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None):
        ttl = ttl if ttl is not None else self.default_ttl
        self.metrics["sets"] += 1

        # Set in L1 cache
        self._set_l1(key, value, ttl)

        # Set in L2 cache (Redis)
        try:
            await self.l2_cache.setex(key, ttl, json.dumps(value))
        except Exception as e:
            print(f"Error setting value in Redis L2 cache for key {key}: {e}")

    def _set_l1(self, key: str, value: Any, ttl: int):
        expiry_time = time.time() + ttl
        if key in self.l1_cache:
            self.l1_cache.pop(key) # Remove to update position
        elif len(self.l1_cache) >= self.l1_capacity:
            # Evict LRU item
            self.l1_cache.popitem(last=False)
            self.metrics["l1_evictions"] += 1
        self.l1_cache[key] = (value, expiry_time)

    async def invalidate(self, key: str):
        self.metrics["invalidations"] += 1
        # Invalidate in L1
        if key in self.l1_cache:
            del self.l1_cache[key]
        # Invalidate in L2 (Redis)
        try:
            await self.l2_cache.delete(key)
        except Exception as e:
            print(f"Error invalidating key {key} in Redis L2 cache: {e}")

    async def preload(self, keys_values: Dict[str, Any], ttl: Optional[int] = None):
        """
        Precarga múltiples claves-valores en la caché.
        Ideal para datos que se sabe que serán accedidos frecuentemente.
        """
        for key, value in keys_values.items():
            await self.set(key, value, ttl)
        print(f"Precargados {len(keys_values)} elementos en la caché.")

    def get_metrics(self) -> Dict[str, Any]:
        """
        Devuelve las métricas actuales del sistema de caché.
        """
        return {
            "l1_cache_size": len(self.l1_cache),
            "l1_capacity": self.l1_capacity,
            **self.metrics
        }

    async def clear_all_caches(self):
        """
        Limpia completamente ambas cachés (L1 y L2).
        """
        self.l1_cache.clear()
        try:
            await self.l2_cache.flushdb()
            print("Caché L2 (Redis) vaciada.")
        except Exception as e:
            print(f"Error al vaciar la caché L2 (Redis): {e}")
        
        # Reset metrics after clearing
        self.metrics = {
            "l1_hits": 0,
            "l1_misses": 0,
            "l2_hits": 0,
            "l2_misses": 0,
            "sets": 0,
            "invalidations": 0,
            "l1_evictions": 0,
        }
        print("Caché L1 y métricas reiniciadas.")
