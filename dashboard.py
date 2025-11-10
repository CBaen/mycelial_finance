# dashboard.py
# BIG ROCK 3: THE "BEAUTIFUL" DASHBOARD OVERHAUL
# This version uses dash-bootstrap-components for a professional UI
# and fixes all visual bugs.
import dash
from dash import dcc, html, Input, Output, State
import plotly.graph_objects as go
import logging
import time
import json
import threading
from queue import Queue
import random
import dash_bootstrap_components as dbc
import redis

# --- Import our project's RedisClient ---
from src.connectors.redis_client import RedisClient

# --- Set up basic logging ---
# Quiets down the default "GET /_dash-update-component" messages
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

# --- Thread-Safe Mailbox (Queue) ---
message_queue = Queue()

# --- Initialize the Dash App with Bootstrap Theme ---
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.DARKLY])
app.title = "Mycelial Finance Dashboard"

# --- Define Agent Graph Layout ---
NODE_POSITIONS = {
    'DataMiner_XXBTZUSD_1': {'x': 0.1, 'y': 0.3},
    'DataMiner_XETHZUSD_2': {'x': 0.1, 'y': 0.7},
    'PatternLearner_XXBTZUSD_3': {'x': 0.4, 'y': 0.3},
    'PatternLearner_XETHZUSD_4': {'x': 0.4, 'y': 0.7},
    'Trader_5': {'x': 0.7, 'y': 0.5},
    'RiskManager_6': {'x': 0.4, 'y': 0.95},
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

# --- App Layout (The HTML Structure) ---
app.layout = dbc.Container(fluid=True, style={'fontFamily': 'monospace', 'padding': '20px'}, children=[

    # --- Hidden Components ---
    dcc.Store(id='pnl-data-store', data={'times': [time.strftime('%H:%M:%S')], 'values': [10000]}),
    dcc.Store(id='market-data-store', data={'times': [], 'prices': []}),
    dcc.Store(id='log-data-store', data=[]),
    dcc.Store(id='graph-pulse-store', data={}),
    dcc.Interval(id='interval-component', interval=1 * 1000, n_intervals=0),
    # --- Header ---
    dbc.Row(dbc.Col(html.H1("Mycelial Finance Dashboard (v2.0 - Swarm)", className="text-center text-success mb-4"))),
    # --- Top Row: Status & P&L ---
    dbc.Row([
        # Status Panel
        dbc.Col(dbc.Card([
            dbc.CardHeader(html.H4("System Status", className="text-center")),
            dbc.CardBody(id='status-panel', children=[
                dbc.Spinner(color="success") # Show a spinner on initial load
            ])
        ]), width=12, lg=3, className="mb-4"),
        # P&L Chart
        dbc.Col(dbc.Card([
            dbc.CardHeader(html.H4("Simulated P&L", className="text-center")),
            dbc.CardBody(dcc.Graph(id='pnl-chart', figure=go.Figure(layout=go.Layout(template='plotly_dark'))))
        ]), width=12, lg=9, className="mb-4"),
    ], align="stretch"),
    # --- Middle Row: Brain Scan & Market ---
    dbc.Row([
        # Mycelial "Brain Scan"
        dbc.Col(dbc.Card([
            dbc.CardHeader(html.H4("Mycelial \"Brain Scan\"", className="text-center")),
            dbc.CardBody(dcc.Graph(id='mycelial-graph'))
        ]), width=12, lg=7, className="mb-4"),
        # Market Data
        dbc.Col(dbc.Card([
            dbc.CardHeader(html.H4("Live Market Data (XXBTZUSD)", className="text-center")),
            dbc.CardBody(dcc.Graph(id='market-chart', figure=go.Figure(layout=go.Layout(template='plotly_dark'))))
        ]), width=12, lg=5, className="mb-4"),
    ], align="stretch"),
    # --- Bottom Row: Live Log ---
    dbc.Row(dbc.Col(dbc.Card([
        dbc.CardHeader(html.H4("Live Event Log", className="text-center")),
        dbc.CardBody(html.Pre(id='live-event-log', style={'height': '300px', 'overflowY': 'scroll', 'whiteSpace': 'pre-wrap', 'wordBreak': 'break-all'}))
    ]), width=12, className="mb-4")),
])

# --- Redis Listener Function ---
def start_redis_listener(app_queue: Queue):
    logging.info("Dashboard: Redis listener thread started...")
    try:
        redis_client = RedisClient()
    except Exception as e:
        logging.critical(f"Dashboard: Error connecting to Redis: {e}. Listener not starting.")
        return

    if not redis_client.connection:
        logging.critical("Dashboard: Failed to connect to Redis! Listener not starting.")
        return
    channels_to_listen = {
        'market-data:*': 'market-data',
        'trade-orders': 'trade-order',
        'trade-confirmations': 'trade-confirmation',
        'system-control': 'system-control'
    }
    def create_listener(pattern, msg_type):
        r = RedisClient()
        if not r.connection:
            logging.error(f"Dashboard: Listener for {pattern} failed to connect to Redis.")
            return

        pubsub = r.connection.pubsub(ignore_subscribe_messages=True)

        try:
            pubsub.psubscribe(pattern)
            logging.info(f"Dashboard listener subscribed to '{pattern}'")
            for message in pubsub.listen():
                try:
                    data = json.loads(message['data'])
                    app_queue.put({'type': msg_type, 'data': data, 'channel': message['channel']})
                except json.JSONDecodeError:
                    logging.warning(f"Dashboard: Received non-JSON message from {pattern}: {message['data']}")
                except Exception as e:
                    logging.warning(f"Dashboard: Error processing message from {pattern}: {e}")
        except redis.ConnectionError:
            logging.error(f"Dashboard: Listener for {pattern} lost connection to Redis.")
        except Exception as e:
            logging.error(f"Dashboard: Listener for {pattern} crashed: {e}")
        finally:
            pubsub.close()
            logging.info(f"Dashboard listener for {pattern} stopped.")
    for channel_pattern, msg_type in channels_to_listen.items():
        listener_thread = threading.Thread(
            target=create_listener,
            args=(channel_pattern, msg_type),
            daemon=True
        )
        listener_thread.start()

# --- CALLBACK 1: Main Data Processing Loop (The "Heart") ---
@app.callback(
    Output('pnl-data-store', 'data'),
    Output('market-data-store', 'data'),
    Output('log-data-store', 'data'),
    Output('status-panel', 'children'),
    Output('graph-pulse-store', 'data'),
    Input('interval-component', 'n_intervals'),
    State('pnl-data-store', 'data'),
    State('market-data-store', 'data'),
    State('log-data-store', 'data'),
    State('graph-pulse-store', 'data')
)
def update_data_stores(n, pnl_data, market_data, log_data, pulse_data):
    status_msg = "RUNNING"
    status_color = "success"
    active_agents = 6 # MVS default
    last_heartbeat = time.strftime('%Y-%m-%d %H:%M:%S')

    current_time = time.time()
    active_pulses = {
        edge: pulse for edge, pulse in pulse_data.items()
        if current_time - pulse['time'] < 1.0 # Pulse lasts 1 second
    }
    new_logs = []
    while not message_queue.empty():
        try:
            msg = message_queue.get_nowait()
            msg_time_str = time.strftime('%H:%M:%S')

            if msg['type'] == 'market-data':
                source_agent = msg['data']['source']
                if msg['channel'] == b'market-data:XXBTZUSD':
                    price = float(msg['data']['data']['c'][0])
                    market_data['times'].append(msg_time_str)
                    market_data['prices'].append(price)
                    market_data['times'] = market_data['times'][-100:]
                    market_data['prices'] = market_data['prices'][-100:]
                    edge_id = f"{source_agent}->PatternLearner_XXBTZUSD_3"
                    active_pulses[edge_id] = {'color': '#3498db', 'time': current_time}

                elif msg['channel'] == b'market-data:XETHZUSD':
                    edge_id = f"{source_agent}->PatternLearner_XETHZUSD_4"
                    active_pulses[edge_id] = {'color': '#3498db', 'time': current_time}

                log_entry = f"[{msg_time_str}] [MARKET] {msg['data']['source']}: Price {msg['data']['data']['c'][0]}"
                new_logs.append(log_entry)

            elif msg['type'] == 'trade-order':
                source_agent = msg['data']['source']
                target_agent = 'Trader_5'
                log_entry = f"[{msg_time_str}] [ORDER] {source_agent} -> {target_agent}: {msg['data']['direction'].upper()} {msg['data']['amount']} {msg['data']['pair']}"
                new_logs.append(log_entry)
                edge_id = f"{source_agent}->{target_agent}"
                active_pulses[edge_id] = {'color': '#f1c40f', 'time': current_time}

            elif msg['type'] == 'trade-confirmation':
                source_agent = 'Trader_5'
                target_agent = 'RiskManager_6'
                log_entry = f"[{msg_time_str}] [CONFIRM] {source_agent}: Order {msg['data']['execution_result'].get('status', 'FAILED')}"
                new_logs.append(log_entry)
                edge_id = f"{source_agent}->{target_agent}"
                active_pulses[edge_id] = {'color': '#f39c12', 'time': current_time}

                if msg['data']['execution_result'].get('status') == 'success':
                    last_pnl = pnl_data['values'][-1]
                    sim_result = random.uniform(-50, 75)
                    new_pnl = last_pnl + sim_result
                    pnl_data['values'].append(new_pnl)
                    pnl_data['times'].append(msg_time_str)
                    pnl_data['values'] = pnl_data['values'][-100:]
                    pnl_data['times'] = pnl_data['times'][-100:]

            elif msg['type'] == 'system-control':
                if msg['data'].get('command') == 'HALT_TRADING':
                    status_msg = "HALTED!"
                    status_color = "danger"
                    log_entry = f"[{msg_time_str}] [CRITICAL] {msg['data']['source']}: {msg['data']['reason']}"
                    new_logs.append(log_entry)
                    source_agent = msg['data']['source']
                    active_pulses[f"{source_agent}->PatternLearner_XXBTZUSD_3"] = {'color': '#e74c3c', 'time': current_time}
                    active_pulses[f"{source_agent}->PatternLearner_XETHZUSD_4"] = {'color': '#e74c3c', 'time': current_time}
        except Exception as e:
            logging.error(f"Dashboard: Error processing message: {e}")
    log_data.extend(new_logs)
    log_data = log_data[-50:]
    status_panel = [
        dbc.Alert(f"STATUS: {status_msg}", color=status_color, className="fw-bold text-center"),
        html.P(f"LAST HEARTBEAT: {last_heartbeat}"),
        html.P(f"ACTIVE AGENTS: {active_agents}"),
    ]

    return pnl_data, market_data, log_data, status_panel, active_pulses

# --- CALLBACK 2: Update P&L Chart ---
@app.callback(
    Output('pnl-chart', 'figure'),
    Input('pnl-data-store', 'data')
)
def update_pnl_chart(data):
    fig = go.Figure(layout=go.Layout(template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)'))
    fig.add_trace(go.Scatter(
        x=data['times'],
        y=data['values'],
        mode='lines',
        line={'color': '#00C853'}
    ))

    # This logic fixes the "falling balls" and "stretching" bug
    min_val = min(data['values'])
    max_val = max(data['values'])
    padding = (max_val - min_val) * 0.1 + 100 # Add 10% padding + 100
    fig.update_layout(
        xaxis_title="Time",
        yaxis_title="Simulated Portfolio Value ($)",
        showlegend=False,
        yaxis_range=[min_val - padding, max_val + padding] # Lock the y-axis
    )
    return fig

# --- CALLBACK 3: Update Market Chart ---
@app.callback(
    Output('market-chart', 'figure'),
    Input('market-data-store', 'data')
)
def update_market_chart(data):
    fig = go.Figure(layout=go.Layout(template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)'))
    fig.add_trace(go.Scatter(
        x=data['times'],
        y=data['prices'],
        mode='lines',
        line={'color': '#3498db'}
    ))
    fig.update_layout(
        xaxis_title="Time",
        yaxis_title="Price (XXBTZUSD)",
        showlegend=False
    )
    return fig

# --- CALLBACK 4: Update Live Log ---
@app.callback(
    Output('live-event-log', 'children'),
    Input('log-data-store', 'data')
)
def update_live_log(log_data):
    return "\n".join(reversed(log_data))

# --- CALLBACK 5: Update "Brain Scan" Graph ---
@app.callback(
    Output('mycelial-graph', 'figure'),
    Input('graph-pulse-store', 'data')
)
def update_mycelial_graph(pulse_data):
    node_x, node_y, node_text, node_colors = [], [], [], []
    for node_name, pos in NODE_POSITIONS.items():
        node_x.append(pos['x'])
        node_y.append(pos['y'])
        node_text.append(node_name.split('_')[0])

        if 'DataMiner' in node_name: node_colors.append('#3498db')
        elif 'PatternLearner' in node_name: node_colors.append('#2ecc71')
        elif 'Trader' in node_name: node_colors.append('#f1c40f')
        elif 'RiskManager' in node_name: node_colors.append('#e74c3c')
        else: node_colors.append('grey')
    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode='markers+text',
        text=node_text,
        textposition="top center",
        marker=dict(size=30, color=node_colors, line=dict(width=3, color='#e0e0e0')),
        hoverinfo='text',
        hovertext=list(NODE_POSITIONS.keys())
    )
    edge_traces = []
    for (source, target) in NODE_EDGES:
        pos_source = NODE_POSITIONS[source]
        pos_target = NODE_POSITIONS[target]

        edge_id = f"{source}->{target}"
        pulse = pulse_data.get(edge_id)

        pulse_color = '#333' # Default "off" color
        pulse_width = 2
        if pulse:
            pulse_color = pulse['color'] # "Swirl" color (blue, yellow, red)
            pulse_width = 6 # "Pulse" width

        edge_traces.append(go.Scatter(
            x=[pos_source['x'], pos_target['x']],
            y=[pos_source['y'], pos_target['y']],
            mode='lines',
            line=dict(width=pulse_width, color=pulse_color),
            hoverinfo='none'
        ))
    fig = go.Figure(
        data=edge_traces + [node_trace],
        layout=go.Layout(
            template='plotly_dark',
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            showlegend=False,
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[-0.1, 1.1]),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[-0.1, 1.2]),
            margin=dict(l=10, r=10, t=10, b=10)
        )
    )
    return fig

# --- Main entry point to run the dashboard server ---
if __name__ == '__main__':
    try:
        listener_thread = threading.Thread(target=start_redis_listener, args=(message_queue,), daemon=True)
        listener_thread.start()

        logging.info("Starting Dash web server on http://127.0.0.1:8050")
        app.run_server(debug=False, port=8050) # Use debug=False for production
    except redis.exceptions.ConnectionError as e:
        logging.critical("FATAL: Cannot connect to Redis. Is the Docker container running?")
        logging.critical("Run: docker run -d -p 6379:6379 --name mycelial-redis redis:latest")
    except Exception as e:
        logging.critical(f"FATAL: Dashboard failed to start: {e}")
