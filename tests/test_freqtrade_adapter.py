import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import httpx # Importar httpx
from src.mcp_server.adapters.freqtrade import FreqtradeAdapter
from src.mcp_server.schemas import Tool, ToolParameter, ResourceSchema
from src.mcp_server.schemas import RequestPayload, ResponsePayload # Importar los payloads reales

@pytest.fixture
def freqtrade_adapter():
    """Fixture para el adaptador Freqtrade con un cliente httpx mockeado."""
    adapter = FreqtradeAdapter(
        config={"freqtrade_api_url": "http://localhost:8080/api/v1"}
    )
    # Mockear la instancia de httpx.AsyncClient que ya fue creada
    adapter.client = AsyncMock(spec=httpx.AsyncClient)
    return adapter

@pytest.mark.asyncio
async def test_initialize_adapter(freqtrade_adapter):
    """Verifica la inicialización del adaptador."""
    assert freqtrade_adapter.server_name == "freqtrade"
    assert freqtrade_adapter.description == "Adaptador para Freqtrade"
    assert freqtrade_adapter.config["freqtrade_api_url"] == "http://localhost:8080/api/v1"
    assert isinstance(freqtrade_adapter.client, AsyncMock) # Asegurar que el cliente es un mock

@pytest.mark.asyncio
async def test_get_tools_definitions(freqtrade_adapter):
    """Verifica que las definiciones de herramientas se generen correctamente."""
    tools = freqtrade_adapter.get_tools()
    assert isinstance(tools, list)
    assert len(tools) > 0
    # Verificar una herramienta específica, por ejemplo 'execute_strategy'
    execute_strategy_tool = next((t for t in tools if t.name == "execute_strategy"), None)
    assert execute_strategy_tool is not None
    assert execute_strategy_tool.description == "Ejecuta una estrategia de trading en Freqtrade."
    assert any(p.name == "strategy_name" and p.type == "string" for p in execute_strategy_tool.parameters)

@pytest.mark.asyncio
async def test_execute_tool_status_success(freqtrade_adapter):
    """Prueba la ejecución exitosa de la herramienta 'status'."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"status": "running", "pairs": ["BTC/USDT"]}
    mock_response.raise_for_status.return_value = None
    freqtrade_adapter.client.get.return_value = mock_response

    tool_args = {"tool_name": "status", "arguments": {"pair": "BTC/USDT"}}
    result = await freqtrade_adapter.handle_tool_request(tool_args["tool_name"], tool_args["arguments"])

    assert isinstance(result, dict)
    assert result.get("status") == "success"
    assert result.get("live_status") == {"status": "running", "pairs": ["BTC/USDT"]}
    freqtrade_adapter.client.get.assert_called_once_with("http://localhost:8080/api/v1/live_trading_status", params=None)

@pytest.mark.asyncio
async def test_execute_tool_status_error(freqtrade_adapter):
    """Prueba el manejo de errores en la ejecución de la herramienta 'status'."""
    mock_response_error = MagicMock()
    mock_response_error.status_code = 500
    mock_response_error.text = "Internal Server Error"
    freqtrade_adapter.client.get.side_effect = httpx.HTTPStatusError(
        "Internal Server Error", request=httpx.Request("GET", "http://localhost"), response=mock_response_error
    )

    tool_args = {"tool_name": "status", "arguments": {"pair": "BTC/USDT"}}
    result = await freqtrade_adapter.handle_tool_request(tool_args["tool_name"], tool_args["arguments"])

    assert isinstance(result, dict)
    assert result.get("status") == "error"
    output_content = result.get("message")
    assert isinstance(output_content, str)
    assert "Error al obtener estado de trading en vivo" in output_content
    assert "Internal Server Error" in output_content
    freqtrade_adapter.client.get.assert_called_once_with("http://localhost:8080/api/v1/live_trading_status", params=None)

@pytest.mark.asyncio
async def test_execute_tool_start_trade_success(freqtrade_adapter):
    """Prueba la ejecución exitosa de la herramienta 'start_trade'."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"message": "Trade started", "trade_id": "123"}
    mock_response.raise_for_status.return_value = None
    freqtrade_adapter.client.post.return_value = mock_response

    tool_args = {"tool_name": "start_trade", "arguments": {"pair": "ETH/USDT", "amount": 0.05}}
    result = await freqtrade_adapter.handle_tool_request(tool_args["tool_name"], tool_args["arguments"])

    assert isinstance(result, dict)
    assert result.get("status") == "success"
    assert result.get("message") == "Trade started"
    freqtrade_adapter.client.post.assert_called_once_with(
        "http://localhost:8080/api/v1/execute_strategy",
        json={"strategy_name": None, "pair": "ETH/USDT", "timeframe": None}
    )

