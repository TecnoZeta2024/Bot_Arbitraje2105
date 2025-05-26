import json
import zlib
from typing import Any, Dict, Optional

from pydantic import BaseModel


class MCPRequest(BaseModel):
    mcp_id: str
    tool_name: str
    args: Dict[str, Any]
    version: str = "1.0"

class MCPResponse(BaseModel):
    status: str # "success" or "error"
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    version: str = "1.0"

class MCPProtocol:
    @staticmethod
    def serialize_message(message: BaseModel, compress: bool = False) -> bytes:
        json_data = message.json().encode('utf-8')
        if compress:
            return zlib.compress(json_data)
        return json_data

    @staticmethod
    def deserialize_request(data: bytes) -> MCPRequest:
        try:
            decompressed_data = zlib.decompress(data)
            return MCPRequest.parse_raw(decompressed_data)
        except zlib.error:
            return MCPRequest.parse_raw(data)
        except Exception as e:
            raise ValueError(f"Error deserializing request: {e}")

    @staticmethod
    def deserialize_response(data: bytes) -> MCPResponse:
        try:
            decompressed_data = zlib.decompress(data)
            return MCPResponse.parse_raw(decompressed_data)
        except zlib.error:
            return MCPResponse.parse_raw(data)
        except Exception as e:
            raise ValueError(f"Error deserializing response: {e}")

    @staticmethod
    def create_error_response(error_message: str) -> MCPResponse:
        return MCPResponse(status="error", error=error_message)
