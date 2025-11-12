# 🍄 Mycelial Finance - Storytelling Dashboard & Memory Builder Guide

## What Is This?

You asked for a system that:
- **Talks to you like a friend** - no confusing technical jargon
- **Tells stories with data** - explains what's happening in plain English
- **Builds agent memory** - creates a knowledge base your AI can learn from

This guide explains the three new tools we've built for you.

---

## 🎯 Three New Tools

### 1. **Market Data Aggregator** (`src/connectors/market_data_aggregator.py`)
Combines three APIs to give your agents enriched market intelligence:
- **CoinMarketCap**: Market rankings, social sentiment, coin metadata
- **Twelve Data**: Technical indicators, forex correlations
- **Free Crypto API**: Real-time prices, backup data source

### 2. **Storytelling Dashboard** (`dashboard_storytelling.py`)
A friendly dashboard that explains crypto markets like a friend would:
- **Market Story**: "Hey! Here's what's happening right now..."
- **Coin Deep Dive**: Simple explanations of price, volume, trends
- **Agent Insights**: What your AI is thinking and learning
- **Memory Bank**: Historical patterns your agents have learned

### 3. **Memory Builder** (`run_memory_builder.py`)
Runs backtests and stores patterns in agent memory so they can learn from history.

---

## 🚀 Quick Start Guide

### Step 1: Install Dependencies

First, make sure you have the required packages:

```bash
pip install chromadb streamlit scikit-learn
```

### Step 2: Set Up API Keys (Optional)

Create a `.env` file with your API keys:

```bash
# CoinMarketCap (Free tier: 333 calls/day)
CMC_API_KEY=your_coinmarketcap_key

# Twelve Data (Free tier: 800 calls/day)
TWELVE_DATA_API_KEY=your_twelve_data_key

# Free Crypto API - NO KEY NEEDED
```

**Note:** The Free Crypto API works without any key. The other two are optional but give you more data.

### Step 3: Build Agent Memory

Run the memory builder to create historical knowledge for your agents:

```bash
python run_memory_builder.py
```

This will:
1. Run 90-day backtests on BTC, ETH, LTC, XRP
2. Store all successful and failed patterns
3. Fetch current market data from APIs
4. Create a `memory_summary.json` file
5. Build a ChromaDB database in `./chroma_db/`

**What you'll see:**
```
[MEMORY] Starting backtest for 4 pairs, 90 days back
[MEMORY] Loading historical data...
[MEMORY] Running backtest with both strategies...
[MEMORY] Storing patterns from TA-Only Strategy...
[MEMORY] Storing patterns from Cross-Moat Strategy...
[MEMORY] Stored 156 patterns from TA-Only Strategy (Success rate: 52.3%)
[MEMORY] Enriching memory with current market data...
[MEMORY] MEMORY BUILDING COMPLETE!
```

### Step 4: Launch the Storytelling Dashboard

```bash
streamlit run dashboard_storytelling.py
```

Your browser will open to `http://localhost:8501`

---

## 📖 Using the Storytelling Dashboard

The dashboard has **four views** designed to explain things simply:

### View 1: 📰 Market Story

**What you'll see:**
- A big emoji showing the market mood (🚀 bullish, 📉 bearish, 😌 neutral)
- Friendly text explaining what's happening:
  > "Hey! Here's what's happening in crypto right now:
  >
  > The market is looking bright. Out of the top 10 coins, 7 are up and 3 are down in the last 24 hours.
  >
  > Overall, prices have moved +2.34% on average.
  >
  > Right now the vibe is: **BULLISH** 📊
  >
  > 🚀 Things are moving fast! Our agents are watching for opportunities."

**When to use it:**
First thing in the morning to understand the overall market vibe.

---

### View 2: 🔍 Coin Deep Dive

**What you'll see:**
- Select a coin (BTC, ETH, LTC, XRP)
- Simple explanations like:
  - **Size:** "$850 billion - one of the biggest players"
  - **Activity:** "TONS of trading ($45B today) - very popular right now! 🔥"
  - **Volatility:** "Big moves today - this coin is feeling energetic! ⚡"

**When to use it:**
When you're curious about a specific cryptocurrency.

---

### View 3: 🤖 What Agents Think

**What you'll see:**
- How many patterns your agents have learned
- Recent "thoughts" from agents, like:
  > Agent #1: "I spotted a good opportunity in XXBTZUSD! Went BUY and made 2.8% profit. I'll remember this pattern! 🎯"

**When to use it:**
To understand what your AI is learning and how it's improving.

---

### View 4: 📊 Memory Bank

**What you'll see:**
- Total memories stored
- Success rate of learned patterns
- Top 10 best trades the agents remember
- A table showing profitable patterns

**When to use it:**
To see the historical knowledge your AI has built up.

---

## 🧠 How Agent Memory Works

### What Is "Agent Memory"?

Your AI agents learn by storing **trading patterns** as **vector embeddings** in a database (ChromaDB).

Think of it like this:
- Each trade creates a "memory"
- Similar trades are stored near each other
- When a new situation appears, agents search for similar memories
- They learn: "This looks like that time we made money!"

### What Gets Stored?

Each pattern includes:
- **Technical data**: RSI, MACD, volume, price change
- **Outcome**: Did it make money or lose money?
- **Context**: What coin, what time, market conditions
- **Performance**: How much profit/loss (%)

### Example Pattern Memory:

```json
{
  "pair": "XXBTZUSD",
  "direction": "BUY",
  "rsi": 65.0,
  "macd": 1.2,
  "volume": 5000000,
  "pnl_pct": 2.8,
  "timestamp": "2024-11-11T10:30:00"
}
```

