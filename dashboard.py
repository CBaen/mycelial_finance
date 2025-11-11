# dashboard.py - MYCELIAL INTELLIGENCE v12.0: BIG ROCK 41 (Corrected) - The Trifecta P&L Engine
# Mission: Signal Collision Detection, Three P&L Streams, Synthesis Gateway Visualization

import dash
from dash import dcc, html, Input, Output, State
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import logging
import time
import json
import threading
from queue import Queue
import math
import dash_bootstrap_components as dbc
import uuid
import numpy as np
from datetime import datetime
from collections import defaultdict
from sklearn.cluster import KMeans
from scipy import stats

from src.connectors.redis_client import RedisClient

# === SETUP ===
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

message_queue = Queue()
SESSION_ID = str(uuid.uuid4())[:8]

# Professional color palette
COLORS = {
    'primary': '#a855f7',
    'success': '#10b981',
    'warning': '#f59e0b',
    'danger': '#ef4444',
    'info': '#3b82f6',
    'corp': '#FF5733',
    'background': '#0f1419',
    'card': '#1a202c',
    'text': '#e2e8f0',
    'text_muted': '#9ca3af',
    'border': '#2d3748',
}

# === INTERESTINGNESS FORMULA (All components use REAL data) ===
def calculate_interestingness(agent_data, all_agents):
    """5-Component Interestingness Score using REAL data only."""
    score = 0

    def get_normalized_vector(data):
        vec = np.array(data.get('vector', [0, 0, 0, 0]))
        if vec.ndim == 1 and len(vec) < 4:
            vec = np.pad(vec, (0, 4 - len(vec)), mode='constant')
        return vec / np.linalg.norm(vec) if np.linalg.norm(vec) > 0 else np.zeros(4)

    # 1. Novelty (20pts) - based on real parent difference
    parent_id = agent_data.get('parent')
    if parent_id and parent_id != 'Genesis' and parent_id in all_agents:
        parent_vec = get_normalized_vector(all_agents[parent_id])
        current_vec = get_normalized_vector(agent_data)
        novelty = np.linalg.norm(current_vec - parent_vec)
        score += min(novelty * 10, 20)
    else:
        score += 10

    # 2. Performance (20pts) - based on real patterns discovered
    patterns = agent_data.get('patterns_discovered', 0)
    performance = min(patterns / 10.0, 1.0)  # Normalize to 0-1
    score += performance * 20

    # 3. Diversity (20pts) - based on real vector distances
    if all_agents:
        my_vec = get_normalized_vector(agent_data)
        distances = []
        for a_id, a_data in all_agents.items():
            if a_id != agent_data.get('id', ''):
                distances.append(np.linalg.norm(my_vec - get_normalized_vector(a_data)))
        avg_distance = np.mean(distances) if distances else 0
        score += min(avg_distance * 8, 20)

    # 4. Evolution (20pts) - based on real generation
    generation = agent_data.get('generation', 0)
    score += min(generation * 2, 20)

    # 5. Growth Bonus (20pts) - based on REAL policy shares
    policy_shares = agent_data.get('policy_shares', 0)
    share_frequency = min(policy_shares / 20.0, 1.0)  # Normalize
    score += share_frequency * 20

    return min(score, 100)

# === DYNAMIC AGENT METADATA SYSTEM ===
def discover_agent_metadata(agent_id):
    """
    Dynamically assign metadata to any agent based on its ID pattern.
    No more hardcoded AGENT_INFO!
    """
    # Default metadata
    metadata = {
        'name': agent_id,
        'type': 'Unknown',
        'color': COLORS['text_muted'],
        'product': 'System',
        'icon': 'fa-robot'
    }

    # Pattern matching for agent types
    if 'DataEngineer' in agent_id or 'DataMiner' in agent_id:
        metadata['type'] = 'Data Engineer'
        metadata['color'] = COLORS['primary']
        metadata['icon'] = 'fa-database'
        if 'BTC' in agent_id or 'XXBTZUSD' in agent_id:
            metadata['name'] = 'BTC Sensor'
            metadata['product'] = 'Finance'
            metadata['icon'] = 'fa-bitcoin'
        elif 'ETH' in agent_id or 'XETHZUSD' in agent_id:
            metadata['name'] = 'ETH Sensor'
            metadata['product'] = 'Finance'
            metadata['icon'] = 'fa-ethereum'
        else:
            metadata['name'] = f"Data Engineer {agent_id.split('_')[-1]}"
            metadata['product'] = 'Finance'

    elif 'RepoScraper' in agent_id:
        metadata['name'] = f"Code Hunter {agent_id.split('_')[-1]}"
        metadata['type'] = 'Code Scraper'
        metadata['color'] = COLORS['success']
        metadata['product'] = 'Code Innovation'
        metadata['icon'] = 'fa-code'

    elif 'LogisticsMiner' in agent_id:
        metadata['name'] = f"Flow Tracker {agent_id.split('_')[-1]}"
        metadata['type'] = 'Logistics Miner'
        metadata['color'] = COLORS['warning']
        metadata['product'] = 'Logistics'
        metadata['icon'] = 'fa-truck'

    elif 'GovtDataMiner' in agent_id:
        metadata['name'] = f"Policy Scout {agent_id.split('_')[-1]}"
        metadata['type'] = 'Government Analyst'
        metadata['color'] = COLORS['info']
        metadata['product'] = 'Government'
        metadata['icon'] = 'fa-landmark'

    elif 'CorpDataMiner' in agent_id:
        metadata['name'] = f"Corp Intel {agent_id.split('_')[-1]}"
        metadata['type'] = 'Corporate Analyst'
        metadata['color'] = COLORS['corp']
        metadata['product'] = 'US Corporations'
        metadata['icon'] = 'fa-building'

    elif 'SwarmBrain' in agent_id:
        # Extract product focus from agent name (e.g., SwarmBrain_7_Finance)
        parts = agent_id.split('_')
        product = 'Finance'  # default
        if len(parts) >= 3:
            product = parts[2]

        metadata['name'] = f"Brain {parts[1] if len(parts) > 1 else '?'}"
        metadata['type'] = 'Pattern Learner'
        metadata['icon'] = 'fa-brain'

        # Color by product
        if 'Finance' in product:
            metadata['color'] = COLORS['primary']
            metadata['product'] = 'Finance'
        elif 'Code' in product:
            metadata['color'] = COLORS['success']
            metadata['product'] = 'Code Innovation'
        elif 'Logistics' in product:
            metadata['color'] = COLORS['warning']
            metadata['product'] = 'Logistics'
        elif 'Government' in product:
            metadata['color'] = COLORS['info']
            metadata['product'] = 'Government'
        elif 'Corporation' in product:
            metadata['color'] = COLORS['corp']
            metadata['product'] = 'US Corporations'
        else:
            metadata['color'] = COLORS['primary']
            metadata['product'] = 'Finance'

    elif 'Trader' in agent_id:
        metadata['name'] = 'Trade Executor'
        metadata['type'] = 'Action Agent'
        metadata['color'] = '#fbbf24'
        metadata['product'] = 'System'
        metadata['icon'] = 'fa-bolt'

    elif 'RiskManager' in agent_id:
        metadata['name'] = 'Safety Monitor'
        metadata['type'] = 'HAVEN Guardian'
        metadata['color'] = COLORS['danger']
        metadata['product'] = 'System'
        metadata['icon'] = 'fa-shield-alt'

    elif 'Builder' in agent_id or 'AutonomousBuilder' in agent_id:
        metadata['name'] = 'Builder'
        metadata['type'] = 'Evolution Engine'
        metadata['color'] = '#9333ea'
        metadata['product'] = 'System'
        metadata['icon'] = 'fa-cogs'

    return metadata

# === INTELLIGENT PATTERN DISCOVERY ENGINE ===
class PatternDiscoveryEngine:
    """
    Intelligent pattern analysis with clustering, anomaly detection, and correlation.
    This is the brain that finds REAL patterns, not just data observations.
    """
    def __init__(self):
        self.historical_data = defaultdict(list)  # Store data by moat
        self.pattern_relationships = []  # Track pattern evolution
        self.agent_collaborations = defaultdict(set)  # Track which agents work together

    def add_data_point(self, moat, features, agent_id, timestamp):
        """Store data for intelligent analysis."""
        self.historical_data[moat].append({
            'features': features,
            'agent': agent_id,
            'time': timestamp
        })

        # Limit history
        if len(self.historical_data[moat]) > 100:
            self.historical_data[moat] = self.historical_data[moat][-100:]

    def detect_anomaly(self, moat, current_features):
        """
        Detect statistical anomalies using Z-score.
        Returns (is_anomaly, confidence, description)
        """
        if len(self.historical_data[moat]) < 10:
            return False, 0.0, ""

        try:
            # Extract key metrics from historical data
            values = []
            for item in self.historical_data[moat]:
                # Get first numeric feature value
                feat = item['features']
                for v in feat.values():
                    if isinstance(v, (int, float)):
                        values.append(v)
                        break

            if len(values) < 10:
                return False, 0.0, ""

            # Calculate Z-score for current value
            current_val = next((v for v in current_features.values() if isinstance(v, (int, float))), None)
            if current_val is None:
                return False, 0.0, ""

            mean = np.mean(values)
            std = np.std(values)
            if std == 0:
                return False, 0.0, ""

            z_score = abs((current_val - mean) / std)

            if z_score > 2.5:  # 2.5 sigma threshold
                confidence = min(z_score / 5.0, 1.0)  # Normalize to 0-1
                description = f"Anomaly: Value {current_val:.2f} deviates {z_score:.1f}σ from mean {mean:.2f}"
                return True, confidence, description

        except Exception as e:
            logging.debug(f"Anomaly detection error: {e}")

        return False, 0.0, ""

    def find_cross_moat_correlation(self, moat1, moat2, threshold=0.7):
        """
        Find correlations between two moats.
        Returns (is_correlated, correlation, description)
        """
        if len(self.historical_data[moat1]) < 20 or len(self.historical_data[moat2]) < 20:
            return False, 0.0, ""

        try:
            # Extract time-series values
            values1 = []
            values2 = []

            # Get last 20 data points
            data1 = self.historical_data[moat1][-20:]
            data2 = self.historical_data[moat2][-20:]

            for item in data1:
                for v in item['features'].values():
                    if isinstance(v, (int, float)):
                        values1.append(v)
                        break

            for item in data2:
                for v in item['features'].values():
                    if isinstance(v, (int, float)):
                        values2.append(v)
                        break

            if len(values1) < 10 or len(values2) < 10:
                return False, 0.0, ""

            # Align lengths
            min_len = min(len(values1), len(values2))
            values1 = values1[:min_len]
            values2 = values2[:min_len]

            # Calculate Pearson correlation
            correlation = np.corrcoef(values1, values2)[0, 1]

            if abs(correlation) > threshold:
                direction = "positive" if correlation > 0 else "negative"
                description = f"Strong {direction} correlation ({correlation:.2f}) between {moat1} and {moat2}"
                return True, abs(correlation), description

        except Exception as e:
            logging.debug(f"Correlation analysis error: {e}")

        return False, 0.0, ""

    def cluster_similar_patterns(self, moat, n_clusters=3):
        """
        Cluster similar patterns using K-means.
        Returns (cluster_id, cluster_description)
        """
        if len(self.historical_data[moat]) < 10:
            return None, ""

        try:
            # Extract feature vectors
            vectors = []
            for item in self.historical_data[moat]:
                vec = [v for v in item['features'].values() if isinstance(v, (int, float))]
                if vec:
                    vectors.append(vec[:4])  # Take first 4 features

            if len(vectors) < 5:
                return None, ""

            # Pad vectors to same length
            max_len = max(len(v) for v in vectors)
            vectors = [v + [0] * (max_len - len(v)) for v in vectors]

            # K-means clustering
            vectors_array = np.array(vectors)
            kmeans = KMeans(n_clusters=min(n_clusters, len(vectors)), random_state=42, n_init=10)
            kmeans.fit(vectors_array)

            # Get cluster for latest data point
            latest_cluster = kmeans.labels_[-1]
            cluster_size = np.sum(kmeans.labels_ == latest_cluster)

            description = f"Pattern belongs to cluster {latest_cluster} ({cluster_size} similar patterns)"
            return int(latest_cluster), description

        except Exception as e:
            logging.debug(f"Clustering error: {e}")

        return None, ""

    def track_agent_collaboration(self, agents_list, pattern_id):
        """Track which agents work together on patterns."""
        if len(agents_list) >= 2:
            # Record all pairwise collaborations
            for i, agent1 in enumerate(agents_list):
                for agent2 in agents_list[i+1:]:
                    pair = tuple(sorted([agent1, agent2]))
                    self.agent_collaborations[pair].add(pattern_id)

    def get_collaboration_strength(self, agent1, agent2):
        """Get collaboration strength between two agents."""
        pair = tuple(sorted([agent1, agent2]))
        return len(self.agent_collaborations.get(pair, set()))

    def track_pattern_evolution(self, parent_pattern_id, child_pattern_id, relationship_type):
        """Track how patterns evolve from each other."""
        self.pattern_relationships.append({
            'parent': parent_pattern_id,
            'child': child_pattern_id,
            'type': relationship_type,
            'time': datetime.now().strftime('%H:%M:%S')
        })

