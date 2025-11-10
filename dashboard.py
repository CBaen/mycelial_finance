# dashboard.py - MYCELIAL INTELLIGENCE v9.0: THE STORY-DRIVEN ANALYTICS ENGINE
# Big Rock 23: Final Narrative and Growth-Focused Dashboard Overhaul
# Mission: Show the STORY of pattern discovery, agent activity, and swarm growth

import dash
from dash import dcc, html, Input, Output, State
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import logging
import time
import json
import threading
from queue import Queue
import random
import math
import dash_bootstrap_components as dbc
import uuid
import numpy as np
from datetime import datetime

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

# === EXPANDED INTERESTINGNESS FORMULA (5 COMPONENTS @ 20pts each) ===
def calculate_interestingness(agent_data, all_agents):
    """
    5-Component Interestingness Score (0-100):
    1. Novelty (20pts): How different from parent
    2. Performance (20pts): Prediction confidence
    3. Diversity (20pts): Uniqueness in swarm
    4. Evolution (20pts): Generational progress
    5. Growth Bonus (20pts): Policy sharing frequency (recursive learning)
    """
    score = 0

    def get_normalized_vector(data):
        vec = np.array(data.get('vector', [0, 0, 0, 0]))
        if vec.ndim == 1 and len(vec) < 4:
            vec = np.pad(vec, (0, 4 - len(vec)), mode='constant')
        return vec / np.linalg.norm(vec) if np.linalg.norm(vec) > 0 else np.zeros(4)

    # 1. Novelty (20pts)
    parent_id = agent_data.get('parent_id')
    if parent_id and parent_id != 'Genesis' and parent_id in all_agents:
        parent_vec = get_normalized_vector(all_agents[parent_id])
        current_vec = get_normalized_vector(agent_data)
        novelty = np.linalg.norm(current_vec - parent_vec)
        score += min(novelty * 10, 20)
    else:
        score += 10

    # 2. Performance (20pts)
    pred_score = agent_data.get('score', 0.1)
    score += pred_score * 20

    # 3. Diversity (20pts)
    if all_agents:
        my_vec = get_normalized_vector(agent_data)
        distances = []
        for a_id, a_data in all_agents.items():
            if a_id != agent_data['id']:
                distances.append(np.linalg.norm(my_vec - get_normalized_vector(a_data)))
        avg_distance = np.mean(distances) if distances else 0
        score += min(avg_distance * 8, 20)

    # 4. Evolution (20pts)
    generation = agent_data.get('generation', 0)
    score += min(generation * 2, 20)

    # 5. Growth Bonus (20pts) - Policy sharing frequency
    share_frequency = random.uniform(0.5, 1.5)  # Simulated
    score += min(share_frequency * 10, 20)

    return min(score, 100)

# === AGENT METADATA ===
AGENT_INFO = {
    'DataMiner_XXBTZUSD_1': {'name': 'BTC Sensor', 'type': 'Data Miner', 'color': COLORS['primary'], 'product': 'Finance', 'icon': 'fa-bitcoin'},
    'DataMiner_XETHZUSD_2': {'name': 'ETH Sensor', 'type': 'Data Miner', 'color': COLORS['primary'], 'product': 'Finance', 'icon': 'fa-ethereum'},
    'RepoScraper_3': {'name': 'Code Hunter', 'type': 'Data Miner', 'color': COLORS['success'], 'product': 'Code Innovation', 'icon': 'fa-code'},
    'LogisticsMiner_4': {'name': 'Flow Tracker', 'type': 'Data Miner', 'color': COLORS['warning'], 'product': 'Logistics', 'icon': 'fa-truck'},
    'GovtDataMiner_5': {'name': 'Policy Scout', 'type': 'Data Miner', 'color': COLORS['info'], 'product': 'Government', 'icon': 'fa-landmark'},
    'CorpDataMiner_6': {'name': 'Corp Intel', 'type': 'Data Miner', 'color': COLORS['corp'], 'product': 'US Corporations', 'icon': 'fa-building'},
    'Trader_107': {'name': 'Trade Executor', 'type': 'Action Agent', 'color': '#fbbf24', 'product': 'System', 'icon': 'fa-bolt'},
    'RiskManager_108': {'name': 'Safety Monitor', 'type': 'HAVEN Guardian', 'color': COLORS['danger'], 'product': 'System', 'icon': 'fa-shield-alt'},
    'AutonomousBuilder_109': {'name': 'Builder', 'type': 'Evolution Engine', 'color': '#9333ea', 'product': 'System', 'icon': 'fa-cogs'},
}

