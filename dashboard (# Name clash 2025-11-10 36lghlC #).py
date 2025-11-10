# dashboard.py - MYCELIAL INTELLIGENCE v8.1: ENTERPRISE EDITION
# Professional Business Intelligence Dashboard
# Clean, corporate design focused on actionable insights

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
from collections import defaultdict, deque
from datetime import datetime

from src.connectors.redis_client import RedisClient

# === SETUP ===
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

message_queue = Queue()
SESSION_ID = str(uuid.uuid4())[:8]

# === INTERESTINGNESS FORMULA ===
def calculate_interestingness(agent_data, all_agents):
    """
    Calculate how 'interesting' an agent is based on:
    - Novelty: How different from its parent
    - Performance: Prediction score quality
    - Diversity: Uniqueness in the swarm
    - Evolution: Generation and improvement rate
    Returns score 0-100
    """
    score = 0

    # 1. Novelty Score (30 points): Distance from parent strategy
    if 'parent_vector' in agent_data and agent_data['parent_vector']:
        parent_vec = np.array(agent_data['parent_vector'])
        current_vec = np.array(agent_data['vector'])
        novelty = np.linalg.norm(current_vec - parent_vec)
        score += min(novelty * 10, 30)
    else:
        score += 15  # Genesis agents get baseline

    # 2. Performance Score (30 points): Prediction quality
    pred_score = agent_data.get('score', 0.5)
    score += pred_score * 30

    # 3. Diversity Score (20 points): How unique in the swarm
    if all_agents:
        vectors = [a['vector'] for a in all_agents.values()]
        my_vec = np.array(agent_data['vector'])
        distances = [np.linalg.norm(my_vec - np.array(v)) for v in vectors]
        avg_distance = np.mean(distances) if distances else 0
        score += min(avg_distance * 5, 20)

    # 4. Evolution Bonus (20 points): Generation progress
    generation = agent_data.get('generation', 0)
    score += min(generation * 2, 20)

    return min(score, 100)

# === DASH APP ===
app = dash.Dash(
    __name__,
    external_stylesheets=[
        dbc.themes.FLATLY,  # Clean, professional Bootstrap theme
        "https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Roboto:wght@400;500;700&display=swap"
    ],
    suppress_callback_exceptions=True,
)
app.title = "Mycelial Intelligence | Enterprise Analytics"

# Professional color palette
COLORS = {
    'primary': '#1e40af',      # Professional blue
    'secondary': '#64748b',    # Slate gray
    'success': '#059669',      # Professional green
    'warning': '#d97706',      # Amber
    'danger': '#dc2626',       # Red
    'info': '#0284c7',         # Sky blue
    'background': '#f8fafc',   # Light gray background
    'card': '#ffffff',         # White cards
    'text': '#1e293b',         # Dark slate text
    'text_muted': '#64748b',   # Muted text
    'border': '#e2e8f0',       # Light border
}

# === LAYOUT ===
app.layout = dbc.Container(
    fluid=True,
    className="p-4",
    style={'backgroundColor': COLORS['background'], 'minHeight': '100vh', 'fontFamily': "'Inter', sans-serif"},
    children=[
        # Data stores
        dcc.Store(id='agent-intelligence-data', data={}),
        dcc.Store(id='pattern-discoveries-data', data=[]),
        dcc.Store(id='moat-activity-data', data={}),
        dcc.Store(id='evolution-network-data', data={}),
        dcc.Interval(id='interval', interval=2000, n_intervals=0),

        # === HEADER ===
        dbc.Row(dbc.Col([
            html.Div([
                html.H1("Mycelial Intelligence Platform",
                       style={'fontSize': '2rem', 'fontWeight': '600', 'color': COLORS['primary'],
                              'marginBottom': '0.25rem'}),
                html.P("Enterprise Pattern Discovery & Agent Analytics",
                      style={'color': COLORS['text_muted'], 'fontSize': '0.95rem', 'marginBottom': '0'}),
            ], className="mb-4")
        ], width=12)),

        # === TABS ===
        dbc.Tabs(id="tabs", active_tab="tab-overview", className="mb-4", children=[
            dbc.Tab(label="Overview", tab_id="tab-overview"),
            dbc.Tab(label="Pattern Discovery", tab_id="tab-patterns"),
            dbc.Tab(label="Agent Performance", tab_id="tab-agents"),
            dbc.Tab(label="Market Intelligence", tab_id="tab-moats"),
            dbc.Tab(label="Evolution Tracking", tab_id="tab-evolution"),
        ]),
        html.Div(id="tab-content"),

        # Footer
        html.Div([
            html.Span(f"Session: {SESSION_ID}", style={'marginRight': '20px'}),
            html.Span("System Status: Active", style={'color': COLORS['success']}),
        ], className="text-center mt-4", style={'color': COLORS['text_muted'], 'fontSize': '0.85rem', 'paddingTop': '1rem', 'borderTop': f'1px solid {COLORS["border"]}'})
    ]
)

# === REDIS LISTENER ===
def start_redis_listener(app_queue: Queue):
    logging.info("Dashboard v8.1 (Enterprise): Redis listener started")
    try:
        redis_client = RedisClient()
    except Exception as e:
        logging.critical(f"Redis error: {e}")
        return
    if not redis_client.connection:
        return

    channels = {
        'market-data:*': 'market-data',
        'govt-data:*': 'govt-data',
        'corp-data:*': 'corp-data',
        'repo-data:*': 'repo-data',
        'logistics-data:*': 'logistics-data',
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
                    app_queue.put({'type': msg_type, 'data': data, 'time': time.time()})
                except:
                    pass
        except:
            pass
        finally:
            pubsub.close()

    for pattern, msg_type in channels.items():
        t = threading.Thread(target=create_listener, args=(pattern, msg_type), daemon=True)
        t.start()

# === TAB CONTENT ===
@app.callback(Output("tab-content", "children"), Input("tabs", "active_tab"))
def render_tab_content(active_tab):

    if active_tab == "tab-overview":
        return dbc.Row([
            # KPI Cards
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H6("Total Agents", className="text-muted mb-2"),
                        html.H2(id='kpi-total-agents', className="mb-0", style={'color': COLORS['primary']}),
                    ])
                ], style={'border': f'1px solid {COLORS["border"]}', 'background': COLORS['card']})
            ], width=12, md=3, className="mb-3"),

            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H6("High Performers", className="text-muted mb-2"),
                        html.H2(id='kpi-high-performers', className="mb-0", style={'color': COLORS['success']}),
                    ])
                ], style={'border': f'1px solid {COLORS["border"]}', 'background': COLORS['card']})
            ], width=12, md=3, className="mb-3"),

            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H6("Avg Confidence", className="text-muted mb-2"),
                        html.H2(id='kpi-avg-confidence', className="mb-0", style={'color': COLORS['info']}),
                    ])
                ], style={'border': f'1px solid {COLORS["border"]}', 'background': COLORS['card']})
            ], width=12, md=3, className="mb-3"),

            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H6("Strategy Diversity", className="text-muted mb-2"),
                        html.H2(id='kpi-diversity', className="mb-0", style={'color': COLORS['warning']}),
                    ])
                ], style={'border': f'1px solid {COLORS["border"]}', 'background': COLORS['card']})
            ], width=12, md=3, className="mb-3"),

            # Swarm Summary
            dbc.Col(dbc.Card([
                dbc.CardHeader("System Overview", style={'background': COLORS['card'], 'borderBottom': f'2px solid {COLORS["primary"]}', 'fontWeight': '600'}),
                dbc.CardBody(html.Div(id='swarm-summary'))
            ], style={'border': f'1px solid {COLORS["border"]}'}, className="mb-3"), width=12, lg=7),

            # Activity Chart
            dbc.Col(dbc.Card([
                dbc.CardHeader("Market Activity", style={'background': COLORS['card'], 'borderBottom': f'2px solid {COLORS["primary"]}', 'fontWeight': '600'}),
                dbc.CardBody(dcc.Graph(id='activity-chart', config={'displayModeBar': False}, style={'height': '280px'}))
            ], style={'border': f'1px solid {COLORS["border"]}'}, className="mb-3"), width=12, lg=5),
        ])

    elif active_tab == "tab-patterns":
        return dbc.Row([
            # Pattern Timeline
            dbc.Col(dbc.Card([
                dbc.CardHeader("Discovered Patterns", style={'background': COLORS['card'], 'borderBottom': f'2px solid {COLORS["primary"]}', 'fontWeight': '600'}),
                dbc.CardBody(html.Div(id='pattern-timeline', style={'height': '500px', 'overflowY': 'auto'}))
            ], style={'border': f'1px solid {COLORS["border"]}'}, className="mb-3"), width=12, lg=8),

            # Top Performers
            dbc.Col(dbc.Card([
                dbc.CardHeader("Top 10 Performers", style={'background': COLORS['card'], 'borderBottom': f'2px solid {COLORS["primary"]}', 'fontWeight': '600'}),
                dbc.CardBody(html.Div(id='top-performers'))
            ], style={'border': f'1px solid {COLORS["border"]}'}, className="mb-3"), width=12, lg=4),
        ])

    elif active_tab == "tab-agents":
        return dbc.Row([
            dbc.Col(dbc.Card([
                dbc.CardHeader("Agent Performance Analysis", style={'background': COLORS['card'], 'borderBottom': f'2px solid {COLORS["primary"]}', 'fontWeight': '600'}),
                dbc.CardBody(html.Div(id='agent-details'))
            ], style={'border': f'1px solid {COLORS["border"]}'}, className="mb-3"), width=12),
        ])

    elif active_tab == "tab-moats":
        return dbc.Row([
            dbc.Col(dbc.Card([
                dbc.CardHeader("Market Intelligence Distribution", style={'background': COLORS['card'], 'borderBottom': f'2px solid {COLORS["primary"]}', 'fontWeight': '600'}),
                dbc.CardBody(dcc.Graph(id='moat-analysis', config={'displayModeBar': False}, style={'height': '500px'}))
            ], style={'border': f'1px solid {COLORS["border"]}'}, className="mb-3"), width=12),
        ])

    elif active_tab == "tab-evolution":
        return dbc.Row([
            dbc.Col(dbc.Card([
                dbc.CardHeader("Agent Evolution Network", style={'background': COLORS['card'], 'borderBottom': f'2px solid {COLORS["primary"]}', 'fontWeight': '600'}),
                dbc.CardBody([
                    html.P("Visualization of agent lineage and performance relationships",
                          className="text-muted mb-3"),
                    dcc.Graph(id='evolution-network', config={'displayModeBar': False}, style={'height': '600px'})
                ])
            ], style={'border': f'1px solid {COLORS["border"]}'}, className="mb-3"), width=12),
        ])

    return html.Div("Loading...")

