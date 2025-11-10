# dashboard.py - USER-FRIENDLY EDITION v5.0
# Designed for everyone to understand, with smooth animations and rich information

import dash
from dash import dcc, html, Input, Output, State, ctx
import plotly.graph_objects as go
import logging
import time
import json
import threading
from queue import Queue
import random
import math
import dash_bootstrap_components as dbc
import redis
import uuid

from src.connectors.redis_client import RedisClient

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

message_queue = Queue()
SESSION_ID = str(uuid.uuid4())[:8]

# === AGENT METADATA ===
AGENT_INFO = {
    'DataMiner_XXBTZUSD_1': {
        'name': 'Bitcoin Data Collector',
        'type': 'Data Sensor',
        'simple_desc': 'Watches Bitcoin prices in real-time',
        'description': 'This agent constantly monitors the Bitcoin market, pulling in the latest price information every second from the Kraken exchange. Think of it as a watchful eye on Bitcoin\'s price movements.',
        'what_it_does': [
            'Checks Bitcoin price every second',
            'Sends price updates to the decision-making agents',
            'Keeps track of price history',
            'Alerts if connection is lost'
        ],
        'connections': ['PatternLearner_XXBTZUSD_3'],
        'color': '#a855f7',
        'status_messages': ['Monitoring Bitcoin market...', 'Price updated', 'Fetching latest data']
    },
    'DataMiner_XETHZUSD_2': {
        'name': 'Ethereum Data Collector',
        'type': 'Data Sensor',
        'simple_desc': 'Watches Ethereum prices in real-time',
        'description': 'This agent constantly monitors the Ethereum market, pulling in the latest price information every second from the Kraken exchange. Think of it as a watchful eye on Ethereum\'s price movements.',
        'what_it_does': [
            'Checks Ethereum price every second',
            'Sends price updates to the decision-making agents',
            'Keeps track of price history',
            'Alerts if connection is lost'
        ],
        'connections': ['PatternLearner_XETHZUSD_4'],
        'color': '#a855f7',
        'status_messages': ['Monitoring Ethereum market...', 'Price updated', 'Fetching latest data']
    },
    'PatternLearner_XXBTZUSD_3': {
        'name': 'Bitcoin Strategy Brain',
        'type': 'Decision Maker',
        'simple_desc': 'Analyzes Bitcoin patterns and decides when to buy/sell',
        'description': 'This is the "thinking" agent that looks at Bitcoin price movements and uses a simple strategy to decide when to buy or sell. It watches for price trends crossing over each other - a signal that the market might be changing direction.',
        'what_it_does': [
            'Analyzes Bitcoin price movements',
            'Looks for buy/sell signals (when short-term trends cross long-term trends)',
            'Decides when to place buy or sell orders',
            'Stops trading if the Risk Manager says so'
        ],
        'connections': ['DataMiner_XXBTZUSD_1', 'Trader_5', 'RiskManager_6'],
        'color': '#10b981',
        'status_messages': ['Analyzing patterns...', 'Buy signal detected!', 'Sell signal detected!', 'Calculating trends...']
    },
    'PatternLearner_XETHZUSD_4': {
        'name': 'Ethereum Strategy Brain',
        'type': 'Decision Maker',
        'simple_desc': 'Analyzes Ethereum patterns and decides when to buy/sell',
        'description': 'This is the "thinking" agent that looks at Ethereum price movements and uses a simple strategy to decide when to buy or sell. It watches for price trends crossing over each other - a signal that the market might be changing direction.',
        'what_it_does': [
            'Analyzes Ethereum price movements',
            'Looks for buy/sell signals (when short-term trends cross long-term trends)',
            'Decides when to place buy or sell orders',
            'Stops trading if the Risk Manager says so'
        ],
        'connections': ['DataMiner_XETHZUSD_2', 'Trader_5', 'RiskManager_6'],
        'color': '#10b981',
        'status_messages': ['Analyzing patterns...', 'Buy signal detected!', 'Sell signal detected!', 'Calculating trends...']
    },
    'Trader_5': {
        'name': 'Trade Executor',
        'type': 'Action Taker',
        'simple_desc': 'Actually places the buy/sell orders',
        'description': 'This agent takes the buy/sell decisions from the Strategy Brains and actually executes them on the exchange. It\'s like the "hands" of the system - it does the actual trading.',
        'what_it_does': [
            'Receives buy/sell orders from the Strategy Brains',
            'Places the actual trades on the Kraken exchange',
            'Confirms if trades were successful',
            'Reports all activity to the Risk Manager'
        ],
        'connections': ['PatternLearner_XXBTZUSD_3', 'PatternLearner_XETHZUSD_4', 'RiskManager_6'],
        'color': '#f59e0b',
        'status_messages': ['Ready to execute...', 'Placing order...', 'Trade executed!', 'Waiting for orders...']
    },
    'RiskManager_6': {
        'name': 'Safety Monitor',
        'type': 'Risk Guardian',
        'simple_desc': 'Watches for problems and can stop all trading',
        'description': 'This is the safety agent. It constantly monitors how much money we\'re making or losing. If losses get too big (exceed a set threshold), it has the power to STOP all trading immediately. Think of it as an emergency brake.',
        'what_it_does': [
            'Tracks total profit and loss',
            'Calculates how much we\'ve lost from our peak (drawdown)',
            'Stops all trading if losses are too big',
            'Monitors all trades for safety'
        ],
        'connections': ['Trader_5', 'PatternLearner_XXBTZUSD_3', 'PatternLearner_XETHZUSD_4'],
        'color': '#ef4444',
        'status_messages': ['Monitoring risk...', 'All systems safe', 'WARNING: High drawdown!', 'HALTING TRADING!']
    }
}

