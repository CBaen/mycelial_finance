# dashboard_v2.py - BIG ROCK 40: Human-Readable Intelligence Platform
# Plain English dashboard for non-traders across all 5 moats

import dash
from dash import dcc, html, Input, Output
import plotly.graph_objects as go
import logging
import time
import json
import sqlite3
from collections import defaultdict, deque
from datetime import datetime
import dash_bootstrap_components as dbc

from src.connectors.redis_client import RedisClient

# Setup
logging.basicConfig(level=logging.INFO)
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

# App initialization with modern theme
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "Mycelial Intelligence"

# Professional color palette
COLORS = {
    'bg': '#0F172A',        # Main background
    'card': '#1E293B',      # Card backgrounds (was surface)
    'border': '#334155',    # Borders
    'text': '#F1F5F9',      # Primary text
    'text_muted': '#94A3B8', # Secondary text
    'primary': '#3B82F6',   # Blue accent
    'success': '#10B981',   # Green
    'warning': '#F59E0B',   # Amber
    'danger': '#EF4444',    # Red
    'info': '#3B82F6',      # Blue
    'accent': '#7C3AED',    # Violet
}

# Custom CSS for modern professional look
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <style>
            body {
                background-color: #0F172A;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
                margin: 0;
                padding: 0;
            }
            .metric-card {
                background: linear-gradient(135deg, #1E293B 0%, #334155 100%);
                border-radius: 12px;
                padding: 24px;
                border: 1px solid #334155;
                transition: transform 0.2s ease, box-shadow 0.2s ease;
            }
            .metric-card:hover {
                transform: translateY(-2px);
                box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.3);
            }
            .stat-number {
                font-size: 2.5rem;
                font-weight: 700;
                line-height: 1;
                margin-bottom: 8px;
            }
            .stat-label {
                font-size: 0.875rem;
                color: #94A3B8;
                text-transform: uppercase;
                letter-spacing: 0.05em;
                font-weight: 500;
            }
            .section-card {
                background: #1E293B;
                border-radius: 16px;
                padding: 32px;
                border: 1px solid #334155;
                margin-bottom: 24px;
            }
            .section-title {
                font-size: 1.25rem;
                font-weight: 600;
                color: #F1F5F9;
                margin-bottom: 8px;
            }
            .section-subtitle {
                font-size: 0.875rem;
                color: #94A3B8;
                margin-bottom: 24px;
            }
            .signal-badge {
                display: inline-block;
                padding: 6px 16px;
                border-radius: 9999px;
                font-size: 0.75rem;
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 0.05em;
            }
            .badge-very-strong {
                background: rgba(239, 68, 68, 0.1);
                color: #EF4444;
                border: 1px solid rgba(239, 68, 68, 0.3);
            }
            .badge-strong {
                background: rgba(245, 158, 11, 0.1);
                color: #F59E0B;
                border: 1px solid rgba(245, 158, 11, 0.3);
            }
            .badge-moderate {
                background: rgba(59, 130, 246, 0.1);
                color: #3B82F6;
                border: 1px solid rgba(59, 130, 246, 0.3);
            }
            .badge-weak {
                background: rgba(148, 163, 184, 0.1);
                color: #94A3B8;
                border: 1px solid rgba(148, 163, 184, 0.3);
            }
            .moat-grid {
                display: grid;
                grid-template-columns: repeat(5, 1fr);
                gap: 16px;
                margin-top: 24px;
            }
            .moat-item {
                background: #0F172A;
                border-radius: 12px;
                padding: 20px;
                text-align: center;
                border: 1px solid #334155;
            }
            .moat-label {
                font-size: 0.75rem;
                color: #94A3B8;
                text-transform: uppercase;
                letter-spacing: 0.05em;
                margin-bottom: 8px;
            }
            .moat-value {
                font-size: 1.5rem;
                font-weight: 600;
                color: #F1F5F9;
            }
            .moat-status {
                font-size: 0.75rem;
                color: #64748B;
                margin-top: 4px;
            }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

# Global data stores
latest_btc_price = {"value": 0, "change_24h": 0}
latest_eth_price = {"value": 0, "change_24h": 0}
latest_gov_data = {"stability": 0, "intensity": 0}
latest_logistics_data = {"congestion": 0, "velocity": 0}
latest_corp_data = {"health": "Unknown"}
latest_code_data = {"activity": "Unknown"}
pattern_narratives = deque(maxlen=50)  # Store last 50 narratives
high_confidence_patterns = deque(maxlen=20)  # Top patterns