# === DATA PROCESSING ===
@app.callback(
    Output('agent-intelligence-data', 'data'),
    Output('pattern-discoveries-data', 'data'),
    Output('moat-activity-data', 'data'),
    Output('evolution-network-data', 'data'),
    Input('interval', 'n_intervals'),
    State('agent-intelligence-data', 'data'),
    State('pattern-discoveries-data', 'data'),
    State('moat-activity-data', 'data'),
)
def update_intelligence_data(n, agents, patterns, moat_data):
    current_time = time.time()

    moat_counts = {'Finance': 0, 'Code': 0, 'Logistics': 0, 'Government': 0, 'Corporations': 0}

    while not message_queue.empty():
        try:
            msg = message_queue.get_nowait()
            msg_type = msg['type']
            if 'market-data' in msg_type:
                moat_counts['Finance'] += 1
            elif 'repo-data' in msg_type:
                moat_counts['Code'] += 1
            elif 'logistics-data' in msg_type:
                moat_counts['Logistics'] += 1
            elif 'govt-data' in msg_type:
                moat_counts['Government'] += 1
            elif 'corp-data' in msg_type:
                moat_counts['Corporations'] += 1
        except:
            pass

    for moat in moat_counts:
        moat_data[moat] = moat_data.get(moat, 0) + moat_counts[moat]

    try:
        redis_conn = RedisClient()
        policy_keys = redis_conn.connection.keys("policy:SwarmBrain_*")  # type: ignore

        for key in policy_keys[:100]:  # type: ignore
            try:
                data = redis_conn.connection.get(key)  # type: ignore
                if data:
                    policy = json.loads(data)  # type: ignore
                    agent_id = policy.get('agent_id', key.decode().replace('policy:', ''))  # type: ignore

                    parent_id = policy.get('parent_id')
                    parent_vector = None
                    if parent_id and parent_id in agents:
                        parent_vector = agents[parent_id].get('vector')

                    agent_profile = {
                        'id': str(agent_id),
                        'vector': policy.get('strategy_vector', [70, 1.0, 0, 50]),
                        'score': policy.get('prediction_score', 0.5),
                        'generation': policy.get('generation', 0),
                        'parent_id': parent_id or 'Genesis',
                        'parent_vector': parent_vector,
                        'birth_time': policy.get('birth_timestamp', current_time),
                        'product_focus': policy.get('product_focus', 'Finance'),
                    }

                    interestingness = calculate_interestingness(agent_profile, agents)
                    agent_profile['interestingness'] = interestingness
                    agents[str(agent_id)] = agent_profile

                    if interestingness > 75 and not any(p.get('agent_id') == agent_id for p in patterns):
                        pattern = {
                            'time': datetime.now().strftime('%H:%M:%S'),
                            'agent_id': agent_id,
                            'type': 'High Performance',
                            'description': f"Agent {agent_id} achieved {interestingness:.0f}% performance score in {policy.get('product_focus', 'Unknown')} domain",
                            'score': interestingness,
                            'generation': policy.get('generation', 0)
                        }
                        patterns.append(pattern)
                        patterns = patterns[-50:]
            except:
                pass
    except:
        pass

    network = {'nodes': [], 'edges': []}
    for agent_id, agent in agents.items():
        network['nodes'].append({
            'id': agent_id,
            'interestingness': agent.get('interestingness', 50),
            'score': agent.get('score', 0.5),
            'generation': agent.get('generation', 0),
            'product': agent.get('product_focus', 'Finance')
        })
        if agent.get('parent_id') and agent['parent_id'] != 'Genesis':
            network['edges'].append({'source': agent['parent_id'], 'target': agent_id})

    return agents, patterns, moat_data, network