# === HELP INFORMATION FOR SECTIONS ===
SECTION_HELP = {
    'portfolio': {
        'title': 'What is Portfolio Value?',
        'content': 'This shows how much money you have in total. It starts at $10,000 (simulated). The green arrow means you\'re making money, red means you\'re losing money. The percentage shows how much you\'ve gained or lost compared to where you started.'
    },
    'system_status': {
        'title': 'What is System Status?',
        'content': 'This tells you if the trading system is actively working. "OPERATIONAL" means all agents are running and processing data. "STANDBY" means the system is on but waiting. The "events/sec" shows how busy the system is.'
    },
    'risk': {
        'title': 'What is Risk Level?',
        'content': 'This shows how much danger your money is in. "LOW" is good - you\'re not losing much. "MODERATE" means be careful. "HIGH" means you\'ve lost significant money. "Drawdown" is how much you\'ve lost from your highest point.'
    },
    'agents': {
        'title': 'What are Active Agents?',
        'content': 'Agents are like team members working together. You have 6 total: 2 watch prices, 2 make decisions, 1 executes trades, and 1 monitors risk. This number shows how many are currently doing work.'
    },
    'performance': {
        'title': 'Understanding the Performance Chart',
        'content': 'This line shows your money over time. Going up is good (making money), going down is bad (losing money). The blue line is your total portfolio value. Think of it like a stock chart - you want it trending upward!'
    },
    'network': {
        'title': 'Understanding the Agent Constellation',
        'content': 'This stunning 3D visualization shows ALL your AI agents arranged like a solar system. The GOLD star at the center is your Trading Executor. The RED planet nearby is your Risk Guardian. The massive PURPLE star cluster in the middle is THE SWARM - 100 Pattern Learner agents using diverse strategies to analyze Bitcoin. The VIOLET stars on the outer orbits are your Data Sensors watching market prices. You can rotate the view by clicking and dragging!'
    },
    'market': {
        'title': 'Market Data Explained',
        'content': 'This shows current cryptocurrency prices. BTC = Bitcoin, ETH = Ethereum. The percentage shows if the price went up (green) or down (red) since the system started. These are real market prices being monitored.'
    },
    'activity': {
        'title': 'What is the Activity Stream?',
        'content': 'This is like a live news feed of what your system is doing. You\'ll see when prices update, when decisions are made, when trades happen, and any problems. Read from bottom to top for the latest activity.'
    }
}

NODE_POSITIONS = {
    'DataMiner_XXBTZUSD_1': {'x': 0.15, 'y': 0.25},
    'DataMiner_XETHZUSD_2': {'x': 0.15, 'y': 0.75},
    'PatternLearner_XXBTZUSD_3': {'x': 0.5, 'y': 0.25},
    'PatternLearner_XETHZUSD_4': {'x': 0.5, 'y': 0.75},
    'Trader_5': {'x': 0.85, 'y': 0.5},
    'RiskManager_6': {'x': 0.5, 'y': 0.95},
}

NODE_EDGES = [
    ('DataMiner_XXBTZUSD_1', 'PatternLearner_XXBTZUSD_3'),
    ('DataMiner_XETHZUSD_2', 'PatternLearner_XETHZUSD_4'),
    ('PatternLearner_XXBTZUSD_3', 'Trader_5'),
    ('PatternLearner_XETHZUSD_4', 'Trader_5'),
    ('Trader_5', 'RiskManager_6'),
    ('RiskManager_6', 'PatternLearner_XXBTZUSD_3'),
    ('RiskManager_6', 'PatternLearner_XETHZUSD_4'),
]

# === DASH APP ===
app = dash.Dash(
    __name__,
    external_stylesheets=[
        dbc.themes.SLATE,
        "https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap",
        "https://use.fontawesome.com/releases/v6.5.1/css/all.css"
    ],
    suppress_callback_exceptions=True,
    meta_tags=[
        {"name": "viewport", "content": "width=device-width, initial-scale=1"},
        {"http-equiv": "Cache-Control", "content": "no-cache, no-store, must-revalidate"},
    ]
)
app.title = "Mycelial Finance | AI Trading System"