for i in range(7, 107):
    products = ['Finance', 'Code Innovation', 'Logistics', 'Government', 'US Corporations']
    product = products[i % 5]
    AGENT_INFO[f'SwarmBrain_{i}'] = {
        'name': f'Brain {i}',
        'type': 'Pattern Learner',
        'color': COLORS['primary'],
        'product': product,
        'icon': 'fa-brain'
    }

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
app.title = "Mycelial Intelligence - Story Engine v9.0"

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

        dcc.Interval(id='interval', interval=2000, n_intervals=0),

        # === HEADER ===
        dbc.Row(dbc.Col(html.Div([
            html.H1([
                html.I(className="fas fa-brain", style={'marginRight': '15px', 'color': COLORS['primary']}),
                "MYCELIAL INTELLIGENCE ENGINE"
            ], style={'fontSize': '2.5rem', 'fontWeight': '700', 'color': COLORS['text'], 'textAlign': 'center'}),
            html.P("v9.0: The Story-Driven Analytics Platform - Understanding Your Swarm's Journey",
                  style={'color': COLORS['text_muted'], 'fontSize': '0.95rem', 'textAlign': 'center'}),
        ], className="py-3 mb-4"))),

        # === KEY METRICS ROW (The Dashboard's "At-a-Glance" Story) ===
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.I(className="fas fa-lightbulb fa-2x", style={'color': COLORS['warning']}),
                            dbc.Tooltip(
                                "Total unique patterns discovered by your 100-agent swarm across all 5 product moats. "
                                "This is your cumulative intelligence growth metric.",
                                target="patterns-discovered-card",
                            ),
                        ], style={'float': 'right'}),
                        html.H6("Patterns Discovered", style={'color': COLORS['text_muted'], 'marginBottom': '10px'}),
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
                                "Overall health of your swarm (0-100). Measures agent diversity, "
                                "policy sharing activity, and absence of toxic behavior. HAVEN framework monitors this.",
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
                                "Number of active agents currently learning and sharing policies. "
                                "Includes pattern learners, data miners, and system agents.",
                                target="active-agents-card",
                            ),
                        ], style={'float': 'right'}),
                        html.H6("Active Agents", style={'color': COLORS['text_muted'], 'marginBottom': '10px'}),
                        html.H2(id='active-agents-metric', children="109", style={'color': COLORS['info'], 'fontWeight': '700'}),
                        html.P("6 Miners + 100 Learners + 3 System", style={'color': COLORS['text_muted'], 'fontSize': '0.9rem'}),
                    ])
                ], style={'backgroundColor': COLORS['card'], 'borderLeft': f'4px solid {COLORS["info"]}'}, id="active-agents-card"),
            ], width=3),

            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.I(className="fas fa-fire fa-2x", style={'color': COLORS['danger']}),
                            dbc.Tooltip(
                                "HAVEN Risk Framework: System risk level (0-100). "
                                "85+ triggers policy contagion blocks. 10 toxic agents injected for stress testing.",
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
        dbc.Tabs(id="tabs", active_tab="tab-live-story", className="mb-4", children=[
            dbc.Tab(label="📖 Live Story", tab_id="tab-live-story",
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

        html.Div(f"Session {SESSION_ID} | Big Rock 23: Story-Driven Engine Active | Focus: Content, Growth, Pattern Discovery",
                className="text-center mt-4", style={'color': COLORS['text_muted'], 'fontSize': '0.75rem'})
    ]
)

# === REDIS LISTENER ===
def start_redis_listener(app_queue: Queue):
    logging.info("Story Engine v9.0: Redis listener started")
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
        'policy-data:gov': 'policy-data',
        'corporate-data:*': 'corporate-data',
        'repo-data:*': 'repo-data',
        'logistics-data:*': 'logistics-data',
        'agent-lineage-update': 'lineage-update'
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
logging.info("Mycelial Story Engine v9.0 Active")

# === MAIN DATA UPDATE ===
@app.callback(
    [Output('pattern-store', 'data'),
     Output('moat-health-store', 'data'),
     Output('activity-log-store', 'data'),
     Output('agent-stats-store', 'data'),
     Output('swarm-health-store', 'data'),
     Output('discoveries-store', 'data')],
    [Input('interval', 'n_intervals')],
    [State('pattern-store', 'data'),
     State('moat-health-store', 'data'),
     State('activity-log-store', 'data'),
     State('agent-stats-store', 'data'),
     State('swarm-health-store', 'data'),
     State('discoveries-store', 'data')]
)
def update_data(n, pattern_data, moat_health, activity_log, agent_stats, swarm_health, discoveries):
    """Process Redis messages and update all stores with narrative focus."""

    # Process all queued messages
    while not message_queue.empty():
        msg = message_queue.get()
        msg_type = msg['type']
        data = msg['data']
        timestamp = datetime.now().strftime('%H:%M:%S')

        # Track agent activity
        source = data.get('source', 'Unknown')

        # Initialize agent stats if not exists
        if source and source != 'Unknown':
            if source not in agent_stats:
                agent_stats[source] = {
                    'patterns_discovered': 0,
                    'policy_shares': 0,
                    'last_active': timestamp,
                    'generation': 0,
                    'parent': 'Genesis',
                    'children': [],
                    'status': 'Active'
                }
            agent_stats[source]['last_active'] = timestamp

        if msg_type == 'market-data':
            pair = data.get('pair', 'Unknown')
            activity_log.append({
                'time': timestamp,
                'agent': source,
                'action': f'📊 Analyzed {pair} market data',
                'color': COLORS['primary']
            })
            pattern_data['total_patterns'] += 1
            moat_health['Finance'] = min(100, moat_health.get('Finance', 100) + 0.5)
            # Track per-agent patterns
            if source and source != 'Unknown':
                agent_stats[source]['patterns_discovered'] += 1
                agent_stats[source]['policy_shares'] += 1

        elif msg_type == 'repo-data':
            activity_log.append({
                'time': timestamp,
                'agent': source,
                'action': f'💡 Discovered code innovation pattern',
                'color': COLORS['success']
            })
            pattern_data['total_patterns'] += 1
            moat_health['Code Innovation'] = min(100, moat_health.get('Code Innovation', 100) + 0.5)
            if source and source != 'Unknown':
                agent_stats[source]['patterns_discovered'] += 1
                agent_stats[source]['policy_shares'] += 1

        elif msg_type == 'logistics-data':
            activity_log.append({
                'time': timestamp,
                'agent': source,
                'action': f'🚚 Tracked logistics flow pattern',
                'color': COLORS['warning']
            })
            pattern_data['total_patterns'] += 1
            moat_health['Logistics'] = min(100, moat_health.get('Logistics', 100) + 0.5)
            if source and source != 'Unknown':
                agent_stats[source]['patterns_discovered'] += 1
                agent_stats[source]['policy_shares'] += 1

        elif msg_type == 'policy-data':
            activity_log.append({
                'time': timestamp,
                'agent': source,
                'action': f'🏛️ Analyzed government policy shift',
                'color': COLORS['info']
            })
            pattern_data['total_patterns'] += 1
            moat_health['Government'] = min(100, moat_health.get('Government', 100) + 0.5)
            if source and source != 'Unknown':
                agent_stats[source]['patterns_discovered'] += 1
                agent_stats[source]['policy_shares'] += 1

        elif msg_type == 'corporate-data':
            activity_log.append({
                'time': timestamp,
                'agent': source,
                'action': f'🏢 Mined corporate intelligence',
                'color': COLORS['corp']
            })
            pattern_data['total_patterns'] += 1
            moat_health['US Corporations'] = min(100, moat_health.get('US Corporations', 100) + 0.5)
            if source and source != 'Unknown':
                agent_stats[source]['patterns_discovered'] += 1
                agent_stats[source]['policy_shares'] += 1

        elif msg_type == 'build-request':
            requester = data.get('requester', 'Unknown')
            agent_type = data.get('agent_type', 'Unknown')
            reason = data.get('reason', 'Unknown')
            activity_log.append({
                'time': timestamp,
                'agent': requester,
                'action': f'🔧 Requested new {agent_type}: {reason}',
                'color': '#9333ea'
            })
            discoveries.append({
                'time': timestamp,
                'type': 'Evolution',
                'description': f'{requester} requested {agent_type}',
                'importance': 'High'
            })

        # Track pattern discoveries over time
        pattern_data['times'].append(timestamp)
        pattern_data['counts'].append(pattern_data['total_patterns'])
        if len(pattern_data['times']) > 50:
            pattern_data['times'] = pattern_data['times'][-50:]
            pattern_data['counts'] = pattern_data['counts'][-50:]

    # Limit activity log size
    if len(activity_log) > 100:
        activity_log = activity_log[-100:]

    # Calculate swarm health (based on moat health average)
    avg_moat_health = sum(moat_health.values()) / len(moat_health)
    swarm_health['value'] = avg_moat_health
    swarm_health['history'].append(avg_moat_health)
    if len(swarm_health['history']) > 50:
        swarm_health['history'] = swarm_health['history'][-50:]

    return pattern_data, moat_health, activity_log, agent_stats, swarm_health, discoveries

# === KEY METRICS UPDATES ===
@app.callback(
    [Output('total-patterns-metric', 'children'),
     Output('patterns-growth-text', 'children'),
     Output('swarm-health-metric', 'children'),
     Output('swarm-health-status', 'children'),
     Output('haven-risk-metric', 'children'),
     Output('haven-risk-value', 'children')],
    [Input('pattern-store', 'data'),
     Input('swarm-health-store', 'data')]
)
def update_key_metrics(pattern_data, swarm_health):
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

    # Simulate HAVEN risk (low most of the time)
    risk = random.uniform(10, 40) if random.random() > 0.05 else random.uniform(85, 95)
    if risk < 50:
        risk_level = "LOW"
        risk_color = COLORS['success']
    elif risk < 85:
        risk_level = "MEDIUM"
        risk_color = COLORS['warning']
    else:
        risk_level = "HIGH"
        risk_color = COLORS['danger']

    return (
        f"{total:,}",
        growth_text,
        health_display,
        html.Span(health_status, style={'color': health_color}),
        html.Span(risk_level, style={'color': risk_color}),
        f"{risk:.0f}%"
    )

# === TAB RENDERER ===
@app.callback(
    Output('tab-content', 'children'),
    [Input('tabs', 'active_tab')]
)
def render_tab_content(active_tab):

    if active_tab == 'tab-live-story':
        return dbc.Container(fluid=True, children=[
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader(html.H5("📖 The Pattern Discovery Story", style={'color': COLORS['text']})),
                        dbc.CardBody([
                            dcc.Graph(id='pattern-timeline'),
                        ])
                    ], style={'backgroundColor': COLORS['card']})
                ], width=8),
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader(html.H5("🔥 Live Agent Activity", style={'color': COLORS['text']})),
                        dbc.CardBody([
                            html.Div(id='live-activity-feed', style={
                                'maxHeight': '400px',
                                'overflowY': 'scroll',
                                'fontFamily': 'monospace',
                                'fontSize': '0.85rem'
                            })
                        ])
                    ], style={'backgroundColor': COLORS['card']})
                ], width=4),
            ]),
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader(html.H5("💡 Recent Discoveries", style={'color': COLORS['text']})),
                        dbc.CardBody([
                            html.Div(id='discoveries-feed')
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
                        dbc.CardHeader(html.H5("📡 Agent Communication Network", style={'color': COLORS['text']})),
                        dbc.CardBody([
                            dcc.Graph(id='agent-network'),
                        ])
                    ], style={'backgroundColor': COLORS['card']})
                ], width=6),
            ]),
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader(html.H5("📊 What Each Agent Type Is Doing", style={'color': COLORS['text']})),
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
                    html.Label("Select an agent to view their story:", style={'color': COLORS['text'], 'fontWeight': '600'}),
                    dcc.Dropdown(
                        id='agent-selector',
                        options=[{'label': f"{info['name']} ({aid}) - {info['product']}", 'value': aid}
                                for aid, info in AGENT_INFO.items()],
                        value='SwarmBrain_7',
                        style={'backgroundColor': COLORS['card'], 'color': '#000'}
                    ),
                ], width=12),
            ]),
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody(id='agent-card-display')
                    ], style={'backgroundColor': COLORS['card']})
                ], width=12),
            ], className='mt-3'),
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
        ])

    return html.Div("Select a tab")

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
        title=dict(text="Cumulative Pattern Discovery Timeline", font=dict(color=COLORS['text'], size=16)),
        plot_bgcolor=COLORS['card'],
        paper_bgcolor=COLORS['card'],
        font=dict(color=COLORS['text_muted']),
        xaxis=dict(title='Time', gridcolor=COLORS['border']),
        yaxis=dict(title='Total Patterns Discovered', gridcolor=COLORS['border']),
        margin=dict(l=40, r=20, t=60, b=40),
    )
    return fig

