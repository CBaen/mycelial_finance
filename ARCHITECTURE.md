# Mycelial Finance - System Architecture

## Overview

Mycelial Finance is a 121-agent "Trifecta P&L" cryptocurrency trading engine built on the principles of **decentralized, peer-to-peer learning**. Unlike traditional hierarchical multi-agent systems, this architecture implements a "mycelial" network where agents collaborate directly through Redis pub/sub channels, creating a resilient, adaptive system with no single point of failure.

**Key Innovation:** Signal Collision Detection - trades are only executed when BOTH mycelial pattern discoveries AND technical analysis signals agree within a 5-second window, creating the highest-conviction "Trifecta" signal.

---

## System Components

### 1. Agent Architecture (121 Total Agents)

#### 1.1 Data Collection Layer (18 Agents)
**DataMinerAgent** - Market data collectors
- **Count:** 18 agents (one per trading pair)
- **Function:** Fetch real-time OHLCV data from Kraken API
- **Output:** Publishes to `market-data:{PAIR}` Redis channels
- **Pairs:** XXBTZUSD, XETHZUSD, SOLUSD, ADAUSD, DOTUSD, MATICUSD, UNIUSD, LINKUSD, DOGEUSD, AAVEUSD, ATOMUSD, ALGOUSD, XLMUSD, EOSUSD, TRXUSD, XTZUSD, NEARUSD, FILUSD

#### 1.2 Pattern Learning Layer (100 Agents)
**PatternLearnerAgent** - "SwarmBrains"
- **Count:** 100 agents distributed across 5 product moats
- **Distribution:**
  - Finance Moat: ~60 agents
  - Code Moat: ~10 agents
  - Logistics Moat: ~10 agents
  - Government Moat: ~10 agents
  - Corporations Moat: ~10 agents
- **Function:** Watch market data and cross-moat signals, discover causal patterns
- **Output:** Publishes trade ideas to `mycelial-trade-ideas` channel
- **Learning:** Archives high-value patterns to `mycelial_patterns.db`

#### 1.3 Multi-Moat Data Collection (5 Agents)
**Moat-Specific Miners**
- **RepoScrapeAgent** (1): GitHub trending repos (Code Moat)
- **LogisticsMinerAgent** (1): Supply chain signals (Logistics Moat)
- **GovtDataMinerAgent** (1): Policy/regulation signals (Government Moat)
- **CorpDataMinerAgent** (1): Corporate earnings/news (Corporations Moat)
- **Output:** Publishes to moat-specific Redis channels

#### 1.4 Technical Analysis Layer (Dynamically Deployed)
**TechnicalAnalysisAgent** - Competitive baseline
- **Count:** Deployed per-asset as needed by BuilderAgent
- **Function:** RSI, MACD, Bollinger Bands analysis
- **Output:** Publishes to `baseline-trade-ideas` channel
- **Purpose:** Provides competitive benchmark for swarm performance

#### 1.5 Market Explorer Teams (9 Agents)
**MarketExplorerAgent** - Opportunity discovery
- **Count:** 9 agents (3 teams of 3)
- **Teams:**
  - HFT Team (3 agents): <5min holding periods
  - Day-Trade Team (3 agents): 5min-24hr periods
  - Swing-Trade Team (3 agents): >24hr periods
- **Function:** Discover and qualify new trading opportunities
- **Output:** Asset recommendations to BuilderAgent

#### 1.6 Execution Layer (1 Agent)
**TradingAgent** - Signal collision detector
- **Count:** 1 agent
- **Function:**
  - Listens to BOTH `mycelial-trade-ideas` AND `baseline-trade-ideas`
  - Only executes when signals AGREE within 5-second window
  - Tracks 3 P&L streams: Baseline, Mycelial, Synthesized
- **Output:**
  - Logs trades to `trades.db`
  - Publishes confirmations to `trade-confirmations` channel

#### 1.7 Risk Governance Layer (1 Agent)
**RiskManagementAgent** - System guardian
- **Count:** 1 agent
- **Function:**
  - Monitors max drawdown (5% default)
  - Detects policy contagion (80% threshold)
  - Emergency shutdown capability
- **HAVEN Framework:** Lightweight coordination without hierarchy

#### 1.8 Autonomy Layer (1 Agent)
**BuilderAgent** - Dynamic deployment
- **Count:** 1 agent
- **Function:**
  - Deploys TechnicalAnalysisAgents for new assets
  - Manages active asset portfolio (max 15)
  - Responds to MarketExplorerAgent recommendations

#### 1.9 Collaboration Enforcement Layer (3 Agents)
**MycelialInstigatorAgent** - Rule of 3
- **Count:** 3 agents
- **Function:** Enforce collaborative pattern validation
- **Rule:** Patterns must be confirmed by ≥3 agents before publishing