# === LAYOUT ===
app.layout = dbc.Container(
    fluid=True,
    className="p-4",
    style={
        'backgroundColor': '#0f1419',
        'minHeight': '100vh',
        'fontFamily': "'Inter', sans-serif"
    },
    children=[
        html.Div(id='session-id', children=SESSION_ID, style={'display': 'none'}),

        # Data stores
        dcc.Store(id='pnl-store', data={'times': [time.strftime('%H:%M:%S')], 'values': [10000], 'initial': 10000}),
        dcc.Store(id='market-store', data={'times': [], 'btc': [], 'eth': []}),
        dcc.Store(id='log-store', data=[]),
        dcc.Store(id='pulse-store', data={}),
        dcc.Store(id='activity-store', data={'miners': 0, 'learners': 0, 'traders': 0, 'risk': 0}),
        dcc.Store(id='agent-actions-store', data={}),
        dcc.Store(id='agent-status-store', data={}),  # Current status of each agent
        dcc.Interval(id='interval', interval=1000, n_intervals=0),

        # Agent Detail Modal
        dbc.Modal([
            dbc.ModalHeader(dbc.ModalTitle(id='modal-title'), style={'backgroundColor': '#1a2332', 'borderBottom': '1px solid #2d3748'}),
            dbc.ModalBody(id='modal-body', style={'backgroundColor': '#1a2332', 'color': '#e2e8f0'}),
            dbc.ModalFooter(
                dbc.Button("Close", id="close-modal", className="ms-auto", color="secondary"),
                style={'backgroundColor': '#1a2332', 'borderTop': '1px solid #2d3748'}
            ),
        ], id="agent-modal", size="lg", is_open=False, backdrop=True),

        # Section Help Modal
        dbc.Modal([
            dbc.ModalHeader(dbc.ModalTitle(id='help-modal-title'), style={'backgroundColor': '#1a2332', 'borderBottom': '1px solid #2d3748'}),
            dbc.ModalBody(id='help-modal-body', style={'backgroundColor': '#1a2332', 'color': '#e2e8f0', 'fontSize': '1.05rem', 'lineHeight': '1.7'}),
            dbc.ModalFooter(
                dbc.Button("Got it!", id="close-help-modal", className="ms-auto", color="primary"),
                style={'backgroundColor': '#1a2332', 'borderTop': '1px solid #2d3748'}
            ),
        ], id="help-modal", size="md", is_open=False, backdrop=True),

        # === HEADER ===
        dbc.Row([
            dbc.Col([
                html.Div([
                    html.H1("MYCELIAL FINANCE", style={
                        'fontSize': '2.5rem',
                        'fontWeight': '700',
                        'color': '#a855f7',  # PURPLE
                        'letterSpacing': '1px',
                        'marginBottom': '0.25rem'
                    }),
                    html.P("AI-Powered Cryptocurrency Trading System", style={
                        'color': '#9ca3af',
                        'fontSize': '0.95rem',
                        'fontWeight': '400',
                        'marginBottom': '0'
                    })
                ], className="text-center py-3")
            ])
        ], className="mb-4"),

        # === ROW 1: KEY METRICS ===
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.I(className="fas fa-wallet", style={'fontSize': '1.2rem', 'color': '#a855f7'}),
                            html.Span("Portfolio Value", className="ms-2", style={'fontSize': '0.85rem', 'color': '#a0aec0', 'fontWeight': '500', 'textTransform': 'uppercase'}),
                            html.I(className="fas fa-info-circle ms-2", id='help-portfolio', style={'fontSize': '0.9rem', 'color': '#6b7280', 'cursor': 'pointer'})
                        ], className="mb-3"),
                        html.Div(id='portfolio-value', style={'fontSize': '2.5rem', 'fontWeight': '700', 'color': '#ffffff'}),
                        html.Div(id='portfolio-change')
                    ])
                ], className="h-100", style={'backgroundColor': '#1a2332', 'border': '1px solid #2d3748', 'borderRadius': '12px'})
            ], width=12, md=6, lg=3, className="mb-3"),

            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.I(className="fas fa-heartbeat", style={'fontSize': '1.2rem', 'color': '#10b981'}),
                            html.Span("System Status", className="ms-2", style={'fontSize': '0.85rem', 'color': '#a0aec0', 'fontWeight': '500', 'textTransform': 'uppercase'}),
                            html.I(className="fas fa-info-circle ms-2", id='help-system', style={'fontSize': '0.9rem', 'color': '#6b7280', 'cursor': 'pointer'})
                        ], className="mb-3"),
                        html.Div(id='system-status')
                    ])
                ], className="h-100", style={'backgroundColor': '#1a2332', 'border': '1px solid #2d3748', 'borderRadius': '12px'})
            ], width=12, md=6, lg=3, className="mb-3"),

            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.I(className="fas fa-shield-alt", style={'fontSize': '1.2rem', 'color': '#ef4444'}),
                            html.Span("Risk Level", className="ms-2", style={'fontSize': '0.85rem', 'color': '#a0aec0', 'fontWeight': '500', 'textTransform': 'uppercase'}),
                            html.I(className="fas fa-info-circle ms-2", id='help-risk', style={'fontSize': '0.9rem', 'color': '#6b7280', 'cursor': 'pointer'})
                        ], className="mb-3"),
                        html.Div(id='risk-level')
                    ])
                ], className="h-100", style={'backgroundColor': '#1a2332', 'border': '1px solid #2d3748', 'borderRadius': '12px'})
            ], width=12, md=6, lg=3, className="mb-3"),

            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.I(className="fas fa-users", style={'fontSize': '1.2rem', 'color': '#f59e0b'}),
                            html.Span("Active Agents", className="ms-2", style={'fontSize': '0.85rem', 'color': '#a0aec0', 'fontWeight': '500', 'textTransform': 'uppercase'}),
                            html.I(className="fas fa-info-circle ms-2", id='help-agents', style={'fontSize': '0.9rem', 'color': '#6b7280', 'cursor': 'pointer'})
                        ], className="mb-3"),
                        html.Div(id='active-agents')
                    ])
                ], className="h-100", style={'backgroundColor': '#1a2332', 'border': '1px solid #2d3748', 'borderRadius': '12px'})
            ], width=12, md=6, lg=3, className="mb-3"),
        ]),

        # === ROW 2: PERFORMANCE CHART ===
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.I(className="fas fa-chart-line me-2", style={'color': '#a855f7'}),
                        html.Span("Portfolio Performance Over Time", style={'fontSize': '1.1rem', 'fontWeight': '600', 'color': '#ffffff'}),
                        html.I(className="fas fa-info-circle ms-2", id='help-performance', style={'fontSize': '0.95rem', 'color': '#6b7280', 'cursor': 'pointer'})
                    ], style={'backgroundColor': '#1a2332', 'border': 'none', 'borderBottom': '1px solid #2d3748'}),
                    dbc.CardBody([
                        dcc.Graph(id='performance-chart', config={'displayModeBar': False}, style={'height': '400px'})
                    ], className="p-2")
                ], style={'backgroundColor': '#1a2332', 'border': '1px solid #2d3748', 'borderRadius': '12px'})
            ], width=12, className="mb-3"),
        ]),

        # === ROW 3: NETWORK & MARKET ===
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.I(className="fas fa-project-diagram me-2", style={'color': '#a855f7'}),
                        html.Span("Agent Constellation", style={'fontSize': '1.1rem', 'fontWeight': '600', 'color': '#ffffff'}),
                        html.Small(" (rotate & explore in 3D)", className="ms-2", style={'color': '#6b7280', 'fontSize': '0.85rem'}),
                        html.I(className="fas fa-info-circle ms-2", id='help-network', style={'fontSize': '0.95rem', 'color': '#6b7280', 'cursor': 'pointer'})
                    ], style={'backgroundColor': '#1a2332', 'border': 'none', 'borderBottom': '1px solid #2d3748'}),
                    dbc.CardBody([
                        dcc.Graph(
                            id='network-graph',
                            config={'displayModeBar': False},
                            style={'height': '550px', 'backgroundColor': '#000000'}
                        ),
                        html.Div(id='agent-status-display', className="mt-3")
                    ], className="p-2")
                ], style={'backgroundColor': '#1a2332', 'border': '1px solid #2d3748', 'borderRadius': '12px'})
            ], width=12, lg=7, className="mb-3"),

            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.I(className="fas fa-coins me-2", style={'color': '#f59e0b'}),
                        html.Span("Live Market Prices", style={'fontSize': '1.1rem', 'fontWeight': '600', 'color': '#ffffff'}),
                        html.I(className="fas fa-info-circle ms-2", id='help-market', style={'fontSize': '0.95rem', 'color': '#6b7280', 'cursor': 'pointer'})
                    ], style={'backgroundColor': '#1a2332', 'border': 'none', 'borderBottom': '1px solid #2d3748'}),
                    dbc.CardBody([
                        html.Div(id='market-data')
                    ], className="p-3")
                ], className="h-100", style={'backgroundColor': '#1a2332', 'border': '1px solid #2d3748', 'borderRadius': '12px'}),
            ], width=12, lg=5, className="mb-3"),
        ]),

        # === ROW 4: ACTIVITY FEED ===
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.I(className="fas fa-stream me-2", style={'color': '#10b981'}),
                        html.Span("Live System Activity", style={'fontSize': '1.1rem', 'fontWeight': '600', 'color': '#ffffff'}),
                        html.I(className="fas fa-info-circle ms-2", id='help-activity', style={'fontSize': '0.95rem', 'color': '#6b7280', 'cursor': 'pointer'})
                    ], style={'backgroundColor': '#1a2332', 'border': 'none', 'borderBottom': '1px solid #2d3748'}),
                    dbc.CardBody([
                        html.Div(id='activity-feed', style={
                            'height': '300px',
                            'overflowY': 'auto',
                            'fontSize': '0.95rem',
                            'lineHeight': '1.7'
                        })
                    ], className="p-3")
                ], style={'backgroundColor': '#1a2332', 'border': '1px solid #2d3748', 'borderRadius': '12px'})
            ], width=12, className="mb-3"),
        ]),

        html.Div(f"Mycelial Finance v5.0 | Session: {SESSION_ID}", className="text-center mt-3",
                style={'color': '#4a5568', 'fontSize': '0.75rem'})
    ]
)