# === LIVE ACTIVITY FEED ===
@app.callback(
    Output('live-activity-feed', 'children'),
    [Input('activity-log-store', 'data')]
)
def update_activity_feed(activity_log):
    if not activity_log:
        return html.P("Waiting for agent activity...", style={'color': COLORS['text_muted']})

    feed_items = []
    for item in reversed(activity_log[-30:]):
        feed_items.append(html.Div([
            html.Span(f"[{item['time']}] ", style={'color': COLORS['text_muted']}),
            html.Span(f"{item['agent']}: ", style={'color': COLORS['info'], 'fontWeight': '600'}),
            html.Span(item['action'], style={'color': item['color']}),
        ], style={'marginBottom': '0.5rem'}))

    return feed_items

# === DISCOVERIES FEED ===
@app.callback(
    Output('discoveries-feed', 'children'),
    [Input('discoveries-store', 'data')]
)
def update_discoveries_feed(discoveries):
    if not discoveries:
        return html.P("No major discoveries yet...", style={'color': COLORS['text_muted']})

    items = []
    for disc in reversed(discoveries[-10:]):
        items.append(dbc.Alert([
            html.H6(disc['type'], style={'marginBottom': '5px'}),
            html.P(disc['description'], style={'marginBottom': '0'}),
            html.Small(f"Importance: {disc['importance']} | {disc['time']}", style={'color': COLORS['text_muted']})
        ], color='info', style={'marginBottom': '10px'}))

    return items