# Initialize pattern discovery engine
pattern_engine = PatternDiscoveryEngine()

# === HELPER FUNCTIONS FROM DASHBOARD_V2 (Human-Readable Intelligence) ===

def translate_crypto_symbol(symbol_or_pair):
    """Convert Kraken symbols to human names"""
    mapping = {
        'XXBTZUSD': 'Bitcoin',
        'XETHZUSD': 'Ethereum',
        'BTC': 'Bitcoin',
        'ETH': 'Ethereum'
    }
    for key, value in mapping.items():
        if key in str(symbol_or_pair):
            return value
    return symbol_or_pair

def explain_pattern_plain_english(pattern_data):
    """Convert technical pattern data to plain English explanation"""
    raw_features = pattern_data.get('raw_features', {})
    close_price = raw_features.get('close', 0)

    # Detect crypto from agent_id
    agent_id = str(pattern_data.get('agent_id', ''))
    crypto_name = "Unknown Asset"

    if 'XXBTZUSD' in agent_id or 'DataEngineer_1' in agent_id:
        crypto_name = "Bitcoin"
    elif 'XETHZUSD' in agent_id or 'DataEngineer_2' in agent_id:
        crypto_name = "Ethereum"

    # Build plain English explanation
    explanation = f"{crypto_name} "

    if close_price > 100000:  # Bitcoin range
        explanation += f"is currently at ${close_price:,.0f}. "
    elif close_price > 1000:  # Ethereum range
        explanation += f"is currently at ${close_price:,.2f}. "

    # Add pattern insight
    pattern_value = pattern_data.get('pattern_value', 0)
    if pattern_value >= 75:
        explanation += "This is a VERY STRONG pattern showing high confidence in continued movement. "
    elif pattern_value >= 60:
        explanation += "This is a STRONG pattern with good reliability. "
    elif pattern_value >= 40:
        explanation += "This is a MODERATE pattern worth monitoring. "

    return explanation

def synthesize_cross_moat_intelligence(sql_patterns):
    """
    Cross-Moat Synthesis: Detects when multiple moats align.
    Returns plain English intelligence briefing.
    """
    # Categorize patterns by moat
    govt_patterns = [p for p in sql_patterns if 'GovtDataMiner' in str(p.get('agent_id', ''))]
    logistics_patterns = [p for p in sql_patterns if 'LogisticsMiner' in str(p.get('agent_id', ''))]
    corp_patterns = [p for p in sql_patterns if 'CorpDataMiner' in str(p.get('agent_id', ''))]
    code_patterns = [p for p in sql_patterns if 'RepoScraper' in str(p.get('agent_id', ''))]
    finance_patterns = [p for p in sql_patterns if 'DataEngineer' in str(p.get('agent_id', ''))]

    # Calculate moat strength
    def get_moat_strength(patterns):
        if not patterns:
            return 'None', 0
        recent = patterns[:5]
        avg_value = sum(p['pattern_value'] for p in recent) / len(recent)
        if avg_value >= 70:
            return 'Strong', avg_value
        elif avg_value >= 55:
            return 'Moderate', avg_value
        elif avg_value >= 40:
            return 'Weak', avg_value
        else:
            return 'None', avg_value

    # Get strength for each moat
    govt_strength, govt_value = get_moat_strength(govt_patterns)
    logistics_strength, logistics_value = get_moat_strength(logistics_patterns)
    corp_strength, corp_value = get_moat_strength(corp_patterns)
    code_strength, code_value = get_moat_strength(code_patterns)
    finance_strength, finance_value = get_moat_strength(finance_patterns)

    # Count strong moats
    strong_moats = []
    if govt_strength in ['Strong', 'Moderate']:
        strong_moats.append('Government Policy')
    if logistics_strength in ['Strong', 'Moderate']:
        strong_moats.append('Supply Chain')
    if corp_strength in ['Strong', 'Moderate']:
        strong_moats.append('Tech Corporations')
    if code_strength in ['Strong', 'Moderate']:
        strong_moats.append('Code Innovation')
    if finance_strength in ['Strong', 'Moderate']:
        strong_moats.append('Crypto Markets')

    # Generate synthesis report
    synthesis = {
        'alignment_count': len(strong_moats),
        'aligned_moats': strong_moats,
        'signal_strength': 'NONE',
        'briefing': '',
        'recommendation': '',
        'moat_details': {
            'Government': {'strength': govt_strength, 'value': govt_value},
            'Logistics': {'strength': logistics_strength, 'value': logistics_value},
            'Corporations': {'strength': corp_strength, 'value': corp_value},
            'Code': {'strength': code_strength, 'value': code_value},
            'Finance': {'strength': finance_strength, 'value': finance_value}
        }
    }

    # Determine overall signal
    if len(strong_moats) >= 4:
        synthesis['signal_strength'] = 'VERY STRONG'
        synthesis['briefing'] = f"MAJOR ALIGNMENT DETECTED: {len(strong_moats)} out of 5 moats are showing strong patterns simultaneously. This is extremely rare and indicates a high-confidence market environment."
        synthesis['recommendation'] = "When 4+ moats align, it historically signals a major trend. This is the highest confidence signal the system can produce."

    elif len(strong_moats) == 3:
        synthesis['signal_strength'] = 'STRONG'
        moat_list = ', '.join(strong_moats)
        synthesis['briefing'] = f"STRONG ALIGNMENT: {moat_list} are all showing coordinated patterns. Three-way alignment suggests a developing trend."
        synthesis['recommendation'] = "Three moats agreeing is a strong signal. Watch for the 4th moat to confirm."

    elif len(strong_moats) == 2:
        synthesis['signal_strength'] = 'MODERATE'
        moat_list = ', '.join(strong_moats)
        synthesis['briefing'] = f"MODERATE SIGNAL: {moat_list} are showing aligned patterns. Two-moat alignment is worth monitoring."
        synthesis['recommendation'] = "Two moats agreeing is interesting but needs confirmation from other areas."

    elif len(strong_moats) == 1:
        synthesis['signal_strength'] = 'WEAK'
        synthesis['briefing'] = f"SINGLE MOAT SIGNAL: Only {strong_moats[0]} is showing patterns."
        synthesis['recommendation'] = "Wait for at least 2 moats to align before taking action."

    else:
        synthesis['signal_strength'] = 'NONE'
        synthesis['briefing'] = "NO CLEAR SIGNAL: None of the 5 moats are showing strong patterns. Market is in consolidation."
        synthesis['recommendation'] = "When moats don't align, the best strategy is patience."

    return synthesis