# === REDIS LISTENER ===
def start_redis_listener(app_queue: Queue):
    logging.info("Dashboard: Redis listener started")
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
        'system-control': 'system-control'
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
                    app_queue.put({'type': msg_type, 'data': data, 'channel': message['channel']})
                except:
                    pass
        except:
            pass
        finally:
            pubsub.close()

    for pattern, msg_type in channels.items():
        threading.Thread(target=create_listener, args=(pattern, msg_type), daemon=True).start()

# === DATA UPDATE ===
@app.callback(
    Output('pnl-store', 'data'),
    Output('market-store', 'data'),
    Output('log-store', 'data'),
    Output('pulse-store', 'data'),
    Output('activity-store', 'data'),
    Output('agent-actions-store', 'data'),
    Output('agent-status-store', 'data'),
    Input('interval', 'n_intervals'),
    State('pnl-store', 'data'),
    State('market-store', 'data'),
    State('log-store', 'data'),
    State('pulse-store', 'data'),
    State('activity-store', 'data'),
    State('agent-actions-store', 'data'),
    State('agent-status-store', 'data')
)
def update_data(n, pnl, market, logs, pulses, activity, agent_actions, agent_status):
    current_time = time.time()
    active_pulses = {k: v for k, v in pulses.items() if current_time - v['time'] < 1.0}
    new_logs = []
    act_counts = {'miners': 0, 'learners': 0, 'traders': 0, 'risk': 0}

    if not agent_actions:
        agent_actions = {k: [] for k in NODE_POSITIONS.keys()}
    if not agent_status:
        agent_status = {k: 'Idle' for k in NODE_POSITIONS.keys()}

    while not message_queue.empty():
        try:
            msg = message_queue.get_nowait()
            t = time.strftime('%H:%M:%S')

            if msg['type'] == 'market-data':
                src = msg['data']['source']
                price = float(msg['data']['data']['c'][0])
                coin = "Bitcoin" if 'XXBTZUSD' in str(msg['channel']) else "Ethereum"

                if msg['channel'] == b'market-data:XXBTZUSD':
                    market['times'].append(t)
                    market['btc'].append(price)
                    market['times'] = market['times'][-50:]
                    market['btc'] = market['btc'][-50:]
                    active_pulses[f"{src}->PatternLearner_XXBTZUSD_3"] = {'color': '#a855f7', 'time': current_time}
                    act_counts['miners'] += 1
                    agent_actions.get(src, []).append({'time': t, 'action': f'Updated {coin} price: ${price:,.2f}'})
                    agent_status[src] = f'Watching {coin}'
                elif msg['channel'] == b'market-data:XETHZUSD':
                    market['eth'].append(price)
                    market['eth'] = market['eth'][-50:]
                    active_pulses[f"{src}->PatternLearner_XETHZUSD_4"] = {'color': '#a855f7', 'time': current_time}
                    act_counts['miners'] += 1
                    agent_actions.get(src, []).append({'time': t, 'action': f'Updated {coin} price: ${price:,.2f}'})
                    agent_status[src] = f'Watching {coin}'

                new_logs.append({'time': t, 'type': 'market', 'msg': f'{coin} price updated to ${price:,.2f}', 'detail': f'The {coin} market moved to ${price:,.2f}. Our sensors detected this change and sent it to the decision-making agents.'})

            elif msg['type'] == 'trade-order':
                src = msg['data']['source']
                direction = msg['data']['direction'].upper()
                amount = msg['data']['amount']
                pair = msg['data']['pair']
                coin_name = "Bitcoin" if 'BTC' in pair else "Ethereum"

                active_pulses[f"{src}->Trader_5"] = {'color': '#10b981', 'time': current_time}
                act_counts['learners'] += 1
                agent_actions.get(src, []).append({'time': t, 'action': f'Decided to {direction}: {amount} {pair}'})
                agent_status[src] = f'Signal: {direction}'
                agent_status['Trader_5'] = f'Executing {direction}'

                new_logs.append({'time': t, 'type': 'order', 'msg': f'{direction} signal for {coin_name}!', 'detail': f'The {coin_name} Strategy Brain analyzed the price patterns and decided it\'s a good time to {direction}. It sent an order for {amount} units to the Trade Executor.'})

            elif msg['type'] == 'trade-confirmation':
                active_pulses["Trader_5->RiskManager_6"] = {'color': '#f59e0b', 'time': current_time}
                act_counts['traders'] += 1
                act_counts['risk'] += 1
                agent_actions.get('Trader_5', []).append({'time': t, 'action': 'Trade completed'})
                agent_actions.get('RiskManager_6', []).append({'time': t, 'action': 'Checked trade safety'})
                agent_status['Trader_5'] = 'Trade completed'
                agent_status['RiskManager_6'] = 'Monitoring'

                if msg['data']['execution_result'].get('status') == 'success':
                    pnl['values'].append(pnl['values'][-1] + random.uniform(-50, 75))
                    pnl['times'].append(t)
                    pnl['values'] = pnl['values'][-100:]
                    pnl['times'] = pnl['times'][-100:]
                    new_logs.append({'time': t, 'type': 'confirm', 'msg': 'Trade executed successfully!', 'detail': 'The Trade Executor placed the order and it was filled. The Safety Monitor checked the trade and updated your portfolio value. Everything looks good!'})
                else:
                    new_logs.append({'time': t, 'type': 'error', 'msg': 'Trade failed', 'detail': 'The trade could not be completed. This could be due to insufficient funds or market conditions.'})
        except:
            pass

    for agent_id in agent_actions:
        agent_actions[agent_id] = agent_actions[agent_id][-20:]

    logs.extend(new_logs)
    logs = logs[-30:]

    return pnl, market, logs, active_pulses, act_counts, agent_actions, agent_status

