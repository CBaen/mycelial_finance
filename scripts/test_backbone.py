# scripts/test_backbone.py
import sys
import os
import time
import logging

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.connectors.redis_client import RedisClient

# Set up basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# This callback function simulates what an agent will do
def handle_test_message(message: dict):
    """Callback function to process a received message."""
    logging.info(f"[Receiver] Got message! Data: {message}")

def run_test():
    logging.info("--- Starting Redis Backbone Test ---")

    # Create two "agents" (clients)
    publisher_client = RedisClient()
    subscriber_client = RedisClient()

    if not publisher_client.connection or not subscriber_client.connection:
        logging.error("Failed to connect to Redis. Test aborted.")
        return

    # Define the channel
    test_channel = "mycelial-test-channel"

    # 2. The subscriber listens
    # This is non-blocking and starts a background thread
    subscriber_client.subscribe(test_channel, handle_test_message)

    logging.info(f"[Subscriber] Listening on '{test_channel}'...")
    time.sleep(1) # Give the subscriber thread a second to start

    # 1. The publisher sends a message
    test_message = {"sender": "Publisher", "content": "Hello Mycelium!", "timestamp": time.time()}
    logging.info(f"[Publisher] Sending message: {test_message}")
    publisher_client.publish_message(test_channel, test_message)

    # Wait to ensure the message is received
    time.sleep(2)
    logging.info("--- Test Complete ---")

if __name__ == "__main__":
    run_test()
