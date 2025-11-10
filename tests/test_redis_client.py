"""
Mycelial Finance - Redis Client Unit Tests
Based on Research Document: Part 4.2 (Three-Layer Redis Architecture)

Unit tests for the RedisClient connector.
Tests all three layers of the Redis backbone.

Run with: pytest tests/test_redis_client.py
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from src.connectors.redis_client import RedisClient


class TestRedisClient:
    """Unit tests for RedisClient"""

    @pytest.fixture
    def mock_redis(self):
        """Create a mock Redis connection"""
        with patch('src.connectors.redis_client.Redis') as mock:
            mock_conn = MagicMock()
            mock.return_value = mock_conn
            mock_conn.ping.return_value = True
            yield mock_conn

    @pytest.fixture
    def redis_client(self, mock_redis):
        """Create a RedisClient instance with mocked connection"""
        client = RedisClient(
            host="localhost",
            port=6379,
            db=0,
            password=None
        )
        client.redis_conn = mock_redis
        return client

    def test_initialization(self, redis_client):
        """Test client initializes correctly"""
        assert redis_client.host == "localhost"
        assert redis_client.port == 6379
        assert redis_client.db == 0

    def test_connection_test(self, redis_client, mock_redis):
        """Test connection test method"""
        mock_redis.ping.return_value = True
        assert redis_client.test_connection() is True

        mock_redis.ping.side_effect = Exception("Connection failed")
        assert redis_client.test_connection() is False

    # ========================================================================
    # LAYER 1: REDIS STREAMS TESTS
    # ========================================================================

    def test_create_consumer_group(self, redis_client, mock_redis):
        """Test creating a consumer group for streams"""
        mock_redis.xgroup_create.return_value = True

        result = redis_client.create_stream_consumer_group(
            "test_stream",
            "test_group"
        )

        assert result is True
        mock_redis.xgroup_create.assert_called_once()

    def test_write_to_stream(self, redis_client, mock_redis):
        """Test writing data to Redis Stream"""
        mock_redis.xadd.return_value = "1234567890-0"

        message_id = redis_client.write_to_stream(
            "test_stream",
            {"type": "trade", "price": 50000.0}
        )

        assert message_id == "1234567890-0"
        mock_redis.xadd.assert_called_once()

    def test_read_from_stream(self, redis_client, mock_redis):
        """Test reading from Redis Stream"""
        mock_redis.xreadgroup.return_value = [
            [
                "test_stream",
                [
                    ["1234567890-0", {"type": "trade", "price": "50000.0"}]
                ]
            ]
        ]

        messages = redis_client.read_from_stream(
            "test_stream",
            "test_group",
            "consumer1"
        )

        assert len(messages) == 1
        assert messages[0]["type"] == "trade"
        mock_redis.xreadgroup.assert_called_once()

    def test_acknowledge_message(self, redis_client, mock_redis):
        """Test acknowledging stream message"""
        mock_redis.xack.return_value = 1

        result = redis_client.acknowledge_message(
            "test_stream",
            "test_group",
            "1234567890-0"
        )

        assert result is True
        mock_redis.xack.assert_called_once()

    # ========================================================================
    # LAYER 2: REDIS PUB/SUB TESTS
    # ========================================================================

    def test_publish_message(self, redis_client, mock_redis):
        """Test publishing message to Pub/Sub channel"""
        mock_redis.publish.return_value = 3  # 3 subscribers

        num_subscribers = redis_client.publish_message(
            "test_channel",
            {"type": "policy_update", "version": 2}
        )

        assert num_subscribers == 3
        mock_redis.publish.assert_called_once()

    # ========================================================================
    # LAYER 3: KEY-VALUE TESTS
    # ========================================================================

    def test_set_agent_state(self, redis_client, mock_redis):
        """Test saving agent state to Redis"""
        mock_redis.set.return_value = True

        state_data = {
            "agent_id": 1,
            "balance": 10000.0,
            "active": True
        }

        result = redis_client.set_agent_state(1, state_data)

        assert result is True
        mock_redis.set.assert_called_once()

    def test_get_agent_state(self, redis_client, mock_redis):
        """Test retrieving agent state from Redis"""
        mock_state = '{"agent_id": 1, "balance": 10000.0, "active": true}'
        mock_redis.get.return_value = mock_state

        state = redis_client.get_agent_state(1)

        assert state is not None
        assert state["agent_id"] == 1
        assert state["balance"] == 10000.0
        mock_redis.get.assert_called_once()

    def test_get_agent_state_not_found(self, redis_client, mock_redis):
        """Test retrieving non-existent agent state"""
        mock_redis.get.return_value = None

        state = redis_client.get_agent_state(999)

        assert state is None

    def test_delete_agent_state(self, redis_client, mock_redis):
        """Test deleting agent state"""
        mock_redis.delete.return_value = 1

        result = redis_client.delete_agent_state(1)

        assert result is True
        mock_redis.delete.assert_called_once()

    def test_set_value(self, redis_client, mock_redis):
        """Test setting generic key-value"""
        mock_redis.set.return_value = True

        result = redis_client.set_value("test:key", {"data": "value"})

        assert result is True
        mock_redis.set.assert_called_once()

    def test_get_value(self, redis_client, mock_redis):
        """Test getting generic value"""
        mock_redis.get.return_value = '{"data": "value"}'

        value = redis_client.get_value("test:key")

        assert value is not None
        assert value["data"] == "value"

    def test_set_value_with_ttl(self, redis_client, mock_redis):
        """Test setting value with TTL"""
        mock_redis.setex.return_value = True

        result = redis_client.set_value("test:key", {"data": "value"}, ttl=3600)

        assert result is True
        mock_redis.setex.assert_called_once()

    def test_is_json_utility(self):
        """Test JSON detection utility method"""
        assert RedisClient._is_json('{"key": "value"}') is True
        assert RedisClient._is_json('not json') is False
        assert RedisClient._is_json('[1, 2, 3]') is True