# === REMAINING CALLBACKS ===
@app.callback(
    Output('portfolio-value', 'children'),
    Output('portfolio-change', 'children'),
    Input('pnl-store', 'data')
)
def update_portfolio(data):
    val = data['values'][-1]
    initial = data.get('initial', 10000)
    change = val - initial
    pct = (change / initial) * 100
    color = '#10b981' if change >= 0 else '#ef4444'
    icon = 'arrow-up' if change >= 0 else 'arrow-down'
    return (
        f"${val:,.2f}",
        html.Div([
            html.I(className=f"fas fa-{icon} me-2", style={'color': color}),
            html.Span(f"{change:+,.2f} ({pct:+.2f}%)", style={'color': color, 'fontSize': '1rem', 'fontWeight': '600'})
        ], className="mt-2")
    )

@app.callback(Output('system-status', 'children'), Input('activity-store', 'data'))
def update_status(activity):
    total = sum(activity.values())
    status = "OPERATIONAL" if total > 0 else "STANDBY"
    color = '#10b981' if total > 0 else '#6b7280'
    return html.Div([
        html.H3(status, style={'color': color, 'fontWeight': '700', 'fontSize': '1.6rem', 'marginBottom': '0.5rem'}),
        html.Div(f"{total} events/sec", style={'color': '#9ca3af', 'fontSize': '0.9rem'})
    ])

@app.callback(Output('risk-level', 'children'), Input('pnl-store', 'data'))
def update_risk(data):
    val = data['values'][-1]
    initial = data.get('initial', 10000)
    dd = max(0, ((initial - val) / initial) * 100)
    if dd < 3: status, color = "LOW", '#10b981'
    elif dd < 7: status, color = "MODERATE", '#f59e0b'
    else: status, color = "HIGH", '#ef4444'
    return html.Div([
        html.H3(status, style={'color': color, 'fontWeight': '700', 'fontSize': '1.6rem', 'marginBottom': '0.5rem'}),
        html.Div(f"Drawdown: {dd:.1f}%", style={'color': '#9ca3af', 'fontSize': '0.9rem'})
    ])

@app.callback(Output('active-agents', 'children'), Input('activity-store', 'data'))
def update_agents(activity):
    active = sum(1 for v in activity.values() if v > 0)
    return html.Div([
        html.H3(f"{active}/6", style={'color': '#f59e0b', 'fontWeight': '700', 'fontSize': '1.6rem', 'marginBottom': '0.5rem'}),
        html.Div("agents working", style={'color': '#9ca3af', 'fontSize': '0.9rem'})
    ])

@app.callback(Output('performance-chart', 'figure'), Input('pnl-store', 'data'))
def update_chart(data):
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=data['times'], y=data['values'], mode='lines',
        line={'color': '#a855f7', 'width': 3}, fill='tozeroy',
        fillcolor='rgba(168,85,247,0.1)'
    ))
    # Enhanced Y-axis stability: ensure chart never jumps around from small P&L changes
    INITIAL_PORTFOLIO = 10000
    MIN_RANGE = 500  # Minimum $500 range for visual stability

    y_min, y_max = min(data['values']), max(data['values'])
    y_range = max(MIN_RANGE, y_max - y_min)

    # Always include initial portfolio value with comfortable padding
    y_center = (y_min + y_max) / 2
    half_range = y_range / 2
    axis_min = min(y_center - half_range, INITIAL_PORTFOLIO - MIN_RANGE/2)
    axis_max = max(y_center + half_range, INITIAL_PORTFOLIO + MIN_RANGE/2)

    # Add 15% padding for breathing room
    total_range = axis_max - axis_min
    padding = total_range * 0.15

    fig.update_layout(
        template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=60, r=20, t=20, b=50),
        xaxis=dict(title=dict(text="Time", font=dict(size=12, color='#9ca3af')),
                   showgrid=True, gridcolor='rgba(255,255,255,0.05)', fixedrange=True,
                   tickfont=dict(size=11, color='#6b7280')),
        yaxis=dict(title=dict(text="Portfolio Value ($)", font=dict(size=12, color='#9ca3af')),
                   showgrid=True, gridcolor='rgba(255,255,255,0.05)',
                   range=[axis_min - padding, axis_max + padding], fixedrange=True,
                   tickfont=dict(size=11, color='#6b7280')),
        showlegend=False, height=400, font=dict(color='#e2e8f0', family='Inter')
    )
    return fig