When the agent sees RSI=65, MACD=1.2, high volume again, it can search its memory and think: "Last time this happened, we made 2.8%. Let's consider buying!"

---

## 📊 Understanding the Memory Summary

After running `run_memory_builder.py`, you'll get a `memory_summary.json` file:

```json
{
  "timestamp": "2024-11-11T...",
  "stats": {
    "trading_patterns": 156,    // Successful trades
    "failed_patterns": 144,     // Failed trades
    "agent_knowledge": 4,       // Number of trained agents
    "total": 304
  },
  "top_patterns": [
    {
      "id": "cross_moat_XXBTZUSD_...",
      "pnl_pct": 5.2,            // 5.2% profit!
      "metadata": { ... }
    }
  ]
}
```

**What to look for:**
- **High total patterns**: More memories = smarter agents
- **Good success rate**: trading_patterns / total > 50% is good
- **Top patterns**: Learn what worked best

---

## 🎓 What the Three APIs Give You

### CoinMarketCap
- **What**: Official rankings, market cap data, social links
- **Why it matters**: Tells you which coins are "important"
- **Example**: Bitcoin is #1, has $850B market cap, very active community

### Twelve Data
- **What**: Technical indicators, forex rates, stock correlations
- **Why it matters**: Shows connections between crypto and traditional markets
- **Example**: When EUR/USD drops, sometimes Bitcoin rises (inverse correlation)

### Free Crypto API
- **What**: Real-time prices, 24h changes, trading volume
- **Why it matters**: Always available, no API key needed
- **Example**: Current Bitcoin price, up 3.2% in 24 hours

**Together**: These give a complete picture - price + context + relationships.

---

## 🔧 Customization Options

### Change Backtest Duration

Edit `run_memory_builder.py`:

```python
results = builder.run_backtest_and_store(
    pairs=pairs,
    days_back=180,  # Change to 180 for 6 months of history
    initial_capital=10000.0
)
```

### Add More Coins

Edit `run_memory_builder.py`:

```python
pairs = ["XXBTZUSD", "XETHZUSD", "XLTCZUSD", "XXRPZUSD", "XADAZUSD"]
```

(Check Kraken API for valid pair names)

### Change Dashboard Refresh Rate

In `dashboard_storytelling.py` sidebar:

```python
auto_refresh = st.checkbox("Auto-refresh (every 30s)", value=True)  # Enable by default
```

---

## 🎯 Recommended Workflow

### Daily Routine:

1. **Morning** (5 minutes):
   - Open dashboard: `streamlit run dashboard_storytelling.py`
   - Check "Market Story" view
   - Understand today's vibe

2. **Mid-Day** (if curious):
   - Check "Coin Deep Dive" for coins you're interested in
   - See if anything changed

3. **Weekly** (30 minutes):
   - Run `python run_memory_builder.py` to update agent memory
   - Check "Memory Bank" view to see what agents learned
   - Review top performing patterns

---

## 🚨 Troubleshooting

### "ChromaDB not installed"
```bash
pip install chromadb
```

### "No API key found"
This is just a warning. The Free Crypto API works without keys. You can ignore this unless you want extra data from CoinMarketCap or Twelve Data.

### "Having trouble reading the market right now"
- Check your internet connection
- APIs might be rate-limited (wait 1 minute)
- Free Crypto API might be down (rare)

### "Memory bank is empty"
Run the memory builder first:
```bash
python run_memory_builder.py
```

### Dashboard won't start
Make sure Streamlit is installed:
```bash
pip install streamlit
```

---

## 📈 Next Steps

Now that you have:
- ✅ Enriched market data from 3 APIs
- ✅ A friendly storytelling dashboard
- ✅ Agent memory built from backtesting

**What to do next:**

1. **Build More Memory**: Run longer backtests (180-365 days)
2. **Monitor Daily**: Check dashboard each morning
3. **Learn Patterns**: Study what makes agents successful
4. **Paper Trade**: Test strategies without real money first

**When ready for live trading:**
- Phase 5.1: Live trading integration
- Phase 5.2: Real-money deployment
- Phase 5.3: Production monitoring

---

## 💡 Key Concepts Explained Simply

### What is "enriched market data"?
Instead of just price, we get:
- Price + market cap + volume + sentiment + social activity + technical indicators + correlations

It's like knowing not just "Bitcoin is $43,000" but "Bitcoin is $43,000, up 3%, high trading volume, bullish sentiment, trending on Twitter, and moving opposite to the US dollar."

### What is "vector similarity search"?
Imagine each trade as a point in space. Similar trades are close together. When a new situation appears, we find the nearest points (similar past situations) and learn from them.

### What is "backtesting"?
Testing strategies on historical data. Like saying: "If I had traded this way for the past 90 days, would I have made money?"

### What is "agent memory"?
A database of learned patterns. Every trade creates a memory. Over time, agents build intuition by recognizing similar patterns.

---

## 📞 Questions?

If you're confused about:
- **What the dashboard is showing**: Check this guide's dashboard section
- **Why something isn't working**: Check troubleshooting
- **How to customize**: Check customization options
- **What something means**: Check "Key Concepts" section

Remember: This is designed to be **friendly and simple**. If something feels too technical, that's a bug - let me know!

---

## 🎉 You're All Set!

Your Mycelial Finance system now:
1. **Talks to you like a friend** ✅
2. **Tells stories with data** ✅
3. **Builds intelligent agent memory** ✅

Enjoy exploring your AI-powered crypto insights! 🍄
