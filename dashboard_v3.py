# dashboard_v3.py - Professional Dashboard with Modern Design
# Inspired by Google Analytics, Stripe, and Vercel dashboards

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

# App initialization with modern Bootstrap theme
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "Mycelial Intelligence"

# Professional color palette
COLORS = {
    'bg': '#0F172A',        # Main background
    'surface': '#1E293B',   # Card backgrounds
    'border': '#334155',    # Borders
    'text': '#F1F5F9',      # Primary text
    'text_secondary': '#94A3B8',  # Secondary text
    'primary': '#3B82F6',   # Blue accent
    'success': '#10B981',   # Green
    'warning': '#F59E0B',   # Amber
    'danger': '#EF4444',    # Red
}

# Data stores
high_confidence_patterns = deque(maxlen=20)

# Custom CSS for modern look
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

#===========================================
# Data Processing Functions
#===========================================

def get_sql_patterns():
    """Query SQL database for archived patterns"""
    try:
        conn = sqlite3.connect('mycelial_patterns.db')
        cursor = conn.cursor()
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

def synthesize_cross_moat_intelligence(sql_patterns):
    """Cross-Moat Synthesis"""
    govt_patterns = [p for p in sql_patterns if 'GovtDataMiner' in str(p.get('agent_id', ''))]
    logistics_patterns = [p for p in sql_patterns if 'LogisticsMiner' in str(p.get('agent_id', ''))]
    corp_patterns = [p for p in sql_patterns if 'CorpDataMiner' in str(p.get('agent_id', ''))]
    code_patterns = [p for p in sql_patterns if 'RepoScraper' in str(p.get('agent_id', ''))]
    finance_patterns = [p for p in sql_patterns if 'DataEngineer' in str(p.get('agent_id', ''))]

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

    govt_strength, govt_value = get_moat_strength(govt_patterns)
    logistics_strength, logistics_value = get_moat_strength(logistics_patterns)
    corp_strength, corp_value = get_moat_strength(corp_patterns)
    code_strength, code_value = get_moat_strength(code_patterns)
    finance_strength, finance_value = get_moat_strength(finance_patterns)

    strong_moats = []
    if govt_strength in ['Strong', 'Moderate']:
        strong_moats.append('Government')
    if logistics_strength in ['Strong', 'Moderate']:
        strong_moats.append('Supply Chain')
    if corp_strength in ['Strong', 'Moderate']:
        strong_moats.append('Corporations')
    if code_strength in ['Strong', 'Moderate']:
        strong_moats.append('Code Innovation')
    if finance_strength in ['Strong', 'Moderate']:
        strong_moats.append('Crypto Markets')

    synthesis = {
        'alignment_count': len(strong_moats),
        'aligned_moats': strong_moats,
        'signal_strength': 'NONE',
        'briefing': '',
        'moat_details': {
            'Government': {'strength': govt_strength, 'value': govt_value},
            'Logistics': {'strength': logistics_strength, 'value': logistics_value},
            'Corporations': {'strength': corp_strength, 'value': corp_value},
            'Code': {'strength': code_strength, 'value': code_value},
            'Finance': {'strength': finance_strength, 'value': finance_value}
        }
    }

    if len(strong_moats) >= 4:
        synthesis['signal_strength'] = 'VERY STRONG'
        synthesis['briefing'] = f"Critical alignment: {len(strong_moats)}/5 moats showing coordinated patterns"
    elif len(strong_moats) == 3:
        synthesis['signal_strength'] = 'STRONG'
        synthesis['briefing'] = f"Strong alignment: {', '.join(strong_moats)} coordinated"
    elif len(strong_moats) == 2:
        synthesis['signal_strength'] = 'MODERATE'
        synthesis['briefing'] = f"Moderate signal: {', '.join(strong_moats)} aligned"
    elif len(strong_moats) == 1:
        synthesis['signal_strength'] = 'WEAK'
        synthesis['briefing'] = f"Weak signal: Only {strong_moats[0]} active"
    else:
        synthesis['signal_strength'] = 'NONE'
        synthesis['briefing'] = "No clear cross-moat alignment detected"

    return synthesis