@pytest.mark.asyncio
async def test_execute_tool_start_trade_validation_error(freqtrade_adapter):
    """Prueba el manejo de errores de validación en 'start_trade'."""
    mock_response_error = MagicMock()
    mock_response_error.status_code = 400
    mock_response_error.text = "Missing amount"
    freqtrade_adapter.client.post.side_effect = httpx.HTTPStatusError(
        "Bad Request", request=httpx.Request("POST", "http://localhost"), response=mock_response_error
    )

    tool_args = {"tool_name": "start_trade", "arguments": {"pair": "ETH/USDT"}}
    result = await freqtrade_adapter.handle_tool_request(tool_args["tool_name"], tool_args["arguments"])

    assert isinstance(result, dict)
    assert result.get("status") == "error"
    output_content = result.get("message")
    assert isinstance(output_content, str)
    assert "Error al ejecutar estrategia" in output_content
    assert "Missing amount" in output_content
    freqtrade_adapter.client.post.assert_called_once_with(
        "http://localhost:8080/api/v1/execute_strategy",
        json={"strategy_name": None, "pair": "ETH/USDT", "timeframe": None}
    )

@pytest.mark.asyncio
async def test_execute_tool_unknown_tool(freqtrade_adapter):
    """Prueba el manejo de una herramienta desconocida."""
    tool_args = {"tool_name": "unknown_tool", "arguments": {}}
    with pytest.raises(ValueError) as excinfo:
        await freqtrade_adapter.handle_tool_request(tool_args["tool_name"], tool_args["arguments"])

    assert "Herramienta Freqtrade no soportada: unknown_tool" == str(excinfo.value)

@pytest.mark.asyncio
async def test_execute_tool_get_strategies_success(freqtrade_adapter):
    """Prueba la ejecución exitosa de la herramienta 'get_strategies'."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"strategies": ["MyStrategy", "AnotherStrategy"]}
    mock_response.raise_for_status.return_value = None
    freqtrade_adapter.client.get.return_value = mock_response

    tool_args = {"tool_name": "get_strategies", "arguments": {}}
    result = await freqtrade_adapter.handle_tool_request(tool_args["tool_name"], tool_args["arguments"])

    assert isinstance(result, dict)
    assert result.get("status") == "success"
    assert result.get("strategies") == ["MyStrategy", "AnotherStrategy"]
    freqtrade_adapter.client.get.assert_called_once_with("http://localhost:8080/api/v1/strategies", params=None)

@pytest.mark.asyncio
async def test_execute_tool_load_strategy_success(freqtrade_adapter):
    """Prueba la ejecución exitosa de la herramienta 'load_strategy'."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"message": "Strategy loaded", "strategy": "MyStrategy"}
    mock_response.raise_for_status.return_value = None
    freqtrade_adapter.client.post.return_value = mock_response

    tool_args = {"tool_name": "load_strategy", "arguments": {"strategy_name": "MyStrategy", "strategy_content": "some content", "strategy_filename": "MyStrategy.py"}}
    result = await freqtrade_adapter.handle_tool_request(tool_args["tool_name"], tool_args["arguments"])

    assert isinstance(result, dict)
    assert result.get("status") == "success"
    assert result.get("message") == "Strategy loaded"
    freqtrade_adapter.client.post.assert_called_once_with(
        "http://localhost:8080/api/v1/upload_strategy",
        json={"strategy_content": "some content", "strategy_filename": "MyStrategy.py"}
    )