#### 1.10 Quality Assurance Layer (3 Agents)
**DeepResearchAgent** - Redundant validation
- **Count:** 3 agents
- **Function:** Independently verify high-value patterns
- **Output:** Quality scores and validation flags

---

## 2. Data Flow Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                          KRAKEN API                                  │
│                      (18 Trading Pairs)                             │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     DATA COLLECTION LAYER                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │
│  │ DataMiner    │  │   RepoScrape │  │  Logistics   │  [+ 2 more]  │
│  │ (18 agents)  │  │   (1 agent)  │  │   (1 agent)  │             │
│  └──────────────┘  └──────────────┘  └──────────────┘             │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      REDIS PUB/SUB BACKBONE                          │
│  market-data:{PAIR}  │  repo-data:{LANG}  │  logistics-data:{REG}  │
│  govt-data:{REG}     │  corp-data:{SECTOR}                          │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                    ┌─────────────┴─────────────┐
                    ▼                           ▼
┌─────────────────────────────┐  ┌─────────────────────────────┐
│  PATTERN LEARNING LAYER     │  │  TECHNICAL ANALYSIS LAYER    │
│                             │  │                             │
│  ┌───────────────────────┐ │  │  ┌───────────────────────┐ │
│  │ PatternLearner (100)  │ │  │  │ TechnicalAnalysis (N) │ │
│  │ - Finance Moat (60)   │ │  │  │ - RSI, MACD, BB       │ │
│  │ - Code Moat (10)      │ │  │  │ - Per-asset deploy    │ │
│  │ - Logistics (10)      │ │  │  └───────────────────────┘ │
│  │ - Government (10)     │ │  │                             │
│  │ - Corporations (10)   │ │  └─────────────────────────────┘
│  └───────────────────────┘ │
│            │               │                  │
│            ▼               │                  │
│  ┌───────────────────────┐│                  │
│  │ mycelial_patterns.db  ││                  │
│  │   (12,293 patterns)   ││                  │
│  └───────────────────────┘│                  │
└─────────────────────────────┘                  │
                    │                           │
                    ▼                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    REDIS TRADE IDEA CHANNELS                         │
│          mycelial-trade-ideas  │  baseline-trade-ideas              │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      SIGNAL COLLISION DETECTION                      │
│                         (TradingAgent)                              │
│                                                                     │
│  ┌────────────────────────────────────────────────────────────────┐│
│  │  IF (Mycelial Signal) AND (Baseline Signal) within 5 seconds:  ││
│  │    → EXECUTE TRADE                                              ││
│  │    → Log to trades.db                                           ││
│  │    → Publish confirmation                                       ││
│  └────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────┘
                                  │
                    ┌─────────────┴─────────────┐
                    ▼                           ▼
┌─────────────────────────────┐  ┌─────────────────────────────┐
│      TRADES DATABASE        │  │     VECTOR DATABASE          │
│       (trades.db)           │  │      (ChromaDB)             │
│                             │  │                             │
│  - Trade history            │  │  - Pattern embeddings       │
│  - P&L tracking             │  │  - Semantic search          │
│  - Strategy performance     │  │  - Knowledge retrieval      │
└─────────────────────────────┘  └─────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        LEARNING LOOP                                 │
│                       (MemoryAgent)                                 │
│                                                                     │
│  Completed Trade → Extract Features → Store in ChromaDB            │
│                  → Update Agent Knowledge                           │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 3. Five-Moat Product Architecture

The system is designed to generate value from **5 distinct product moats**, not just cryptocurrency trading:

### Moat 1: Finance (Primary)
- **Data Source:** Kraken API (18 crypto pairs)
- **Agents:** 60 PatternLearners + 18 DataMiners
- **Product:** Cryptocurrency trading signals

### Moat 2: Code
- **Data Source:** GitHub trending repositories
- **Agents:** 10 PatternLearners + 1 RepoScraper
- **Product:** Early detection of technology trends that may impact crypto valuations

### Moat 3: Logistics
- **Data Source:** Supply chain disruption signals
- **Agents:** 10 PatternLearners + 1 LogisticsMiner
- **Product:** Macro supply chain indicators correlated with crypto volatility

### Moat 4: Government/Policy
- **Data Source:** Regulatory announcements, policy changes
- **Agents:** 10 PatternLearners + 1 GovtDataMiner
- **Product:** Regulatory risk signals for crypto markets

### Moat 5: Corporations
- **Data Source:** Corporate earnings, tech sector news
- **Agents:** 10 PatternLearners + 1 CorpDataMiner
- **Product:** Institutional adoption signals

**Cross-Moat Correlation:** Pattern learners in non-finance moats publish signals that finance-focused learners can use for causal pattern discovery.