# === KPI CALLBACKS ===
@app.callback(
    Output('kpi-total-agents', 'children'),
    Output('kpi-high-performers', 'children'),
    Output('kpi-avg-confidence', 'children'),
    Output('kpi-diversity', 'children'),
    Input('agent-intelligence-data', 'data')
)
def update_kpis(agents):
    if not agents:
        return "0", "0", "0%", "0.00"

    total = len(agents)
    high_perf = sum(1 for a in agents.values() if a.get('interestingness', 0) > 70)
    avg_conf = np.mean([a['score'] for a in agents.values()])
    diversity = np.std([a['vector'][0] for a in agents.values()]) if agents else 0

    return str(total), str(high_perf), f"{avg_conf:.1%}", f"{diversity:.2f}"

# === OVERVIEW ===
@app.callback(Output('swarm-summary', 'children'), Input('agent-intelligence-data', 'data'))
def update_summary(agents):
    if not agents:
        return html.P("System initializing...", className="text-muted")

    total_agents = len(agents)
    avg_score = np.mean([a['score'] for a in agents.values()])
    avg_gen = np.mean([a['generation'] for a in agents.values()])
    max_gen = max([a['generation'] for a in agents.values()]) if agents else 0

    product_dist = {}
    for agent in agents.values():
        product = agent.get('product_focus', 'Unknown')
        product_dist[product] = product_dist.get(product, 0) + 1

    most_active = max(product_dist, key=product_dist.get) if product_dist else "N/A"
    top_agent = max(agents.values(), key=lambda x: x.get('interestingness', 0))

    return html.Div([
        html.Div([
            html.Strong("Active Agents: "),
            html.Span(f"{total_agents} (Generation {avg_gen:.1f}, Max Gen {max_gen})", className="ms-2")
        ], className="mb-2"),
        html.Div([
            html.Strong("Average Confidence: "),
            html.Span(f"{avg_score:.1%}", className="ms-2", style={'color': COLORS['success']})
        ], className="mb-2"),
        html.Div([
            html.Strong("Primary Focus Area: "),
            html.Span(f"{most_active} ({product_dist.get(most_active, 0)} agents)", className="ms-2")
        ], className="mb-2"),
        html.Div([
            html.Strong("Top Performer: "),
            html.Span(f"{top_agent['id']} (Score: {top_agent.get('interestingness', 0):.0f})",
                     className="ms-2", style={'color': COLORS['primary']})
        ]),
    ])