#===========================================
# Layout
#===========================================

app.layout = html.Div(style={'backgroundColor': COLORS['bg'], 'minHeight': '100vh', 'padding': '40px 0'}, children=[
    dcc.Interval(id='interval-component', interval=2000, n_intervals=0),

    # Main Container
    dbc.Container(fluid=True, style={'maxWidth': '1400px'}, children=[

        # Header
        html.Div(style={'marginBottom': '48px'}, children=[
            html.H1("Mycelial Intelligence",
                   style={'color': COLORS['text'], 'fontSize': '2rem', 'fontWeight': '700',
                          'marginBottom': '8px', 'letterSpacing': '-0.025em'}),
            html.P("Real-time insights across 5 intelligence moats",
                  style={'color': COLORS['text_secondary'], 'fontSize': '1rem', 'margin': 0})
        ]),

        # Content
        html.Div(id='dashboard-content')
    ])
])

#===========================================
# Callback
#===========================================

@app.callback(
    Output('dashboard-content', 'children'),
    Input('interval-component', 'n_intervals')
)
def update_dashboard(n):
    sql_patterns = get_sql_patterns()
    synthesis = synthesize_cross_moat_intelligence(sql_patterns)

    # Signal badge style
    badge_class = {
        'VERY STRONG': 'badge-very-strong',
        'STRONG': 'badge-strong',
        'MODERATE': 'badge-moderate',
        'WEAK': 'badge-weak',
        'NONE': 'badge-weak'
    }.get(synthesis['signal_strength'], 'badge-weak')

    return [
        # Top Stats Row
        dbc.Row(style={'marginBottom': '32px'}, children=[
            dbc.Col(width=3, children=[
                html.Div(className='metric-card', children=[
                    html.Div(className='stat-number',
                            style={'color': COLORS['primary']},
                            children=str(len(sql_patterns))),
                    html.Div(className='stat-label', children='Patterns Discovered')
                ])
            ]),
            dbc.Col(width=3, children=[
                html.Div(className='metric-card', children=[
                    html.Div(className='stat-number',
                            style={'color': COLORS['success']},
                            children=str(synthesis['alignment_count'])),
                    html.Div(className='stat-label', children='Moats Aligned')
                ])
            ]),
            dbc.Col(width=3, children=[
                html.Div(className='metric-card', children=[
                    html.Div(className='stat-number',
                            style={'color': COLORS['warning']},
                            children='121'),
                    html.Div(className='stat-label', children='Active Agents')
                ])
            ]),
            dbc.Col(width=3, children=[
                html.Div(className='metric-card', children=[
                    html.Div(className='stat-number',
                            style={'color': COLORS['text']},
                            children=datetime.now().strftime('%H:%M')),
                    html.Div(className='stat-label', children='Last Updated')
                ])
            ])
        ]),

        # Cross-Moat Signal Section
        html.Div(className='section-card', children=[
            html.Div(className='section-title', children='Cross-Moat Intelligence'),
            html.Div(className='section-subtitle', children='Pattern alignment across all intelligence sources'),

            html.Div(style={'display': 'flex', 'alignItems': 'center', 'gap': '16px', 'marginBottom': '24px'}, children=[
                html.Span(className=f'signal-badge {badge_class}', children=synthesis['signal_strength']),
                html.Span(style={'color': COLORS['text'], 'fontSize': '1.125rem'}, children=synthesis['briefing'])
            ]),

            # Moat Grid
            html.Div(className='moat-grid', children=[
                html.Div(className='moat-item', children=[
                    html.Div(className='moat-label', children='GOVERNMENT'),
                    html.Div(className='moat-value',
                            style={'color': get_color_for_strength(synthesis['moat_details']['Government']['strength'])},
                            children=synthesis['moat_details']['Government']['strength']),
                    html.Div(className='moat-status',
                            children=f"{synthesis['moat_details']['Government']['value']:.0f}")
                ]),
                html.Div(className='moat-item', children=[
                    html.Div(className='moat-label', children='LOGISTICS'),
                    html.Div(className='moat-value',
                            style={'color': get_color_for_strength(synthesis['moat_details']['Logistics']['strength'])},
                            children=synthesis['moat_details']['Logistics']['strength']),
                    html.Div(className='moat-status',
                            children=f"{synthesis['moat_details']['Logistics']['value']:.0f}")
                ]),
                html.Div(className='moat-item', children=[
                    html.Div(className='moat-label', children='CORPORATIONS'),
                    html.Div(className='moat-value',
                            style={'color': get_color_for_strength(synthesis['moat_details']['Corporations']['strength'])},
                            children=synthesis['moat_details']['Corporations']['strength']),
                    html.Div(className='moat-status',
                            children=f"{synthesis['moat_details']['Corporations']['value']:.0f}")
                ]),
                html.Div(className='moat-item', children=[
                    html.Div(className='moat-label', children='CODE'),
                    html.Div(className='moat-value',
                            style={'color': get_color_for_strength(synthesis['moat_details']['Code']['strength'])},
                            children=synthesis['moat_details']['Code']['strength']),
                    html.Div(className='moat-status',
                            children=f"{synthesis['moat_details']['Code']['value']:.0f}")
                ]),
                html.Div(className='moat-item', children=[
                    html.Div(className='moat-label', children='FINANCE'),
                    html.Div(className='moat-value',
                            style={'color': get_color_for_strength(synthesis['moat_details']['Finance']['strength'])},
                            children=synthesis['moat_details']['Finance']['strength']),
                    html.Div(className='moat-status',
                            children=f"{synthesis['moat_details']['Finance']['value']:.0f}")
                ])
            ])
        ]),

        # Recent Patterns Section
        html.Div(className='section-card', children=[
            html.Div(className='section-title', children='Recent Patterns'),
            html.Div(className='section-subtitle', children=f'{len(sql_patterns)} patterns discovered in the last analysis cycle'),

            html.Div(children=[
                html.Div(style={'background': COLORS['bg'], 'padding': '16px', 'borderRadius': '8px',
                               'marginBottom': '12px', 'border': f'1px solid {COLORS["border"]}'}, children=[
                    html.Div(style={'display': 'flex', 'justifyContent': 'space-between', 'alignItems': 'start', 'marginBottom': '8px'}, children=[
                        html.Span(style={'color': COLORS['text'], 'fontWeight': '500'},
                                 children=f"Pattern #{i+1}"),
                        html.Span(style={'color': COLORS['warning'], 'fontSize': '0.875rem', 'fontWeight': '600'},
                                 children=f"{p['pattern_value']:.0f}% confidence")
                    ]),
                    html.Div(style={'color': COLORS['text_secondary'], 'fontSize': '0.875rem'},
                            children=f"Agent: {str(p['agent_id'])[:30]}..."),
                    html.Div(style={'color': COLORS['text_secondary'], 'fontSize': '0.75rem', 'marginTop': '8px'},
                            children=datetime.fromtimestamp(p['timestamp']).strftime('%Y-%m-%d %H:%M:%S'))
                ])
                for i, p in enumerate(sql_patterns[:5])
            ])
        ])
    ]

def get_color_for_strength(strength):
    """Map strength to color"""
    return {
        'Strong': COLORS['success'],
        'Moderate': COLORS['warning'],
        'Weak': COLORS['text_secondary'],
        'None': COLORS['border']
    }.get(strength, COLORS['border'])

#===========================================
# Run Server
#===========================================

if __name__ == '__main__':
    logging.info("Mycelial Intelligence Platform v3.0 - Modern Design")
    logging.info("Starting server on http://127.0.0.1:8057/")
    app.run(debug=False, host='127.0.0.1', port=8057)
