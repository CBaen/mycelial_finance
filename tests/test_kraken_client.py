"""
Mycelial Finance - Kraken Client Unit Tests
Based on Research Document: Part 6.1 (Kraken Pro Interface)

Unit tests for the KrakenClient connector.
Uses mock data to test functionality without requiring live API access.

Run with: pytest tests/test_kraken_client.py
"""

import pytest
from unittest.mock import Mock, patch
from src.connectors.kraken_client import KrakenClient


class TestKrakenClient:
    """Unit tests for KrakenClient"""

    @pytest.fixture
    def kraken_client(self):
        """Create a KrakenClient instance for testing"""
        return KrakenClient(
            api_key="test_key",
            api_secret="test_secret",
            api_url="https://api.kraken.com",
            tier="pro"
        )

    def test_initialization(self, kraken_client):
        """Test client initializes with correct parameters"""
        assert kraken_client.api_key == "test_key"
        assert kraken_client.api_secret == "test_secret"
        assert kraken_client.tier == "pro"
        assert kraken_client.rate_limit_threshold == 180
        assert kraken_client.rate_limit_decay == 3.75

    def test_initialization_intermediate_tier(self):
        """Test initialization with intermediate tier"""
        client = KrakenClient(
            api_key="test_key",
            api_secret="test_secret",
            tier="intermediate"
        )
        assert client.rate_limit_threshold == 125
        assert client.rate_limit_decay == 2.34

    def test_get_ticker(self, kraken_client):
        """Test getting ticker data"""
        ticker = kraken_client.get_ticker("XBTUSD")

        assert ticker is not None
        assert "pair" in ticker
        assert "bid" in ticker
        assert "ask" in ticker
        assert ticker["pair"] == "XBTUSD"

    def test_get_orderbook(self, kraken_client):
        """Test getting order book data"""
        orderbook = kraken_client.get_orderbook("XBTUSD", depth=10)

        assert orderbook is not None
        assert "bids" in orderbook
        assert "asks" in orderbook
        assert len(orderbook["bids"]) > 0
        assert len(orderbook["asks"]) > 0

    def test_place_limit_order(self, kraken_client):
        """Test placing a limit order"""
        order = kraken_client.place_limit_order(
            side="buy",
            pair="XBTUSD",
            volume=1.0,
            price=50000.0,
            post_only=True
        )

        assert order is not None
        assert order["side"] == "buy"
        assert order["volume"] == 1.0
        assert order["price"] == 50000.0
        assert order["post_only"] is True

    def test_place_limit_order_invalid_side(self, kraken_client):
        """Test that invalid order side raises error"""
        order = kraken_client.place_limit_order(
            side="invalid",
            pair="XBTUSD",
            volume=1.0,
            price=50000.0
        )

        assert order is None

    def test_place_limit_order_negative_volume(self, kraken_client):
        """Test that negative volume raises error"""
        order = kraken_client.place_limit_order(
            side="buy",
            pair="XBTUSD",
            volume=-1.0,
            price=50000.0
        )

        assert order is None

    def test_place_market_order(self, kraken_client):
        """Test placing a market order"""
        order = kraken_client.place_market_order(
            side="sell",
            pair="XBTUSD",
            volume=0.5
        )

        assert order is not None
        assert order["side"] == "sell"
        assert order["volume"] == 0.5
        assert order["type"] == "market"

    def test_get_balance(self, kraken_client):
        """Test getting account balance"""
        balance = kraken_client.get_balance()

        assert balance is not None
        assert "USD" in balance
        assert "XBT" in balance

    def test_get_open_orders(self, kraken_client):
        """Test getting open orders"""
        orders = kraken_client.get_open_orders()

        assert orders is not None
        assert isinstance(orders, list)

    def test_cancel_order(self, kraken_client):
        """Test canceling an order"""
        result = kraken_client.cancel_order("ORDER_12345")

        assert result is True

    def test_rate_limit_counter_management(self, kraken_client):
        """Test that rate limit counter is managed correctly"""
        initial_counter = kraken_client.rate_limit_counter

        # Make a request
        kraken_client.get_ticker("XBTUSD")

        # Counter should have increased
        assert kraken_client.rate_limit_counter > initial_counter