# === ACTIVITY CHART ===
@app.callback(Output('activity-chart', 'figure'), Input('moat-activity-data', 'data'))
def update_activity(moat_data):
    if not moat_data:
        moat_data = {'Finance': 0, 'Code': 0, 'Logistics': 0, 'Government': 0, 'Corporations': 0}

    colors_map = {
        'Finance': COLORS['primary'],
        'Code': COLORS['success'],
        'Logistics': COLORS['warning'],
        'Government': COLORS['info'],
        'Corporations': COLORS['danger']
    }

    fig = go.Figure(data=[go.Bar(
        x=list(moat_data.keys()),
        y=list(moat_data.values()),
        marker_color=[colors_map.get(k, COLORS['secondary']) for k in moat_data.keys()],
        text=list(moat_data.values()),
        textposition='outside'
    )])

    fig.update_layout(
        template='plotly_white',
        margin=dict(l=40, r=20, t=20, b=60),
        xaxis=dict(title='Market', showgrid=False),
        yaxis=dict(title='Activity', showgrid=True, gridcolor='#f1f5f9'),
        showlegend=False,
        font=dict(family="'Inter', sans-serif", size=12),
        plot_bgcolor='white',
        paper_bgcolor='white'
    )

    return fig

# === PATTERN TIMELINE ===
@app.callback(Output('pattern-timeline', 'children'), Input('pattern-discoveries-data', 'data'))
def update_patterns(patterns):
    if not patterns:
        return html.Div("No significant patterns detected yet.", className="text-muted text-center py-5")

    items = []
    for i, pattern in enumerate(reversed(patterns)):
        badge_color = COLORS['success'] if pattern['score'] > 85 else COLORS['info'] if pattern['score'] > 75 else COLORS['secondary']

        items.append(
            html.Div([
                html.Div([
                    dbc.Badge(f"Gen {pattern['generation']}", color="light", className="me-2",
                             style={'color': badge_color, 'borderColor': badge_color, 'border': '1px solid'}),
                    html.Span(pattern['time'], className="text-muted me-3", style={'fontSize': '0.85rem'}),
                    html.Strong(pattern['type'], style={'color': COLORS['text']}),
                ], className="mb-2"),
                html.P(pattern['description'], className="mb-1", style={'color': COLORS['text'], 'marginLeft': '0'}),
                html.Small(f"Performance Score: {pattern['score']:.0f}/100", className="text-muted"),
                html.Hr(style={'borderColor': COLORS['border'], 'margin': '1rem 0'})
            ], className="mb-2")
        )

    return html.Div(items)

