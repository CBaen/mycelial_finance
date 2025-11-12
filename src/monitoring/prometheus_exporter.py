# src/monitoring/prometheus_exporter.py - PHASE 4.3: Prometheus Metrics Exporter
"""
PHASE 4.3: Prometheus Metrics Exporter for Mycelial Finance

Exposes system and business metrics in Prometheus format for monitoring and alerting.

Metrics Categories:
- System Health: CPU, memory, Redis connectivity
- Agent Metrics: Active agents, consensus rate, deployments
- Trading Metrics: P&L, active assets, trade count, win rate
- Data Moat Metrics: Signal quality, API health
"""

import logging
import time
import psutil
from typing import Dict, Optional
from prometheus_client import Counter, Gauge, Histogram, Info, generate_latest, CONTENT_TYPE_LATEST
from prometheus_client import start_http_server
import redis


# =============================================================================
# SYSTEM METRICS
# =============================================================================

# CPU and Memory
system_cpu_percent = Gauge('mycelial_system_cpu_percent', 'CPU usage percentage')
system_memory_percent = Gauge('mycelial_system_memory_percent', 'Memory usage percentage')
system_memory_bytes = Gauge('mycelial_system_memory_bytes', 'Memory usage in bytes')

# Redis connectivity
redis_connection_status = Gauge('mycelial_redis_connection_status', '1 if connected, 0 if disconnected')
redis_used_memory_bytes = Gauge('mycelial_redis_used_memory_bytes', 'Redis memory usage in bytes')
redis_connected_clients = Gauge('mycelial_redis_connected_clients', 'Number of Redis connected clients')
redis_total_keys = Gauge('mycelial_redis_total_keys', 'Total number of keys in Redis')

# SQLite database
database_size_bytes = Gauge('mycelial_database_size_bytes', 'SQLite database size in bytes')

# =============================================================================
# AGENT METRICS
# =============================================================================

# Active agents
active_agents_total = Gauge('mycelial_active_agents_total', 'Total number of active agents')
active_agents_by_type = Gauge('mycelial_active_agents_by_type', 'Active agents by type', ['agent_type'])

# Agent lifecycle
agents_spawned_total = Counter('mycelial_agents_spawned_total', 'Total agents spawned', ['agent_type'])
agents_stopped_total = Counter('mycelial_agents_stopped_total', 'Total agents stopped', ['agent_type'])

# Consensus
consensus_reached_total = Counter('mycelial_consensus_reached_total', 'Total consensus events', ['team_type'])
consensus_rate = Gauge('mycelial_consensus_rate', 'Consensus success rate (last hour)')

# Builder Agent
deployments_attempted_total = Counter('mycelial_deployments_attempted_total', 'Total deployment attempts')
deployments_successful_total = Counter('mycelial_deployments_successful_total', 'Total successful deployments')
deployments_rejected_total = Counter('mycelial_deployments_rejected_total', 'Total rejected deployments', ['reason'])

# =============================================================================
# TRADING METRICS
# =============================================================================

# Assets
active_assets_total = Gauge('mycelial_active_assets_total', 'Number of active trading assets')
hibernated_assets_total = Gauge('mycelial_hibernated_assets_total', 'Number of hibernated assets')

# P&L
cumulative_pnl_percent = Gauge('mycelial_cumulative_pnl_percent', 'Cumulative P&L percentage', ['asset'])
cumulative_pnl_usd = Gauge('mycelial_cumulative_pnl_usd', 'Cumulative P&L in USD', ['asset'])

# Trades
trades_executed_total = Counter('mycelial_trades_executed_total', 'Total trades executed', ['asset', 'direction'])
trade_execution_duration_seconds = Histogram('mycelial_trade_execution_duration_seconds',
                                             'Trade execution duration in seconds', ['asset'])

# Win rate
win_rate_percent = Gauge('mycelial_win_rate_percent', 'Win rate percentage', ['asset'])

# Probation status
probation_level = Gauge('mycelial_probation_level', 'Probation level (0=normal, 1=level1, 2=level2)', ['asset'])

# =============================================================================
# DATA MOAT METRICS
# =============================================================================

# Signal quality
moat_signal_quality = Gauge('mycelial_moat_signal_quality', 'Data moat signal quality score', ['moat_type'])
moat_last_update_timestamp = Gauge('mycelial_moat_last_update_timestamp', 'Last update timestamp for moat', ['moat_type'])