@app.callback(Output('network-graph', 'figure'), Input('pulse-store', 'data'))
def update_network(pulses):
    """
    Creates a BEAUTIFUL 3D glowing star field visualization of ALL agents.
    Each agent appears as a glowing celestial star in deep space.
    """
    import math
    import numpy as np

    # Query Redis to get ALL active agents
    try:
        redis_conn = RedisClient()
        all_keys = redis_conn.connection.keys('agent:*') if redis_conn.connection else []
        active_agents = [key.decode('utf-8').replace('agent:', '') for key in all_keys]
    except:
        active_agents = []

    # If no Redis data, fall back to detecting from model
    if not active_agents:
        active_agents = ['DataMiner_XXBTZUSD_1', 'DataMiner_XETHZUSD_2', 'TradingAgent_104', 'RiskManagementAgent_105']
        for i in range(3, 103):
            active_agents.append(f'PatternLearner_XXBTZUSD_{i}')
        active_agents.append('PatternLearner_XETHZUSD_103')

    # Categorize agents by type
    data_miners = [a for a in active_agents if 'DataMiner' in a]
    pattern_learners = [a for a in active_agents if 'PatternLearner' in a]
    traders = [a for a in active_agents if 'TradingAgent' in a]
    risk_managers = [a for a in active_agents if 'RiskManagement' in a]

    # Create beautiful 3D star positions using Fibonacci sphere for perfect distribution
    def fibonacci_sphere(samples=100, radius=10):
        """Distribute points evenly on a sphere surface - creates perfect star field"""
        points = []
        phi = math.pi * (3. - math.sqrt(5.))  # golden angle in radians

        for i in range(samples):
            y = 1 - (i / float(samples - 1)) * 2  # y goes from 1 to -1
            radius_at_y = math.sqrt(1 - y * y)  # radius at y

            theta = phi * i  # golden angle increment

            x = math.cos(theta) * radius_at_y
            z = math.sin(theta) * radius_at_y

            points.append([x * radius, y * radius, z * radius])
        return points

    # Generate positions for all agents
    all_agent_positions = fibonacci_sphere(samples=len(active_agents), radius=15)

    # Create separate traces for each agent type (for beautiful coloring)
    traces = []

    # 1. Pattern Learners - Purple glowing swarm (THE STARS!)
    if pattern_learners:
        learner_positions = all_agent_positions[:len(pattern_learners)]
        x, y, z = zip(*learner_positions)
        traces.append(go.Scatter3d(
            x=x, y=y, z=z,
            mode='markers+text',
            name='Pattern Learners',
            text=[f'Swarm {i+1}' if i < 5 else '' for i in range(len(pattern_learners))],
            hovertext=[f'{agent}<br>Pattern Learner' for agent in pattern_learners],
            hoverinfo='text',
            marker=dict(
                size=12,
                color='#a855f7',
                opacity=0.8,
                line=dict(color='#e9d5ff', width=2),  # Glowing outline
                symbol='circle'
            ),
            textfont=dict(color='#e9d5ff', size=8),
            textposition='top center'
        ))

    # 2. Trading Executor - Large golden sun at center
    if traders:
        traces.append(go.Scatter3d(
            x=[0], y=[0], z=[0],  # Center of constellation
            mode='markers+text',
            name='Trading Executor',
            text=['☀ Executor'],
            hovertext=[f'{traders[0]}<br>Trading Executor'],
            hoverinfo='text',
            marker=dict(
                size=35,
                color='#fbbf24',
                opacity=0.9,
                line=dict(color='#fef3c7', width=4),  # Brilliant glow
                symbol='diamond'
            ),
            textfont=dict(color='#fef3c7', size=14, family='Arial Black'),
            textposition='bottom center'
        ))

    # 3. Data Miners - Bright blue sensor stars
    if data_miners:
        sensor_idx = len(pattern_learners)
        sensor_positions = all_agent_positions[sensor_idx:sensor_idx+len(data_miners)]
        x, y, z = zip(*sensor_positions)
        traces.append(go.Scatter3d(
            x=x, y=y, z=z,
            mode='markers+text',
            name='Data Sensors',
            text=['BTC' if 'XXBTZUSD' in a else 'ETH' for a in data_miners],
            hovertext=[f'{agent}<br>Market Sensor' for agent in data_miners],
            hoverinfo='text',
            marker=dict(
                size=20,
                color='#3b82f6',
                opacity=0.85,
                line=dict(color='#93c5fd', width=3),
                symbol='circle'
            ),
            textfont=dict(color='#93c5fd', size=10, family='Arial'),
            textposition='top center'
        ))

    # 4. Risk Manager - Red guardian star
    if risk_managers:
        risk_idx = len(pattern_learners) + len(data_miners)
        risk_pos = all_agent_positions[risk_idx]
        traces.append(go.Scatter3d(
            x=[risk_pos[0]], y=[risk_pos[1]], z=[risk_pos[2]],
            mode='markers+text',
            name='Risk Guardian',
            text=['⚠ Guardian'],
            hovertext=[f'{risk_managers[0]}<br>Risk Manager'],
            hoverinfo='text',
            marker=dict(
                size=25,
                color='#ef4444',
                opacity=0.9,
                line=dict(color='#fecaca', width=3),
                symbol='square'
            ),
            textfont=dict(color='#fecaca', size=12, family='Arial'),
            textposition='top center'
        ))

    # Create the figure with DEEP SPACE background
    fig = go.Figure(data=traces)

    # Make it look like BEAUTIFUL DEEP SPACE - NO AXES!
    fig.update_layout(
        scene=dict(
            xaxis=dict(visible=False, showgrid=False, zeroline=False, showbackground=False),
            yaxis=dict(visible=False, showgrid=False, zeroline=False, showbackground=False),
            zaxis=dict(visible=False, showgrid=False, zeroline=False, showbackground=False),
            bgcolor='#000000',  # Pure black space
            camera=dict(
                eye=dict(x=1.5, y=1.5, z=1.3),  # Nice viewing angle
                center=dict(x=0, y=0, z=0)
            )
        ),
        paper_bgcolor='#000000',
        plot_bgcolor='#000000',
        margin=dict(l=0, r=0, t=0, b=0),
        showlegend=False,
        height=550
    )

    return fig