#===========================================
# Layout
#===========================================

app.layout = dbc.Container([
    dcc.Interval(id='interval-component', interval=2000, n_intervals=0),  # 2 second updates

    # Header - Modern spacing and design
    dbc.Row([
        dbc.Col([
            html.H1("Mycelial Intelligence Platform",
                   style={'color': COLORS['text'], 'marginTop': '48px', 'marginBottom': '8px', 'fontWeight': '600', 'letterSpacing': '-0.025em', 'fontSize': '2rem'}),
            html.P("Real-time insights across Finance, Government, Logistics, Corporations, and Code Innovation",
                  style={'color': COLORS['text_muted'], 'fontSize': '0.875rem', 'marginBottom': '32px'})
        ])
    ]),

    # Tabs - Modern spacing
    dbc.Tabs([
        # Tab 1: Executive Summary
        dbc.Tab(label="Executive Summary", tab_id="tab-summary", children=[
            html.Div(id='summary-content', style={'padding': '40px'})
        ]),

        # Tab 2: Crypto Markets
        dbc.Tab(label="Crypto Markets", tab_id="tab-crypto", children=[
            html.Div(id='crypto-content', style={'padding': '40px'})
        ]),

        # Tab 3: All 5 Moats
        dbc.Tab(label="5 Moat Intelligence", tab_id="tab-moats", children=[
            html.Div(id='moats-content', style={'padding': '40px'})
        ]),

        # Tab 4: Pattern Deep Dives
        dbc.Tab(label="Pattern Deep Dives", tab_id="tab-patterns", children=[
            html.Div(id='patterns-content', style={'padding': '40px'})
        ])
    ], id="tabs", active_tab="tab-summary", style={'marginBottom': '32px'}),

    # Hidden stores for data
    dcc.Store(id='data-store'),

], fluid=True, style={'backgroundColor': COLORS['bg'], 'minHeight': '100vh', 'color': COLORS['text']})

#===========================================
# Data Processing Functions
#===========================================

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
    """
    Convert technical pattern data to plain English explanation
    """
    raw_features = pattern_data.get('raw_features', {})
    close_price = raw_features.get('close', 0)

    # Detect crypto from agent_id or features (convert to string for safety)
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
    BIG ROCK 40: Cross-Moat Synthesis
    Detects when multiple moats align to create high-confidence signals.
    Returns plain English intelligence briefing.
    """
    # Categorize patterns by moat (convert agent_id to string for safety)
    govt_patterns = [p for p in sql_patterns if 'GovtDataMiner' in str(p.get('agent_id', ''))]
    logistics_patterns = [p for p in sql_patterns if 'LogisticsMiner' in str(p.get('agent_id', ''))]
    corp_patterns = [p for p in sql_patterns if 'CorpDataMiner' in str(p.get('agent_id', ''))]
    code_patterns = [p for p in sql_patterns if 'RepoScraper' in str(p.get('agent_id', ''))]
    finance_patterns = [p for p in sql_patterns if 'DataEngineer' in str(p.get('agent_id', ''))]

    # Calculate moat strength (average pattern value for recent patterns)
    def get_moat_strength(patterns, threshold=60):
        """Returns strength level: 'Strong', 'Moderate', 'Weak', 'None'"""
        if not patterns:
            return 'None', 0
        recent = patterns[:5]  # Last 5 patterns
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
        synthesis['recommendation'] = "When 4+ moats align, it historically signals a major trend. This is the highest confidence signal the system can produce. Consider this a significant market inflection point."

    elif len(strong_moats) == 3:
        synthesis['signal_strength'] = 'STRONG'
        moat_list = ', '.join(strong_moats)
        synthesis['briefing'] = f"STRONG ALIGNMENT: {moat_list} are all showing coordinated patterns. Three-way alignment suggests a developing trend with good reliability."
        synthesis['recommendation'] = "Three moats agreeing is a strong signal. Watch for the 4th moat to confirm or contradict. If Government policy also aligns, confidence increases significantly."

    elif len(strong_moats) == 2:
        synthesis['signal_strength'] = 'MODERATE'
        moat_list = ', '.join(strong_moats)
        synthesis['briefing'] = f"MODERATE SIGNAL: {moat_list} are showing aligned patterns. Two-moat alignment is worth monitoring but needs confirmation from other areas."
        synthesis['recommendation'] = "Two moats agreeing is interesting but not actionable alone. Look for Government policy or Supply Chain data to confirm the direction."

    elif len(strong_moats) == 1:
        synthesis['signal_strength'] = 'WEAK'
        synthesis['briefing'] = f"SINGLE MOAT SIGNAL: Only {strong_moats[0]} is showing patterns. This is not sufficient for high-confidence decisions."
        synthesis['recommendation'] = "Wait for at least 2 moats to align before taking action. Single-moat signals have historically been unreliable."

    else:
        synthesis['signal_strength'] = 'NONE'
        synthesis['briefing'] = "NO CLEAR SIGNAL: None of the 5 moats are showing strong patterns. This typically means the market is in a consolidation or uncertainty phase."
        synthesis['recommendation'] = "When moats don't align, the best strategy is patience. Wait for clearer signals to emerge before making moves."

    return synthesis

def get_sql_patterns():
    """Query SQL database for archived patterns"""
    try:
        conn = sqlite3.connect('mycelial_patterns.db')
        cursor = conn.cursor()

        # Get last 50 patterns
        cursor.execute("""
            SELECT agent_id, timestamp, pattern_value, raw_features, age_minutes, decay_factor
            FROM patterns
            ORDER BY timestamp DESC
            LIMIT 50
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
        logging.error(f"Error querying SQL: {e}")
        return []

