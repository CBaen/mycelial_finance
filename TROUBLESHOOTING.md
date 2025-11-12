# Mycelial Finance - Troubleshooting Guide

This guide covers common issues, error messages, and recovery procedures for the Mycelial Finance trading system.

---

## Table of Contents
1. [System Startup Issues](#1-system-startup-issues)
2. [Import Errors](#2-import-errors)
3. [Database Problems](#3-database-problems)
4. [Kraken API Issues](#4-kraken-api-issues)
5. [Redis Connection Problems](#5-redis-connection-problems)
6. [Agent Failures](#6-agent-failures)
7. [Learning Loop Issues](#7-learning-loop-issues)
8. [Performance Problems](#8-performance-problems)
9. [Emergency Procedures](#9-emergency-procedures)
10. [Diagnostic Commands](#10-diagnostic-commands)

---

## 1. System Startup Issues

### Issue: `ModuleNotFoundError: No module named 'src'`

**Symptoms:**
```
ModuleNotFoundError: No module named 'src'
```

**Cause:** Python path not configured correctly

**Solution:**
```bash
# Option 1: Run from project root
cd C:\Users\camer\OneDrive\Desktop\Trading Bot\mycelial_finance
python test_system.py

# Option 2: Add to PYTHONPATH
set PYTHONPATH=%PYTHONPATH%;C:\Users\camer\OneDrive\Desktop\Trading Bot\mycelial_finance
python test_system.py
```

---

### Issue: `ImportError: No module named 'mesa'`

**Symptoms:**
```
ImportError: No module named 'mesa'
```

**Cause:** Dependencies not installed

**Solution:**
```bash
pip install -r requirements.txt
```

---

### Issue: System hangs on startup

**Symptoms:**
- No output after "Initializing..."
- Terminal frozen

**Possible Causes:**
1. Redis not running
2. Kraken API not responding
3. Database lock

**Solution:**
```bash
# 1. Check Redis
redis-cli ping
# Should return: PONG

# 2. Check database locks
del trades.db-journal
del mycelial_patterns.db-journal

# 3. Restart system
python test_system.py
```

---

## 2. Import Errors

### Issue: `No module named 'storage'`

**Symptoms:**
```
WARNING - [LEARNING-LOOP] Components not available: No module named 'storage'
```

**Cause:** Missing `src.` prefix in imports

**Solution:**
Check the following files have correct imports:

**File:** `src/agents/trading_agent.py`
```python
# CORRECT:
from src.storage.trade_database import TradeDatabase
from src.storage.chroma_client import ChromaDBClient
from src.agents.memory_agent import MemoryAgent

# INCORRECT:
from storage.trade_database import TradeDatabase  # Missing src.
from agents.memory_agent import MemoryAgent       # Missing src.
```

---

### Issue: `No module named 'kraken'`

**Symptoms:**
```
ModuleNotFoundError: No module named 'kraken'
```

**Cause:** Kraken SDK not installed

**Solution:**
```bash
pip install python-kraken-sdk>=2.0.0
```

---

### Issue: `No module named 'redis'`

**Symptoms:**
```
ModuleNotFoundError: No module named 'redis'
```

**Cause:** Redis library not installed

**Solution:**
```bash
pip install redis>=5.0.0
```

---

## 3. Database Problems

### Issue: `trades.db` has no tables

**Symptoms:**
```python
sqlite3.OperationalError: no such table: trades
```

**Cause:** TradeDatabase not initialized

**Diagnosis:**
```bash
python -c "import sqlite3; conn = sqlite3.connect('trades.db'); c = conn.cursor(); c.execute('SELECT name FROM sqlite_master WHERE type=\"table\"'); print('Tables:', [row[0] for row in c.fetchall()]); conn.close()"
```

**If output is `Tables: []`:**

**Solution:**
1. Verify `src/core/model.py` has TradeDatabase initialization:
```python
from src.storage.trade_database import TradeDatabase
# ... in __init__:
self.trade_db = TradeDatabase("./trades.db")
```

2. Delete empty database and restart:
```bash
del trades.db
python test_system.py
```

---

### Issue: `database is locked`

**Symptoms:**
```
sqlite3.OperationalError: database is locked
```

**Cause:** Multiple processes accessing database OR previous crash left lock file

**Solution:**
```bash
# 1. Close all Python processes
taskkill /F /IM python.exe

# 2. Delete journal files
del trades.db-journal
del mycelial_patterns.db-journal

# 3. Restart
python test_system.py
```

---

### Issue: ChromaDB collection errors

**Symptoms:**
```
ValueError: Collection 'trading_patterns' does not exist
```

**Cause:** ChromaDB not properly initialized

**Solution:**
```bash
# 1. Delete ChromaDB directory
rmdir /S /Q chroma_db

# 2. Restart system (will recreate)
python test_system.py
```

---

## 4. Kraken API Issues

### Issue: `name 'KrakenException' is not defined`

**Symptoms:**
```
ERROR - [KRAKEN] Failed to fetch market data for MATICUSD: name 'KrakenException' is not defined
```

**Cause:** Trying to catch non-existent exception class

**Solution:**
**File:** `src/connectors/kraken_client.py`
```python
# CORRECT:
except (KrakenAuthenticationError, KrakenBadRequestError,
        KrakenRateLimitExceededError, KrakenServiceUnavailableError) as e:
    # ... error handling

# INCORRECT:
except KrakenException as e:  # This class doesn't exist!
```

---

### Issue: Authentication Error

**Symptoms:**
```
ERROR - [KRAKEN] Auth error (not retrying): KrakenAuthenticationError
```

**Cause:** Invalid API credentials

**Solution:**
1. Check `.env` file:
```
KRAKEN_API_KEY=your_actual_key_here
KRAKEN_API_SECRET=your_actual_secret_here
```

2. Verify credentials at https://www.kraken.com/u/settings/api

3. Restart system

---

### Issue: Rate Limit Exceeded

**Symptoms:**
```
ERROR - [KRAKEN] Error: KrakenRateLimitExceededError
```

**Cause:** Too many API requests

**Solution:**
System automatically retries with exponential backoff. If persistent:

1. Reduce agent count:
**File:** `test_system.py`
```python
# Reduce from 18 to 10 pairs
pairs_to_trade = [
    "XXBTZUSD", "XETHZUSD", "SOLUSD", "ADAUSD", "DOTUSD",
    "UNIUSD", "LINKUSD", "AAVEUSD", "ATOMUSD", "ALGOUSD"
]
```

2. Upgrade Kraken account to Pro tier for higher limits

---

### Issue: Service Unavailable

**Symptoms:**
```
ERROR - [KRAKEN] Error: KrakenServiceUnavailableError
```

**Cause:** Kraken API temporarily down

**Solution:**
System automatically retries. Check Kraken status:
```bash
curl https://status.kraken.com/api/v2/status.json
```

If persistent downtime, wait for Kraken to resolve.

---

## 5. Redis Connection Problems

### Issue: `ConnectionError: Error -1 connecting to localhost:6379`

**Symptoms:**
```
redis.exceptions.ConnectionError: Error -1 connecting to localhost:6379
```

**Cause:** Redis server not running

**Solution (Windows):**
```bash
# 1. Check if Redis is installed
where redis-server

# 2. Start Redis
redis-server

# 3. Verify connection
redis-cli ping
# Should return: PONG
```

**Solution (Linux/WSL):**
```bash
# Start Redis
sudo service redis-server start

# Verify
redis-cli ping
```

---

### Issue: Redis pub/sub not receiving messages

**Symptoms:**
- Agents start but no messages logged
- Pattern learners not receiving market data

**Diagnosis:**
```bash
# Monitor Redis channels
redis-cli
> PSUBSCRIBE *
# Should see messages flowing
```

**Solution:**
1. Verify Redis is running: `redis-cli ping`
2. Check agent listeners are registered:
```python
# In agent logs, look for:
INFO - [Agent_123] Registered listener on channel: market-data:XXBTZUSD
```

3. Restart system if listeners not registered

---

## 6. Agent Failures

### Issue: Agent crashes during execution

**Symptoms:**
```
ERROR - [PatternLearner_45] Exception in step(): ...
```

**Diagnosis:**
Check logs for full traceback

**Solution:**
1. Identify failing agent from logs
2. Check agent's data sources (market data, Redis channels)
3. Verify agent configuration in `config/agent_config.yaml`
4. If persistent, disable agent temporarily:
```python
# In src/core/model.py, comment out:
# learner = PatternLearnerAgent(self, ...)
```

---

### Issue: No pattern discoveries

**Symptoms:**
- System runs but `mycelial_patterns.db` stays empty
- No `mycelial-trade-ideas` messages

**Diagnosis:**
```bash
# Check pattern count
python -c "import sqlite3; conn = sqlite3.connect('mycelial_patterns.db'); c = conn.cursor(); c.execute('SELECT COUNT(*) FROM patterns'); print(f'Patterns: {c.fetchone()[0]}'); conn.close()"
```

**Possible Causes:**
1. Market data not flowing (check DataMiner agents)
2. Pattern thresholds too high (agents not finding patterns)
3. Redis connection issues

**Solution:**
1. Check market data:
```bash
redis-cli
> SUBSCRIBE market-data:XXBTZUSD
# Should see OHLCV data flowing
```

2. Lower pattern thresholds (temporarily for testing):
**File:** `src/agents/pattern_learner_agent.py`
```python
# Lower threshold
self.pattern_threshold = 0.1  # Was: 0.5
```

---

### Issue: No trades executed

**Symptoms:**
- System runs, patterns discovered, but no trades logged
- `trades.db` is empty

**Diagnosis:**
```bash
# Check if trades.db has schema
python -c "import sqlite3; conn = sqlite3.connect('trades.db'); c = conn.cursor(); c.execute('SELECT name FROM sqlite_master WHERE type=\"table\"'); print('Tables:', [row[0] for row in c.fetchall()]); conn.close()"
```

**If no tables:** See Section 3 (Database Problems)

**If tables exist but no trades:**

**Possible Causes:**
1. No signal collisions (mycelial and baseline not agreeing)
2. TradingAgent not receiving messages
3. Learning loop not initialized

**Solution:**
1. Check for signal collisions in logs:
```
INFO - [Trader_1] Signal COLLISION detected for XXBTZUSD
```

2. Verify TradingAgent is listening:
```bash
redis-cli
> SUBSCRIBE mycelial-trade-ideas
> SUBSCRIBE baseline-trade-ideas
# Should see signals from both channels
```

3. Check learning loop status:
```
INFO - [Trader_1] BIG ROCK 45: Learning Loop activated
```

If not activated, check import errors (Section 2)

---

## 7. Learning Loop Issues

### Issue: `[LEARNING-LOOP] Components not available`

**Symptoms:**
```
WARNING - [LEARNING-LOOP] Components not available: No module named 'storage'
```

**Cause:** Import path errors

**Solution:** See Section 2 (Import Errors)

---

### Issue: MemoryAgent not processing trades

**Symptoms:**
- Trades logged to `trades.db`
- But ChromaDB collections remain empty

**Diagnosis:**
```python
# Check ChromaDB contents
python -c "from src.storage.chroma_client import ChromaDBClient; client = ChromaDBClient('./chroma_db'); for col in client.client.list_collections(): print(f'{col.name}: {col.count()} items')"
```

**Solution:**
1. Verify MemoryAgent is created:
```python
# In TradingAgent __init__, look for:
self.memory_agent = MemoryAgent(...)
```

2. Check for MemoryAgent errors in logs:
```
ERROR - [MemoryAgent] ...
```

3. If persistent, check ChromaDB version:
```bash
pip install --upgrade chromadb>=0.4.0
```

---

## 8. Performance Problems

### Issue: System is very slow

**Symptoms:**
- Each step takes >1 second
- High CPU usage

**Possible Causes:**
1. Too many agents (121 is a lot!)
2. Database writes blocking
3. Redis message queue backlog

**Solution:**
1. **Reduce agent count** (for testing):
```python
# In test_system.py
model = MycelialModel(
    pairs_to_trade=pairs_to_trade[:5],  # Only 5 pairs instead of 18
    num_swarm_agents=50,  # 50 instead of 100
)
```

2. **Monitor system resources:**
```bash
# Windows Task Manager: Ctrl+Shift+Esc
# Check Python CPU and memory usage
```

3. **Check Redis queue length:**
```bash
redis-cli
> INFO stats
# Look for: instantaneous_ops_per_sec
```

---

### Issue: Memory usage grows unbounded

**Symptoms:**
- Python process memory increases over time
- System eventually crashes with MemoryError

**Cause:** Memory leak in pattern storage or agent state

**Solution:**
1. **Enable pattern decay** (should be default):
```python
# In PatternLearnerAgent, verify:
self.pattern_decay_enabled = True
```

2. **Limit pattern archive size:**
```python
# In model.py, add periodic cleanup:
if self.step_counter % 10000 == 0:
    # Clean old patterns
    self.db_cursor.execute('DELETE FROM patterns WHERE age_minutes > 1440')  # 24 hours
    self.db_connection.commit()
```

3. **Restart system periodically** during long runs

---

### Issue: Database writes are slow

**Symptoms:**
```
WARNING - [SQL] Write queue backlog: 500+ items
```

**Cause:** Too many writes, single-threaded bottleneck

**Solution:**
System uses thread-safe write queue (PHASE 2.2). If persistent:

1. **Reduce write frequency:**
```python
# In PatternLearnerAgent, increase threshold:
self.archive_threshold = 0.8  # Only archive very high-value patterns
```

2. **Batch writes:**
```python
# In model.py, increase batch size:
self.db_batch_size = 100  # Write 100 at a time
```

---

## 9. Emergency Procedures

### Emergency Shutdown

**When to use:** System behaving erratically, need immediate stop

**Method 1: Redis Control Channel**
```bash
redis-cli PUBLISH system-control '{"command": "shutdown", "reason": "emergency"}'
```

**Method 2: Kill Process**
```bash
# Windows
taskkill /F /IM python.exe

# Linux
pkill -9 python
```

---

### Data Recovery After Crash

**Scenario:** System crashed, databases may be corrupt

**Procedure:**
```bash
# 1. Check for journal files
dir *.db-journal

# 2. If present, databases may be recovering
# Wait 30 seconds, then check again

# 3. If journals persist, manual recovery:
del trades.db-journal
del mycelial_patterns.db-journal

# 4. Verify database integrity
python -c "import sqlite3; conn = sqlite3.connect('trades.db'); conn.execute('PRAGMA integrity_check'); print('OK'); conn.close()"

# 5. If corrupt, restore from backup (if available)
copy trades.db.backup trades.db

# 6. If no backup, delete and restart fresh
del trades.db
```

---

### Reset to Clean State

**When to use:** System completely broken, need fresh start

**Warning:** This deletes all data!

```bash
# 1. Stop system
taskkill /F /IM python.exe

# 2. Delete databases
del trades.db
del mycelial_patterns.db
rmdir /S /Q chroma_db

# 3. Clear Redis
redis-cli FLUSHALL

# 4. Reinstall dependencies
pip install --force-reinstall -r requirements.txt

# 5. Restart
python test_system.py
```

---

## 10. Diagnostic Commands

### Quick System Health Check
```bash
# All-in-one diagnostic
python -c "
import sys
import sqlite3
import redis
try:
    # Check imports
    import mesa
    import kraken.spot
    from src.storage.trade_database import TradeDatabase
    print('✓ Imports OK')

    # Check Redis
    r = redis.Redis(host='localhost', port=6379)
    r.ping()
    print('✓ Redis OK')

    # Check databases
    conn1 = sqlite3.connect('trades.db')
    conn2 = sqlite3.connect('mycelial_patterns.db')
    print('✓ Databases OK')

    # Check ChromaDB
    import chromadb
    client = chromadb.PersistentClient(path='./chroma_db')
    print('✓ ChromaDB OK')

    print('\n✅ System healthy!')
except Exception as e:
    print(f'❌ Error: {e}')
    sys.exit(1)
"
```

---

### Check Agent Count
```bash
# From running system logs
findstr /C:"Registered agent" test_output.log | find /C /V ""
```

---

### Monitor Redis Traffic
```bash
redis-cli --stat
# Shows ops/sec, hit rate, memory usage
```

---

### Check Database Sizes
```bash
dir *.db
# Look at file sizes
```

---

### View Recent Patterns
```bash
python -c "import sqlite3; conn = sqlite3.connect('mycelial_patterns.db'); c = conn.cursor(); c.execute('SELECT agent_id, timestamp, pattern_value, moat FROM patterns ORDER BY created_at DESC LIMIT 10'); for row in c.fetchall(): print(row); conn.close()"
```

---

### View Recent Trades
```bash
python -c "import sqlite3; conn = sqlite3.connect('trades.db'); c = conn.cursor(); c.execute('SELECT pair, entry_price, exit_price, pnl_pct, trade_result FROM trades ORDER BY created_at DESC LIMIT 10'); for row in c.fetchall(): print(row); conn.close()"
```

---

### Check Learning Loop Status
```bash
# From logs
findstr /C:"Learning Loop" test_output.log
# Should see: "BIG ROCK 45: Learning Loop activated"
```

---

### Monitor System Resources
```bash
# Windows
powershell "Get-Process python | Select-Object CPU, WorkingSet, ProcessName"

# Linux
ps aux | grep python
```

---

## Common Error Patterns & Quick Fixes

| Error Message | Quick Fix |
|---------------|-----------|
| `No module named 'X'` | `pip install -r requirements.txt` |
| `database is locked` | `del *.db-journal` + restart |
| `ConnectionError: redis` | Start Redis: `redis-server` |
| `KrakenException` not defined | Check `kraken_client.py` line 62 |
| `No such table: trades` | Delete `trades.db` and restart |
| `Learning Loop not available` | Fix imports in `trading_agent.py` |
| System hangs | Check Redis running: `redis-cli ping` |
| High CPU | Reduce agent count in `test_system.py` |
| No trades executing | Check for signal collisions in logs |

---

## Getting Help

1. **Check Logs:** `test_output.log` (if logging to file)
2. **Read Error Message:** Full traceback provides context
3. **Search This Guide:** Ctrl+F for error text
4. **Check AUDIT_REPORT.md:** Known issues and fixes
5. **Check ARCHITECTURE.md:** System design and data flow

---

## Preventive Maintenance

### Daily (During Active Development)
- [ ] Check log file size (delete if >100MB)
- [ ] Verify Redis is running
- [ ] Check database sizes (archive if >1GB)

### Weekly
- [ ] Review error logs for patterns
- [ ] Clean old patterns (>7 days)
- [ ] Backup databases to `backups/`
- [ ] Update dependencies: `pip install --upgrade -r requirements.txt`

### Monthly
- [ ] Full system reset and validation
- [ ] Review ChromaDB size and performance
- [ ] Analyze P&L trends (are we improving?)

---

**End of Troubleshooting Guide**

For architecture details, see `ARCHITECTURE.md`
For audit findings, see `AUDIT_REPORT.md`
For implementation status, see `IMPLEMENTATION_PROGRESS.md`