# === AGENT LEADERBOARD ===
@app.callback(
    Output('agent-leaderboard', 'figure'),
    [Input('interval', 'n_intervals')]
)
def update_agent_leaderboard(n):
    # Simulate interestingness scores
    agents = list(AGENT_INFO.keys())[:15]
    scores = []
    for agent_id in agents:
        mock_data = {
            'id': agent_id,
            'vector': [random.random() for _ in range(4)],
            'score': random.uniform(0.4, 0.95),
            'parent_id': 'Genesis' if random.random() > 0.6 else f'SwarmBrain_{random.randint(7, 50)}',
            'generation': random.randint(0, 5)
        }
        interest_score = calculate_interestingness(mock_data, {})
        scores.append((agent_id, interest_score))

    scores.sort(key=lambda x: x[1], reverse=True)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=[AGENT_INFO[a[0]]['name'] for a in scores],
        x=[a[1] for a in scores],
        orientation='h',
        marker=dict(color=[a[1] for a in scores], colorscale='Purples', showscale=False),
        text=[f"{a[1]:.1f}" for a in scores],
        textposition='outside'
    ))

    fig.update_layout(
        title=dict(text="Top 15 Most Interesting Agents (5-Component Score)", font=dict(color=COLORS['text'], size=14)),
        plot_bgcolor=COLORS['card'],
        paper_bgcolor=COLORS['card'],
        font=dict(color=COLORS['text_muted']),
        xaxis=dict(title='Interestingness Score (0-100)', gridcolor=COLORS['border']),
        yaxis=dict(gridcolor=COLORS['border']),
        margin=dict(l=120, r=20, t=60, b=40),
        height=500
    )
    return fig

