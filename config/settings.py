# config/settings.py - Enhanced with PHASE 3.4: Centralized Configuration
import os
from dotenv import load_dotenv
import logging
import yaml
from pathlib import Path

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

# PHASE 3.2: GitHub API Token (for Code moat data)
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')

# Log a warning if critical keys are missing
if not KRAKEN_API_KEY or not KRAKEN_API_SECRET:
    logging.warning("Kraken API keys are not set. Trading functions will fail.")

if not GITHUB_TOKEN:
    logging.warning("GITHUB_TOKEN not set. RepoScrapeAgent will use simulated data.")


# =============================================================================
# PHASE 3.4: YAML Configuration Loader
# =============================================================================

class AgentConfig:
    """
    PHASE 3.4: Centralized configuration loader

    Loads agent_config.yaml and provides easy access to all system parameters.
    Supports environment-specific overrides (dev/prod/test).
    """

    def __init__(self, config_file='agent_config.yaml', environment=None):
        """
        Load configuration from YAML file

        Args:
            config_file: Name of config file (default: agent_config.yaml)
            environment: Optional environment override (dev/prod/test)
        """
        self.config_dir = Path(__file__).parent
        self.config_path = self.config_dir / config_file

        # Load base configuration
        if self.config_path.exists():
            with open(self.config_path, 'r') as f:
                self._config = yaml.safe_load(f)
            logging.info(f"[CONFIG] Loaded configuration from {config_file}")
        else:
            logging.warning(f"[CONFIG] Configuration file not found: {config_file} | Using defaults")
            self._config = {}

        # Load environment-specific overrides
        if environment:
            env_config_path = self.config_dir / f"agent_config.{environment}.yaml"
            if env_config_path.exists():
                with open(env_config_path, 'r') as f:
                    env_overrides = yaml.safe_load(f)
                    self._merge_config(env_overrides)
                logging.info(f"[CONFIG] Applied {environment} environment overrides")

    def _merge_config(self, overrides):
        """Recursively merge override config into base config"""
        def merge_dict(base, override):
            for key, value in override.items():
                if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                    merge_dict(base[key], value)
                else:
                    base[key] = value

        merge_dict(self._config, overrides)

    def get(self, path, default=None):
        """
        Get configuration value by dot-separated path

        Examples:
            config.get('trading.fees.trading_fee_pct')  # Returns 0.26
            config.get('risk_management.probation.level_1_threshold')  # Returns -5.0
        """
        keys = path.split('.')
        value = self._config

        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default

        return value

    def get_section(self, section):
        """Get entire configuration section as dict"""
        return self._config.get(section, {})

    @property
    def trading(self):
        """Trading configuration section"""
        return self.get_section('trading')

    @property
    def risk_management(self):
        """Risk management configuration section"""
        return self.get_section('risk_management')

    @property
    def consensus(self):
        """Consensus configuration section"""
        return self.get_section('consensus')

    @property
    def prospecting(self):
        """Prospecting configuration section"""
        return self.get_section('prospecting')

    @property
    def technical_analysis(self):
        """Technical analysis configuration section"""
        return self.get_section('technical_analysis')

    @property
    def data_moats(self):
        """Data moats configuration section"""
        return self.get_section('data_moats')

    @property
    def builder(self):
        """Builder agent configuration section"""
        return self.get_section('builder')

    @property
    def database(self):
        """Database configuration section"""
        return self.get_section('database')

    @property
    def error_recovery(self):
        """Error recovery configuration section"""
        return self.get_section('error_recovery')

    @property
    def agent_lifecycle(self):
        """Agent lifecycle configuration section"""
        return self.get_section('agent_lifecycle')


# Create global config instance
try:
    # Detect environment from ENV variable
    ENV = os.getenv('APP_ENV', None)  # e.g., 'dev', 'prod', 'test'
    CONFIG = AgentConfig(environment=ENV)
except Exception as e:
    logging.error(f"[CONFIG] Failed to load agent configuration: {e}")
    CONFIG = None
