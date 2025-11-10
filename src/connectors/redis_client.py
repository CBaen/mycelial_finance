# src/connectors/redis_client.py
import redis
import json
import logging
import threading
from config.settings import REDIS_HOST, REDIS_PORT

class RedisClient:
    """
    Implements the 'Nervous System' (Part 4.2) of our Mycelial network.
    Handles all Redis Pub/Sub communication, serializing and deserializing
    messages (Python dicts <-> JSON strings) for the agents.
    """
    def __init__(self):
        try:
            self.connection = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0, decode_responses=False)
            self.connection.ping()
            # No longer creating a shared pubsub object - each subscriber gets its own
            logging.info(f"RedisClient connected to {REDIS_HOST}:{REDIS_PORT}")
        except Exception as e:
            logging.error(f"Failed to connect to Redis: {e}")
            self.connection = None

    def publish_message(self, channel: str, message: dict):
        """
        Publishes a Python dictionary as a JSON string to a Redis channel.
        """
        if not self.connection:
            logging.error("Redis not connected. Message not published.")
            return
        try:
            json_message = json.dumps(message)
            self.connection.publish(channel, json_message)
            logging.debug(f"Published to {channel}: {json_message}")
        except Exception as e:
            logging.error(f"Error publishing to {channel}: {e}")

    def subscribe(self, channel: str, callback_function):
        """
        Subscribes to a channel and runs the callback function for each message.
        This must run in a non-blocking background thread.
        Each subscription gets its own isolated pubsub object (private mailbox).
        """
        if not self.connection:
            logging.error("Redis connection not initialized. Cannot subscribe.")
            return

        def _listener_thread():
            # Create a new, isolated pubsub object for this subscriber
            pubsub = self.connection.pubsub(ignore_subscribe_messages=True)

            try:
                pubsub.subscribe(channel)
                logging.info(f"Subscribed to Redis channel: {channel}")
                for message in pubsub.listen():
                    try:
                        # Deserialize the JSON message back into a Python dict
                        data = json.loads(message['data'])
                        # Pass the dict to the agent's callback
                        callback_function(data)
                    except Exception as e:
                        logging.warning(f"Error processing message from {channel}: {e} | Data: {message['data']}")
            except redis.ConnectionError:
                logging.error(f"Redis connection lost in listener thread for {channel}. Stopping.")
            except Exception as e:
                logging.error(f"Unhandled error in listener thread for {channel}: {e}")
            finally:
                # Clean up: close the pubsub connection to prevent memory leaks
                try:
                    pubsub.close()
                    logging.debug(f"Closed pubsub connection for {channel}")
                except Exception as e:
                    logging.warning(f"Error closing pubsub for {channel}: {e}")

        # Start the listener in a daemon thread so it doesn't block
        thread = threading.Thread(target=_listener_thread, daemon=True)
        thread.start()
        logging.info(f"Subscription listener thread started for {channel}.")