#===========================================
# Callback: Main Data Update
#===========================================

@app.callback(
    [Output('summary-content', 'children'),
     Output('crypto-content', 'children'),
     Output('moats-content', 'children'),
     Output('patterns-content', 'children')],
    [Input('interval-component', 'n_intervals')]
)
def update_dashboard(n):
    """Main callback to update all dashboard content"""

    # Get latest patterns from SQL
    sql_patterns = get_sql_patterns()

    # BIG ROCK 40: Generate cross-moat synthesis
    synthesis = synthesize_cross_moat_intelligence(sql_patterns)

    # Process patterns to update global stores
    for pattern in sql_patterns[:10]:  # Process top 10
        explanation = explain_pattern_plain_english(pattern)

        if pattern['pattern_value'] >= 70:
            high_confidence_patterns.appendleft({
                'explanation': explanation,
                'value': pattern['pattern_value'],
                'timestamp': datetime.fromtimestamp(pattern['timestamp']).strftime('%H:%M:%S'),
                'raw_features': pattern['raw_features']
            })

    #===========================================
    # Tab 1: Executive Summary
    #===========================================

    summary_content = [
        # Top Metric Cards (Modern design from v3)
        dbc.Row([
            dbc.Col(width=3, children=[
                html.Div(className='metric-card', children=[
                    html.Div(className='stat-number', style={'color': COLORS['primary']}, children=str(len(sql_patterns))),
                    html.Div(className='stat-label', children='Patterns Discovered')
                ])
            ]),
            dbc.Col(width=3, children=[
                html.Div(className='metric-card', children=[
                    html.Div(className='stat-number', style={'color': COLORS['success']}, children='121'),
                    html.Div(className='stat-label', children='Active Agents')
                ])
            ]),
            dbc.Col(width=3, children=[
                html.Div(className='metric-card', children=[
                    html.Div(className='stat-number', style={'color': COLORS['warning']}, children='5'),
                    html.Div(className='stat-label', children='Intelligence Moats')
                ])
            ]),
            dbc.Col(width=3, children=[
                html.Div(className='metric-card', children=[
                    html.Div(className='stat-number', style={'color': COLORS['info']}, children=str(synthesis['alignment_count'])),
                    html.Div(className='stat-label', children='Moats Aligned')
                ])
            ])
        ], style={'marginBottom': '32px'}),

        # Cross-Moat Intelligence Synthesis (Friend-to-Friend Language)
        html.Div(className='section-card', children=[
            html.Div(className='section-title', children="What's Happening Right Now"),
            html.Div(className='section-subtitle', children=f"Last updated: {datetime.now().strftime('%H:%M:%S')}"),

            # Signal Strength Badge
            html.Div(children=[
                html.Span(
                    className=f"signal-badge badge-{'very-strong' if synthesis['alignment_count'] >= 4 else 'strong' if synthesis['alignment_count'] == 3 else 'moderate' if synthesis['alignment_count'] == 2 else 'weak'}",
                    children=f"{synthesis['signal_strength']} SIGNAL"
                )
            ], style={'marginBottom': '24px'}),

            # Friend-to-friend briefing
            html.P(
                children=synthesis['briefing'],
                style={'fontSize': '1.125rem', 'lineHeight': '1.75', 'color': COLORS['text'], 'marginBottom': '24px'}
            ),

            html.P(
                children=synthesis['recommendation'],
                style={'fontSize': '1rem', 'lineHeight': '1.75', 'color': COLORS['text_muted'], 'marginBottom': '32px'}
            ),

            # Moat Grid (Modern 5-column design)
            html.Div(className='moat-grid', children=[
                html.Div(className='moat-item', children=[
                    html.Div(className='moat-label', children='GOVERNMENT'),
                    html.Div(className='moat-value',
                            style={'color': COLORS['success'] if synthesis['moat_details']['Government']['strength'] == 'Strong'
                                  else COLORS['warning'] if synthesis['moat_details']['Government']['strength'] == 'Moderate'
                                  else COLORS['text_muted']},
                            children=synthesis['moat_details']['Government']['strength']),
                    html.Div(className='moat-status', children=f"{synthesis['moat_details']['Government']['value']:.0f} confidence")
                ]),
                html.Div(className='moat-item', children=[
                    html.Div(className='moat-label', children='LOGISTICS'),
                    html.Div(className='moat-value',
                            style={'color': COLORS['success'] if synthesis['moat_details']['Logistics']['strength'] == 'Strong'
                                  else COLORS['warning'] if synthesis['moat_details']['Logistics']['strength'] == 'Moderate'
                                  else COLORS['text_muted']},
                            children=synthesis['moat_details']['Logistics']['strength']),
                    html.Div(className='moat-status', children=f"{synthesis['moat_details']['Logistics']['value']:.0f} confidence")
                ]),
                html.Div(className='moat-item', children=[
                    html.Div(className='moat-label', children='CORPORATIONS'),
                    html.Div(className='moat-value',
                            style={'color': COLORS['success'] if synthesis['moat_details']['Corporations']['strength'] == 'Strong'
                                  else COLORS['warning'] if synthesis['moat_details']['Corporations']['strength'] == 'Moderate'
                                  else COLORS['text_muted']},
                            children=synthesis['moat_details']['Corporations']['strength']),
                    html.Div(className='moat-status', children=f"{synthesis['moat_details']['Corporations']['value']:.0f} confidence")
                ]),
                html.Div(className='moat-item', children=[
                    html.Div(className='moat-label', children='CODE'),
                    html.Div(className='moat-value',
                            style={'color': COLORS['success'] if synthesis['moat_details']['Code']['strength'] == 'Strong'
                                  else COLORS['warning'] if synthesis['moat_details']['Code']['strength'] == 'Moderate'
                                  else COLORS['text_muted']},
                            children=synthesis['moat_details']['Code']['strength']),
                    html.Div(className='moat-status', children=f"{synthesis['moat_details']['Code']['value']:.0f} confidence")
                ]),
                html.Div(className='moat-item', children=[
                    html.Div(className='moat-label', children='FINANCE'),
                    html.Div(className='moat-value',
                            style={'color': COLORS['success'] if synthesis['moat_details']['Finance']['strength'] == 'Strong'
                                  else COLORS['warning'] if synthesis['moat_details']['Finance']['strength'] == 'Moderate'
                                  else COLORS['text_muted']},
                            children=synthesis['moat_details']['Finance']['strength']),
                    html.Div(className='moat-status', children=f"{synthesis['moat_details']['Finance']['value']:.0f} confidence")
                ])
            ])
        ]),

        # High Priority Patterns (Friend-to-Friend Language)
        html.Div(className='section-card', children=[
            html.Div(className='section-title', children="Patterns You Should Know About"),
            html.Div(className='section-subtitle', children="These are the most interesting things happening right now"),

            html.Div([
                html.Div(style={'backgroundColor': COLORS['bg'], 'padding': '20px', 'borderRadius': '12px', 'marginBottom': '16px', 'border': f"1px solid {COLORS['border']}"}, children=[
                    html.Div(style={'marginBottom': '12px'}, children=[
                        html.Span(className='signal-badge badge-strong', children=f"{p['value']:.0f}% CONFIDENCE")
                    ]),
                    html.P(p['explanation'], style={'fontSize': '1.125rem', 'lineHeight': '1.75', 'color': COLORS['text'], 'marginBottom': '8px'}),
                    html.Small(f"Spotted at {p['timestamp']}", style={'color': COLORS['text_muted'], 'fontSize': '0.875rem'})
                ])
                for i, p in enumerate(list(high_confidence_patterns)[:3])
            ]) if high_confidence_patterns else html.P("Your agents are actively searching for patterns. Give them a moment to find something interesting!",
                                                       style={'color': COLORS['text_muted'], 'fontStyle': 'italic', 'fontSize': '1rem'})
        ])
    ]

    #===========================================
    # Tab 2: Crypto Markets
    #===========================================

    # Extract BTC and ETH patterns (convert agent_id to string for safety)
    btc_patterns = [p for p in sql_patterns if 'DataEngineer_1' in str(p.get('agent_id', '')) or 'XXBTZUSD' in str(p.get('agent_id', ''))]
    eth_patterns = [p for p in sql_patterns if 'DataEngineer_2' in str(p.get('agent_id', '')) or 'XETHZUSD' in str(p.get('agent_id', ''))]

    # Get latest prices and technical data
    btc_price = btc_patterns[0]['raw_features'].get('close', 0) if btc_patterns else 0
    eth_price = eth_patterns[0]['raw_features'].get('close', 0) if eth_patterns else 0

    # Get technical indicators for Bitcoin
    btc_rsi = btc_patterns[0]['raw_features'].get('RSI', 0) if btc_patterns else 0
    btc_atr = btc_patterns[0]['raw_features'].get('ATR', 0) if btc_patterns else 0
    btc_mom = btc_patterns[0]['raw_features'].get('MOM', 0) if btc_patterns else 0

    # Get technical indicators for Ethereum
    eth_rsi = eth_patterns[0]['raw_features'].get('RSI', 0) if eth_patterns else 0
    eth_atr = eth_patterns[0]['raw_features'].get('ATR', 0) if eth_patterns else 0
    eth_mom = eth_patterns[0]['raw_features'].get('MOM', 0) if eth_patterns else 0

    crypto_content = [
        # Bitcoin Section
        html.Div(className='section-card', children=[
            html.Div(className='section-title', children="Bitcoin (BTC)"),
            html.Div(className='section-subtitle', children="The original cryptocurrency and digital gold"),

            # Price display
            html.Div(style={'marginBottom': '32px'}, children=[
                html.Div(className='stat-number', style={'color': COLORS['warning']},
                        children=f"${btc_price:,.2f}" if btc_price else "Loading...")
            ]),

            # Friend-to-friend explanation
            html.P(
                children=explain_pattern_plain_english(btc_patterns[0]) if btc_patterns
                        else "Hey! Bitcoin data is still loading. Give me a sec while I check the price, "
                             "see what the government's doing, and figure out if this is a good time to pay attention.",
                style={'fontSize': '1.125rem', 'lineHeight': '1.75', 'color': COLORS['text'], 'marginBottom': '24px'}
            ),

            # Technical indicators in friend language
            html.Div(className='section-subtitle', style={'marginTop': '24px', 'marginBottom': '16px'},
                    children="Here's what the numbers are saying:"),

            dbc.Row([
                dbc.Col(width=4, children=[
                    html.Div(className='metric-card', children=[
                        html.Div(className='stat-label', children='Market Mood'),
                        html.Div(className='stat-number', style={
                            'color': COLORS['danger'] if btc_rsi > 70 else COLORS['success'] if btc_rsi < 30 else COLORS['primary'],
                            'fontSize': '2rem'
                        }, children=f"{btc_rsi:.0f}" if btc_rsi else "..."),
                        html.P(
                            children="Overheated" if btc_rsi > 70 else "Beaten down" if btc_rsi < 30 else "Steady",
                            style={'fontSize': '0.875rem', 'color': COLORS['text_muted'], 'marginTop': '8px'}
                        )
                    ])
                ]),
                dbc.Col(width=4, children=[
                    html.Div(className='metric-card', children=[
                        html.Div(className='stat-label', children='Volatility'),
                        html.Div(className='stat-number', style={
                            'color': COLORS['warning'] if btc_atr > 2000 else COLORS['success'],
                            'fontSize': '2rem'
                        }, children=f"${btc_atr:.0f}" if btc_atr else "..."),
                        html.P(
                            children="Wild swings" if btc_atr > 2000 else "Calm waters",
                            style={'fontSize': '0.875rem', 'color': COLORS['text_muted'], 'marginTop': '8px'}
                        )
                    ])
                ]),
                dbc.Col(width=4, children=[
                    html.Div(className='metric-card', children=[
                        html.Div(className='stat-label', children='Momentum'),
                        html.Div(className='stat-number', style={
                            'color': COLORS['success'] if btc_mom > 0 else COLORS['danger'],
                            'fontSize': '2rem'
                        }, children=f"${btc_mom:,.0f}" if btc_mom else "..."),
                        html.P(
                            children="Going up" if btc_mom > 0 else "Going down",
                            style={'fontSize': '0.875rem', 'color': COLORS['text_muted'], 'marginTop': '8px'}
                        )
                    ])
                ])
            ]),

            html.P(
                f"I've spotted {len(btc_patterns)} different patterns in Bitcoin's behavior so far.",
                style={'fontSize': '0.875rem', 'color': COLORS['text_muted'], 'marginTop': '24px'}
            )
        ]),

        # Ethereum Section
        html.Div(className='section-card', children=[
            html.Div(className='section-title', children="Ethereum (ETH)"),
            html.Div(className='section-subtitle', children="Smart contracts and decentralized apps platform"),

            # Price display
            html.Div(style={'marginBottom': '32px'}, children=[
                html.Div(className='stat-number', style={'color': COLORS['info']},
                        children=f"${eth_price:,.2f}" if eth_price else "Loading...")
            ]),

            # Friend-to-friend explanation
            html.P(
                children=explain_pattern_plain_english(eth_patterns[0]) if eth_patterns
                        else "Ethereum data is coming in. This one powers a lot of the cool stuff in crypto - "
                             "think of it like the computer that runs all the decentralized apps.",
                style={'fontSize': '1.125rem', 'lineHeight': '1.75', 'color': COLORS['text'], 'marginBottom': '24px'}
            ),

            # Technical indicators in friend language
            html.Div(className='section-subtitle', style={'marginTop': '24px', 'marginBottom': '16px'},
                    children="Here's what the numbers are saying:"),

            dbc.Row([
                dbc.Col(width=4, children=[
                    html.Div(className='metric-card', children=[
                        html.Div(className='stat-label', children='Market Mood'),
                        html.Div(className='stat-number', style={
                            'color': COLORS['danger'] if eth_rsi > 70 else COLORS['success'] if eth_rsi < 30 else COLORS['primary'],
                            'fontSize': '2rem'
                        }, children=f"{eth_rsi:.0f}" if eth_rsi else "..."),
                        html.P(
                            children="Overheated" if eth_rsi > 70 else "Beaten down" if eth_rsi < 30 else "Steady",
                            style={'fontSize': '0.875rem', 'color': COLORS['text_muted'], 'marginTop': '8px'}
                        )
                    ])
                ]),
                dbc.Col(width=4, children=[
                    html.Div(className='metric-card', children=[
                        html.Div(className='stat-label', children='Volatility'),
                        html.Div(className='stat-number', style={
                            'color': COLORS['warning'] if eth_atr > 100 else COLORS['success'],
                            'fontSize': '2rem'
                        }, children=f"${eth_atr:.0f}" if eth_atr else "..."),
                        html.P(
                            children="Wild swings" if eth_atr > 100 else "Calm waters",
                            style={'fontSize': '0.875rem', 'color': COLORS['text_muted'], 'marginTop': '8px'}
                        )
                    ])
                ]),
                dbc.Col(width=4, children=[
                    html.Div(className='metric-card', children=[
                        html.Div(className='stat-label', children='Momentum'),
                        html.Div(className='stat-number', style={
                            'color': COLORS['success'] if eth_mom > 0 else COLORS['danger'],
                            'fontSize': '2rem'
                        }, children=f"${eth_mom:,.0f}" if eth_mom else "..."),
                        html.P(
                            children="Going up" if eth_mom > 0 else "Going down",
                            style={'fontSize': '0.875rem', 'color': COLORS['text_muted'], 'marginTop': '8px'}
                        )
                    ])
                ])
            ]),

            html.P(
                f"I've spotted {len(eth_patterns)} different patterns in Ethereum's behavior so far.",
                style={'fontSize': '0.875rem', 'color': COLORS['text_muted'], 'marginTop': '24px'}
            )
        ])
    ]

    #===========================================
    # Tab 3: All 5 Moats Intelligence
    #===========================================

    # Categorize patterns by moat (convert agent_id to string for safety)
    govt_patterns = [p for p in sql_patterns if 'GovtDataMiner' in str(p.get('agent_id', ''))]
    logistics_patterns = [p for p in sql_patterns if 'LogisticsMiner' in str(p.get('agent_id', ''))]
    corp_patterns = [p for p in sql_patterns if 'CorpDataMiner' in str(p.get('agent_id', ''))]
    code_patterns = [p for p in sql_patterns if 'RepoScraper' in str(p.get('agent_id', ''))]
    finance_patterns = [p for p in sql_patterns if 'DataEngineer' in str(p.get('agent_id', ''))]

    moats_content = [
        # Overview header
        html.Div(style={'marginBottom': '32px'}, children=[
            html.Div(className='section-title', children="Your 5 Intelligence Sources"),
            html.Div(className='section-subtitle', children="Think of these as different windows into what's really happening in the world")
        ]),

        # Government Moat
        html.Div(className='section-card', children=[
            dbc.Row([
                dbc.Col(width=8, children=[
                    html.Div(className='section-title', style={'marginBottom': '8px'}, children="Government & Policy"),
                    html.Div(className='section-subtitle', style={'marginBottom': '24px'},
                            children="What politicians and regulators are up to"),
                    html.P(
                        "Think of this as your early warning system for regulatory changes. When the government is "
                        "stable and predictable (high scores above 90), that's usually good news for crypto and tech. "
                        "When they start making a lot of policy changes quickly (score drops), markets get nervous.",
                        style={'fontSize': '1rem', 'lineHeight': '1.75', 'color': COLORS['text']}
                    )
                ]),
                dbc.Col(width=4, children=[
                    html.Div(className='metric-card', children=[
                        html.Div(className='stat-label', children='Patterns Found'),
                        html.Div(className='stat-number', style={'color': COLORS['info']}, children=str(len(govt_patterns)))
                    ])
                ])
            ])
        ]),

        # Corporations Moat
        html.Div(className='section-card', children=[
            dbc.Row([
                dbc.Col(width=8, children=[
                    html.Div(className='section-title', style={'marginBottom': '8px'}, children="Tech Corporations"),
                    html.Div(className='section-subtitle', style={'marginBottom': '24px'},
                            children="How big tech companies are doing"),
                    html.P(
                        "Big tech companies and crypto tend to move together. When Apple, Google, or Microsoft are "
                        "spending big on R&D and posting strong earnings, that confidence usually spills over into "
                        "crypto markets. Both are seen as 'innovation bets' by investors.",
                        style={'fontSize': '1rem', 'lineHeight': '1.75', 'color': COLORS['text']}
                    )
                ]),
                dbc.Col(width=4, children=[
                    html.Div(className='metric-card', children=[
                        html.Div(className='stat-label', children='Patterns Found'),
                        html.Div(className='stat-number', style={'color': COLORS['warning']}, children=str(len(corp_patterns)))
                    ])
                ])
            ])
        ]),

        # Logistics Moat
        html.Div(className='section-card', children=[
            dbc.Row([
                dbc.Col(width=8, children=[
                    html.Div(className='section-title', style={'marginBottom': '8px'}, children="Supply Chain & Logistics"),
                    html.Div(className='section-subtitle', style={'marginBottom': '24px'},
                            children="How smoothly stuff is moving around the world"),
                    html.P(
                        "This tracks shipping ports on the West Coast. When ports are jammed (high congestion), "
                        "it means the economy is slowing down - bad for everything. When ships are moving fast and "
                        "smoothly (low congestion, high velocity), the economy is humming along nicely. That's when "
                        "risk assets like crypto do well.",
                        style={'fontSize': '1rem', 'lineHeight': '1.75', 'color': COLORS['text']}
                    )
                ]),
                dbc.Col(width=4, children=[
                    html.Div(className='metric-card', children=[
                        html.Div(className='stat-label', children='Patterns Found'),
                        html.Div(className='stat-number', style={'color': COLORS['accent']}, children=str(len(logistics_patterns)))
                    ])
                ])
            ])
        ]),

        # Code Innovation Moat
        html.Div(className='section-card', children=[
            dbc.Row([
                dbc.Col(width=8, children=[
                    html.Div(className='section-title', style={'marginBottom': '8px'}, children="Code & Innovation"),
                    html.Div(className='section-subtitle', style={'marginBottom': '24px'},
                            children="What developers are building"),
                    html.P(
                        "This watches GitHub to see how active developers are. Lots of new code commits and library "
                        "releases means innovation is accelerating. This often predicts new products and features "
                        "coming to market in AI, crypto, and tech - which can move prices before most people notice.",
                        style={'fontSize': '1rem', 'lineHeight': '1.75', 'color': COLORS['text']}
                    )
                ]),
                dbc.Col(width=4, children=[
                    html.Div(className='metric-card', children=[
                        html.Div(className='stat-label', children='Patterns Found'),
                        html.Div(className='stat-number', style={'color': COLORS['primary']}, children=str(len(code_patterns)))
                    ])
                ])
            ])
        ]),

        # Finance Moat
        html.Div(className='section-card', children=[
            dbc.Row([
                dbc.Col(width=8, children=[
                    html.Div(className='section-title', style={'marginBottom': '8px'}, children="Crypto Markets"),
                    html.Div(className='section-subtitle', style={'marginBottom': '24px'},
                            children="Bitcoin and Ethereum price action"),
                    html.P(
                        "This is the real-time feed from Kraken exchange. We're watching price movements, trading "
                        "volume, and looking for patterns that have historically meant something big is about to happen. "
                        "When you see patterns here that match up with signals from the other 4 moats, that's when "
                        "things get interesting.",
                        style={'fontSize': '1rem', 'lineHeight': '1.75', 'color': COLORS['text']}
                    )
                ]),
                dbc.Col(width=4, children=[
                    html.Div(className='metric-card', children=[
                        html.Div(className='stat-label', children='Patterns Found'),
                        html.Div(className='stat-number', style={'color': COLORS['danger']}, children=str(len(finance_patterns)))
                    ])
                ])
            ])
        ])
    ]

    #===========================================
    # Tab 4: Pattern Deep Dives
    #===========================================

    patterns_content = [
        # Header
        html.Div(style={'marginBottom': '32px'}, children=[
            html.Div(className='section-title', children=f"All the Patterns We've Found ({len(sql_patterns)} total)"),
            html.Div(className='section-subtitle', children="Here's everything the system has spotted, newest first")
        ]),

        # Pattern cards
        html.Div([
            html.Div(style={'backgroundColor': COLORS['card'], 'padding': '24px', 'borderRadius': '12px',
                           'marginBottom': '16px', 'border': f"1px solid {COLORS['border']}"}, children=[
                # Header row with confidence badge
                dbc.Row([
                    dbc.Col(width=8, children=[
                        html.Div(style={'marginBottom': '16px'}, children=[
                            html.Span(
                                className=f"signal-badge badge-{'very-strong' if p['pattern_value'] >= 75 else 'strong' if p['pattern_value'] >= 60 else 'moderate'}",
                                children=f"{p['pattern_value']:.0f}% CONFIDENCE"
                            ),
                            html.Span(
                                style={'marginLeft': '12px', 'fontSize': '0.75rem', 'color': COLORS['text_muted']},
                                children=f"Pattern #{i+1}"
                            )
                        ])
                    ]),
                    dbc.Col(width=4, children=[
                        html.Div(style={'textAlign': 'right', 'fontSize': '0.75rem', 'color': COLORS['text_muted']},
                                children=f"Found {datetime.fromtimestamp(p['timestamp']).strftime('%H:%M:%S')}")
                    ])
                ]),

                # Explanation
                html.P(
                    explain_pattern_plain_english(p),
                    style={'fontSize': '1.125rem', 'lineHeight': '1.75', 'color': COLORS['text'], 'marginBottom': '16px'}
                ),

                # Expandable technical details
                html.Details([
                    html.Summary("Show me the nerdy details", style={'cursor': 'pointer', 'color': COLORS['text_muted'],
                                                                     'fontSize': '0.875rem', 'marginTop': '8px'}),
                    html.Div(style={'marginTop': '16px', 'padding': '16px', 'backgroundColor': COLORS['bg'],
                                   'borderRadius': '8px', 'fontFamily': 'monospace', 'fontSize': '0.875rem'}, children=[
                        html.P(f"Agent: {p['agent_id']}", style={'marginBottom': '8px'}),
                        html.P(f"Pattern Strength: {p['pattern_value']:.2f}%", style={'marginBottom': '8px'}),
                        html.P(f"Age: {p['age_minutes']:.1f} minutes", style={'marginBottom': '8px'}),
                        html.P(f"Decay Factor: {p['decay_factor']:.4f}", style={'marginBottom': '8px'}),
                        html.P("Raw Data:", style={'marginBottom': '8px', 'fontWeight': 'bold'}),
                        html.Pre(
                            json.dumps(p['raw_features'], indent=2),
                            style={'fontSize': '0.75rem', 'color': COLORS['text_muted'], 'overflow': 'auto'}
                        )
                    ])
                ])
            ])
            for i, p in enumerate(sql_patterns[:30])  # Show top 30 patterns
        ])
    ]

    return summary_content, crypto_content, moats_content, patterns_content

#===========================================
# Run Server
#===========================================

if __name__ == '__main__':
    logging.info("Mycelial Intelligence Platform v2.0 - Human-Readable Dashboard")
    logging.info("Starting server on http://127.0.0.1:8056/")
    app.run(debug=False, host='127.0.0.1', port=8056)