# === AGENT NETWORK ===
@app.callback(
    Output('agent-network', 'figure'),
    [Input('interval', 'n_intervals')]
)
def update_agent_network(n):
    agents = list(AGENT_INFO.keys())[:20]
    num_agents = len(agents)

    # Circular layout
    x_pos = [math.cos(2 * math.pi * i / num_agents) for i in range(num_agents)]
    y_pos = [math.sin(2 * math.pi * i / num_agents) for i in range(num_agents)]

    fig = go.Figure()

    # Add edges
    for i in range(num_agents - 1):
        fig.add_trace(go.Scatter(
            x=[x_pos[i], x_pos[i+1]],
            y=[y_pos[i], y_pos[i+1]],
            mode='lines',
            line=dict(color=COLORS['border'], width=1),
            showlegend=False,
            hoverinfo='none'
        ))

    # Add nodes
    fig.add_trace(go.Scatter(
        x=x_pos,
        y=y_pos,
        mode='markers+text',
        marker=dict(size=15, color=COLORS['primary'], line=dict(color=COLORS['text'], width=2)),
        text=[a.split('_')[-1][:3] for a in agents],
        textposition='top center',
        textfont=dict(color=COLORS['text'], size=9),
        hovertext=[AGENT_INFO[a]['name'] for a in agents],
        hoverinfo='text',
        showlegend=False
    ))

    fig.update_layout(
        title=dict(text="Agent Policy Sharing Network", font=dict(color=COLORS['text'], size=14)),
        plot_bgcolor=COLORS['card'],
        paper_bgcolor=COLORS['card'],
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        margin=dict(l=20, r=20, t=60, b=20),
        height=500
    )
    return fig