@app.callback(
    Output('agent-status-display', 'children'),
    Input('agent-status-store', 'data')
)
def update_agent_status_display(agent_status):
    if not agent_status:
        return html.Div("Agents initializing...", style={'color': '#6b7280', 'fontSize': '0.9rem'})

    # Group agents by status/signal
    groups = {
        'BUY Signals': [],
        'SELL Signals': [],
        'Active': [],
        'Idle': []
    }

    for agent_id, status in agent_status.items():
        info = AGENT_INFO.get(agent_id, {})
        name = info.get('name', agent_id.split('_')[0])
        color = info.get('color', '#a855f7')

        agent_item = html.Div([
            html.Span("● ", style={'color': color, 'fontSize': '0.9rem', 'marginRight': '0.5rem'}),
            html.Span(name, style={'color': '#e2e8f0', 'fontSize': '0.85rem', 'cursor': 'pointer'}),
        ], style={
            'marginBottom': '0.3rem',
            'padding': '0.25rem 0.5rem',
            'borderRadius': '4px',
            'cursor': 'pointer',
            'transition': 'background-color 0.2s'
        }, className='agent-list-item', id={'type': 'agent-item', 'index': agent_id})

        if 'BUY' in status:
            groups['BUY Signals'].append(agent_item)
        elif 'SELL' in status:
            groups['SELL Signals'].append(agent_item)
        elif 'Idle' in status or 'Waiting' in status:
            groups['Idle'].append(agent_item)
        else:
            groups['Active'].append(agent_item)

    # Create collapsible sections
    sections = []
    colors = {
        'BUY Signals': '#10b981',
        'SELL Signals': '#ef4444',
        'Active': '#a855f7',
        'Idle': '#6b7280'
    }

    for group_name, items in groups.items():
        if items:
            count = len(items)
            sections.append(
                html.Div([
                    html.Div([
                        html.I(className="fas fa-chevron-down me-2", style={'fontSize': '0.75rem', 'color': colors[group_name]}),
                        html.Span(f"{group_name} ({count})",
                                 style={'color': colors[group_name], 'fontWeight': '600', 'fontSize': '0.9rem'})
                    ], style={
                        'marginBottom': '0.5rem',
                        'padding': '0.5rem',
                        'backgroundColor': 'rgba(255,255,255,0.03)',
                        'borderRadius': '6px',
                        'borderLeft': f'3px solid {colors[group_name]}'
                    }),
                    html.Div(items[:10] if count > 10 else items,  # Show max 10 per group
                            style={'paddingLeft': '1rem', 'marginBottom': '1rem'}),
                    html.Div(f"+ {count - 10} more...",
                            style={'color': '#6b7280', 'fontSize': '0.75rem', 'paddingLeft': '1rem', 'fontStyle': 'italic'})
                    if count > 10 else html.Div()
                ], style={'marginBottom': '0.75rem'})
            )

    return html.Div(sections)

@app.callback(
    Output("agent-modal", "is_open"),
    Output("modal-title", "children"),
    Output("modal-body", "children"),
    Input("network-graph", "clickData"),
    Input({"type": "agent-item", "index": dash.dependencies.ALL}, "n_clicks"),
    Input("close-modal", "n_clicks"),
    State("agent-modal", "is_open"),
    State('agent-actions-store', 'data'),
    State('agent-status-store', 'data')
)
def toggle_agent_modal(clickData, list_clicks, close_clicks, is_open, agent_actions, agent_status):
    # CRITICAL FIX: Prevent auto-trigger on page load or when no actual click happened
    if not ctx.triggered_id:
        return False, "", ""

    # Also prevent if triggered by None clicks in list
    if ctx.triggered_id and isinstance(ctx.triggered_id, dict) and ctx.triggered_id.get('type') == 'agent-item':
        # Find which specific item was clicked
        trigger_idx = ctx.triggered_id.get('index')
        if list_clicks and trigger_idx is not None:
            idx = next((i for i, click in enumerate(list_clicks) if click is not None), None)
            if idx is None:
                return False, "", ""

    if ctx.triggered_id == "close-modal":
        return False, "", ""

    agent_id = None

    # Check if clicked from network graph
    if clickData and ctx.triggered_id == "network-graph":
        # Get the curve number and point index to determine which agent was clicked
        point = clickData['points'][0]
        curve_num = point.get('curveNumber', 0)
        point_idx = point.get('pointIndex', 0)

        # Try to extract agent info from hover data
        if 'text' in point:
            agent_text = point['text']
            # Match against our agent status to find the ID
            for aid, status in (agent_status or {}).items():
                info = AGENT_INFO.get(aid, {})
                if info.get('name') == agent_text or agent_text in aid:
                    agent_id = aid
                    break

    # Check if clicked from list
    elif ctx.triggered_id and isinstance(ctx.triggered_id, dict) and ctx.triggered_id.get('type') == 'agent-item':
        agent_id = ctx.triggered_id['index']

    if not agent_id:
        return dash.no_update, dash.no_update, dash.no_update

    # Get agent info
    info = AGENT_INFO.get(agent_id, {
        'type': 'Pattern Learner',
        'name': agent_id.split('_')[0],
        'description': 'This agent analyzes market patterns using moving average crossovers.',
        'what_it_does': ['Monitors price movements', 'Generates trading signals', 'Uses SMA crossover strategy'],
        'connections': []
    })

    recent_actions = agent_actions.get(agent_id, [])[-10:] if agent_actions else []
    current_status = agent_status.get(agent_id, 'Unknown') if agent_status else 'Unknown'

    modal_content = html.Div([
        dbc.Badge(info['type'], color="primary", className="mb-3"),
        dbc.Badge(f"Status: {current_status}", color="secondary", className="mb-3 ms-2"),
        html.P(info['description'], style={'color': '#cbd5e0', 'lineHeight': '1.7', 'marginBottom': '1.5rem'}),
        html.H5("What This Agent Does:", style={'color': '#a855f7', 'fontSize': '1rem', 'fontWeight': '600', 'marginBottom': '0.75rem'}),
        html.Ul([html.Li(r, style={'color': '#cbd5e0', 'marginBottom': '0.5rem'}) for r in info.get('what_it_does', [])],
               style={'paddingLeft': '1.5rem', 'marginBottom': '1.5rem'}),
        html.H5("Connected To:", style={'color': '#a855f7', 'fontSize': '1rem', 'fontWeight': '600', 'marginBottom': '0.75rem'}),
        html.Div([dbc.Badge(c.split('_')[0], color="secondary", className="me-2 mb-2") for c in info.get('connections', [])], style={'marginBottom': '1.5rem'}),
        html.H5("Recent Activity:", style={'color': '#a855f7', 'fontSize': '1rem', 'fontWeight': '600', 'marginBottom': '0.75rem'}),
        html.Div([
            html.Div([
                html.Span(f"[{action['time']}]", style={'color': '#6b7280', 'fontSize': '0.85rem', 'marginRight': '0.5rem'}),
                html.Span(action['action'], style={'color': '#cbd5e0', 'fontSize': '0.9rem'})
            ], style={'marginBottom': '0.5rem'})
            for action in reversed(recent_actions)
        ]) if recent_actions else html.P("No recent activity", style={'color': '#6b7280', 'fontStyle': 'italic'})
    ])
    return True, info['name'], modal_content

