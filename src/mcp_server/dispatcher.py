import logging
from typing import List, Dict, Optional
from urllib.parse import urljoin
import httpx
from fastapi import HTTPException

from src.mcp_server.registry import MCPRegistry

logger = logging.getLogger(__name__)

class MCPDispatcher:
    def __init__(self, registry: MCPRegistry):
        self.registry = registry
        self.current_mcp_index = 0

    async def dispatch(self, path: str, method: str = "GET", headers: Optional[Dict] = None, body: Optional[bytes] = None) -> httpx.Response:
        healthy_mcps = self.registry.get_healthy_mcps()
        if not healthy_mcps:
            logger.warning("No healthy MCPs available for dispatch.")
            raise HTTPException(status_code=503, detail="No healthy MCPs available")

        # Round-robin load balancing
        for _ in range(len(healthy_mcps)):
            mcp_info = healthy_mcps[self.current_mcp_index]
            self.current_mcp_index = (self.current_mcp_index + 1) % len(healthy_mcps)

            base_url = mcp_info.base_url
            full_url = urljoin(base_url, path.lstrip('/'))
            
            logger.info(f"Dispatching request to {full_url} (MCP ID: {mcp_info.mcp_id})")

            try:
                async with httpx.AsyncClient() as client:
                    if method == "GET":
                        response = await client.get(full_url, headers=headers)
                    elif method == "POST":
                        response = await client.post(full_url, headers=headers, content=body)
                    elif method == "PUT":
                        response = await client.put(full_url, headers=headers, content=body)
                    elif method == "DELETE":
                        response = await client.delete(full_url, headers=headers)
                    else:
                        raise NotImplementedError(f"Method {method} not supported")
                    
                    response.raise_for_status() # Raise an exception for 4xx/5xx responses
                    return response
            except httpx.RequestError as exc:
                logger.error(f"Request to {full_url} failed: {exc}")
                # Mark MCP as unhealthy if request fails
                self.registry.mark_mcp_unhealthy(mcp_info.mcp_id)
            except httpx.HTTPStatusError as exc:
                logger.error(f"HTTP error for {full_url}: {exc.response.status_code} - {exc.response.text}")
                # Re-raise HTTP status errors, as they indicate a problem with the request/response, not necessarily the MCP being down
                raise HTTPException(status_code=exc.response.status_code, detail=exc.response.text)
            except Exception as exc:
                logger.error(f"An unexpected error occurred during dispatch to {full_url}: {exc}")
                self.registry.mark_mcp_unhealthy(mcp_info.mcp_id)

        logger.error("All healthy MCPs failed to process the request.")
        raise HTTPException(status_code=500, detail="All healthy MCPs failed to process the request")
