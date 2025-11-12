# dashboard_storytelling.py - Professional Storytelling Dashboard
"""
Professional dashboard that combines:
- Sleek, modern design from dashboard_v3.py
- Comprehensive macro/micro statistics
- Friendly storytelling that explains what's happening
- Real-time market intelligence with narrative context
"""

import streamlit as st
import logging
import sys
import sqlite3
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import pandas as pd
import plotly.graph_objects as go
from collections import defaultdict

# Add src to path
sys.path.insert(0, './src')

from connectors.market_data_aggregator import MarketDataAggregator
try:
    from storage.chroma_client import ChromaDBClient
    CHROMA_AVAILABLE = True
except:
    CHROMA_AVAILABLE = False

# Configure logging
logging.basicConfig(level=logging.INFO)

# Page configuration
st.set_page_config(
    page_title="Mycelial Finance Intelligence",
    page_icon="🍄",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Professional dark theme CSS (from dashboard_v3.py)
st.markdown("""
<style>
    /* Global Styles */
    .stApp {
        background-color: #0F172A;
    }

    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* Metric Cards */
    .metric-card {
        background: linear-gradient(135deg, #1E293B 0%, #334155 100%);
        border-radius: 16px;
        padding: 28px;
        border: 1px solid #334155;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
        margin-bottom: 16px;
    }
    .metric-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.4);
    }

    /* Stats */
    .stat-number {
        font-size: 2.5rem;
        font-weight: 700;
        line-height: 1;
        margin-bottom: 8px;
        background: linear-gradient(135deg, #3B82F6 0%, #8B5CF6 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .stat-label {
        font-size: 0.875rem;
        color: #94A3B8;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        font-weight: 600;
    }
    .stat-change-positive {
        color: #10B981;
        font-size: 0.875rem;
        font-weight: 600;
    }
    .stat-change-negative {
        color: #EF4444;
        font-size: 0.875rem;
        font-weight: 600;
    }

    /* Story Cards */
    .story-card {
        background: #1E293B;
        border-radius: 16px;
        padding: 32px;
        border: 1px solid #334155;
        margin-bottom: 24px;
    }
    .story-title {
        font-size: 1.5rem;
        font-weight: 700;
        color: #F1F5F9;
        margin-bottom: 16px;
        display: flex;
        align-items: center;
        gap: 12px;
    }
    .story-content {
        font-size: 1.125rem;
        line-height: 1.75;
        color: #CBD5E1;
    }
    .story-highlight {
        color: #3B82F6;
        font-weight: 600;
    }
    .story-emoji {
        font-size: 2.5rem;
    }

    /* Signal Badges */
    .signal-badge {
        display: inline-block;
        padding: 8px 20px;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .badge-bullish {
        background: rgba(16, 185, 129, 0.15);
        color: #10B981;
        border: 2px solid rgba(16, 185, 129, 0.4);
    }
    .badge-bearish {
        background: rgba(239, 68, 68, 0.15);
        color: #EF4444;
        border: 2px solid rgba(239, 68, 68, 0.4);
    }
    .badge-neutral {
        background: rgba(59, 130, 246, 0.15);
        color: #3B82F6;
        border: 2px solid rgba(59, 130, 246, 0.4);
    }

    /* Insight Cards */
    .insight-card {
        background: #0F172A;
        border-radius: 12px;
        padding: 20px;
        border-left: 4px solid #3B82F6;
        margin: 16px 0;
    }
    .insight-title {
        font-size: 1rem;
        font-weight: 600;
        color: #F1F5F9;
        margin-bottom: 8px;
    }
    .insight-text {
        font-size: 0.95rem;
        color: #94A3B8;
        line-height: 1.6;
    }

    /* Moat Grid */
    .moat-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 16px;
        margin: 24px 0;
    }
    .moat-item {
        background: #0F172A;
        border-radius: 12px;
        padding: 24px;
        text-align: center;
        border: 1px solid #334155;
        transition: all 0.2s ease;
    }
    .moat-item:hover {
        border-color: #3B82F6;
        transform: translateY(-2px);
    }
    .moat-label {
        font-size: 0.75rem;
        color: #64748B;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 12px;
        font-weight: 600;
    }
    .moat-value {
        font-size: 1.75rem;
        font-weight: 700;
        margin-bottom: 8px;
    }
    .moat-status {
        font-size: 0.875rem;
        color: #94A3B8;
    }

    /* Agent Activity */
    .agent-activity {
        background: #0F172A;
        border-radius: 8px;
        padding: 16px;
        margin: 8px 0;
        border: 1px solid #334155;
    }
    .agent-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 8px;
    }
    .agent-name {
        color: #F1F5F9;
        font-weight: 600;
        font-size: 0.95rem;
    }
    .agent-confidence {
        color: #10B981;
        font-weight: 700;
        font-size: 0.9rem;
    }
    .agent-thought {
        color: #94A3B8;
        font-size: 0.875rem;
        font-style: italic;
        line-height: 1.5;
    }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# DATA FETCHING FUNCTIONS
# =============================================================================

@st.cache_data(ttl=30)
def get_market_data_cached():
    """Fetch and cache market data"""
    try:
        aggregator = MarketDataAggregator()
        story = aggregator.get_market_story()

        # Get data for major coins
        btc_data = aggregator.get_enriched_market_data('BTC')
        eth_data = aggregator.get_enriched_market_data('ETH')

        return {
            'story': story,
            'btc': btc_data,
            'eth': eth_data,
            'timestamp': datetime.now()
        }
    except Exception as e:
        logging.error(f"Error fetching market data: {e}")
        return None

def get_sql_patterns():
    """Get patterns from SQL database"""
    try:
        conn = sqlite3.connect('mycelial_patterns.db')
        cursor = conn.cursor()
        cursor.execute("""
            SELECT agent_id, timestamp, pattern_value, raw_features, age_minutes
            FROM patterns
            ORDER BY timestamp DESC
            LIMIT 100
        """)
        patterns = []
        for row in cursor.fetchall():
            patterns.append({
                'agent_id': row[0],
                'timestamp': row[1],
                'pattern_value': row[2],
                'raw_features': json.loads(row[3]) if row[3] else {},
                'age_minutes': row[4]
            })
        conn.close()
        return patterns
    except Exception as e:
        logging.error(f"SQL error: {e}")
        return []

def get_chroma_stats():
    """Get ChromaDB statistics"""
    if not CHROMA_AVAILABLE:
        return None
    try:
        chroma = ChromaDBClient(persist_directory="./chroma_db")
        stats = chroma.get_collection_stats()
        top_patterns = chroma.get_top_performing_patterns(n_results=5)
        return {
            'stats': stats,
            'top_patterns': top_patterns
        }
    except Exception as e:
        logging.error(f"ChromaDB error: {e}")
        return None

def synthesize_cross_moat_intelligence(sql_patterns):
    """Analyze cross-moat alignment"""
    govt_patterns = [p for p in sql_patterns if 'GovtDataMiner' in str(p.get('agent_id', ''))]
    logistics_patterns = [p for p in sql_patterns if 'LogisticsMiner' in str(p.get('agent_id', ''))]
    corp_patterns = [p for p in sql_patterns if 'CorpDataMiner' in str(p.get('agent_id', ''))]
    code_patterns = [p for p in sql_patterns if 'RepoScraper' in str(p.get('agent_id', ''))]
    finance_patterns = [p for p in sql_patterns if 'DataEngineer' in str(p.get('agent_id', ''))]

    def get_moat_strength(patterns):
        if not patterns:
            return 'None', 0, "No activity"
        recent = patterns[:5]
        avg_value = sum(p['pattern_value'] for p in recent) / len(recent)
        if avg_value >= 70:
            return 'Strong', avg_value, "High confidence signals"
        elif avg_value >= 55:
            return 'Moderate', avg_value, "Moderate activity"
        elif avg_value >= 40:
            return 'Weak', avg_value, "Low signals"
        else:
            return 'None', avg_value, "Minimal activity"

    moats = {
        'Government': get_moat_strength(govt_patterns),
        'Logistics': get_moat_strength(logistics_patterns),
        'Corporations': get_moat_strength(corp_patterns),
        'Code': get_moat_strength(code_patterns),
        'Finance': get_moat_strength(finance_patterns)
    }

    strong_moats = [name for name, (strength, _, _) in moats.items() if strength in ['Strong', 'Moderate']]

    return {
        'moats': moats,
        'strong_count': len(strong_moats),
        'strong_moats': strong_moats
    }

# =============================================================================
# MAIN DASHBOARD
# =============================================================================

def main():
    # Header
    st.markdown("""
        <div style='padding: 40px 0 32px 0;'>
            <h1 style='color: #F1F5F9; font-size: 2.5rem; font-weight: 800; margin-bottom: 8px; letter-spacing: -0.025em;'>
                🍄 Mycelial Intelligence
            </h1>
            <p style='color: #64748B; font-size: 1.125rem; margin: 0;'>
                Real-time crypto intelligence with friendly explanations
            </p>
        </div>
    """, unsafe_allow_html=True)

    # Fetch data
    market_data = get_market_data_cached()
    sql_patterns = get_sql_patterns()
    chroma_data = get_chroma_stats()
    cross_moat = synthesize_cross_moat_intelligence(sql_patterns)

    # =============================================================================
    # TOP METRICS ROW
    # =============================================================================

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown("""
            <div class='metric-card'>
                <div class='stat-number'>{}</div>
                <div class='stat-label'>Patterns Discovered</div>
                <div class='stat-change-positive'>+{} last hour</div>
            </div>
        """.format(
            len(sql_patterns),
            len([p for p in sql_patterns if p['age_minutes'] < 60])
        ), unsafe_allow_html=True)

    with col2:
        moats_aligned = cross_moat['strong_count']
        st.markdown("""
            <div class='metric-card'>
                <div class='stat-number'>{}/5</div>
                <div class='stat-label'>Data Moats Aligned</div>
                <div class='stat-change-{}'>{}</div>
            </div>
        """.format(
            moats_aligned,
            'positive' if moats_aligned >= 3 else 'negative',
            "Strong signal" if moats_aligned >= 3 else "Weak signal"
        ), unsafe_allow_html=True)

    with col3:
        if chroma_data:
            success_rate = 0
            total = chroma_data['stats']['trading_patterns'] + chroma_data['stats']['failed_patterns']
            if total > 0:
                success_rate = (chroma_data['stats']['trading_patterns'] / total) * 100

            st.markdown("""
                <div class='metric-card'>
                    <div class='stat-number'>{:.1f}%</div>
                    <div class='stat-label'>Agent Success Rate</div>
                    <div class='stat-change-{}'>{} memories</div>
                </div>
            """.format(
                success_rate,
                'positive' if success_rate > 50 else 'negative',
                chroma_data['stats']['total']
            ), unsafe_allow_html=True)
        else:
            st.markdown("""
                <div class='metric-card'>
                    <div class='stat-number'>-</div>
                    <div class='stat-label'>Agent Success Rate</div>
                    <div class='stat-change-neutral'>Building memory...</div>
                </div>
            """, unsafe_allow_html=True)

    with col4:
        st.markdown("""
            <div class='metric-card'>
                <div class='stat-number'>{}</div>
                <div class='stat-label'>Last Updated</div>
                <div class='stat-change-positive'>Live data</div>
            </div>
        """.format(datetime.now().strftime('%H:%M')), unsafe_allow_html=True)

    # =============================================================================
    # MARKET STORY SECTION
    # =============================================================================

    if market_data and market_data['story']:
        story = market_data['story']
        sentiment = story.get('sentiment', 'NEUTRAL')

        # Determine emoji and badge
        if sentiment == 'BULLISH':
            emoji = "🚀"
            badge_class = "badge-bullish"
        elif sentiment == 'BEARISH':
            emoji = "📉"
            badge_class = "badge-bearish"
        else:
            emoji = "😌"
            badge_class = "badge-neutral"

        st.markdown(f"""
            <div class='story-card'>
                <div class='story-title'>
                    <span class='story-emoji'>{emoji}</span>
                    <span>What's Happening in Crypto Right Now</span>
                </div>
                <div style='margin-bottom: 20px;'>
                    <span class='signal-badge {badge_class}'>{sentiment}</span>
                </div>
                <div class='story-content'>
                    {story.get('story', 'Checking market conditions...')}
                </div>
            </div>
        """, unsafe_allow_html=True)

    # =============================================================================
    # CROSS-MOAT INTELLIGENCE
    # =============================================================================

    st.markdown("""
        <div class='story-card'>
            <div class='story-title'>🌐 Intelligence Across All Data Moats</div>
        </div>
    """, unsafe_allow_html=True)

    # Moat grid
    cols = st.columns(5)
    moat_names = ['Government', 'Logistics', 'Corporations', 'Code', 'Finance']
    moat_icons = ['🏛️', '📦', '🏢', '💻', '💰']

    for idx, (col, name, icon) in enumerate(zip(cols, moat_names, moat_icons)):
        strength, value, status = cross_moat['moats'][name]

        color = {
            'Strong': '#10B981',
            'Moderate': '#F59E0B',
            'Weak': '#64748B',
            'None': '#334155'
        }[strength]

        with col:
            st.markdown(f"""
                <div class='moat-item'>
                    <div style='font-size: 2rem; margin-bottom: 8px;'>{icon}</div>
                    <div class='moat-label'>{name}</div>
                    <div class='moat-value' style='color: {color};'>{strength}</div>
                    <div class='moat-status'>{status}</div>
                    <div class='moat-status' style='font-weight: 600; color: {color}; margin-top: 8px;'>{value:.0f}</div>
                </div>
            """, unsafe_allow_html=True)

    # Cross-moat insights
    if cross_moat['strong_count'] >= 3:
        st.markdown(f"""
            <div class='insight-card' style='border-left-color: #10B981;'>
                <div class='insight-title'>💡 Strong Cross-Moat Signal Detected</div>
                <div class='insight-text'>
                    {cross_moat['strong_count']} out of 5 data moats are showing coordinated patterns:
                    <strong>{', '.join(cross_moat['strong_moats'])}</strong>.
                    When multiple independent data sources align, it often indicates a significant market event or trend.
                </div>
            </div>
        """, unsafe_allow_html=True)
    elif cross_moat['strong_count'] == 2:
        st.markdown(f"""
            <div class='insight-card' style='border-left-color: #F59E0B;'>
                <div class='insight-title'>📊 Moderate Signal</div>
                <div class='insight-text'>
                    Two data moats are aligned: <strong>{', '.join(cross_moat['strong_moats'])}</strong>.
                    This suggests some market activity, but not yet a strong coordinated signal.
                </div>
            </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
            <div class='insight-card' style='border-left-color: #64748B;'>
                <div class='insight-title'>🔍 Monitoring Mode</div>
                <div class='insight-text'>
                    No strong cross-moat alignment detected. Markets appear calm.
                    Our agents continue monitoring for emerging patterns.
                </div>
            </div>
        """, unsafe_allow_html=True)

    # =============================================================================
    # AGENT INTELLIGENCE
    # =============================================================================

    st.markdown("""
        <div class='story-card'>
            <div class='story-title'>🤖 What Our AI Agents Are Thinking</div>
        </div>
    """, unsafe_allow_html=True)

    if chroma_data and chroma_data['top_patterns']:
        for i, pattern in enumerate(chroma_data['top_patterns'][:3]):
            metadata = pattern.get('metadata', {})
            pnl = pattern.get('pnl_pct', 0)
            pair = metadata.get('pair', 'Unknown')
            direction = metadata.get('direction', 'UNKNOWN')

            if pnl > 0:
                thought = f"I spotted a profitable pattern in {pair}! Went {direction} and made {pnl:.2f}% profit. I'm storing this in my memory for future reference."
                confidence_color = "#10B981"
            else:
                thought = f"Tested a {direction} strategy on {pair}, but it lost {abs(pnl):.2f}%. Learning from this mistake to avoid repeating it."
                confidence_color = "#EF4444"

            st.markdown(f"""
                <div class='agent-activity'>
                    <div class='agent-header'>
                        <div class='agent-name'>Agent #{i+1}</div>
                        <div class='agent-confidence' style='color: {confidence_color};'>{abs(pnl):.2f}% P&L</div>
                    </div>
                    <div class='agent-thought'>"{thought}"</div>
                </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown("""
            <div class='insight-card'>
                <div class='insight-title'>Building Intelligence...</div>
                <div class='insight-text'>
                    Our AI agents are currently building their memory bank through backtesting.
                    Run the memory builder to generate historical patterns for agents to learn from.
                </div>
            </div>
        """, unsafe_allow_html=True)

    # =============================================================================
    # DETAILED COIN ANALYSIS
    # =============================================================================

    st.markdown("""
        <div class='story-card'>
            <div class='story-title'>📊 Major Crypto Assets</div>
        </div>
    """, unsafe_allow_html=True)

    if market_data:
        col1, col2 = st.columns(2)

        for col, coin_data, name, icon in [
            (col1, market_data.get('btc'), 'Bitcoin', '₿'),
            (col2, market_data.get('eth'), 'Ethereum', 'Ξ')
        ]:
            with col:
                if coin_data and 'price' in coin_data:
                    price = coin_data['price']
                    change = coin_data.get('change_24h', 0)
                    volume = coin_data.get('volume_24h', 0)
                    mcap = coin_data.get('market_cap', 0)

                    change_color = "#10B981" if change > 0 else "#EF4444"
                    change_text = f"+{change:.2f}%" if change > 0 else f"{change:.2f}%"

                    # Explain the change
                    if abs(change) > 5:
                        explanation = "BIG moves today! High volatility."
                    elif abs(change) > 2:
                        explanation = "Moderate price action."
                    else:
                        explanation = "Pretty stable today."

                    st.markdown(f"""
                        <div class='metric-card'>
                            <div style='display: flex; justify-content: space-between; align-items: start; margin-bottom: 16px;'>
                                <div>
                                    <div style='font-size: 1.5rem; color: #F1F5F9; font-weight: 700;'>{icon} {name}</div>
                                    <div style='font-size: 2rem; color: #3B82F6; font-weight: 700; margin-top: 8px;'>${price:,.2f}</div>
                                </div>
                                <div style='text-align: right;'>
                                    <div style='color: {change_color}; font-size: 1.25rem; font-weight: 700;'>{change_text}</div>
                                    <div style='color: #64748B; font-size: 0.875rem; margin-top: 4px;'>24h</div>
                                </div>
                            </div>
                            <div style='color: #94A3B8; font-size: 0.95rem; margin-bottom: 12px;'>{explanation}</div>
                            <div style='display: grid; grid-template-columns: 1fr 1fr; gap: 12px; padding-top: 16px; border-top: 1px solid #334155;'>
                                <div>
                                    <div style='color: #64748B; font-size: 0.75rem; text-transform: uppercase;'>Volume 24h</div>
                                    <div style='color: #F1F5F9; font-size: 1rem; font-weight: 600;'>${volume/1e9:.2f}B</div>
                                </div>
                                <div>
                                    <div style='color: #64748B; font-size: 0.75rem; text-transform: uppercase;'>Market Cap</div>
                                    <div style='color: #F1F5F9; font-size: 1rem; font-weight: 600;'>${mcap/1e9:.2f}B</div>
                                </div>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)

    # Footer
    st.markdown("""
        <div style='text-align: center; padding: 40px 0 20px 0; color: #64748B; font-size: 0.875rem;'>
            🍄 Mycelial Finance • Powered by Multi-Moat Intelligence • Updates every 30 seconds
        </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