def get_sql_patterns():
    """Query SQL database for archived patterns"""
    import sqlite3
    try:
        conn = sqlite3.connect('mycelial_patterns.db')
        cursor = conn.cursor()

        cursor.execute("""
            SELECT agent_id, timestamp, pattern_value, raw_features, age_minutes, decay_factor
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
                'age_minutes': row[4],
                'decay_factor': row[5]
            })

        conn.close()
        return patterns
    except Exception as e:
        logging.debug(f"SQL query info: {e}")
        return []

# === DASH APP ===
app = dash.Dash(
    __name__,
    external_stylesheets=[
        dbc.themes.SLATE,
        "https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap",
        "https://use.fontawesome.com/releases/v6.5.1/css/all.css"
    ],
    suppress_callback_exceptions=True,
)
app.title = "Mycelial Intelligence - v12.0 Trifecta P&L Engine"

# === LAYOUT ===
app.layout = dbc.Container(
    fluid=True,
    className="p-4",
    style={'backgroundColor': COLORS['background'], 'minHeight': '100vh', 'fontFamily': "'Inter', sans-serif"},
    children=[
        # Data stores
        dcc.Store(id='pattern-store', data={'total_patterns': 0, 'times': [], 'counts': []}),
        dcc.Store(id='moat-health-store', data={'Finance': 100, 'Code Innovation': 100, 'Logistics': 100, 'Government': 100, 'US Corporations': 100}),
        dcc.Store(id='activity-log-store', data=[]),
        dcc.Store(id='agent-stats-store', data={}),
        dcc.Store(id='discoveries-store', data=[]),
        dcc.Store(id='swarm-health-store', data={'value': 100, 'history': [100]}),
        dcc.Store(id='pattern-details-store', data=[]),  # Enhanced with intelligence
        dcc.Store(id='moat-stats-store', data={
            'Finance': {'patterns': 0, 'agents': []},
            'Code Innovation': {'patterns': 0, 'agents': []},
            'Logistics': {'patterns': 0, 'agents': []},
            'Government': {'patterns': 0, 'agents': []},
            'US Corporations': {'patterns': 0, 'agents': []}
        }),
        dcc.Store(id='haven-risk-store', data={'current_risk': 15, 'history': [15]}),
        dcc.Store(id='agent-carousel-index', data=0),
        dcc.Store(id='collaboration-store', data={}),  # NEW: Agent collaboration tracking
        dcc.Store(id='pattern-evolution-store', data=[]),  # NEW: Pattern lineage
        # BIG ROCK 41 (Corrected): Trifecta P&L Stores
        dcc.Store(id='trifecta-pnl-store', data={
            'times': [],
            'baseline_pnl': [0],
            'mycelial_pnl': [0],
            'synthesized_pnl': [0],
            'baseline_trades': 0,
            'mycelial_trades': 0,
            'synthesized_trades': 0
        }),
        dcc.Store(id='trade-ledger-store', data=[]),  # Live trade ledger

        dcc.Interval(id='interval', interval=2000, n_intervals=0),

        # === HEADER ===
        dbc.Row(dbc.Col(html.Div([
            html.H1([
                html.I(className="fas fa-brain", style={'marginRight': '15px', 'color': COLORS['primary']}),
                "MYCELIAL INTELLIGENCE ENGINE"
            ], style={'fontSize': '2.5rem', 'fontWeight': '700', 'color': COLORS['text'], 'textAlign': 'center'}),
            html.P("v12.0: Trifecta P&L Engine + Cross-Moat Intelligence + Human-Readable Insights",
                  style={'color': COLORS['text_muted'], 'fontSize': '0.95rem', 'textAlign': 'center'}),
            html.P("Real-time insights across Finance, Government, Logistics, Corporations, and Code Innovation",
                  style={'color': COLORS['text_muted'], 'fontSize': '0.875rem', 'textAlign': 'center'}),
        ], className="py-3 mb-4"))),

        # === KEY METRICS ROW ===
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.I(className="fas fa-lightbulb fa-2x", style={'color': COLORS['warning']}),
                            dbc.Tooltip(
                                "Total intelligent patterns discovered through clustering, anomaly detection, and correlation analysis.",
                                target="patterns-discovered-card",
                            ),
                        ], style={'float': 'right'}),
                        html.H6("Intelligent Patterns", style={'color': COLORS['text_muted'], 'marginBottom': '10px'}),
                        html.H2(id='total-patterns-metric', children="0", style={'color': COLORS['warning'], 'fontWeight': '700'}),
                        html.P(id='patterns-growth-text', children="+0 this session", style={'color': COLORS['success'], 'fontSize': '0.9rem'}),
                    ])
                ], style={'backgroundColor': COLORS['card'], 'borderLeft': f'4px solid {COLORS["warning"]}'}, id="patterns-discovered-card"),
            ], width=3),

            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.I(className="fas fa-heartbeat fa-2x", style={'color': COLORS['success']}),
                            dbc.Tooltip(
                                "Overall health of your swarm (0-100). Calculated from average moat health across all 5 pillars.",
                                target="swarm-health-card",
                            ),
                        ], style={'float': 'right'}),
                        html.H6("Swarm Health", style={'color': COLORS['text_muted'], 'marginBottom': '10px'}),
                        html.H2(id='swarm-health-metric', children="100", style={'color': COLORS['success'], 'fontWeight': '700'}),
                        html.P(id='swarm-health-status', children="Excellent", style={'color': COLORS['success'], 'fontSize': '0.9rem'}),
                    ])
                ], style={'backgroundColor': COLORS['card'], 'borderLeft': f'4px solid {COLORS["success"]}'}, id="swarm-health-card"),
            ], width=3),

            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.I(className="fas fa-network-wired fa-2x", style={'color': COLORS['info']}),
                            dbc.Tooltip(
                                "Number of active agents that have published data this session.",
                                target="active-agents-card",
                            ),
                        ], style={'float': 'right'}),
                        html.H6("Active Agents", style={'color': COLORS['text_muted'], 'marginBottom': '10px'}),
                        html.H2(id='active-agents-metric', children="0", style={'color': COLORS['info'], 'fontWeight': '700'}),
                        html.P("Across 5 Product Moats", style={'color': COLORS['text_muted'], 'fontSize': '0.9rem'}),
                    ])
                ], style={'backgroundColor': COLORS['card'], 'borderLeft': f'4px solid {COLORS["info"]}'}, id="active-agents-card"),
            ], width=3),

            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.I(className="fas fa-fire fa-2x", style={'color': COLORS['danger']}),
                            dbc.Tooltip(
                                "HAVEN Risk Framework: System risk level (0-100). Calculated from actual system messages. "
                                "85+ triggers policy contagion blocks.",
                                target="haven-risk-card",
                            ),
                        ], style={'float': 'right'}),
                        html.H6("HAVEN Risk Level", style={'color': COLORS['text_muted'], 'marginBottom': '10px'}),
                        html.H2(id='haven-risk-metric', children="LOW", style={'color': COLORS['success'], 'fontWeight': '700'}),
                        html.P(id='haven-risk-value', children="15%", style={'color': COLORS['text_muted'], 'fontSize': '0.9rem'}),
                    ])
                ], style={'backgroundColor': COLORS['card'], 'borderLeft': f'4px solid {COLORS["danger"]}'}, id="haven-risk-card"),
            ], width=3),
        ], className='mb-4'),

        # === TABS ===
        dbc.Tabs(id="tabs", active_tab="tab-executive-summary", className="mb-4", children=[
            dbc.Tab(label="📊 Executive Summary", tab_id="tab-executive-summary",
                   label_style={'color': COLORS['text_muted']}, active_label_style={'color': COLORS['success'], 'fontWeight': '600'}),
            dbc.Tab(label="💰 Trifecta P&L", tab_id="tab-trifecta-pnl",
                   label_style={'color': COLORS['text_muted']}, active_label_style={'color': '#fbbf24', 'fontWeight': '600'}),
            dbc.Tab(label="🔍 Pattern Discovery", tab_id="tab-pattern-discovery",
                   label_style={'color': COLORS['text_muted']}, active_label_style={'color': COLORS['primary'], 'fontWeight': '600'}),
            dbc.Tab(label="🧠 Agent Activity", tab_id="tab-agent-activity",
                   label_style={'color': COLORS['text_muted']}, active_label_style={'color': COLORS['primary'], 'fontWeight': '600'}),
            dbc.Tab(label="🏰 5-Pillar Moats", tab_id="tab-moats",
                   label_style={'color': COLORS['text_muted']}, active_label_style={'color': COLORS['primary'], 'fontWeight': '600'}),
            dbc.Tab(label="🎴 Agent Cards", tab_id="tab-agent-cards",
                   label_style={'color': COLORS['text_muted']}, active_label_style={'color': COLORS['primary'], 'fontWeight': '600'}),
            dbc.Tab(label="📊 Growth Analytics", tab_id="tab-analytics",
                   label_style={'color': COLORS['text_muted']}, active_label_style={'color': COLORS['primary'], 'fontWeight': '600'}),
        ]),
        html.Div(id="tab-content"),

        html.Div(f"Session {SESSION_ID} | Big Rock 41 (Corrected): The Trifecta P&L Engine | Synthesis Gateway",
                className="text-center mt-4", style={'color': COLORS['text_muted'], 'fontSize': '0.75rem'})
    ]
)

# === REDIS LISTENER ===
def start_redis_listener(app_queue: Queue):
    logging.info("v11.0 Intelligent Engine: Redis listener started")
    try:
        redis_client = RedisClient()
    except Exception as e:
        logging.critical(f"Redis error: {e}")
        return
    if not redis_client.connection:
        return

    channels = {
        'market-data:*': 'market-data',
        'trade-orders': 'trade-order',
        'trade-confirmations': 'trade-confirmation',
        'system-control': 'system-control',
        'system-build-request': 'build-request',
        'policy-data:*': 'policy-data',
        'corporate-data:*': 'corporate-data',
        'repo-data:*': 'repo-data',
        'logistics-data:*': 'logistics-data',
        'agent-lineage-update': 'lineage-update',
        'govt-data:*': 'govt-data',
        'pattern-discovery:*': 'intelligent-pattern',  # For intelligent pattern messages
        'pattern-narrative': 'pattern-narrative',  # BIG ROCK 39: Deep Research Agent narratives
        'ta-signals': 'ta-signals',  # BIG ROCK 39: Technical Analysis signals
        'market-exploration': 'market-exploration',  # BIG ROCK 39: Market Explorer discoveries
        # BIG ROCK 41 (Corrected): The Trifecta P&L Engine
        'mycelial-trade-ideas': 'mycelial-trade-ideas',  # Swarm causal patterns
        'baseline-trade-ideas': 'baseline-trade-ideas',  # Technical Analysis baseline
        'synthesized-trade-log': 'synthesized-trade-log'  # Signal Collision trades
    }

    def create_listener(pattern, msg_type):
        r = RedisClient()
        if not r.connection:
            return
        pubsub = r.connection.pubsub(ignore_subscribe_messages=True)
        try:
            pubsub.psubscribe(pattern)
            for message in pubsub.listen():
                try:
                    data = json.loads(message['data'])
                    app_queue.put({'type': msg_type, 'data': data, 'channel': message['channel'], 'time': time.time()})
                except:
                    pass
        except:
            pass
        finally:
            pubsub.close()

    for pattern, msg_type in channels.items():
        t = threading.Thread(target=create_listener, args=(pattern, msg_type), daemon=True)
        t.start()

listener_thread = threading.Thread(target=start_redis_listener, args=(message_queue,), daemon=True)
listener_thread.start()
logging.info("Mycelial Trifecta P&L Engine v12.0 Active - BIG ROCK 41 (Corrected)")

# === MAIN DATA UPDATE WITH INTELLIGENT PATTERN DISCOVERY ===
@app.callback(
    [Output('pattern-store', 'data'),
     Output('moat-health-store', 'data'),
     Output('activity-log-store', 'data'),
     Output('agent-stats-store', 'data'),
     Output('swarm-health-store', 'data'),
     Output('discoveries-store', 'data'),
     Output('pattern-details-store', 'data'),
     Output('moat-stats-store', 'data'),
     Output('haven-risk-store', 'data'),
     Output('collaboration-store', 'data'),
     Output('pattern-evolution-store', 'data'),
     Output('trifecta-pnl-store', 'data'),
     Output('trade-ledger-store', 'data')],
    [Input('interval', 'n_intervals')],
    [State('pattern-store', 'data'),
     State('moat-health-store', 'data'),
     State('activity-log-store', 'data'),
     State('agent-stats-store', 'data'),
     State('swarm-health-store', 'data'),
     State('discoveries-store', 'data'),
     State('pattern-details-store', 'data'),
     State('moat-stats-store', 'data'),
     State('haven-risk-store', 'data'),
     State('collaboration-store', 'data'),
     State('pattern-evolution-store', 'data'),
     State('trifecta-pnl-store', 'data'),
     State('trade-ledger-store', 'data')]
)
def update_data(n, pattern_data, moat_health, activity_log, agent_stats, swarm_health, discoveries,
                pattern_details, moat_stats, haven_risk, collaboration_data, pattern_evolution,
                trifecta_pnl, trade_ledger):
    """Process Redis messages with INTELLIGENT pattern discovery and Trifecta P&L tracking."""

    # Process all queued messages
    while not message_queue.empty():
        msg = message_queue.get()
        msg_type = msg['type']
        data = msg['data']
        timestamp = datetime.now().strftime('%H:%M:%S')

        source = data.get('source', 'Unknown')

        # Initialize agent stats if not exists (BIG ROCK 31: Pull from actual agent data)
        if source and source != 'Unknown':
            if source not in agent_stats:
                # Extract real agent data from message
                generation = data.get('generation', 0)
                parent_id = data.get('parent_id', None)
                parent_name = f"Agent_{parent_id}" if parent_id else 'Genesis'
                strategy_vector = data.get('strategy_vector', [0.0, 0.0, 0.0, 0.0])

                agent_stats[source] = {
                    'patterns_discovered': 0,
                    'policy_shares': 0,
                    'last_active': timestamp,
                    'generation': generation,
                    'parent': parent_name,
                    'children': [],
                    'status': 'Active',
                    'vector': strategy_vector,
                    'id': source,
                    'collaborators': []
                }
            else:
                # Update dynamic fields from latest message
                if 'generation' in data:
                    agent_stats[source]['generation'] = data.get('generation', agent_stats[source]['generation'])
                if 'strategy_vector' in data:
                    agent_stats[source]['vector'] = data.get('strategy_vector', agent_stats[source]['vector'])
                if 'parent_id' in data:
                    parent_id = data.get('parent_id')
                    agent_stats[source]['parent'] = f"Agent_{parent_id}" if parent_id else agent_stats[source]['parent']

            agent_stats[source]['last_active'] = timestamp

        # === INTELLIGENT PATTERN PROCESSING ===
        if msg_type in ['market-data', 'repo-data', 'logistics-data', 'govt-data', 'policy-data', 'corporate-data']:
            # Determine moat
            moat_map = {
                'market-data': 'Finance',
                'repo-data': 'Code Innovation',
                'logistics-data': 'Logistics',
                'govt-data': 'Government',
                'policy-data': 'Government',
                'corporate-data': 'US Corporations'
            }
            moat = moat_map.get(msg_type, 'Finance')

            features = data.get('features', {})
            if not features:
                continue

            # Add data to intelligent engine
            pattern_engine.add_data_point(moat, features, source, timestamp)

            # === INTELLIGENT ANALYSIS ===
            pattern_types = []
            confidence_scores = []
            descriptions = []

            # 1. Anomaly Detection
            is_anomaly, anomaly_conf, anomaly_desc = pattern_engine.detect_anomaly(moat, features)
            if is_anomaly:
                pattern_types.append('anomaly')
                confidence_scores.append(anomaly_conf)
                descriptions.append(anomaly_desc)

            # 2. Clustering
            cluster_id, cluster_desc = pattern_engine.cluster_similar_patterns(moat)
            if cluster_id is not None:
                pattern_types.append('cluster')
                confidence_scores.append(0.7)  # Moderate confidence
                descriptions.append(cluster_desc)

            # 3. Cross-Moat Correlation (check with one other moat)
            other_moats = [m for m in moat_map.values() if m != moat]
            if other_moats:
                for other_moat in other_moats[:2]:  # Check max 2 for performance
                    is_corr, corr_val, corr_desc = pattern_engine.find_cross_moat_correlation(moat, other_moat)
                    if is_corr:
                        pattern_types.append('correlation')
                        confidence_scores.append(corr_val)
                        descriptions.append(corr_desc)
                        break

            # Create base pattern signature
            feature_str = " | ".join([f"{k}: {v:.2f}" if isinstance(v, float) else f"{k}: {v}"
                                     for k, v in list(features.items())[:3]])

            # Determine pattern type and semantic description
            if pattern_types:
                primary_type = pattern_types[0]
                semantic_desc = descriptions[0]
                effectiveness = confidence_scores[0] * 100
            else:
                primary_type = 'observation'
                semantic_desc = f"Data observation in {moat}"
                effectiveness = 50.0

            # Enhanced pattern record
            pattern_id = f"P{pattern_data['total_patterns'] + 1}"
            pattern_record = {
                'id': pattern_id,
                'time': timestamp,
                'moat': moat,
                'pattern': feature_str,
                'agents': [source],
                'type': primary_type,
                'semantic_description': semantic_desc,
                'effectiveness_score': effectiveness,
                'moat_connections': [moat],  # Can be expanded for correlations
                'parent_patterns': [],  # Will be filled if evolution detected
                'confidence': confidence_scores[0] if confidence_scores else 0.5
            }
            pattern_details.append(pattern_record)

            # Activity log with rich context
            type_icons = {
                'anomaly': '⚡',
                'cluster': '🎯',
                'correlation': '🔗',
                'observation': '📊'
            }
            icon = type_icons.get(primary_type, '📊')

            activity_log.append({
                'time': timestamp,
                'agent': source,
                'action': f'{icon} {primary_type.title()}: {semantic_desc[:50]}...',
                'color': COLORS.get(moat.lower(), COLORS['primary'])
            })

            pattern_data['total_patterns'] += 1
            moat_health[moat] = min(100, moat_health.get(moat, 100) + 0.5)

            # Track moat stats (BIG ROCK 27: Use lists for JSON compatibility)
            if isinstance(moat_stats[moat]['agents'], list):
                if source not in moat_stats[moat]['agents']:
                    moat_stats[moat]['agents'].append(source)
            else:
                moat_stats[moat]['agents'] = [source]
            moat_stats[moat]['patterns'] = moat_stats[moat].get('patterns', 0) + 1

            # BIG ROCK 31: Track patterns_discovered (data observations)
            if source and source != 'Unknown':
                agent_stats[source]['patterns_discovered'] += 1
                # Policy shares tracked separately below for actual policy sharing events

        elif msg_type == 'intelligent-pattern':
            # Handle intelligent patterns published by PatternLearner agents
            # BIG ROCK 31: This is actual policy sharing (high-confidence patterns shared with swarm)
            pattern_type = data.get('pattern_type', 'discovery')
            description = data.get('description', 'Pattern discovered')
            confidence = data.get('confidence', 0.5)
            related_agents = data.get('related_agents', [source])

            # Track policy shares for source agent (actively sharing with swarm)
            if source and source != 'Unknown' and source in agent_stats:
                agent_stats[source]['policy_shares'] += 1

            # Track collaboration
            if len(related_agents) > 1:
                pattern_engine.track_agent_collaboration(related_agents, f"IP{pattern_data['total_patterns']}")
                for agent in related_agents:
                    if agent in agent_stats:
                        collab_list = agent_stats[agent].get('collaborators', [])
                        for other in related_agents:
                            if other != agent and other not in collab_list:
                                collab_list.append(other)
                        agent_stats[agent]['collaborators'] = collab_list[:10]  # Keep top 10

            pattern_details.append({
                'id': f"IP{pattern_data['total_patterns']}",
                'time': timestamp,
                'moat': 'Cross-Moat',
                'pattern': description,
                'agents': related_agents,
                'type': pattern_type,
                'semantic_description': description,
                'effectiveness_score': confidence * 100,
                'moat_connections': ['Multiple'],
                'parent_patterns': [],
                'confidence': confidence
            })
            pattern_data['total_patterns'] += 1

        elif msg_type == 'build-request':
            requester = data.get('requester', 'Unknown')
            agent_type = data.get('agent_type', 'Unknown')
            reason = data.get('reason', 'Unknown')
            activity_log.append({
                'time': timestamp,
                'agent': requester,
                'action': f'🔧 Requested {agent_type}: {reason}',
                'color': '#9333ea'
            })
            discoveries.append({
                'time': timestamp,
                'type': 'Evolution',
                'description': f'{requester} requested {agent_type}',
                'importance': 'High'
            })

        elif msg_type == 'system-control':
            risk_level = data.get('risk_level', haven_risk['current_risk'])
            haven_risk['current_risk'] = risk_level
            haven_risk['history'].append(risk_level)
            if len(haven_risk['history']) > 50:
                haven_risk['history'] = haven_risk['history'][-50:]

        # === BIG ROCK 41 (Corrected): TRIFECTA P&L MESSAGE HANDLERS ===
        elif msg_type == 'mycelial-trade-ideas':
            # Mycelial Swarm pattern trade ideas (tracked separately)
            activity_log.append({
                'time': timestamp,
                'agent': source,
                'action': f'💜 Mycelial: {data.get("direction", "N/A").upper()} {data.get("pair", "N/A")}',
                'color': COLORS['primary']
            })
            trifecta_pnl['mycelial_trades'] += 1

        elif msg_type == 'baseline-trade-ideas':
            # Baseline TA signals (tracked separately)
            activity_log.append({
                'time': timestamp,
                'agent': source,
                'action': f'⚪ Baseline TA: {data.get("direction", "N/A").upper()} {data.get("pair", "N/A")}',
                'color': COLORS['text_muted']
            })
            trifecta_pnl['baseline_trades'] += 1

        elif msg_type == 'synthesized-trade-log':
            # ✓✓✓ SIGNAL COLLISION - THE GOLD STANDARD ✓✓✓
            # This is where both Mycelial and Baseline AGREE
            baseline_pnl = data.get('baseline_pnl', 0.0)
            mycelial_pnl = data.get('mycelial_pnl', 0.0)
            synthesized_pnl = data.get('synthesized_pnl', 0.0)

            # Update P&L arrays
            trifecta_pnl['baseline_pnl'].append(baseline_pnl)
            trifecta_pnl['mycelial_pnl'].append(mycelial_pnl)
            trifecta_pnl['synthesized_pnl'].append(synthesized_pnl)
            trifecta_pnl['times'].append(timestamp)

            # Update trade counts
            trifecta_pnl['baseline_trades'] = data.get('baseline_trades', trifecta_pnl['baseline_trades'])
            trifecta_pnl['mycelial_trades'] = data.get('mycelial_trades', trifecta_pnl['mycelial_trades'])
            trifecta_pnl['synthesized_trades'] = data.get('synthesized_trades', trifecta_pnl['synthesized_trades'])

            # Limit history
            if len(trifecta_pnl['times']) > 100:
                trifecta_pnl['times'] = trifecta_pnl['times'][-100:]
                trifecta_pnl['baseline_pnl'] = trifecta_pnl['baseline_pnl'][-100:]
                trifecta_pnl['mycelial_pnl'] = trifecta_pnl['mycelial_pnl'][-100:]
                trifecta_pnl['synthesized_pnl'] = trifecta_pnl['synthesized_pnl'][-100:]

            # Add to trade ledger
            trade_ledger.append({
                'time': timestamp,
                'signal_type': 'SYNTHESIZED',
                'pair': data.get('pair', 'N/A'),
                'direction': data.get('direction', 'N/A'),
                'price': data.get('current_price', 0),
                'baseline_pnl': baseline_pnl,
                'mycelial_pnl': mycelial_pnl,
                'synthesized_pnl': synthesized_pnl,
                'execution_result': data.get('execution_result', {})
            })

            # Activity log with GOLD color for collisions
            activity_log.append({
                'time': timestamp,
                'agent': source,
                'action': f'✓✓✓ SIGNAL COLLISION: {data.get("direction", "N/A").upper()} {data.get("pair", "N/A")} | P&L: {synthesized_pnl:.2f}%',
                'color': '#fbbf24'  # GOLD
            })

        # Track pattern discoveries over time
        pattern_data['times'].append(timestamp)
        pattern_data['counts'].append(pattern_data['total_patterns'])
        if len(pattern_data['times']) > 50:
            pattern_data['times'] = pattern_data['times'][-50:]
            pattern_data['counts'] = pattern_data['counts'][-50:]

    # Limit sizes
    if len(activity_log) > 100:
        activity_log = activity_log[-100:]
    if len(pattern_details) > 500:
        pattern_details = pattern_details[-500:]

    # Calculate swarm health from moat health
    avg_moat_health = sum(moat_health.values()) / len(moat_health)
    swarm_health['value'] = avg_moat_health
    swarm_health['history'].append(avg_moat_health)
    if len(swarm_health['history']) > 50:
        swarm_health['history'] = swarm_health['history'][-50:]

    # Update collaboration data
    collaboration_data = {}
    for agent_id, agent_data in agent_stats.items():
        collaborators = agent_data.get('collaborators', [])
        if collaborators:
            collaboration_data[agent_id] = collaborators

    # Limit trade ledger size
    if len(trade_ledger) > 200:
        trade_ledger = trade_ledger[-200:]

    return pattern_data, moat_health, activity_log, agent_stats, swarm_health, discoveries, pattern_details, moat_stats, haven_risk, collaboration_data, pattern_evolution, trifecta_pnl, trade_ledger

# === KEY METRICS UPDATES ===
@app.callback(
    [Output('total-patterns-metric', 'children'),
     Output('patterns-growth-text', 'children'),
     Output('swarm-health-metric', 'children'),
     Output('swarm-health-status', 'children'),
     Output('haven-risk-metric', 'children'),
     Output('haven-risk-value', 'children'),
     Output('active-agents-metric', 'children')],
    [Input('pattern-store', 'data'),
     Input('swarm-health-store', 'data'),
     Input('haven-risk-store', 'data'),
     Input('agent-stats-store', 'data')]
)
def update_key_metrics(pattern_data, swarm_health, haven_risk, agent_stats):
    total = pattern_data['total_patterns']
    growth_text = f"+{total} this session"

    health_val = swarm_health['value']
    health_display = f"{health_val:.0f}"
    if health_val >= 90:
        health_status = "Excellent"
        health_color = COLORS['success']
    elif health_val >= 70:
        health_status = "Good"
        health_color = COLORS['info']
    else:
        health_status = "Needs Attention"
        health_color = COLORS['warning']

    risk = haven_risk['current_risk']
    if risk < 50:
        risk_level = "LOW"
        risk_color = COLORS['success']
    elif risk < 85:
        risk_level = "MEDIUM"
        risk_color = COLORS['warning']
    else:
        risk_level = "HIGH"
        risk_color = COLORS['danger']

    active_count = len(agent_stats)

    return (
        f"{total:,}",
        growth_text,
        health_display,
        html.Span(health_status, style={'color': health_color}),
        html.Span(risk_level, style={'color': risk_color}),
        f"{risk:.0f}%",
        str(active_count)
    )

# === TAB RENDERER WITH ENHANCED STORYTELLING ===
@app.callback(
    Output('tab-content', 'children'),
    [Input('tabs', 'active_tab'),
     Input('interval', 'n_intervals')]
)
def render_tab_content(active_tab, n):
    # Get SQL patterns and synthesis for macro views
    sql_patterns = get_sql_patterns()
    synthesis = synthesize_cross_moat_intelligence(sql_patterns)

    if active_tab == 'tab-executive-summary':
        # MACRO VIEW: Cross-Moat Intelligence Summary
        return dbc.Container(fluid=True, children=[
            # Cross-Moat Synthesis Card
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader(html.H5("What's Happening Right Now", style={'color': COLORS['text']})),
                        dbc.CardBody([
                            html.P(f"Last updated: {datetime.now().strftime('%H:%M:%S')}",
                                  style={'color': COLORS['text_muted'], 'fontSize': '0.875rem', 'marginBottom': '20px'}),

                            # Signal Strength Badge
                            html.Div([
                                html.Span(
                                    synthesis['signal_strength'] + " SIGNAL",
                                    style={
                                        'backgroundColor': COLORS['danger'] if synthesis['alignment_count'] >= 4
                                                         else COLORS['warning'] if synthesis['alignment_count'] == 3
                                                         else COLORS['info'] if synthesis['alignment_count'] == 2
                                                         else COLORS['text_muted'],
                                        'color': 'white',
                                        'padding': '8px 20px',
                                        'borderRadius': '20px',
                                        'fontSize': '0.875rem',
                                        'fontWeight': '700',
                                        'textTransform': 'uppercase'
                                    }
                                )
                            ], style={'marginBottom': '24px'}),

                            # Friend-to-friend briefing
                            html.P(synthesis['briefing'],
                                  style={'fontSize': '1.125rem', 'lineHeight': '1.75', 'color': COLORS['text'], 'marginBottom': '24px'}),

                            html.P(synthesis['recommendation'],
                                  style={'fontSize': '1rem', 'lineHeight': '1.75', 'color': COLORS['text_muted']}),
                        ])
                    ], style={'backgroundColor': COLORS['card']})
                ], width=12),
            ]),

            # 5 Moat Status Grid
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader(html.H5("5-Pillar Moat Intelligence", style={'color': COLORS['text']})),
                        dbc.CardBody([
                            dbc.Row([
                                # Government
                                dbc.Col([
                                    html.Div([
                                        html.H6("GOVERNMENT", style={'color': COLORS['text_muted'], 'fontSize': '0.75rem', 'marginBottom': '8px'}),
                                        html.H4(synthesis['moat_details']['Government']['strength'],
                                               style={'color': COLORS['success'] if synthesis['moat_details']['Government']['strength'] == 'Strong'
                                                     else COLORS['warning'] if synthesis['moat_details']['Government']['strength'] == 'Moderate'
                                                     else COLORS['text_muted'], 'fontWeight': '600'}),
                                        html.P(f"{synthesis['moat_details']['Government']['value']:.0f}% confidence",
                                              style={'color': COLORS['text_muted'], 'fontSize': '0.75rem'})
                                    ], style={'textAlign': 'center', 'padding': '20px', 'backgroundColor': COLORS['background'], 'borderRadius': '12px'})
                                ], width=2),
                                # Logistics
                                dbc.Col([
                                    html.Div([
                                        html.H6("LOGISTICS", style={'color': COLORS['text_muted'], 'fontSize': '0.75rem', 'marginBottom': '8px'}),
                                        html.H4(synthesis['moat_details']['Logistics']['strength'],
                                               style={'color': COLORS['success'] if synthesis['moat_details']['Logistics']['strength'] == 'Strong'
                                                     else COLORS['warning'] if synthesis['moat_details']['Logistics']['strength'] == 'Moderate'
                                                     else COLORS['text_muted'], 'fontWeight': '600'}),
                                        html.P(f"{synthesis['moat_details']['Logistics']['value']:.0f}% confidence",
                                              style={'color': COLORS['text_muted'], 'fontSize': '0.75rem'})
                                    ], style={'textAlign': 'center', 'padding': '20px', 'backgroundColor': COLORS['background'], 'borderRadius': '12px'})
                                ], width=2),
                                # Corporations
                                dbc.Col([
                                    html.Div([
                                        html.H6("CORPORATIONS", style={'color': COLORS['text_muted'], 'fontSize': '0.75rem', 'marginBottom': '8px'}),
                                        html.H4(synthesis['moat_details']['Corporations']['strength'],
                                               style={'color': COLORS['success'] if synthesis['moat_details']['Corporations']['strength'] == 'Strong'
                                                     else COLORS['warning'] if synthesis['moat_details']['Corporations']['strength'] == 'Moderate'
                                                     else COLORS['text_muted'], 'fontWeight': '600'}),
                                        html.P(f"{synthesis['moat_details']['Corporations']['value']:.0f}% confidence",
                                              style={'color': COLORS['text_muted'], 'fontSize': '0.75rem'})
                                    ], style={'textAlign': 'center', 'padding': '20px', 'backgroundColor': COLORS['background'], 'borderRadius': '12px'})
                                ], width=2),
                                # Code
                                dbc.Col([
                                    html.Div([
                                        html.H6("CODE", style={'color': COLORS['text_muted'], 'fontSize': '0.75rem', 'marginBottom': '8px'}),
                                        html.H4(synthesis['moat_details']['Code']['strength'],
                                               style={'color': COLORS['success'] if synthesis['moat_details']['Code']['strength'] == 'Strong'
                                                     else COLORS['warning'] if synthesis['moat_details']['Code']['strength'] == 'Moderate'
                                                     else COLORS['text_muted'], 'fontWeight': '600'}),
                                        html.P(f"{synthesis['moat_details']['Code']['value']:.0f}% confidence",
                                              style={'color': COLORS['text_muted'], 'fontSize': '0.75rem'})
                                    ], style={'textAlign': 'center', 'padding': '20px', 'backgroundColor': COLORS['background'], 'borderRadius': '12px'})
                                ], width=2),
                                # Finance
                                dbc.Col([
                                    html.Div([
                                        html.H6("FINANCE", style={'color': COLORS['text_muted'], 'fontSize': '0.75rem', 'marginBottom': '8px'}),
                                        html.H4(synthesis['moat_details']['Finance']['strength'],
                                               style={'color': COLORS['success'] if synthesis['moat_details']['Finance']['strength'] == 'Strong'
                                                     else COLORS['warning'] if synthesis['moat_details']['Finance']['strength'] == 'Moderate'
                                                     else COLORS['text_muted'], 'fontWeight': '600'}),
                                        html.P(f"{synthesis['moat_details']['Finance']['value']:.0f}% confidence",
                                              style={'color': COLORS['text_muted'], 'fontSize': '0.75rem'})
                                    ], style={'textAlign': 'center', 'padding': '20px', 'backgroundColor': COLORS['background'], 'borderRadius': '12px'})
                                ], width=2),
                                # Alignment Count
                                dbc.Col([
                                    html.Div([
                                        html.H6("ALIGNED", style={'color': COLORS['text_muted'], 'fontSize': '0.75rem', 'marginBottom': '8px'}),
                                        html.H4(f"{synthesis['alignment_count']}/5",
                                               style={'color': '#fbbf24', 'fontWeight': '700'}),
                                        html.P("moats strong",
                                              style={'color': COLORS['text_muted'], 'fontSize': '0.75rem'})
                                    ], style={'textAlign': 'center', 'padding': '20px', 'backgroundColor': COLORS['background'], 'borderRadius': '12px'})
                                ], width=2),
                            ])
                        ])
                    ], style={'backgroundColor': COLORS['card']})
                ], width=12),
            ], className='mt-3'),

            # High Priority Patterns
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader(html.H5("Patterns You Should Know About", style={'color': COLORS['text']})),
                        dbc.CardBody([
                            html.P("These are the most interesting things happening right now",
                                  style={'color': COLORS['text_muted'], 'marginBottom': '20px'}),
                            html.Div([
                                html.Div([
                                    html.Span(f"{p['pattern_value']:.0f}% CONFIDENCE",
                                             style={'backgroundColor': COLORS['warning'], 'color': 'white', 'padding': '4px 12px',
                                                   'borderRadius': '12px', 'fontSize': '0.75rem', 'fontWeight': '700', 'marginBottom': '12px', 'display': 'inline-block'}),
                                    html.P(explain_pattern_plain_english(p),
                                          style={'fontSize': '1.125rem', 'lineHeight': '1.75', 'color': COLORS['text'], 'marginTop': '12px', 'marginBottom': '8px'}),
                                    html.Small(f"Spotted at {datetime.fromtimestamp(p['timestamp']).strftime('%H:%M:%S')}",
                                              style={'color': COLORS['text_muted']})
                                ], style={'padding': '20px', 'backgroundColor': COLORS['background'], 'borderRadius': '12px', 'marginBottom': '16px',
                                         'border': f"1px solid {COLORS['border']}"})
                                for p in [p for p in sql_patterns if p['pattern_value'] >= 70][:3]
                            ]) if any(p['pattern_value'] >= 70 for p in sql_patterns) else html.P(
                                "Your agents are actively searching for patterns. Give them a moment!",
                                style={'color': COLORS['text_muted'], 'fontStyle': 'italic'})
                        ])
                    ], style={'backgroundColor': COLORS['card']})
                ], width=12),
            ], className='mt-3'),
        ])

    elif active_tab == 'tab-trifecta-pnl':
        return dbc.Container(fluid=True, children=[
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader(html.H5("💰 Trifecta P&L Dashboard - BIG ROCK 41 (Corrected)", style={'color': '#fbbf24'})),
                        dbc.CardBody([
                            html.P([
                                "The ", html.Strong("Synthesis Gateway", style={'color': '#fbbf24'}),
                                " executes trades ONLY when both Mycelial AI patterns and Baseline TA signals AGREE (Signal Collisions). ",
                                "This creates the highest-conviction \"Synthesized Signal\" - our primary product."
                            ], style={'color': COLORS['text'], 'marginBottom': '20px'}),
                            dbc.Row([
                                dbc.Col([
                                    dbc.Card([
                                        dbc.CardBody([
                                            html.H6("⚪ Baseline P&L", style={'color': COLORS['text_muted']}),
                                            html.H3(id='baseline-pnl-metric', children="0.00%", style={'color': COLORS['text_muted'], 'fontWeight': '700'}),
                                            html.P(id='baseline-trades-count', children="0 trades", style={'color': COLORS['text_muted'], 'fontSize': '0.9rem'}),
                                        ])
                                    ], style={'backgroundColor': COLORS['background']})
                                ], width=4),
                                dbc.Col([
                                    dbc.Card([
                                        dbc.CardBody([
                                            html.H6("💜 Mycelial P&L", style={'color': COLORS['primary']}),
                                            html.H3(id='mycelial-pnl-metric', children="0.00%", style={'color': COLORS['primary'], 'fontWeight': '700'}),
                                            html.P(id='mycelial-trades-count', children="0 trades", style={'color': COLORS['text_muted'], 'fontSize': '0.9rem'}),
                                        ])
                                    ], style={'backgroundColor': COLORS['background']})
                                ], width=4),
                                dbc.Col([
                                    dbc.Card([
                                        dbc.CardBody([
                                            html.H6("✓ Synthesized P&L (GOLD)", style={'color': '#fbbf24'}),
                                            html.H3(id='synthesized-pnl-metric', children="0.00%", style={'color': '#fbbf24', 'fontWeight': '700'}),
                                            html.P(id='synthesized-trades-count', children="0 collisions", style={'color': COLORS['text_muted'], 'fontSize': '0.9rem'}),
                                        ])
                                    ], style={'backgroundColor': COLORS['background']})
                                ], width=4),
                            ])
                        ])
                    ], style={'backgroundColor': COLORS['card']})
                ], width=12),
            ]),
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader(html.H5("📈 Trifecta P&L Over Time", style={'color': COLORS['text']})),
                        dbc.CardBody([
                            dcc.Graph(id='trifecta-pnl-chart'),
                        ])
                    ], style={'backgroundColor': COLORS['card']})
                ], width=12),
            ], className='mt-3'),
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader(html.H5("📋 Live Trade Ledger (Signal Collisions)", style={'color': COLORS['text']})),
                        dbc.CardBody([
                            html.Div(id='trade-ledger', style={
                                'maxHeight': '400px',
                                'overflowY': 'scroll'
                            })
                        ])
                    ], style={'backgroundColor': COLORS['card']})
                ], width=12),
            ], className='mt-3'),
        ])

    elif active_tab == 'tab-pattern-discovery':
        return dbc.Container(fluid=True, children=[
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader(html.H5("🔍 Intelligent Pattern Discovery Dashboard", style={'color': COLORS['text']})),
                        dbc.CardBody([
                            html.Div(id='pattern-headlines')
                        ])
                    ], style={'backgroundColor': COLORS['card']})
                ], width=12),
            ]),
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader(html.H5("📋 Pattern Catalog (Semantic Analysis)", style={'color': COLORS['text']})),
                        dbc.CardBody([
                            html.Div(id='pattern-catalog', style={
                                'maxHeight': '500px',
                                'overflowY': 'scroll'
                            })
                        ])
                    ], style={'backgroundColor': COLORS['card']})
                ], width=12),
            ], className='mt-3'),
        ])

    elif active_tab == 'tab-agent-activity':
        return dbc.Container(fluid=True, children=[
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader(html.H5("🧠 Agent Performance Leaderboard", style={'color': COLORS['text']})),
                        dbc.CardBody([
                            dcc.Graph(id='agent-leaderboard'),
                        ])
                    ], style={'backgroundColor': COLORS['card']})
                ], width=6),
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader(html.H5("📡 Agent Collaboration Network (Real)", style={'color': COLORS['text']})),
                        dbc.CardBody([
                            dcc.Graph(id='agent-network'),
                        ])
                    ], style={'backgroundColor': COLORS['card']})
                ], width=6),
            ]),
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader(html.H5("📊 Agent Type Summary", style={'color': COLORS['text']})),
                        dbc.CardBody([
                            html.Div(id='agent-type-summary')
                        ])
                    ], style={'backgroundColor': COLORS['card']})
                ], width=12),
            ], className='mt-3'),
        ])

    elif active_tab == 'tab-moats':
        return dbc.Container(fluid=True, children=[
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader(html.H5("🏰 5-Pillar Moat Health", style={'color': COLORS['text']})),
                        dbc.CardBody([
                            dcc.Graph(id='moat-health-chart'),
                        ])
                    ], style={'backgroundColor': COLORS['card']})
                ], width=12),
            ]),
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H6("💰 Finance Moat", style={'color': COLORS['primary']}),
                            html.Div(id='finance-moat-detail'),
                        ])
                    ], style={'backgroundColor': COLORS['card']})
                ], width=4),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H6("💻 Code Innovation Moat", style={'color': COLORS['success']}),
                            html.Div(id='code-moat-detail'),
                        ])
                    ], style={'backgroundColor': COLORS['card']})
                ], width=4),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H6("🚚 Logistics Moat", style={'color': COLORS['warning']}),
                            html.Div(id='logistics-moat-detail'),
                        ])
                    ], style={'backgroundColor': COLORS['card']})
                ], width=4),
            ], className='mt-3'),
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H6("🏛️ Government Moat", style={'color': COLORS['info']}),
                            html.Div(id='govt-moat-detail'),
                        ])
                    ], style={'backgroundColor': COLORS['card']})
                ], width=6),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H6("🏢 US Corporations Moat", style={'color': COLORS['corp']}),
                            html.Div(id='corp-moat-detail'),
                        ])
                    ], style={'backgroundColor': COLORS['card']})
                ], width=6),
            ], className='mt-3'),
        ])

    elif active_tab == 'tab-agent-cards':
        return dbc.Container(fluid=True, children=[
            dbc.Row([
                dbc.Col([
                    html.H5("🎴 Agent Card Browser (Dynamic Discovery)", style={'color': COLORS['text'], 'marginBottom': '20px'}),
                    html.P("Browse through all discovered agents. Metadata is auto-generated from agent IDs.",
                          style={'color': COLORS['text_muted']}),
                ], width=12),
            ]),
            dbc.Row([
                dbc.Col([
                    dbc.Button("← Previous", id='prev-agent-btn', color='secondary', className='me-2'),
                    dbc.Button("Next →", id='next-agent-btn', color='secondary'),
                ], width=12, className='mb-3'),
            ]),
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody(id='agent-card-display')
                    ], style={'backgroundColor': COLORS['card']})
                ], width=12),
            ]),
        ])

    elif active_tab == 'tab-analytics':
        return dbc.Container(fluid=True, children=[
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader(html.H5("📈 Swarm Health Over Time", style={'color': COLORS['text']})),
                        dbc.CardBody([
                            dcc.Graph(id='swarm-health-chart'),
                        ])
                    ], style={'backgroundColor': COLORS['card']})
                ], width=6),
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader(html.H5("🎯 Interestingness Distribution", style={'color': COLORS['text']})),
                        dbc.CardBody([
                            dcc.Graph(id='interestingness-dist'),
                        ])
                    ], style={'backgroundColor': COLORS['card']})
                ], width=6),
            ]),
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader(html.H5("📊 Pattern Discovery Timeline", style={'color': COLORS['text']})),
                        dbc.CardBody([
                            dcc.Graph(id='pattern-timeline'),
                        ])
                    ], style={'backgroundColor': COLORS['card']})
                ], width=12),
            ], className='mt-3'),
        ])

    return html.Div("Select a tab")

# === PATTERN HEADLINES WITH SEMANTIC DESCRIPTIONS ===
@app.callback(
    Output('pattern-headlines', 'children'),
    [Input('pattern-details-store', 'data')]
)
def update_pattern_headlines(pattern_details):
    if not pattern_details:
        return html.P("No intelligent patterns discovered yet...", style={'color': COLORS['text_muted']})

    # Get latest 5 patterns
    recent = pattern_details[-5:]

    headlines = []
    for p in reversed(recent):
        moat_color = {
            'Finance': COLORS['primary'],
            'Code Innovation': COLORS['success'],
            'Logistics': COLORS['warning'],
            'Government': COLORS['info'],
            'US Corporations': COLORS['corp'],
            'Cross-Moat': '#9333ea'
        }.get(p['moat'], COLORS['text'])

        type_badges = {
            'anomaly': ('⚡ Anomaly', COLORS['danger']),
            'cluster': ('🎯 Cluster', COLORS['info']),
            'correlation': ('🔗 Correlation', COLORS['warning']),
            'observation': ('📊 Observation', COLORS['text_muted'])
        }
        badge_text, badge_color = type_badges.get(p['type'], ('📊 Pattern', COLORS['text']))

        # BIG ROCK 32: Show RAW PATTERN DATA instead of vague descriptions
        pattern_raw = p.get('pattern', 'No data')  # e.g., "close: 94.24 | RSI: 72.3 | ATR: 1.45"

        headlines.append(dbc.Alert([
            html.Div([
                html.Span(badge_text, style={
                    'backgroundColor': badge_color,
                    'color': 'white',
                    'padding': '2px 8px',
                    'borderRadius': '12px',
                    'fontSize': '0.75rem',
                    'marginRight': '10px'
                }),
                html.Span(f" {p['moat']}", style={'color': moat_color, 'fontWeight': '600'})
            ], style={'marginBottom': '10px'}),
            # Show RAW data instead of semantic description
            html.P([
                html.Strong("Raw Data: ", style={'color': COLORS['text_muted']}),
                html.Span(pattern_raw, style={'color': COLORS['text'], 'fontFamily': 'monospace'})
            ], style={'marginBottom': '5px', 'fontSize': '0.9rem'}),
            html.P(p['semantic_description'], style={'marginBottom': '5px', 'fontSize': '0.85rem', 'color': COLORS['text_muted'], 'fontStyle': 'italic'}),
            html.Small([
                f"Agents: {', '.join(p['agents'][:3])} | ",
                f"Confidence: {p['confidence']*100:.0f}% | ",
                f"Effectiveness: {p.get('effectiveness_score', 0):.0f}% | ",
                f"{p['time']}"
            ], style={'color': COLORS['text_muted']})
        ], color='dark', style={'marginBottom': '10px', 'borderLeft': f'4px solid {moat_color}'}))

    return headlines

# === PATTERN CATALOG WITH RICH METADATA ===
@app.callback(
    Output('pattern-catalog', 'children'),
    [Input('pattern-details-store', 'data')]
)
def update_pattern_catalog(pattern_details):
    if not pattern_details:
        return html.P("No patterns discovered yet...", style={'color': COLORS['text_muted']})

    # Group patterns by moat and type
    moat_groups = {}
    for p in pattern_details:
        moat = p['moat']
        if moat not in moat_groups:
            moat_groups[moat] = {'anomaly': [], 'cluster': [], 'correlation': [], 'observation': []}
        moat_groups[moat][p['type']].append(p)

    catalog = []
    for moat, type_groups in moat_groups.items():
        moat_color = {
            'Finance': COLORS['primary'],
            'Code Innovation': COLORS['success'],
            'Logistics': COLORS['warning'],
            'Government': COLORS['info'],
            'US Corporations': COLORS['corp'],
            'Cross-Moat': '#9333ea'
        }.get(moat, COLORS['text'])

        total_patterns = sum(len(patterns) for patterns in type_groups.values())

        moat_content = []
        for ptype in ['anomaly', 'cluster', 'correlation', 'observation']:
            patterns = type_groups[ptype]
            if patterns:
                type_header = {
                    'anomaly': '⚡ Anomalies',
                    'cluster': '🎯 Clusters',
                    'correlation': '🔗 Correlations',
                    'observation': '📊 Observations'
                }[ptype]

                moat_content.append(html.H6(f"{type_header} ({len(patterns)})",
                                           style={'color': COLORS['text'], 'marginTop': '15px', 'marginBottom': '10px'}))

                for p in reversed(patterns[-10:]):  # Show last 10 per type
                    # BIG ROCK 32: Show RAW pattern data
                    pattern_raw = p.get('pattern', 'No raw data available')
                    moat_content.append(html.P([
                        html.Strong(f"[{p['time']}] ", style={'color': COLORS['text_muted']}),
                        html.Span(pattern_raw, style={'color': COLORS['text'], 'fontFamily': 'monospace', 'fontSize': '0.9rem'}),
                        html.Br(),
                        html.Small(p['semantic_description'], style={'color': COLORS['text_muted'], 'fontStyle': 'italic'}),
                        html.Br(),
                        html.Small([
                            f"Agents: {', '.join(p['agents'][:5])} | ",
                            f"Confidence: {p.get('confidence', 0)*100:.0f}% | ",
                            f"Effectiveness: {p['effectiveness_score']:.0f}%"
                        ], style={'color': COLORS['text_muted']})
                    ], style={'marginBottom': '15px', 'paddingLeft': '10px', 'borderLeft': f'2px solid {moat_color}'}))

        catalog.append(dbc.Card([
            dbc.CardHeader(html.H6(f"{moat} ({total_patterns} patterns)", style={'color': moat_color})),
            dbc.CardBody(moat_content if moat_content else [
                html.P("No patterns yet", style={'color': COLORS['text_muted']})
            ])
        ], style={'backgroundColor': COLORS['background'], 'marginBottom': '15px'}))

    return catalog

# === AGENT LEADERBOARD (DYNAMIC METADATA) ===
@app.callback(
    Output('agent-leaderboard', 'figure'),
    [Input('agent-stats-store', 'data')]
)
def update_agent_leaderboard(agent_stats):
    if not agent_stats:
        return go.Figure()

    # Calculate real interestingness scores with DYNAMIC metadata
    scores = []
    for agent_id, agent_data in agent_stats.items():
        interest_score = calculate_interestingness(agent_data, agent_stats)
        agent_meta = discover_agent_metadata(agent_id)
        scores.append((agent_id, agent_meta['name'], interest_score))

    # Sort and take top 15
    scores.sort(key=lambda x: x[2], reverse=True)
    scores = scores[:15]

    if not scores:
        return go.Figure()

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=[s[1] for s in scores],  # Use friendly name
        x=[s[2] for s in scores],
        orientation='h',
        marker=dict(color=[s[2] for s in scores], colorscale='Purples', showscale=False),
        text=[f"{s[2]:.1f}" for s in scores],
        textposition='outside',
        hovertext=[s[0] for s in scores],  # Show full ID on hover
        hoverinfo='text+x'
    ))

    fig.update_layout(
        title=dict(text="Top 15 Agents by Interestingness (Dynamic Discovery)", font=dict(color=COLORS['text'], size=14)),
        plot_bgcolor=COLORS['card'],
        paper_bgcolor=COLORS['card'],
        font=dict(color=COLORS['text_muted']),
        xaxis=dict(title='Interestingness Score (0-100)', gridcolor=COLORS['border']),
        yaxis=dict(gridcolor=COLORS['border']),
        margin=dict(l=150, r=20, t=60, b=40),
        height=500
    )
    return fig

# === AGENT COLLABORATION NETWORK (REAL COLLABORATION TRACKING) ===
@app.callback(
    Output('agent-network', 'figure'),
    [Input('agent-stats-store', 'data'),
     Input('collaboration-store', 'data')]
)
def update_agent_network(agent_stats, collaboration_data):
    active_agents = list(agent_stats.keys())[:30]  # Show top 30
    if not active_agents:
        return go.Figure()

    num_agents = len(active_agents)
    x_pos = [math.cos(2 * math.pi * i / num_agents) for i in range(num_agents)]
    y_pos = [math.sin(2 * math.pi * i / num_agents) for i in range(num_agents)]

    fig = go.Figure()

    # Add edges based on REAL collaboration data
    for i, agent1 in enumerate(active_agents):
        collaborators = collaboration_data.get(agent1, [])
        for agent2 in collaborators:
            if agent2 in active_agents:
                j = active_agents.index(agent2)
                fig.add_trace(go.Scatter(
                    x=[x_pos[i], x_pos[j]],
                    y=[y_pos[i], y_pos[j]],
                    mode='lines',
                    line=dict(color=COLORS['primary'], width=2, dash='dot'),
                    showlegend=False,
                    hoverinfo='skip'
                ))

    # Add nodes with dynamic metadata
    node_colors = []
    node_names = []
    node_hovertexts = []
    for agent_id in active_agents:
        meta = discover_agent_metadata(agent_id)
        node_colors.append(meta['color'])
        node_names.append(meta['name'][:10])  # Truncate for display
        collab_count = len(collaboration_data.get(agent_id, []))
        node_hovertexts.append(f"{meta['name']}<br>Product: {meta['product']}<br>Collaborators: {collab_count}")

    fig.add_trace(go.Scatter(
        x=x_pos,
        y=y_pos,
        mode='markers+text',
        marker=dict(size=20, color=node_colors, line=dict(color=COLORS['text'], width=2)),
        text=node_names,
        textposition='top center',
        textfont=dict(color=COLORS['text'], size=8),
        hovertext=node_hovertexts,
        hoverinfo='text',
        showlegend=False
    ))

    fig.update_layout(
        title=dict(text="Agent Collaboration Network (Real Connections)", font=dict(color=COLORS['text'], size=14)),
        plot_bgcolor=COLORS['card'],
        paper_bgcolor=COLORS['card'],
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        margin=dict(l=20, r=20, t=60, b=20),
        height=500
    )
    return fig

# === AGENT TYPE SUMMARY (DYNAMIC) ===
@app.callback(
    Output('agent-type-summary', 'children'),
    [Input('agent-stats-store', 'data')]
)
def update_agent_type_summary(agent_stats):
    # Count real active agents by type using dynamic discovery
    type_counts = defaultdict(int)
    for agent_id in agent_stats.keys():
        meta = discover_agent_metadata(agent_id)
        type_counts[meta['type']] += 1

    summary_items = []
    type_icons = {
        'Pattern Learner': ('fa-brain', COLORS['primary'], 'Analyzing data streams, discovering correlations, sharing policies'),
        'Data Engineer': ('fa-database', COLORS['primary'], 'Collecting market data from Finance moat'),
        'Code Scraper': ('fa-code', COLORS['success'], 'Mining GitHub repositories for code innovation patterns'),
        'Logistics Miner': ('fa-truck', COLORS['warning'], 'Tracking logistics flow and cargo velocity'),
        'Government Analyst': ('fa-landmark', COLORS['info'], 'Monitoring government policy and regulatory shifts'),
        'Corporate Analyst': ('fa-building', COLORS['corp'], 'Analyzing corporate earnings and M&A activity'),
        'HAVEN Guardian': ('fa-shield-alt', COLORS['danger'], 'Monitoring system risk, blocking policy contagion at 85% threshold'),
        'Evolution Engine': ('fa-cogs', '#9333ea', 'Autonomously creating new specialized agents when gaps detected'),
        'Action Agent': ('fa-bolt', '#fbbf24', 'Executing high-confidence pattern predictions')
    }

    for agent_type, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
        if agent_type in type_icons:
            icon, color, activity = type_icons[agent_type]
        else:
            icon, color, activity = 'fa-robot', COLORS['text_muted'], 'Unknown activity'

        summary_items.append(dbc.Card([
            dbc.CardBody([
                html.Div([
                    html.I(className=f"fas {icon} fa-2x", style={'color': color, 'marginRight': '15px'}),
                    html.Div([
                        html.H6(f"{agent_type} ({count})", style={'color': COLORS['text'], 'marginBottom': '5px'}),
                        html.P(activity, style={'color': COLORS['text_muted'], 'fontSize': '0.9rem', 'marginBottom': '0'}),
                    ], style={'flex': 1})
                ], style={'display': 'flex', 'alignItems': 'center'})
            ])
        ], style={'backgroundColor': COLORS['background'], 'marginBottom': '10px'}))

    return summary_items

# === MOAT HEALTH CHART ===
@app.callback(
    Output('moat-health-chart', 'figure'),
    [Input('moat-health-store', 'data')]
)
def update_moat_health_chart(moat_health):
    pillars = list(moat_health.keys())
    values = list(moat_health.values())
    colors_list = [COLORS['primary'], COLORS['success'], COLORS['warning'], COLORS['info'], COLORS['corp']]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=pillars,
        y=values,
        marker=dict(color=colors_list),
        text=[f"{v:.0f}%" for v in values],
        textposition='outside'
    ))

    fig.update_layout(
        title=dict(text="5-Pillar Moat Health (0-100%)", font=dict(color=COLORS['text'], size=16)),
        plot_bgcolor=COLORS['card'],
        paper_bgcolor=COLORS['card'],
        font=dict(color=COLORS['text_muted']),
        xaxis=dict(gridcolor=COLORS['border']),
        yaxis=dict(title='Health %', gridcolor=COLORS['border'], range=[0, 100]),
        margin=dict(l=40, r=20, t=60, b=80),
        showlegend=False
    )
    return fig

# === MOAT DETAILS ===
@app.callback(
    [Output('finance-moat-detail', 'children'),
     Output('code-moat-detail', 'children'),
     Output('logistics-moat-detail', 'children'),
     Output('govt-moat-detail', 'children'),
     Output('corp-moat-detail', 'children')],
    [Input('moat-health-store', 'data'),
     Input('moat-stats-store', 'data')]
)
def update_moat_details(moat_health, moat_stats):
    def create_detail(moat_name):
        health = moat_health.get(moat_name, 100)
        patterns = moat_stats.get(moat_name, {}).get('patterns', 0)
        agents_list = moat_stats.get(moat_name, {}).get('agents', [])
        agents_count = len(agents_list) if isinstance(agents_list, list) else 0

        return html.Div([
            html.P(f"Health: {health:.0f}%", style={'color': COLORS['text'], 'fontSize': '1.2rem', 'fontWeight': '600'}),
            html.P(f"Patterns: {patterns}", style={'color': COLORS['text_muted'], 'fontSize': '0.9rem'}),
            html.P(f"Active Agents: {agents_count}", style={'color': COLORS['text_muted'], 'fontSize': '0.9rem'}),
        ])

    return (
        create_detail('Finance'),
        create_detail('Code Innovation'),
        create_detail('Logistics'),
        create_detail('Government'),
        create_detail('US Corporations')
    )

# === AGENT CARD NAVIGATION ===
@app.callback(
    Output('agent-carousel-index', 'data'),
    [Input('prev-agent-btn', 'n_clicks'),
     Input('next-agent-btn', 'n_clicks')],
    [State('agent-carousel-index', 'data'),
     State('agent-stats-store', 'data')]
)
def navigate_agent_cards(prev_clicks, next_clicks, current_index, agent_stats):
    if not agent_stats:
        return 0

    agent_list = list(agent_stats.keys())
    max_index = len(agent_list) - 1

    ctx = dash.callback_context
    if not ctx.triggered:
        return current_index

    button_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if button_id == 'prev-agent-btn' and prev_clicks:
        current_index = max(0, current_index - 1)
    elif button_id == 'next-agent-btn' and next_clicks:
        current_index = min(max_index, current_index + 1)

    return current_index

# === AGENT CARD DISPLAY (DYNAMIC METADATA) ===
@app.callback(
    Output('agent-card-display', 'children'),
    [Input('agent-carousel-index', 'data'),
     Input('agent-stats-store', 'data'),
     Input('collaboration-store', 'data')]
)
def update_agent_card_display(carousel_index, agent_stats, collaboration_data):
    if not agent_stats:
        return html.P("No agents active yet...", style={'color': COLORS['text_muted']})

    agent_list = list(agent_stats.keys())
    if carousel_index >= len(agent_list):
        carousel_index = 0

    agent_id = agent_list[carousel_index]
    agent_meta = discover_agent_metadata(agent_id)  # DYNAMIC!
    agent_data = agent_stats[agent_id]

    # Calculate REAL interestingness
    interestingness = calculate_interestingness(agent_data, agent_stats)

    # Count REAL children
    children_count = len([aid for aid, adata in agent_stats.items()
                         if adata.get('parent') == agent_id])

    # Get collaborators
    collaborators = collaboration_data.get(agent_id, [])

    # Build stats with REAL data (BIG ROCK 33: Include Pattern Decay)
    pattern_age_minutes = agent_data.get('pattern_age_minutes', 0)
    pattern_decay_factor = agent_data.get('pattern_decay_factor', 1.0)
    pattern_current_value = agent_data.get('pattern_current_value', 0)

    stats = {
        'Interestingness Score': f"{interestingness:.1f}/100",
        'Generation': agent_data.get('generation', 0),
        'Patterns Discovered': agent_data.get('patterns_discovered', 0),
        'Policy Shares': agent_data.get('policy_shares', 0),
        'Pattern Age': f"{pattern_age_minutes:.1f} min" if pattern_age_minutes else "N/A",
        'Pattern Decay': f"{(1-pattern_decay_factor)*100:.1f}% decayed" if pattern_decay_factor < 1.0 else "Fresh",
        'Current Value': f"{pattern_current_value:.1f}/100" if pattern_current_value else "N/A",
        'Parent': agent_data.get('parent', 'Genesis'),
        'Children': children_count,
        'Collaborators': len(collaborators),
        'Status': agent_data.get('status', 'Active'),
        'Last Active': agent_data.get('last_active', 'Never')
    }

    # Top 3 collaborators with friendly names
    collab_display = []
    for collab_id in collaborators[:3]:
        collab_meta = discover_agent_metadata(collab_id)
        collab_display.append(collab_meta['name'])

    return html.Div([
        dbc.Row([
            dbc.Col([
                html.Div([
                    html.I(className=f"fas {agent_meta['icon']} fa-5x", style={'color': agent_meta['color']}),
                ], style={'textAlign': 'center', 'padding': '2rem'}),
            ], width=3),
            dbc.Col([
                html.H3(agent_meta['name'], style={'color': agent_meta['color'], 'fontWeight': '700'}),
                html.H5(f"ID: {agent_id}", style={'color': COLORS['text_muted']}),
                html.P(f"Type: {agent_meta['type']}", style={'color': COLORS['text'], 'fontSize': '1.1rem'}),
                html.P(f"Product Moat: {agent_meta['product']}", style={'color': COLORS['text'], 'fontSize': '1.1rem'}),
                html.P(f"Agent {carousel_index + 1} of {len(agent_list)}", style={'color': COLORS['text_muted'], 'fontSize': '0.9rem'}),
            ], width=9),
        ]),
        html.Hr(style={'borderColor': COLORS['border']}),
        dbc.Row([
            dbc.Col([
                html.H5("📊 Agent Statistics (Real Data)", style={'color': COLORS['primary'], 'marginBottom': '1rem'}),
                html.Div([
                    html.P([
                        html.Strong(f"{k}: ", style={'color': COLORS['text_muted']}),
                        html.Span(f"{v}", style={'color': COLORS['text']})
                    ], style={'marginBottom': '0.5rem'})
                    for k, v in stats.items()
                ])
            ], width=6),
            dbc.Col([
                html.H5("🤝 Top Collaborators", style={'color': COLORS['success'], 'marginBottom': '1rem'}),
                html.Div([
                    html.P(name, style={'color': COLORS['text'], 'marginBottom': '0.5rem'})
                    for name in (collab_display if collab_display else ['No collaborations yet'])
                ])
            ], width=6),
        ]),
    ])

# === SWARM HEALTH CHART ===
@app.callback(
    Output('swarm-health-chart', 'figure'),
    [Input('swarm-health-store', 'data')]
)
def update_swarm_health_chart(swarm_health):
    history = swarm_health.get('history', [100])

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        y=history,
        mode='lines+markers',
        line=dict(color=COLORS['success'], width=3),
        marker=dict(size=6, color=COLORS['success']),
        fill='tozeroy',
        fillcolor=f'rgba(16, 185, 129, 0.2)',
    ))

    fig.update_layout(
        title=dict(text="Swarm Health Over Time (0-100)", font=dict(color=COLORS['text'], size=16)),
        plot_bgcolor=COLORS['card'],
        paper_bgcolor=COLORS['card'],
        font=dict(color=COLORS['text_muted']),
        xaxis=dict(title='Time', gridcolor=COLORS['border']),
        yaxis=dict(title='Health', gridcolor=COLORS['border'], range=[0, 100]),
        margin=dict(l=40, r=20, t=60, b=40),
    )
    return fig

# === INTERESTINGNESS DISTRIBUTION ===
@app.callback(
    Output('interestingness-dist', 'figure'),
    [Input('agent-stats-store', 'data')]
)
def update_interestingness_dist(agent_stats):
    if not agent_stats:
        return go.Figure()

    # Calculate REAL interestingness scores for all agents
    scores = []
    for agent_id, agent_data in agent_stats.items():
        score = calculate_interestingness(agent_data, agent_stats)
        scores.append(score)

    if not scores:
        return go.Figure()

    fig = go.Figure()
    fig.add_trace(go.Histogram(
        x=scores,
        nbinsx=20,
        marker=dict(color=COLORS['primary']),
    ))

    fig.update_layout(
        title=dict(text=f"Interestingness Score Distribution ({len(scores)} Active Agents)", font=dict(color=COLORS['text'], size=16)),
        plot_bgcolor=COLORS['card'],
        paper_bgcolor=COLORS['card'],
        font=dict(color=COLORS['text_muted']),
        xaxis=dict(title='Interestingness Score', gridcolor=COLORS['border']),
        yaxis=dict(title='Number of Agents', gridcolor=COLORS['border']),
        margin=dict(l=40, r=20, t=60, b=40),
    )
    return fig

# === PATTERN TIMELINE ===
@app.callback(
    Output('pattern-timeline', 'figure'),
    [Input('pattern-store', 'data')]
)
def update_pattern_timeline(pattern_data):
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=pattern_data.get('times', []),
        y=pattern_data.get('counts', []),
        mode='lines+markers',
        line=dict(color=COLORS['warning'], width=3),
        marker=dict(size=6, color=COLORS['warning']),
        fill='tozeroy',
        fillcolor=f'rgba(245, 158, 11, 0.2)',
        name='Patterns'
    ))

    fig.update_layout(
        title=dict(text="Cumulative Intelligent Pattern Discovery Timeline", font=dict(color=COLORS['text'], size=16)),
        plot_bgcolor=COLORS['card'],
        paper_bgcolor=COLORS['card'],
        font=dict(color=COLORS['text_muted']),
        xaxis=dict(title='Time', gridcolor=COLORS['border']),
        yaxis=dict(title='Total Patterns Discovered', gridcolor=COLORS['border']),
        margin=dict(l=40, r=20, t=60, b=40),
    )
    return fig

# === BIG ROCK 41 (Corrected): TRIFECTA P&L CALLBACKS ===
@app.callback(
    [Output('baseline-pnl-metric', 'children'),
     Output('baseline-trades-count', 'children'),
     Output('mycelial-pnl-metric', 'children'),
     Output('mycelial-trades-count', 'children'),
     Output('synthesized-pnl-metric', 'children'),
     Output('synthesized-trades-count', 'children')],
    [Input('trifecta-pnl-store', 'data')]
)
def update_trifecta_metrics(trifecta_pnl):
    """Update the three P&L metric cards."""
    baseline_pnl = trifecta_pnl['baseline_pnl'][-1] if trifecta_pnl['baseline_pnl'] else 0
    mycelial_pnl = trifecta_pnl['mycelial_pnl'][-1] if trifecta_pnl['mycelial_pnl'] else 0
    synthesized_pnl = trifecta_pnl['synthesized_pnl'][-1] if trifecta_pnl['synthesized_pnl'] else 0

    baseline_trades = trifecta_pnl.get('baseline_trades', 0)
    mycelial_trades = trifecta_pnl.get('mycelial_trades', 0)
    synthesized_trades = trifecta_pnl.get('synthesized_trades', 0)

    return (
        f"{baseline_pnl:+.2f}%",
        f"{baseline_trades} trades",
        f"{mycelial_pnl:+.2f}%",
        f"{mycelial_trades} trades",
        f"{synthesized_pnl:+.2f}%",
        f"{synthesized_trades} collisions"
    )

@app.callback(
    Output('trifecta-pnl-chart', 'figure'),
    [Input('trifecta-pnl-store', 'data')]
)
def update_trifecta_chart(trifecta_pnl):
    """Create the Trifecta P&L chart with three lines."""
    times = trifecta_pnl.get('times', [])
    baseline_pnl = trifecta_pnl.get('baseline_pnl', [0])
    mycelial_pnl = trifecta_pnl.get('mycelial_pnl', [0])
    synthesized_pnl = trifecta_pnl.get('synthesized_pnl', [0])

    fig = go.Figure()

    # Baseline (Gray)
    fig.add_trace(go.Scatter(
        x=list(range(len(baseline_pnl))),
        y=baseline_pnl,
        mode='lines+markers',
        name='Baseline TA',
        line=dict(color='#9ca3af', width=2),
        marker=dict(size=6, color='#9ca3af'),
    ))

    # Mycelial (Purple)
    fig.add_trace(go.Scatter(
        x=list(range(len(mycelial_pnl))),
        y=mycelial_pnl,
        mode='lines+markers',
        name='Mycelial AI',
        line=dict(color=COLORS['primary'], width=2),
        marker=dict(size=6, color=COLORS['primary']),
    ))

    # Synthesized (Gold) - THE PRIMARY PRODUCT
    fig.add_trace(go.Scatter(
        x=list(range(len(synthesized_pnl))),
        y=synthesized_pnl,
        mode='lines+markers',
        name='Synthesized (Signal Collisions)',
        line=dict(color='#fbbf24', width=4),
        marker=dict(size=10, color='#fbbf24', symbol='star'),
    ))

    fig.update_layout(
        title=dict(
            text="Trifecta P&L: Baseline vs Mycelial vs Synthesized (Primary Product)",
            font=dict(color=COLORS['text'], size=16)
        ),
        plot_bgcolor=COLORS['card'],
        paper_bgcolor=COLORS['card'],
        font=dict(color=COLORS['text_muted']),
        xaxis=dict(title='Data Points', gridcolor=COLORS['border']),
        yaxis=dict(title='Cumulative P&L (%)', gridcolor=COLORS['border']),
        margin=dict(l=40, r=20, t=60, b=40),
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='right',
            x=1
        ),
        hovermode='x unified'
    )
    return fig

@app.callback(
    Output('trade-ledger', 'children'),
    [Input('trade-ledger-store', 'data')]
)
def update_trade_ledger(trade_ledger):
    """Display the live trade ledger for Signal Collisions."""
    if not trade_ledger:
        return html.P("No signal collisions yet... Waiting for Mycelial and Baseline to AGREE.",
                     style={'color': COLORS['text_muted'], 'textAlign': 'center', 'padding': '20px'})

    ledger_items = []
    for trade in reversed(trade_ledger[-50:]):  # Show last 50
        direction_color = COLORS['success'] if trade['direction'] == 'buy' else COLORS['danger']
        pnl_color = COLORS['success'] if trade['synthesized_pnl'] > 0 else COLORS['danger']

        ledger_items.append(dbc.Card([
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        html.Span("✓✓✓ COLLISION", style={
                            'backgroundColor': '#fbbf24',
                            'color': 'black',
                            'padding': '4px 12px',
                            'borderRadius': '12px',
                            'fontSize': '0.75rem',
                            'fontWeight': '700',
                            'marginRight': '10px'
                        }),
                        html.Span(trade['direction'].upper(), style={
                            'color': direction_color,
                            'fontWeight': '600',
                            'marginRight': '10px'
                        }),
                        html.Span(trade['pair'], style={'color': COLORS['text'], 'fontWeight': '500'}),
                    ], width=6),
                    dbc.Col([
                        html.Div([
                            html.Small(f"{trade['time']}", style={'color': COLORS['text_muted']})
                        ], style={'textAlign': 'right'})
                    ], width=6),
                ]),
                html.Hr(style={'borderColor': COLORS['border'], 'margin': '10px 0'}),
                dbc.Row([
                    dbc.Col([
                        html.P([
                            html.Small("Price: ", style={'color': COLORS['text_muted']}),
                            html.Span(f"${trade['price']:.2f}", style={'color': COLORS['text']})
                        ], style={'marginBottom': '5px'}),
                        html.P([
                            html.Small("Baseline P&L: ", style={'color': COLORS['text_muted']}),
                            html.Span(f"{trade['baseline_pnl']:+.2f}%", style={'color': COLORS['text']})
                        ], style={'marginBottom': '5px'}),
                    ], width=6),
                    dbc.Col([
                        html.P([
                            html.Small("Mycelial P&L: ", style={'color': COLORS['primary']}),
                            html.Span(f"{trade['mycelial_pnl']:+.2f}%", style={'color': COLORS['primary']})
                        ], style={'marginBottom': '5px'}),
                        html.P([
                            html.Small("Synthesized P&L: ", style={'color': '#fbbf24', 'fontWeight': '700'}),
                            html.Span(f"{trade['synthesized_pnl']:+.2f}%", style={'color': pnl_color, 'fontWeight': '700', 'fontSize': '1.1rem'})
                        ], style={'marginBottom': '0'}),
                    ], width=6),
                ]),
            ])
        ], style={'backgroundColor': COLORS['background'], 'marginBottom': '10px', 'borderLeft': f'4px solid #fbbf24'}))

    return ledger_items

if __name__ == '__main__':
    try:
        app.run(debug=False, port=8055, host='127.0.0.1')
    except Exception as e:
        logging.critical(f"FATAL: {e}")