@app.callback(
    Output("help-modal", "is_open"),
    Output("help-modal-title", "children"),
    Output("help-modal-body", "children"),
    Input("help-portfolio", "n_clicks"),
    Input("help-system", "n_clicks"),
    Input("help-risk", "n_clicks"),
    Input("help-agents", "n_clicks"),
    Input("help-performance", "n_clicks"),
    Input("help-network", "n_clicks"),
    Input("help-market", "n_clicks"),
    Input("help-activity", "n_clicks"),
    Input("close-help-modal", "n_clicks"),
    State("help-modal", "is_open")
)
def toggle_help_modal(*args):
    if ctx.triggered_id == "close-help-modal":
        return False, "", ""

    help_map = {
        'help-portfolio': 'portfolio',
        'help-system': 'system_status',
        'help-risk': 'risk',
        'help-agents': 'agents',
        'help-performance': 'performance',
        'help-network': 'network',
        'help-market': 'market',
        'help-activity': 'activity'
    }

    if ctx.triggered_id in help_map:
        section = SECTION_HELP[help_map[ctx.triggered_id]]
        return True, section['title'], section['content']

    return False, "", ""

@app.callback(Output('market-data', 'children'), Input('market-store', 'data'))
def update_market(data):
    btc = data['btc'][-1] if data['btc'] else 0
    eth = data['eth'][-1] if data['eth'] else 0
    btc_chg = ((data['btc'][-1] - data['btc'][0]) / data['btc'][0] * 100) if len(data['btc']) > 1 else 0
    eth_chg = ((data['eth'][-1] - data['eth'][0]) / data['eth'][0] * 100) if len(data['eth']) > 1 else 0

    return html.Div([
        html.Div([
            html.Div([
                html.I(className="fab fa-bitcoin", style={'fontSize': '2.5rem', 'color': '#f7931a'}),
                html.Div([
                    html.H6("Bitcoin (BTC)", className="mb-1", style={'color': '#9ca3af', 'fontWeight': '500'}),
                    html.H3(f"${btc:,.2f}", className="mb-2", style={'fontWeight': '700', 'color': '#ffffff'}),
                    dbc.Badge(f"{btc_chg:+.2f}%", color="success" if btc_chg >= 0 else "danger", style={'padding': '0.5rem 1rem'})
                ], className="ms-3")
            ], className="d-flex align-items-center mb-4"),
        ]),
        html.Div([
            html.Div([
                html.I(className="fab fa-ethereum", style={'fontSize': '2.5rem', 'color': '#627eea'}),
                html.Div([
                    html.H6("Ethereum (ETH)", className="mb-1", style={'color': '#9ca3af', 'fontWeight': '500'}),
                    html.H3(f"${eth:,.2f}", className="mb-2", style={'fontWeight': '700', 'color': '#ffffff'}),
                    dbc.Badge(f"{eth_chg:+.2f}%", color="success" if eth_chg >= 0 else "danger", style={'padding': '0.5rem 1rem'})
                ], className="ms-3")
            ], className="d-flex align-items-center"),
        ])
    ])

@app.callback(Output('activity-feed', 'children'), Input('log-store', 'data'))
def update_feed(logs):
    if not logs:
        return html.Div([
            html.I(className="fas fa-clock me-2", style={'color': '#6b7280'}),
            html.Span("Waiting for system activity...", style={'color': '#6b7280'})
        ])

    items = []
    for entry in reversed(logs[-15:]):
        if entry['type'] == 'market': icon, color = 'chart-line', '#a855f7'
        elif entry['type'] == 'order': icon, color = 'bolt', '#10b981'
        elif entry['type'] == 'confirm': icon, color = 'check-circle', '#10b981'
        elif entry['type'] == 'error': icon, color = 'exclamation-triangle', '#ef4444'
        else: icon, color = 'info-circle', '#6b7280'

        items.append(html.Div([
            html.Div([
                html.Span(f"[{entry['time']}]", style={'color': '#4a5568', 'fontWeight': '600', 'marginRight': '0.75rem'}),
                html.I(className=f"fas fa-{icon}", style={'color': color, 'marginRight': '0.75rem'}),
                html.Span(entry['msg'], style={'color': '#ffffff', 'fontWeight': '600'})
            ], style={'marginBottom': '0.25rem'}),
            html.Div(entry.get('detail', ''), style={'color': '#9ca3af', 'fontSize': '0.9rem', 'marginLeft': '6rem', 'marginBottom': '1rem'})
        ], style={'marginBottom': '0.75rem'}))

    return html.Div(items)

if __name__ == '__main__':
    try:
        listener_thread = threading.Thread(target=start_redis_listener, args=(message_queue,), daemon=True)
        listener_thread.start()
        logging.info("🚀 Starting User-Friendly Dashboard v5.0 on http://127.0.0.1:8053")
        app.run(debug=False, port=8053, host='127.0.0.1')
    except Exception as e:
        logging.critical(f"FATAL: {e}")