---

## 4. Redis Communication Architecture

### Channel Structure

#### Market Data Channels
```
market-data:XXBTZUSD    → Bitcoin price/volume data
market-data:XETHZUSD    → Ethereum price/volume data
[... 16 more pairs]
```

#### Cross-Moat Signal Channels
```
repo-data:Python        → Python repository trends
logistics-data:US-West  → US West Coast logistics
govt-data:US-Federal    → Federal policy signals
corp-data:Tech          → Tech sector corporate data
```

#### Trade Idea Channels
```
mycelial-trade-ideas    → Pattern discoveries from swarm
baseline-trade-ideas    → Technical analysis signals
```

#### Control Channels
```
system-control          → Emergency shutdown messages
trade-confirmations     → Executed trade logs
synthesized-trade-log   → Synthesized (collision) trades
```

---

## 5. Database Schema

### 5.1 mycelial_patterns.db (SQLite)

**Purpose:** Archive high-value patterns discovered by swarm

```sql
CREATE TABLE patterns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_id INTEGER NOT NULL,
    timestamp REAL NOT NULL,
    pattern_value REAL NOT NULL,
    raw_features TEXT NOT NULL,        -- JSON
    age_minutes REAL NOT NULL,
    decay_factor REAL NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    moat TEXT DEFAULT 'Finance',       -- Finance, Code, Logistics, Government, Corporations
    product TEXT DEFAULT 'Unknown',
    signal_type TEXT DEFAULT 'market-data'
);
```

**Current Status:** 12,293 patterns archived

### 5.2 trades.db (SQLite)

**Purpose:** Log all executed trades for learning loop

```sql
CREATE TABLE trades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trade_id TEXT UNIQUE NOT NULL,
    pair TEXT NOT NULL,
    strategy_type TEXT NOT NULL,           -- 'GENERIC', 'HFT', 'DAY', 'SWING'
    agent_id TEXT NOT NULL,
    pattern_id TEXT,
    entry_timestamp TEXT NOT NULL,
    exit_timestamp TEXT NOT NULL,
    hold_duration_seconds INTEGER NOT NULL,
    entry_price REAL NOT NULL,
    exit_price REAL NOT NULL,
    price_change_pct REAL NOT NULL,
    pnl_pct REAL NOT NULL,
    pnl_absolute REAL NOT NULL,
    trade_result TEXT NOT NULL,            -- 'WIN' or 'LOSS'
    rsi_entry REAL,
    macd_entry REAL,
    bb_position_entry REAL,
    volume_entry REAL,
    atr_entry REAL,
    signal_source TEXT,
    prediction_score REAL,
    cross_moat_score INTEGER,
    collision_detected BOOLEAN,
    position_size REAL NOT NULL,
    fees_paid REAL NOT NULL,
    slippage_pct REAL NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

**Current Status:** Schema initialized on system startup

### 5.3 chroma_db/ (ChromaDB Vector Store)

**Purpose:** Semantic storage and retrieval of trading patterns

**Collections:**
- `trading_patterns`: Successful trade patterns
- `failed_patterns`: Failed trades for avoidance learning
- `agent_knowledge`: Agent-specific learned behaviors

---

## 6. Learning Loop Architecture

The "Big Rock 45" learning loop enables the system to improve from experience:

```
1. Trade Execution (TradingAgent)
   ↓
2. Trade Logging (trades.db)
   ↓
3. Feature Extraction (MemoryAgent)
   ↓
4. Vector Embedding (ChromaDB)
   ↓
5. Knowledge Update (Agent retrieval)
   ↓
