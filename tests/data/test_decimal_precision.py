import pytest
from decimal import Decimal, getcontext
from src.domain.data_models import MarketDataUnified
from src.data.binance_transformer import BinanceTransformer
from src.data.mobula_transformer import MobulaTransformer

# Configurar la precisión global para Decimal
getcontext().prec = 28 # Precisión alta para asegurar exactitud en pruebas

@pytest.fixture(autouse=True)
def set_decimal_context():
    original_prec = getcontext().prec
    getcontext().prec = 28
    yield
    getcontext().prec = original_prec

from datetime import datetime

def test_market_data_unified_decimal_precision():
    data = MarketDataUnified(
        symbol="BTCUSDT",
        timestamp=datetime.fromtimestamp(1678886400),
        price=Decimal("60000.1234567890123456789"),
        volume=Decimal("1000.1234567890123456789"),
        quote_volume=Decimal("60000000.1234567890123456789"),
        high_price=Decimal("61000.1234567890123456789"),
        low_price=Decimal("59000.1234567890123456789"),
        open_price=Decimal("59500.1234567890123456789"),
        close_price=Decimal("60000.1234567890123456789"),
        bid_price=Decimal("60000.1234567890123456789"),
        bid_qty=Decimal("1.234567890123456789"),
        ask_price=Decimal("60001.9876543210987654321"),
        ask_qty=Decimal("0.987654321098765432"),
        source="Test",
        price_change_24h=None,
        price_change_percentage_24h=None,
        market_cap=None,
        rank=None,
        number_of_trades=None
    )
    assert data.price == Decimal("60000.1234567890123456789")
    assert isinstance(data.price, Decimal)
    assert data.bid_price == Decimal("60000.1234567890123456789")
    assert isinstance(data.bid_price, Decimal)
    assert data.ask_price == Decimal("60001.9876543210987654321")
    assert isinstance(data.ask_price, Decimal)

def test_binance_transformer_ticker_precision():
    binance_data = {
        "symbol": "BTCUSDT",
        "lastPrice": "60000.1234567890123456789",
        "volume": "1000.1234567890123456789",
        "quoteVolume": "60000000.1234567890123456789",
        "highPrice": "61000.1234567890123456789",
        "lowPrice": "59000.1234567890123456789",
        "openPrice": "59500.1234567890123456789",
        "bidPrice": "60000.1234567890123456789",
        "bidQty": "1.234567890123456789",
        "askPrice": "60001.9876543210987654321",
        "askQty": "0.987654321098765432",
        "priceChange": "100.0",
        "priceChangePercent": "0.1",
        "count": 1000,
        "closeTime": 1678886400000
    }
    transformer = BinanceTransformer()
    market_data = transformer.transform_ticker_24hr(binance_data)
    assert market_data.price == Decimal("60000.1234567890123456789")
    assert market_data.bid_price == Decimal("60000.1234567890123456789")
    assert market_data.ask_price == Decimal("60001.9876543210987654321")
    assert isinstance(market_data.price, Decimal)
    assert isinstance(market_data.bid_price, Decimal)
    assert isinstance(market_data.ask_price, Decimal)

def test_mobula_transformer_market_data_precision():
    mobula_data = {
        "last_updated": 1678886400000,
        "symbol": "ETH_USDT",
        "price": "3000.501234567890123456",
        "volume": "1000000.1234567890123456",
        "price_change_24h": 50.0,
        "price_change_percentage_24h": 1.5,
        "market_cap": 300000000000.0
    }
    transformer = MobulaTransformer()
    market_data = transformer.transform_market_data(mobula_data)
    assert market_data.price == Decimal("3000.501234567890123456")
    assert isinstance(market_data.price, Decimal)

def test_decimal_arithmetic_precision():
    a = Decimal("0.1234567890123456789012345678")
    b = Decimal("0.9876543210987654321098765432")

    # Suma
    sum_val = a + b
    expected_sum = Decimal("1.1111111101111111110111111110")
    assert sum_val == expected_sum

    # Resta
    sub_val = b - a
    expected_sub = Decimal("0.8641975320864197532086419754")
    assert sub_val == expected_sub

    # Multiplicación
    mul_val = a * b
    expected_mul = Decimal("0.1219326311370217952261850326") # Ajustado a 28 decimales de precisión
    assert mul_val == expected_mul

    # División
    div_val = b / a
    expected_div = Decimal("8.000000072900000663390006043") # Ajustado a 28 decimales de precisión
    assert div_val == expected_div

    assert isinstance(sum_val, Decimal)
    assert isinstance(sub_val, Decimal)
    assert isinstance(mul_val, Decimal)
    assert isinstance(div_val, Decimal)