@pytest.mark.asyncio
async def test_execute_tool_run_backtest_success(freqtrade_adapter):
    """Prueba la ejecución exitosa de la herramienta 'run_backtest'."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"message": "Backtest started", "results": {"profit": 100}}
    mock_response.raise_for_status.return_value = None
    freqtrade_adapter.client.post.return_value = mock_response

    tool_args = {"tool_name": "run_backtest", "arguments": {"strategy_name": "MyStrategy", "timerange": "20230101-20230331"}}
    result = await freqtrade_adapter.handle_tool_request(tool_args["tool_name"], tool_args["arguments"])

    assert isinstance(result, dict)
    assert result.get("status") == "success"
    assert result.get("message") == "Backtest started"
    assert result.get("results") == {"profit": 100}
    freqtrade_adapter.client.post.assert_called_once_with(
        "http://localhost:8080/api/v1/start_backtest",
        json={"strategy_name": "MyStrategy", "timerange": "20230101-20230331", "fiat_display_currency": "USD"}
    )

@pytest.mark.asyncio
async def test_execute_tool_get_trade_history_success(freqtrade_adapter):
    """Prueba la ejecución exitosa de la herramienta 'get_trade_history'."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"trades": [{"id": "trade1", "pair": "BTC/USDT"}]}
    mock_response.raise_for_status.return_value = None
    freqtrade_adapter.client.get.return_value = mock_response

    tool_args = {"tool_name": "get_trade_history", "arguments": {}}
    result = await freqtrade_adapter.handle_tool_request(tool_args["tool_name"], tool_args["arguments"])

    assert isinstance(result, dict)
    assert result.get("status") == "success"
    assert result.get("trades") == [{"id": "trade1", "pair": "BTC/USDT"}]
    freqtrade_adapter.client.get.assert_called_once_with("http://localhost:8080/api/v1/trade_history", params={"limit": 100})

@pytest.mark.asyncio
async def test_execute_tool_get_open_orders_success(freqtrade_adapter):
    """Prueba la ejecución exitosa de la herramienta 'get_open_orders'."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"orders": [{"id": "order1", "pair": "ETH/USDT"}]}
    mock_response.raise_for_status.return_value = None
    freqtrade_adapter.client.get.return_value = mock_response

    tool_args = {"tool_name": "get_open_orders", "arguments": {}}
    result = await freqtrade_adapter.handle_tool_request(tool_args["tool_name"], tool_args["arguments"])

    assert isinstance(result, dict)
    assert result.get("status") == "success"
    assert result.get("orders") == [{"id": "order1", "pair": "ETH/USDT"}]
    freqtrade_adapter.client.get.assert_called_once_with("http://localhost:8080/api/v1/open_orders", params=None)

@pytest.mark.asyncio
async def test_execute_tool_send_telegram_message_success(freqtrade_adapter):
    """Prueba la ejecución exitosa de la herramienta 'send_telegram_message'."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"message": "Message sent"}
    mock_response.raise_for_status.return_value = None
    freqtrade_adapter.client.post.return_value = mock_response

    tool_args = {"tool_name": "send_telegram_message", "arguments": {"message": "Test message"}}
    result = await freqtrade_adapter.handle_tool_request(tool_args["tool_name"], tool_args["arguments"])

    assert isinstance(result, dict)
    assert result.get("status") == "success"
    assert result.get("message") == "Message sent"
    freqtrade_adapter.client.post.assert_called_once_with(
        "http://localhost:8080/api/v1/send_telegram_message", # Corregido el endpoint
        json={"message": "Test message"}
    )