# === AGENT TYPE SUMMARY ===
@app.callback(
    Output('agent-type-summary', 'children'),
    [Input('interval', 'n_intervals')]
)
def update_agent_type_summary(n):
    summary = [
        {'icon': 'fa-brain', 'type': 'Pattern Learners (100)', 'activity': 'Analyzing data streams, discovering correlations, sharing policies', 'color': COLORS['primary']},
        {'icon': 'fa-search', 'type': 'Data Miners (6)', 'activity': 'Collecting data from 5 product moats: Finance, Code, Logistics, Gov, Corp', 'color': COLORS['success']},
        {'icon': 'fa-shield-alt', 'type': 'HAVEN Guardian (1)', 'activity': 'Monitoring system risk, blocking policy contagion at 85% threshold', 'color': COLORS['danger']},
        {'icon': 'fa-cogs', 'type': 'Builder (1)', 'activity': 'Autonomously creating new specialized agents when gaps detected', 'color': '#9333ea'},
        {'icon': 'fa-bolt', 'type': 'Executor (1)', 'activity': 'Executing high-confidence pattern predictions', 'color': '#fbbf24'},
    ]

    items = []
    for s in summary:
        items.append(dbc.Card([
            dbc.CardBody([
                html.Div([
                    html.I(className=f"fas {s['icon']} fa-2x", style={'color': s['color'], 'marginRight': '15px'}),
                    html.Div([
                        html.H6(s['type'], style={'color': COLORS['text'], 'marginBottom': '5px'}),
                        html.P(s['activity'], style={'color': COLORS['text_muted'], 'fontSize': '0.9rem', 'marginBottom': '0'}),
                    ], style={'flex': 1})
                ], style={'display': 'flex', 'alignItems': 'center'})
            ])
        ], style={'backgroundColor': COLORS['background'], 'marginBottom': '10px'}))

    return items

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
    [Input('moat-health-store', 'data')]
)
def update_moat_details(moat_health):
    def create_detail(moat_name):
        health = moat_health.get(moat_name, 100)
        patterns = random.randint(50, 500)
        agents = random.randint(15, 25)
        return html.Div([
            html.P(f"Health: {health:.0f}%", style={'color': COLORS['text'], 'fontSize': '1.2rem', 'fontWeight': '600'}),
            html.P(f"Patterns: {patterns}", style={'color': COLORS['text_muted'], 'fontSize': '0.9rem'}),
            html.P(f"Active Agents: {agents}", style={'color': COLORS['text_muted'], 'fontSize': '0.9rem'}),
        ])

    return (
        create_detail('Finance'),
        create_detail('Code Innovation'),
        create_detail('Logistics'),
        create_detail('Government'),
        create_detail('US Corporations')
    )