# === TOP PERFORMERS ===
@app.callback(Output('top-performers', 'children'), Input('agent-intelligence-data', 'data'))
def update_top_performers(agents):
    if not agents:
        return html.P("No data", className="text-muted")

    sorted_agents = sorted(agents.values(), key=lambda x: x.get('interestingness', 0), reverse=True)[:10]

    items = []
    for rank, agent in enumerate(sorted_agents, 1):
        score = agent.get('interestingness', 0)
        color = COLORS['success'] if score > 85 else COLORS['info'] if score > 75 else COLORS['secondary']

        items.append(
            html.Div([
                html.Div([
                    dbc.Badge(f"#{rank}", color="light", className="me-2"),
                    html.Strong(agent['id'], style={'color': color}),
                ], className="d-flex align-items-center mb-1"),
                html.Div([
                    html.Small(f"Score: {score:.0f} | Gen {agent['generation']} | {agent.get('product_focus', 'N/A')}",
                              className="text-muted")
                ])
            ], className="mb-3", style={'paddingBottom': '0.75rem', 'borderBottom': f'1px solid {COLORS["border"]}'})
        )

    return html.Div(items)

# === AGENT DETAILS ===
@app.callback(Output('agent-details', 'children'), Input('agent-intelligence-data', 'data'))
def update_agent_details(agents):
    if not agents:
        return html.P("No agents available", className="text-muted")

    top_agents = sorted(agents.values(), key=lambda x: x.get('interestingness', 0), reverse=True)[:5]

    cards = []
    for agent in top_agents:
        score = agent.get('interestingness', 0)
        color = COLORS['success'] if score > 85 else COLORS['info'] if score > 75 else COLORS['secondary']

        card = dbc.Card([
            dbc.CardHeader(agent['id'], style={'background': color, 'color': 'white', 'fontWeight': '600'}),
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        html.H6("Performance Score", className="text-muted mb-1"),
                        html.H4(f"{score:.0f}/100", style={'color': color})
                    ], width=3),
                    dbc.Col([
                        html.H6("Generation", className="text-muted mb-1"),
                        html.H4(f"{agent['generation']}")
                    ], width=3),
                    dbc.Col([
                        html.H6("Confidence", className="text-muted mb-1"),
                        html.H4(f"{agent['score']:.1%}")
                    ], width=3),
                    dbc.Col([
                        html.H6("Focus Area", className="text-muted mb-1"),
                        html.H4(agent.get('product_focus', 'N/A'), style={'fontSize': '1rem'})
                    ], width=3),
                ]),
                html.Hr(),
                html.Div([
                    html.Strong("Strategy Vector: "),
                    html.Code(f"[{', '.join(f'{v:.2f}' for v in agent['vector'][:4])}]")
                ])
            ])
        ], className="mb-3", style={'border': f'1px solid {COLORS["border"]}'})

        cards.append(card)

    return html.Div(cards)

