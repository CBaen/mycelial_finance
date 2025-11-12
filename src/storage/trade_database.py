# src/storage/trade_database.py - BIG ROCK 45: Learning Loop Fix
"""
Trade Database: Persistent SQLite storage for all trading activity

Enables post-trade analysis and performance tracking by strategy type.
Complements ChromaDB (pattern storage) with structured trade logging.

Schema:
- Tracks every trade with full context (entry/exit, P&L, indicators, strategy)
- Queryable by pair, strategy_type, time range, agent_id
- Links to ChromaDB patterns via pattern_id
"""

import sqlite3
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from pathlib import Path


class TradeDatabase:
    """
    BIG ROCK 45: Persistent trade logging for learning loop

    Stores every completed trade with enough detail to:
    1. Analyze performance by strategy type (HFT, DAY, SWING)
    2. Link trades to ChromaDB patterns for similarity analysis
    3. Calculate win rates, P&L distributions, drawdowns
    4. Support future calibration of agent parameters
    """

    def __init__(self, db_path: str = "./trades.db"):
        """
        Initialize trade database

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row  # Enable column access by name
        self._create_tables()
        logging.info(f"[TRADE-DB] Database initialized at {db_path}")

    def _create_tables(self):
        """Create database schema if it doesn't exist"""
        cursor = self.conn.cursor()

        # Main trades table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                -- Trade Identification
                trade_id TEXT UNIQUE NOT NULL,
                pair TEXT NOT NULL,
                strategy_type TEXT NOT NULL,  -- 'GENERIC', 'HFT', 'DAY', 'SWING'
                agent_id TEXT NOT NULL,
                pattern_id TEXT,  -- Link to ChromaDB pattern

                -- Trade Lifecycle
                entry_timestamp TEXT NOT NULL,
                exit_timestamp TEXT NOT NULL,
                hold_duration_seconds INTEGER NOT NULL,

                -- Price Action
                entry_price REAL NOT NULL,
                exit_price REAL NOT NULL,
                price_change_pct REAL NOT NULL,

                -- Performance
                pnl_pct REAL NOT NULL,  -- Net P&L after fees/slippage
                pnl_absolute REAL NOT NULL,
                trade_result TEXT NOT NULL,  -- 'WIN' or 'LOSS'

                -- Technical Indicators at Entry
                rsi_entry REAL,
                macd_entry REAL,
                bb_position_entry REAL,
                volume_entry REAL,
                atr_entry REAL,

                -- Signal Context
                signal_source TEXT,  -- 'baseline', 'mycelial', 'synthesized'
                prediction_score REAL,
                cross_moat_score INTEGER,
                collision_detected BOOLEAN,

                -- Execution Details
                position_size REAL NOT NULL,
                fees_paid REAL NOT NULL,
                slippage_pct REAL NOT NULL,

                -- Metadata
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Indexes for common queries
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_pair ON trades(pair)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_strategy ON trades(strategy_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_agent ON trades(agent_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON trades(entry_timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_result ON trades(trade_result)")

        self.conn.commit()
        logging.info("[TRADE-DB] Tables created/verified")

    def store_trade(self, trade_data: Dict) -> str:
        """
        Store a completed trade in the database

        Args:
            trade_data: Dictionary containing all trade details

        Returns:
            trade_id of the stored trade
        """
        cursor = self.conn.cursor()

        # Generate unique trade ID
        trade_id = f"{trade_data['pair']}_{trade_data['entry_timestamp']}_{trade_data['agent_id']}"

        # Calculate derived fields
        hold_duration = (
            datetime.fromisoformat(trade_data['exit_timestamp']) -
            datetime.fromisoformat(trade_data['entry_timestamp'])
        ).total_seconds()

        price_change_pct = (
            (trade_data['exit_price'] - trade_data['entry_price']) /
            trade_data['entry_price'] * 100
        )

        trade_result = 'WIN' if trade_data['pnl_pct'] > 0 else 'LOSS'

        try:
            cursor.execute("""
                INSERT INTO trades (
                    trade_id, pair, strategy_type, agent_id, pattern_id,
                    entry_timestamp, exit_timestamp, hold_duration_seconds,
                    entry_price, exit_price, price_change_pct,
                    pnl_pct, pnl_absolute, trade_result,
                    rsi_entry, macd_entry, bb_position_entry, volume_entry, atr_entry,
                    signal_source, prediction_score, cross_moat_score, collision_detected,
                    position_size, fees_paid, slippage_pct
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                trade_id,
                trade_data['pair'],
                trade_data.get('strategy_type', 'GENERIC'),
                trade_data['agent_id'],
                trade_data.get('pattern_id'),
                trade_data['entry_timestamp'],
                trade_data['exit_timestamp'],
                int(hold_duration),
                trade_data['entry_price'],
                trade_data['exit_price'],
                price_change_pct,
                trade_data['pnl_pct'],
                trade_data.get('pnl_absolute', 0.0),
                trade_result,
                trade_data.get('rsi_entry'),
                trade_data.get('macd_entry'),
                trade_data.get('bb_position_entry'),
                trade_data.get('volume_entry'),
                trade_data.get('atr_entry'),
                trade_data.get('signal_source', 'unknown'),
                trade_data.get('prediction_score'),
                trade_data.get('cross_moat_score', 0),
                trade_data.get('collision_detected', False),
                trade_data.get('position_size', 0.001),
                trade_data.get('fees_paid', 0.0),
                trade_data.get('slippage_pct', 0.1)
            ))

            self.conn.commit()

            logging.info(
                f"[TRADE-DB] Stored trade | "
                f"ID: {trade_id} | "
                f"Result: {trade_result} | "
                f"P&L: {trade_data['pnl_pct']:+.2f}% | "
                f"Duration: {int(hold_duration)}s"
            )

            return trade_id

        except sqlite3.IntegrityError:
            logging.warning(f"[TRADE-DB] Duplicate trade ID: {trade_id}")
            return trade_id

    def get_trades_by_strategy(self, strategy_type: str, limit: int = 100) -> List[Dict]:
        """Get recent trades for a specific strategy"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM trades
            WHERE strategy_type = ?
            ORDER BY entry_timestamp DESC
            LIMIT ?
        """, (strategy_type, limit))

        return [dict(row) for row in cursor.fetchall()]

    def get_trades_by_pair(self, pair: str, limit: int = 100) -> List[Dict]:
        """Get recent trades for a specific trading pair"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM trades
            WHERE pair = ?
            ORDER BY entry_timestamp DESC
            LIMIT ?
        """, (pair, limit))

        return [dict(row) for row in cursor.fetchall()]

    def get_performance_stats(self, strategy_type: Optional[str] = None,
                             pair: Optional[str] = None) -> Dict:
        """
        Calculate performance statistics

        Args:
            strategy_type: Filter by strategy (optional)
            pair: Filter by pair (optional)

        Returns:
            Dictionary with win_rate, avg_pnl, total_trades, etc.
        """
        cursor = self.conn.cursor()

        # Build query with filters
        where_clauses = []
        params = []

        if strategy_type:
            where_clauses.append("strategy_type = ?")
            params.append(strategy_type)

        if pair:
            where_clauses.append("pair = ?")
            params.append(pair)

        where_sql = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""

        # Calculate statistics
        cursor.execute(f"""
            SELECT
                COUNT(*) as total_trades,
                SUM(CASE WHEN trade_result = 'WIN' THEN 1 ELSE 0 END) as wins,
                SUM(CASE WHEN trade_result = 'LOSS' THEN 1 ELSE 0 END) as losses,
                AVG(pnl_pct) as avg_pnl_pct,
                SUM(pnl_absolute) as total_pnl_absolute,
                MAX(pnl_pct) as best_trade_pct,
                MIN(pnl_pct) as worst_trade_pct,
                AVG(hold_duration_seconds) as avg_hold_duration_seconds
            FROM trades
            {where_sql}
        """, params)

        row = cursor.fetchone()

        if row['total_trades'] == 0:
            return {
                'total_trades': 0,
                'win_rate': 0.0,
                'avg_pnl_pct': 0.0,
                'total_pnl_absolute': 0.0,
                'best_trade_pct': 0.0,
                'worst_trade_pct': 0.0,
                'avg_hold_duration_seconds': 0
            }

        win_rate = row['wins'] / row['total_trades'] * 100

        return {
            'total_trades': row['total_trades'],
            'wins': row['wins'],
            'losses': row['losses'],
            'win_rate': win_rate,
            'avg_pnl_pct': row['avg_pnl_pct'],
            'total_pnl_absolute': row['total_pnl_absolute'],
            'best_trade_pct': row['best_trade_pct'],
            'worst_trade_pct': row['worst_trade_pct'],
            'avg_hold_duration_seconds': row['avg_hold_duration_seconds']
        }

    def get_recent_trades(self, limit: int = 50) -> List[Dict]:
        """Get most recent trades across all strategies"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM trades
            ORDER BY entry_timestamp DESC
            LIMIT ?
        """, (limit,))

        return [dict(row) for row in cursor.fetchall()]

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            logging.info("[TRADE-DB] Connection closed")


# =============================================================================
# EXAMPLE USAGE
# =============================================================================

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Initialize database
    db = TradeDatabase("./test_trades.db")

    # Example: Store a trade
    trade_data = {
        'pair': 'XXBTZUSD',
        'strategy_type': 'GENERIC',
        'agent_id': 'trading_agent_001',
        'pattern_id': 'pattern_12345',
        'entry_timestamp': '2024-01-15T10:30:00',
        'exit_timestamp': '2024-01-15T10:35:00',
        'entry_price': 43000.0,
        'exit_price': 43500.0,
        'pnl_pct': 1.16,  # After fees/slippage
        'pnl_absolute': 500.0,
        'rsi_entry': 65.0,
        'macd_entry': 1.2,
        'volume_entry': 5000000,
        'signal_source': 'synthesized',
        'cross_moat_score': 2,
        'collision_detected': True
    }

    trade_id = db.store_trade(trade_data)
    print(f"Stored trade: {trade_id}")

    # Get performance stats
    stats = db.get_performance_stats(strategy_type='GENERIC')
    print(f"\nPerformance Stats: {stats}")

    # Get recent trades
    recent = db.get_recent_trades(limit=10)
    print(f"\nRecent trades: {len(recent)}")

    db.close()
