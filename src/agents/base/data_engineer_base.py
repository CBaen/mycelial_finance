# src/agents/base/data_engineer_base.py - PHASE 3.3: DataEngineer Base Class
import logging
import time
from typing import Dict, Optional, Any
from abc import ABC, abstractmethod
from ..base_agent import MycelialAgent


class DataEngineerBase(MycelialAgent, ABC):
    """
    PHASE 3.3: Base class for all Data Engineer agents (Data Moat agents)

    Extracts common patterns from:
    - DataMinerAgent (Market data moat)
    - RepoScrapeAgent (Code moat)
    - LogisticsMinerAgent (Logistics moat)
    - GovtDataMinerAgent (Government moat)
    - CorpDataMinerAgent (Corporate moat)

    Common functionality:
    - Channel-based communication pattern
    - Data caching with configurable intervals
    - Rate limiting to avoid excessive API calls
    - Standardized message publishing
    - Error handling and logging
    """

    def __init__(
        self,
        model,
        target: str,
        channel_prefix: str,
        agent_name_prefix: str,
        fetch_interval: int = 60,
        cache_enabled: bool = True
    ):
        """
        Initialize a Data Engineer agent

        Args:
            model: MycelialModel instance
            target: Target parameter (pair, region, sector, language, etc.)
            channel_prefix: Redis channel prefix (e.g., "market-data", "code-data")
            agent_name_prefix: Agent name prefix for logging
            fetch_interval: Minimum seconds between data fetches (default: 60)
            cache_enabled: Whether to cache and reuse data (default: True)
        """
        super().__init__(model)

        # Core configuration
        self.target = target
        self.channel_prefix = channel_prefix
        self.channel = f"{channel_prefix}:{target}"
        self.name = f"{agent_name_prefix}_{self.unique_id}"

        # Caching and rate limiting
        self.fetch_interval = fetch_interval
        self.cache_enabled = cache_enabled
        self.last_fetch_time = 0
        self.cached_data: Optional[Dict] = None

        logging.info(
            f"[{self.name}] Initialized | Target: {target} | "
            f"Channel: {self.channel} | "
            f"Fetch interval: {fetch_interval}s | "
            f"Cache: {'enabled' if cache_enabled else 'disabled'}"
        )

    def step(self):
        """
        Standard step method with caching and rate limiting

        Orchestrates:
        1. Check if enough time has passed since last fetch
        2. Fetch new data or use cached data
        3. Publish data to Redis channel
        """
        try:
            current_time = time.time()

            # Rate limiting: check if we should fetch new data
            time_since_last_fetch = current_time - self.last_fetch_time

            if self.cache_enabled and time_since_last_fetch < self.fetch_interval:
                # Use cached data if available
                if self.cached_data:
                    self._publish_cached_data()
                    logging.debug(
                        f"[{self.name}] Using cached data "
                        f"(next fetch in {self.fetch_interval - time_since_last_fetch:.0f}s)"
                    )
                return

            # Fetch fresh data
            logging.debug(f"[{self.name}] Fetching fresh data for {self.target}...")
            data = self._fetch_data()

            if data:
                # Update cache
                if self.cache_enabled:
                    self.cached_data = data
                self.last_fetch_time = current_time

                # Publish to Redis
                self._publish_data(data)
            else:
                logging.warning(f"[{self.name}] No data returned from _fetch_data()")

        except Exception as e:
            logging.error(f"[{self.name}] Error in step: {e}")
            # On error, try to use cached data as fallback
            if self.cache_enabled and self.cached_data:
                logging.info(f"[{self.name}] Using cached data as fallback after error")
                self._publish_cached_data()

    @abstractmethod
    def _fetch_data(self) -> Optional[Dict]:
        """
        Fetch data from external source (API, simulation, etc.)

        Must be implemented by subclasses to provide moat-specific data fetching.

        Returns:
            dict: Enriched data dictionary with moat-specific features
                  Should NOT include standard message wrapping (source, timestamp)
            None: If data fetch failed

        Example return value:
        {
            "NoveltyScore": 7.5,
            "DependencyEntropy": 42.3,
            "Commits24h": 150,
            ...
        }
        """
        pass

    def _publish_data(self, data: Dict):
        """
        Publish enriched data to Redis channel

        Wraps the data in standard message format:
        - source: Agent identifier
        - timestamp: Unix timestamp
        - features: The enriched data

        Args:
            data: Enriched feature dictionary from _fetch_data()
        """
        message = {
            "source": self.name,
            "timestamp": time.time(),
            "features": data
        }

        self.publish(self.channel, message)

        logging.debug(
            f"[{self.name}] Published to {self.channel} | "
            f"Features: {len(data)} keys"
        )

    def _publish_cached_data(self):
        """
        Republish cached data to maintain signal continuity

        Useful when rate limiting prevents new fetches but downstream
        agents still need recent data.
        """
        if self.cached_data:
            self._publish_data(self.cached_data)

    def _ensure_feature_compatibility(self, data: Dict) -> Dict:
        """
        Ensure data dictionary has 'close' field for chart compatibility

        Many downstream agents expect a 'close' field for visualization.
        This helper ensures compatibility with existing dashboard code.

        Args:
            data: Feature dictionary

        Returns:
            data: Same dict with 'close' added if missing
        """
        if 'close' not in data and len(data) > 0:
            # Use first numeric value as 'close' proxy
            for key, value in data.items():
                if isinstance(value, (int, float)):
                    data['close'] = value
                    break

        return data

    def get_cache_status(self) -> Dict[str, Any]:
        """
        Get current cache status for debugging/monitoring

        Returns:
            dict: Cache statistics
        """
        return {
            "agent": self.name,
            "target": self.target,
            "cache_enabled": self.cache_enabled,
            "has_cached_data": self.cached_data is not None,
            "time_since_last_fetch": time.time() - self.last_fetch_time,
            "fetch_interval": self.fetch_interval,
            "next_fetch_in": max(0, self.fetch_interval - (time.time() - self.last_fetch_time))
        }