6. Improved Pattern Recognition (PatternLearner)
```

**Key Components:**
- **TradeDatabase:** Structured storage of all trades
- **ChromaDBClient:** Vector embeddings for semantic search
- **MemoryAgent:** Processes completed trades, extracts features, updates knowledge base

---

## 7. Trifecta P&L Tracking

The TradingAgent tracks THREE separate P&L streams:

### 7.1 Baseline P&L
- **Definition:** What we would earn if we traded EVERY technical analysis signal
- **Purpose:** Competitive benchmark

### 7.2 Mycelial P&L
- **Definition:** What we would earn if we traded EVERY pattern discovery signal
- **Purpose:** Measure swarm intelligence value

### 7.3 Synthesized P&L (THE PRODUCT)
- **Definition:** Actual trades executed (when BOTH signals agree)
- **Purpose:** The "Trifecta" - highest conviction trades
- **Hypothesis:** Synthesized P&L > Baseline P&L AND Synthesized P&L > Mycelial P&L

---

## 8. HAVEN Framework (Risk Governance)

Lightweight coordination layer without hierarchical brittleness:

**Components:**
1. **Max Drawdown Monitoring** (5% default)
2. **Policy Contagion Detection** (80% threshold)
3. **Emergency Shutdown Mechanism** (via `system-control` Redis channel)
4. **Regulatory Compliance Checks** (optional)

**Design Philosophy:** Coordination, not control. Agents remain autonomous but operate within system-level risk constraints.

---

## 9. Deployment Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                           HOST SYSTEM                                │
│                                                                     │
│  ┌────────────────────────────────────────────────────────────────┐│
│  │                    PYTHON RUNTIME                               ││
│  │                                                                 ││
│  │  ┌──────────────────────────────────────────────────────────┐ ││
│  │  │             MESA FRAMEWORK                                │ ││
│  │  │                                                           │ ││
│  │  │  ┌─────────────────────────────────────────────────────┐ │ ││
│  │  │  │      MycelialModel (src/core/model.py)             │ │ ││
│  │  │  │                                                     │ │ ││
│  │  │  │  - 121 Agent Instances                             │ │ ││
│  │  │  │  - Redis connections                               │ │ ││
│  │  │  │  - Database connections                            │ │ ││
│  │  │  └─────────────────────────────────────────────────────┘ │ ││
│  │  └──────────────────────────────────────────────────────────┘ ││
│  └─────────────────────────────────────────────────────────────────┘│
│                                                                     │
│  ┌────────────────────────────────────────────────────────────────┐│
│  │                   REDIS SERVER (localhost:6379)                ││
│  │  - Pub/Sub channels                                            ││
│  │  - Message routing                                             ││
│  └────────────────────────────────────────────────────────────────┘│
│                                                                     │
│  ┌────────────────────────────────────────────────────────────────┐│
│  │                    SQLITE DATABASES                            ││
│  │  - mycelial_patterns.db                                        ││
│  │  - trades.db                                                   ││
│  └────────────────────────────────────────────────────────────────┘│
│                                                                     │
│  ┌────────────────────────────────────────────────────────────────┐│
│  │                   CHROMADB VECTOR STORE                        ││
│  │  ./chroma_db/                                                  ││
│  └────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
                        ┌──────────────────┐
                        │   KRAKEN API     │
                        │ (External HTTP)  │
                        └──────────────────┘
```

---

## 10. Key Design Principles

### 10.1 Decentralization ("Mycelial")
- No central orchestrator
- No single point of failure
- Peer-to-peer agent communication via Redis

### 10.2 Emergent Intelligence
- No top-down macro-strategy
- Bottom-up pattern discovery
- Collective behavior emerges from local interactions

### 10.3 Signal Collision = Conviction
- Trades only when mycelial AND baseline agree
- Reduces false positives
- Creates highest-confidence "Trifecta" signal

### 10.4 Multi-Moat Diversification
- Not just crypto trading
- Cross-domain signal integration
- Resilience through product diversity

### 10.5 Continuous Learning
- Every trade improves the system
- ChromaDB enables semantic pattern retrieval
- Failed trades teach avoidance

---

## 11. Performance Characteristics

### Latency Budget
- Kraken API roundtrip: ~50-200ms
- Redis pub/sub: <5ms
- Database write: <10ms
- Target: Sub-second trade execution

### Scalability
- 121 agents running concurrently
- Thread-safe database writes via queue
- Redis handles 100K+ messages/sec

### Fault Tolerance
- Redis connection retry with exponential backoff
- Graceful degradation on Kraken API failures
- Emergency shutdown mechanism

---

## 12. Entry Points

### Main Execution
```bash
python test_system.py       # 24-hour production test
python src/main.py          # Alternative entry point
```

### Dashboard
```bash
python dashboard.py         # Real-time monitoring dashboard
```

### Utilities
```bash
python scripts/check_db.py          # Verify database state
python scripts/migrate_patterns.py  # Pattern database migration
```

---

## 13. Configuration

### Environment Variables (.env)
```
KRAKEN_API_KEY=<your_key>
KRAKEN_API_SECRET=<your_secret>
REDIS_HOST=localhost
REDIS_PORT=6379
```

### System Parameters (config/agent_config.yaml)
- Agent counts per type
- Risk thresholds
- Trading pair configuration
- Moat targets

---

## 14. Monitoring & Observability

### Prometheus Metrics (monitoring/)
- Agent health status
- Trade execution rate
- P&L tracking (3 streams)
- Redis message throughput
- Database write latency

### Grafana Dashboards (monitoring/)
- Real-time agent population
- Pattern discovery rate
- Signal collision frequency
- System resource usage

---

## Questions & Support

For detailed implementation progress, see `IMPLEMENTATION_PROGRESS.md`
For troubleshooting common issues, see `TROUBLESHOOTING.md`
For audit findings and system state, see `AUDIT_REPORT.md`
