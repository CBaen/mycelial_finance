# src/main.py
import time
import logging
from .core.model import MycelialModel
from config.settings import KRAKEN_API_KEY # Used to check config

def run_simulation():
    """
    Initializes and runs the MycelialModel.
    """
    if not KRAKEN_API_KEY:
        logging.critical("Kraken API keys not found in .env file.")
        logging.critical("Please create a .env file (from .env.example) and add your keys.")
        return

    logging.info("--- Starting Mycelial Finance System ---")

    # Define our simulation parameters
    pairs = ['XBT/USD', 'ETH/USD'] # Using Kraken's ticker pairs

    # Initialize the Model
    try:
        # We are intentionally using the defaults for num_traders=1 and num_risk_managers=1
        model = MycelialModel(pairs_to_trade=pairs)
    except Exception as e:
        logging.critical(f"Failed to initialize model: {e}")
        return

    # Run the simulation loop
    step_count = 0
    while model.running:
        try:
            logging.info(f"--- Model Step {step_count} ---")
            model.step()
            step_count += 1
            time.sleep(10) # Wait 10 seconds between "heartbeats"
        except KeyboardInterrupt:
            logging.info("--- Simulation stopped by user (KeyboardInterrupt) ---")
            model.running = False
        except Exception as e:
            logging.error(f"--- CRITICAL ERROR in run loop: {e} ---")
            model.running = False

    logging.info("--- Mycelial Finance System Halted ---")

if __name__ == "__main__":
    run_simulation()
