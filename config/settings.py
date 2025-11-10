# config/settings.py
import os
from dotenv import load_dotenv
import logging

# Set up basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load .env file
load_dotenv()

# Kraken API Credentials
KRAKEN_API_KEY = os.getenv('KRAKEN_API_KEY')
KRAKEN_API_SECRET = os.getenv('KRAKEN_API_SECRET')

# Redis Configuration
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))

# Log a warning if critical keys are missing
if not KRAKEN_API_KEY or not KRAKEN_API_SECRET:
    logging.warning("Kraken API keys are not set. Trading functions will fail.")