# === MOAT ANALYSIS ===
@app.callback(Output('moat-analysis', 'figure'), Input('agent-intelligence-data', 'data'))
def update_moat_analysis(agents):
    if not agents:
        return go.Figure()

    moat_metrics = {
        'Finance': {'count': 0, 'avg_score': 0, 'avg_interesting': 0},
        'Code': {'count': 0, 'avg_score': 0, 'avg_interesting': 0},
        'Logistics': {'count': 0, 'avg_score': 0, 'avg_interesting': 0},
        'Government': {'count': 0, 'avg_score': 0, 'avg_interesting': 0},
        'Corporations': {'count': 0, 'avg_score': 0, 'avg_interesting': 0},
    }

    for agent in agents.values():
        product = agent.get('product_focus', 'Finance')
        if product in moat_metrics:
            moat_metrics[product]['count'] += 1
            moat_metrics[product]['avg_score'] += agent.get('score', 0)
            moat_metrics[product]['avg_interesting'] += agent.get('interestingness', 0)

    moats = []
    agent_counts = []
    avg_scores = []
    avg_interesting = []

    for moat, metrics in moat_metrics.items():
        moats.append(moat)
        count = metrics['count']
        agent_counts.append(count)
        avg_scores.append(metrics['avg_score'] / count if count > 0 else 0)
        avg_interesting.append(metrics['avg_interesting'] / count if count > 0 else 0)

    colors_map = {
        'Finance': COLORS['primary'],
        'Code': COLORS['success'],
        'Logistics': COLORS['warning'],
        'Government': COLORS['info'],
        'Corporations': COLORS['danger']
    }
    colors = [colors_map.get(m, COLORS['secondary']) for m in moats]

    fig = make_subplots(
        rows=1, cols=3,
        subplot_titles=('Agent Count', 'Avg Confidence', 'Avg Performance Score'),
        specs=[[{'type': 'bar'}, {'type': 'bar'}, {'type': 'bar'}]]
    )

    fig.add_trace(go.Bar(x=moats, y=agent_counts, marker_color=colors, name='Count', showlegend=False), row=1, col=1)
    fig.add_trace(go.Bar(x=moats, y=avg_scores, marker_color=colors, name='Confidence', showlegend=False), row=1, col=2)
    fig.add_trace(go.Bar(x=moats, y=avg_interesting, marker_color=colors, name='Performance', showlegend=False), row=1, col=3)

    fig.update_layout(
        template='plotly_white',
        height=500,
        font=dict(family="'Inter', sans-serif", size=12),
        showlegend=False
    )

    return fig