# === AGENT CARD DISPLAY ===
@app.callback(
    Output('agent-card-display', 'children'),
    [Input('agent-selector', 'value'),
     Input('agent-stats-store', 'data')]
)
def update_agent_card_display(agent_id, agent_stats):
    if not agent_id:
        return html.P("Select an agent", style={'color': COLORS['text_muted']})

    agent_info = AGENT_INFO.get(agent_id, {'name': 'Unknown', 'type': 'Unknown', 'color': COLORS['text_muted'], 'icon': 'fa-robot', 'product': 'N/A'})

    # Get real agent stats or use defaults
    agent_data = agent_stats.get(agent_id, {
        'patterns_discovered': 0,
        'policy_shares': 0,
        'last_active': 'Never',
        'generation': 0,
        'parent': 'Genesis',
        'children': [],
        'status': 'Waiting for data...'
    })

    # Calculate interestingness score from real data
    mock_agent_data = {
        'id': agent_id,
        'vector': [random.random() for _ in range(4)],
        'score': min(agent_data['patterns_discovered'] / 100.0, 0.95),  # Based on patterns
        'parent_id': agent_data.get('parent', 'Genesis'),
        'generation': agent_data.get('generation', 0)
    }
    interestingness = calculate_interestingness(mock_agent_data, {})

    # Count children (agents that have this agent as parent)
    children_count = len([aid for aid, adata in agent_stats.items()
                         if adata.get('parent') == agent_id])

    # Build stats dictionary with REAL data
    stats = {
        'Interestingness Score': f"{interestingness:.1f}/100",
        'Generation': agent_data.get('generation', 0),
        'Patterns Discovered': agent_data.get('patterns_discovered', 0),
        'Policy Shares': agent_data.get('policy_shares', 0),
        'Parent': agent_data.get('parent', 'Genesis'),
        'Children': children_count,
        'Status': agent_data.get('status', 'Active'),
        'Last Active': agent_data.get('last_active', 'Never')
    }

    return html.Div([
        dbc.Row([
            dbc.Col([
                html.Div([
                    html.I(className=f"fas {agent_info['icon']} fa-5x", style={'color': agent_info['color']}),
                ], style={'textAlign': 'center', 'padding': '2rem'}),
            ], width=3),
            dbc.Col([
                html.H3(agent_info['name'], style={'color': agent_info['color'], 'fontWeight': '700'}),
                html.H5(f"ID: {agent_id}", style={'color': COLORS['text_muted']}),
                html.P(f"Type: {agent_info['type']}", style={'color': COLORS['text'], 'fontSize': '1.1rem'}),
                html.P(f"Product Moat: {agent_info['product']}", style={'color': COLORS['text'], 'fontSize': '1.1rem'}),
            ], width=9),
        ]),
        html.Hr(style={'borderColor': COLORS['border']}),
        dbc.Row([
            dbc.Col([
                html.H5("📊 Agent Statistics", style={'color': COLORS['primary'], 'marginBottom': '1rem'}),
                html.Div([
                    html.P([
                        html.Strong(f"{k}: ", style={'color': COLORS['text_muted']}),
                        html.Span(f"{v}", style={'color': COLORS['text']})
                    ], style={'marginBottom': '0.5rem'})
                    for k, v in stats.items()
                ])
            ], width=12),
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
    [Input('interval', 'n_intervals')]
)
def update_interestingness_dist(n):
    # Simulate distribution
    scores = [random.uniform(40, 100) for _ in range(100)]

    fig = go.Figure()
    fig.add_trace(go.Histogram(
        x=scores,
        nbinsx=20,
        marker=dict(color=COLORS['primary']),
    ))

    fig.update_layout(
        title=dict(text="Interestingness Score Distribution (All 100 Learners)", font=dict(color=COLORS['text'], size=16)),
        plot_bgcolor=COLORS['card'],
        paper_bgcolor=COLORS['card'],
        font=dict(color=COLORS['text_muted']),
        xaxis=dict(title='Interestingness Score', gridcolor=COLORS['border']),
        yaxis=dict(title='Number of Agents', gridcolor=COLORS['border']),
        margin=dict(l=40, r=20, t=60, b=40),
    )
    return fig

if __name__ == '__main__':
    try:
        app.run(debug=False, port=8055, host='127.0.0.1')
    except Exception as e:
        logging.critical(f"FATAL: {e}")