# API health
moat_api_calls_total = Counter('mycelial_moat_api_calls_total', 'Total API calls', ['moat_type'])
moat_api_errors_total = Counter('mycelial_moat_api_errors_total', 'Total API errors', ['moat_type'])
moat_api_latency_seconds = Histogram('mycelial_moat_api_latency_seconds', 'API latency in seconds', ['moat_type'])

# Cross-moat signals
cross_moat_signals_detected = Counter('mycelial_cross_moat_signals_detected',
                                      'Cross-moat signals detected', ['asset', 'moat_type'])

# =============================================================================
# APPLICATION INFO
# =============================================================================

app_info = Info('mycelial_app', 'Application information')


# =============================================================================
# METRICS COLLECTOR
# =============================================================================

class PrometheusMetricsCollector:
    """
    PHASE 4.3: Collects and exposes metrics for Prometheus scraping

    Usage:
        collector = PrometheusMetricsCollector(redis_client, model)
        collector.start_http_server(port=9090)

        # In agent code:
        collector.record_trade('XXBTZUSD', 'BUY', pnl_pct=2.5)
        collector.record_consensus('HFT')
    """

    def __init__(self, redis_client=None, model=None, database_path='mycelial_ledger.db'):
        """
        Initialize metrics collector

        Args:
            redis_client: RedisClient instance (optional)
            model: MycelialModel instance (optional)
            database_path: Path to SQLite database
        """
        self.redis_client = redis_client
        self.model = model
        self.database_path = database_path

        # Set application info
        app_info.info({
            'version': '1.0.0',
            'phase': '4.3',
            'name': 'Mycelial Finance'
        })

        logging.info("[PROMETHEUS] Metrics collector initialized")

    def start_http_server(self, port=9090):
        """
        Start Prometheus HTTP server to expose metrics

        Args:
            port: Port to listen on (default: 9090)
        """
        start_http_server(port)
        logging.info(f"[PROMETHEUS] HTTP server started on port {port}")
        logging.info(f"[PROMETHEUS] Metrics available at http://localhost:{port}/metrics")

    def collect_system_metrics(self):
        """Collect system health metrics"""
        try:
            # CPU
            cpu_percent = psutil.cpu_percent(interval=1)
            system_cpu_percent.set(cpu_percent)

            # Memory
            memory = psutil.virtual_memory()
            system_memory_percent.set(memory.percent)
            system_memory_bytes.set(memory.used)

            # Database size
            try:
                import os
                if os.path.exists(self.database_path):
                    db_size = os.path.getsize(self.database_path)
                    database_size_bytes.set(db_size)
            except Exception as e:
                logging.debug(f"[PROMETHEUS] Error getting database size: {e}")

        except Exception as e:
            logging.error(f"[PROMETHEUS] Error collecting system metrics: {e}")

    def collect_redis_metrics(self):
        """Collect Redis metrics"""
        if not self.redis_client:
            return

        try:
            # Connection status
            try:
                self.redis_client.connection.ping()
                redis_connection_status.set(1)

                # Get Redis info
                info = self.redis_client.connection.info()

                # Memory usage
                redis_used_memory_bytes.set(info.get('used_memory', 0))

                # Connected clients
                redis_connected_clients.set(info.get('connected_clients', 0))

                # Total keys (approximate using DBSIZE)
                total_keys = self.redis_client.connection.dbsize()
                redis_total_keys.set(total_keys)

            except Exception:
                redis_connection_status.set(0)

        except Exception as e:
            logging.error(f"[PROMETHEUS] Error collecting Redis metrics: {e}")

    def collect_agent_metrics(self):
        """Collect agent metrics from Redis"""
        if not self.redis_client:
            return

        try:
            # Count agents by type
            agent_types = ['DataMiner', 'TechnicalAnalyst', 'PatternLearner',
                          'MarketExplorer', 'Builder', 'Trading']

            total_agents = 0
            for agent_type in agent_types:
                pattern = f"agent:{agent_type}:*"
                keys = list(self.redis_client.connection.scan_iter(match=pattern, count=100))
                count = len(keys)
                active_agents_by_type.labels(agent_type=agent_type).set(count)
                total_agents += count

            active_agents_total.set(total_agents)

        except Exception as e:
            logging.error(f"[PROMETHEUS] Error collecting agent metrics: {e}")

    def collect_trading_metrics(self):
        """Collect trading metrics"""
        if not self.model:
            return

        try:
            # Active assets
            if hasattr(self.model, 'active_assets'):
                active_count = len(self.model.active_assets)
                active_assets_total.set(active_count)

        except Exception as e:
            logging.error(f"[PROMETHEUS] Error collecting trading metrics: {e}")

    def collect_all_metrics(self):
        """Collect all metrics"""
        self.collect_system_metrics()
        self.collect_redis_metrics()
        self.collect_agent_metrics()
        self.collect_trading_metrics()

    # =========================================================================
    # RECORDING METHODS (called by agents)
    # =========================================================================

    def record_trade(self, asset: str, direction: str, pnl_pct: float = None,
                    execution_time: float = None):
        """Record a trade execution"""
        trades_executed_total.labels(asset=asset, direction=direction).inc()

        if pnl_pct is not None:
            cumulative_pnl_percent.labels(asset=asset).set(pnl_pct)

        if execution_time is not None:
            trade_execution_duration_seconds.labels(asset=asset).observe(execution_time)

    def record_consensus(self, team_type: str):
        """Record a consensus event"""
        consensus_reached_total.labels(team_type=team_type).inc()

    def record_agent_spawn(self, agent_type: str):
        """Record agent spawning"""
        agents_spawned_total.labels(agent_type=agent_type).inc()

    def record_agent_stop(self, agent_type: str):
        """Record agent stopping"""
        agents_stopped_total.labels(agent_type=agent_type).inc()

    def record_deployment(self, success: bool, rejection_reason: str = None):
        """Record deployment attempt"""
        deployments_attempted_total.inc()

        if success:
            deployments_successful_total.inc()
        else:
            reason = rejection_reason or 'unknown'
            deployments_rejected_total.labels(reason=reason).inc()

    def record_moat_api_call(self, moat_type: str, success: bool, latency: float = None):
        """Record data moat API call"""
        moat_api_calls_total.labels(moat_type=moat_type).inc()

        if not success:
            moat_api_errors_total.labels(moat_type=moat_type).inc()

        if latency is not None:
            moat_api_latency_seconds.labels(moat_type=moat_type).observe(latency)

    def record_cross_moat_signal(self, asset: str, moat_type: str):
        """Record cross-moat signal detection"""
        cross_moat_signals_detected.labels(asset=asset, moat_type=moat_type).inc()

    def update_probation_level(self, asset: str, level: int):
        """Update asset probation level"""
        probation_level.labels(asset=asset).set(level)

    def update_win_rate(self, asset: str, win_rate: float):
        """Update asset win rate"""
        win_rate_percent.labels(asset=asset).set(win_rate * 100)

    def update_moat_signal_quality(self, moat_type: str, quality: float):
        """Update moat signal quality score"""
        moat_signal_quality.labels(moat_type=moat_type).set(quality)
        moat_last_update_timestamp.labels(moat_type=moat_type).set(time.time())


# =============================================================================
# BACKGROUND METRICS COLLECTION
# =============================================================================

def start_metrics_collection_loop(collector: PrometheusMetricsCollector, interval: int = 30):
    """
    Start background thread for periodic metrics collection

    Args:
        collector: PrometheusMetricsCollector instance
        interval: Collection interval in seconds (default: 30)
    """
    import threading

    def collection_loop():
        while True:
            try:
                collector.collect_all_metrics()
            except Exception as e:
                logging.error(f"[PROMETHEUS] Error in collection loop: {e}")

            time.sleep(interval)

    thread = threading.Thread(target=collection_loop, daemon=True)
    thread.start()
    logging.info(f"[PROMETHEUS] Metrics collection loop started (interval: {interval}s)")


# =============================================================================
# MAIN - Example Usage
# =============================================================================

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Initialize collector
    collector = PrometheusMetricsCollector()

    # Start HTTP server
    collector.start_http_server(port=9090)

    # Start background collection
    start_metrics_collection_loop(collector, interval=30)

    print("Prometheus metrics available at http://localhost:9090/metrics")
    print("Press Ctrl+C to stop...")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down...")
