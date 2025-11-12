# src/connectors/redis_client.py
import redis
import json
import logging
import threading
import time
from config.settings import REDIS_HOST, REDIS_PORT

class RedisClient:
    """
    Implements the 'Nervous System' (Part 4.2) of our Mycelial network.
    Handles all Redis Pub/Sub communication, serializing and deserializing
    messages (Python dicts <-> JSON strings) for the agents.

    PHASE 2.4: Added error recovery with exponential backoff and reconnection logic.
    """
    def __init__(self):
        self.host = REDIS_HOST
        self.port = REDIS_PORT
        self.connection = None
        self.connection_lock = threading.Lock()
        self.max_retries = 5
        self.base_delay = 1.0  # seconds

        # Initial connection with retry logic
        self._connect_with_retry()

    def _connect_with_retry(self):
        """
        PHASE 2.4: Connect to Redis with exponential backoff retry logic

        Retry schedule:
        - Attempt 1: Immediate
        - Attempt 2: 1s delay
        - Attempt 3: 2s delay
        - Attempt 4: 4s delay
        - Attempt 5: 8s delay
        """
        for attempt in range(self.max_retries):
            try:
                with self.connection_lock:
                    self.connection = redis.Redis(
                        host=self.host,
                        port=self.port,
                        db=0,
                        decode_responses=False,
                        socket_connect_timeout=5,
                        socket_keepalive=True,
                        health_check_interval=30
                    )
                    self.connection.ping()
                    logging.info(f"[REDIS] Connected to {self.host}:{self.port}")
                    return True

            except redis.ConnectionError as e:
                delay = self.base_delay * (2 ** attempt)
                logging.warning(
                    f"[REDIS] Connection attempt {attempt + 1}/{self.max_retries} failed: {e} | "
                    f"Retrying in {delay}s..."
                )
                if attempt < self.max_retries - 1:
                    time.sleep(delay)
                else:
                    logging.error(f"[REDIS] Failed to connect after {self.max_retries} attempts")
                    self.connection = None
                    return False

            except Exception as e:
                logging.error(f"[REDIS] Unexpected error during connection: {e}")
                self.connection = None
                return False

    def _ensure_connection(self) -> bool:
        """
        PHASE 2.4: Check connection health and reconnect if needed

        Returns:
            True if connected, False if connection failed
        """
        try:
            if self.connection:
                self.connection.ping()
                return True
        except (redis.ConnectionError, redis.TimeoutError):
            logging.warning("[REDIS] Connection lost, attempting reconnection...")
            return self._connect_with_retry()
        except Exception as e:
            logging.error(f"[REDIS] Health check failed: {e}")
            return False

        # No connection exists
        logging.warning("[REDIS] No active connection, attempting to connect...")
        return self._connect_with_retry()

    def publish_message(self, channel: str, message: dict):
        """
        PHASE 2.4: Publishes a Python dictionary as a JSON string to a Redis channel.
        Now includes automatic reconnection on failure.
        """
        if not self._ensure_connection():
            logging.error("[REDIS] Cannot publish - connection unavailable")
            return

        try:
            json_message = json.dumps(message)
            self.connection.publish(channel, json_message)
            logging.debug(f"[REDIS] Published to {channel}: {json_message[:100]}...")
        except (redis.ConnectionError, redis.TimeoutError) as e:
            logging.error(f"[REDIS] Connection error publishing to {channel}: {e}")
            # Attempt reconnection for next operation
            self._ensure_connection()
        except Exception as e:
            logging.error(f"[REDIS] Error publishing to {channel}: {e}")

    def subscribe(self, channel: str, callback_function):
        """
        PHASE 2.4: Subscribes to a channel and runs the callback function for each message.
        Now includes automatic reconnection on connection loss.

        This must run in a non-blocking background thread.
        Each subscription gets its own isolated pubsub object (private mailbox).
        """
        if not self._ensure_connection():
            logging.error(f"[REDIS] Cannot subscribe to {channel} - connection unavailable")
            return

        def _listener_thread():
            retry_delay = 1.0
            max_retry_delay = 60.0

            while True:  # Auto-reconnect loop
                try:
                    # Ensure connection before creating pubsub
                    if not self._ensure_connection():
                        logging.error(f"[REDIS] Failed to connect for {channel}, retrying in {retry_delay}s...")
                        time.sleep(retry_delay)
                        retry_delay = min(retry_delay * 2, max_retry_delay)
                        continue

                    # Create a new, isolated pubsub object for this subscriber
                    pubsub = self.connection.pubsub(ignore_subscribe_messages=True)
                    pubsub.subscribe(channel)
                    logging.info(f"[REDIS] Subscribed to channel: {channel}")

                    # Reset retry delay on successful connection
                    retry_delay = 1.0

                    # Listen for messages
                    for message in pubsub.listen():
                        try:
                            # Deserialize the JSON message back into a Python dict
                            data = json.loads(message['data'])
                            # Pass the dict to the agent's callback
                            callback_function(data)
                        except json.JSONDecodeError as e:
                            logging.warning(f"[REDIS] Invalid JSON from {channel}: {e}")
                        except Exception as e:
                            logging.warning(f"[REDIS] Error processing message from {channel}: {e}")

                except redis.ConnectionError as e:
                    logging.error(
                        f"[REDIS] Connection lost for {channel}: {e} | "
                        f"Reconnecting in {retry_delay}s..."
                    )
                    try:
                        pubsub.close()
                    except:
                        pass
                    time.sleep(retry_delay)
                    retry_delay = min(retry_delay * 2, max_retry_delay)

                except Exception as e:
                    logging.error(f"[REDIS] Unhandled error in listener for {channel}: {e}")
                    try:
                        pubsub.close()
                    except:
                        pass
                    time.sleep(retry_delay)
                    retry_delay = min(retry_delay * 2, max_retry_delay)

        # Start the listener in a daemon thread so it doesn't block
        thread = threading.Thread(target=_listener_thread, daemon=True)
        thread.start()
        logging.info(f"[REDIS] Subscription listener thread started for {channel}")