# === EVOLUTION NETWORK ===
@app.callback(Output('evolution-network', 'figure'), Input('evolution-network-data', 'data'))
def update_evolution_network(network):
    if not network or not network.get('nodes'):
        fig = go.Figure()
        fig.add_annotation(text="Building agent network...", showarrow=False, font={'size': 14, 'color': COLORS['text_muted']})
        fig.update_layout(template='plotly_white', height=600)
        return fig

    nodes = network['nodes'][:50]
    edges = network['edges']

    n = len(nodes)
    node_positions = {}
    for i, node in enumerate(nodes):
        angle = 2 * math.pi * i / n
        radius = 100 + node['generation'] * 20
        x = radius * math.cos(angle)
        y = radius * math.sin(angle)
        node_positions[node['id']] = (x, y)

    edge_x, edge_y = [], []
    for edge in edges:
        if edge['source'] in node_positions and edge['target'] in node_positions:
            x0, y0 = node_positions[edge['source']]
            x1, y1 = node_positions[edge['target']]
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])

    node_x, node_y, node_sizes, node_colors, node_text = [], [], [], [], []
    for node in nodes:
        if node['id'] in node_positions:
            x, y = node_positions[node['id']]
            node_x.append(x)
            node_y.append(y)
            node_sizes.append(10 + node['interestingness'] / 5)
            node_colors.append(node['score'] * 100)
            node_text.append(f"{node['id']}<br>Gen {node['generation']}<br>Score: {node['interestingness']:.0f}")

    fig = go.Figure()

    fig.add_trace(go.Scatter(x=edge_x, y=edge_y, mode='lines', line=dict(color='#cbd5e1', width=1),
                            hoverinfo='none', showlegend=False))

    fig.add_trace(go.Scatter(x=node_x, y=node_y, mode='markers',
        marker=dict(size=node_sizes, color=node_colors, colorscale='Blues',
                   colorbar=dict(title='Confidence %'), line=dict(color=COLORS['primary'], width=1)),
        text=node_text, hoverinfo='text', showlegend=False))

    fig.update_layout(
        template='plotly_white',
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        height=600,
        margin=dict(l=0, r=0, t=0, b=0)
    )

    return fig

# === RUN ===
if __name__ == '__main__':
    try:
        listener_thread = threading.Thread(target=start_redis_listener, args=(message_queue,), daemon=True)
        listener_thread.start()
        logging.info("Mycelial Intelligence v8.1 (Enterprise Edition)")
        logging.info("Professional analytics dashboard active")
        app.run(debug=False, port=8055, host='127.0.0.1')
    except Exception as e:
        logging.critical(f"FATAL: {e}")
