"""
F1 Telemetry Dashboard
A Dash web application for analyzing Formula 1 telemetry data
"""

import base64
import os
import io
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from dash import Dash, dcc, html, Input, Output, State, dash_table
from dash.exceptions import PreventUpdate
import dash
import telemetry_utils as tu
import icons
from app.features.analytics import (
    compute_correlation_matrix,
    compute_distributions,
    compute_consistency_scores,
    compute_rolling_stats,
    compute_percentile_profile,
    NUMERIC_TELEMETRY_COLS,
)

# UDP Listener is initialized in the main execution block (if run directly) or externally


# Initialize the Dash app
# Initialize the Dash app
app = Dash(__name__, suppress_callback_exceptions=True)
app.title = "F1 Telemetry Dashboard"
server = app.server

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def validate_dataframe(df):
    """Validate that the uploaded DataFrame has required columns"""
    required_columns = ['driver', 'lap', 'time_stamp']
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    if missing_columns:
        return False, f"Missing required columns: {', '.join(missing_columns)}"
    return True, "Valid"


def compute_lap_times(df):
    """Compute lap times from time_stamp if lap_time_ms is missing"""
    if 'lap_time_ms' in df.columns:
        return df
    
    # Group by driver and lap, compute duration from time_stamp
    lap_times = df.groupby(['driver', 'lap'])['time_stamp'].agg(['min', 'max'])
    lap_times['lap_time_ms'] = ((lap_times['max'] - lap_times['min']) * 1000).astype(int)
    lap_times = lap_times.reset_index()[['driver', 'lap', 'lap_time_ms']]
    
    # Merge back to original dataframe
    df = df.merge(lap_times, on=['driver', 'lap'], how='left')
    return df


def get_dataset_summary(df):
    """Generate summary statistics for the dataset"""
    if df is None or df.empty:
        return {}
    
    total_laps = df.groupby(['driver', 'lap']).ngroups
    drivers = df['driver'].unique().tolist()
    
    # Compute lap times if needed
    df_with_times = compute_lap_times(df.copy())
    lap_summary = df_with_times.groupby(['driver', 'lap'])['lap_time_ms'].first().reset_index()
    
    if not lap_summary.empty:
        fastest_lap_row = lap_summary.loc[lap_summary['lap_time_ms'].idxmin()]
        fastest_lap = f"{fastest_lap_row['driver']} - Lap {fastest_lap_row['lap']} ({fastest_lap_row['lap_time_ms']/1000:.3f}s)"
        avg_lap_time = f"{lap_summary['lap_time_ms'].mean()/1000:.3f}s"
    else:
        fastest_lap = "N/A"
        avg_lap_time = "N/A"
    
    session_duration = f"{df['time_stamp'].max():.1f}s"
    
    return {
        'total_laps': total_laps,
        'drivers': ', '.join(drivers),
        'drivers_count': len(drivers),
        'fastest_lap': fastest_lap,
        'avg_lap_time': avg_lap_time,
        'session_duration': session_duration,
        'total_rows': len(df)
    }


def parse_upload_contents(contents, filename):
    """Parse uploaded CSV file"""
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    
    try:
        if 'csv' in filename.lower():
            df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
            return df, None
        else:
            return None, "Please upload a CSV file"
    except Exception as e:
        return None, f"Error parsing file: {str(e)}"

def load_default_data():
    """Load example telemetry if no file is uploaded"""
    try:
        default_path = os.path.join("data", "example_telemetry.csv")
        if os.path.exists(default_path):
            print(f"INFO: Loading default data from {default_path}")
            df = pd.read_csv(default_path)
            return df.to_json(date_format='iso', orient='split')
    except Exception as e:
        print(f"WARN: Could not load default data: {e}")
    return None


# ============================================================================
# STYLING
# ============================================================================

# F1 Broadcast Theme Colors - Pro UI
# F1 Broadcast Theme Colors - Pro UI
COLORS = {
    # Core backgrounds
    'card_bg': '#141414',
    'background': '#0d0d0d', # Used in layout
    
    # F1 Signature colors
    'f1_red': '#e10600',
    'f1_cyan': '#00d2be',
    'f1_gold': '#f0c514',
    
    # Text colors
    'text_primary': '#ffffff',
    'text_secondary': '#8a8a8a',
    'text_accent': '#00d2be',
    'text_muted': '#666666',
    
    # Chart colors
    'grid_line': 'rgba(255, 255, 255, 0.05)',
    'border': 'rgba(255, 255, 255, 0.08)',
    
    # Data series colors - F1 team inspired
    'series': ['#e10600', '#00d2be', '#f0c514', '#00ff87', '#ff4757'],
    
    # Data state colors
    'positive': '#00ff87',
    'negative': '#ff4757',
    'warning': '#ffa502',
    
    # Table colors
    'table_header': '#0d0d0d',
    'table_row_even': '#141414',
    'table_row_odd': '#1a1a1a',
    'header_gradient_start': '#e10600', # Kept for dynamic styling
}

# Custom CSS
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Rajdhani:wght@300;400;600;700&display=swap" rel="stylesheet">
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body {
                font-family: 'Rajdhani', sans-serif;
                background-color: #0d0d0d;
                color: #ffffff;
                margin: 0;
                padding: 0;
                -webkit-font-smoothing: antialiased;
                -moz-osx-font-smoothing: grayscale;
            }
            
            #react-entry-point {
                height: 100vh;
                overflow-y: auto;
            }
            
            /* Scrollbar styling */
            ::-webkit-scrollbar {
                width: 10px;
                height: 10px;
            }
            
            ::-webkit-scrollbar-track {
                background: #141414;
            }
            
            ::-webkit-scrollbar-thumb {
                background: #2a2a2a;
                border-radius: 5px;
            }
            
            ::-webkit-scrollbar-thumb:hover {
                background: #00d2be;
            }
            
            /* Dropdown styling for visibility */
            .Select-menu-outer {
                background-color: #0c101c !important;
                border: 1px solid #1c2840 !important;
                border-radius: 6px !important;
            }
            
            .Select-option {
                background-color: #0c101c !important;
                color: #ffffff !important;
                padding: 10px !important;
            }
            
            .Select-option:hover {
                background-color: #151e31 !important;
                color: #47d7ff !important;
            }
            
            .Select-value-label {
                color: #ffffff !important;
            }
            
            /* Modern Dash dropdown styling */
            div[class*="css-"] div[class*="menu"] {
                background-color: #0c101c !important;
                border: 1px solid #1c2840 !important;
            }
            
            div[class*="css-"] div[class*="option"] {
                background-color: #0c101c !important;
                color: #ffffff !important;
            }
            
            div[class*="css-"] div[class*="option"]:hover {
                background-color: #151e31 !important;
                color: #47d7ff !important;
            }
            
            div[class*="css-"] div[class*="singleValue"] {
                color: #ffffff !important;
            }
            
            div[class*="css-"] div[class*="placeholder"] {
                color: #9aa5c6 !important;
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

# Common styles
CARD_STYLE = {
    'backgroundColor': COLORS['card_bg'],
    'borderRadius': '12px',
    'padding': '20px',
    'marginBottom': '20px',
    'border': f'1px solid {COLORS["border"]}',
    'boxShadow': '0 4px 6px rgba(0, 0, 0, 0.3)',
}

def create_disabled_figure(title, message):
    """Create a placeholder figure for disabled features"""
    fig = go.Figure()
    fig.update_layout(
        template='plotly_dark',
        paper_bgcolor=COLORS['card_bg'],
        plot_bgcolor=COLORS['card_bg'],
        xaxis={'visible': False},
        yaxis={'visible': False},
        annotations=[{
            'text': f'<b>{title}</b><br><br>{message}',
            'xref': 'paper',
            'yref': 'paper',
            'x': 0.5,
            'y': 0.5,
            'showarrow': False,
            'font': {'size': 14, 'color': COLORS['text_secondary']},
            'align': 'center'
        }],
        margin={'l': 20, 'r': 20, 't': 20, 'b': 20}
    )
    return fig


METRIC_STYLE = {
    'textAlign': 'center',
    'padding': '15px',
}

SECTION_TITLE_STYLE = {
    'fontSize': '16px',
    'fontWeight': '700',
    'color': COLORS['text_primary'],
    'letterSpacing': '0.08em',
    'marginBottom': '15px',
    'textTransform': 'uppercase',
    'borderBottom': f'2px solid {COLORS["header_gradient_start"]}',
    'paddingBottom': '8px',
    'fontFamily': 'Orbitron, sans-serif',
}

METRIC_VALUE_STYLE = {
    'fontSize': '32px',
    'fontWeight': '700',
    'color': COLORS['f1_cyan'],
    'fontFamily': 'Orbitron, sans-serif',
    'textShadow': '0 0 30px rgba(0, 210, 190, 0.4)',
    'transition': 'text-shadow 0.3s ease',
}

METRIC_LABEL_STYLE = {
    'fontSize': '12px',
    'color': COLORS['text_secondary'],
    'marginTop': '5px',
    'textTransform': 'uppercase',
    'letterSpacing': '0.05em',
}

DROPDOWN_STYLE = {
    'backgroundColor': COLORS['card_bg'],
    'borderRadius': '6px',
}

DROPDOWN_CLASSNAME = 'custom-dropdown'

# ============================================================================
# LAYOUT
# ============================================================================

app.layout = html.Div(style={'backgroundColor': COLORS['background'], 'minHeight': '100vh', 'padding': '0'}, children=[
    
    
    # Hidden data store
    dcc.Store(id='stored-data', data=load_default_data()),
    
    # Header - F1 Broadcast Style
    html.Div(className='f1-header', style={
        'background': COLORS['background'],
        'height': '100px',
        'display': 'flex',
        'alignItems': 'center',
        'justifyContent': 'space-between',
        'padding': '0 40px',
        'marginBottom': '30px',
        'borderBottom': f'3px solid {COLORS["f1_red"]}',
        'position': 'relative',
    }, children=[
        # Left: Branding
        html.Div(children=[
            html.H1('F1 TELEMETRY', style={
                'fontSize': '36px',
                'fontWeight': '900',
                'color': '#ffffff',
                'margin': '0',
                'fontFamily': 'Orbitron, sans-serif',
                'letterSpacing': '0.15em',
                'textShadow': '0 2px 10px rgba(0, 0, 0, 0.5)',
            }),
            html.P('REAL-TIME ANALYSIS', style={
                'fontSize': '12px',
                'color': COLORS['text_secondary'],
                'margin': '4px 0 0 0',
                'fontWeight': '600',
                'letterSpacing': '0.2em',
                'textTransform': 'uppercase',
            }),
        ]),

        # Animated gradient bar at bottom (via CSS)
    ]),
    
    # Main container
    html.Div(style={'padding': '0 30px 30px 30px', 'maxWidth': '1800px', 'margin': '0 auto'}, children=[
        
        # Top band: Upload + Summary + Lap Overview
        html.Div(style={'display': 'grid', 'gridTemplateColumns': '32% 22% 46%', 'gap': '20px', 'marginBottom': '20px'}, children=[
            
            # Upload card
            html.Div(style=CARD_STYLE, className='dashboard-card', children=[
                html.Div('Upload & Summary', style=SECTION_TITLE_STYLE),
                dcc.Upload(
                    id='upload-data',
                    children=html.Div([
                        icons.get_icon('upload', size=48, color=COLORS['f1_red'], className='icon-svg'),
                        html.Div('Drag and Drop or ', style={'fontSize': '14px', 'marginTop': '10px'}),
                        html.A('Select CSV File', style={'color': COLORS['header_gradient_start'], 'fontWeight': '600'}),
                    ], style={
                        'textAlign': 'center',
                        'padding': '40px',
                        'border': f'2px dashed {COLORS["border"]}',
                        'borderRadius': '8px',
                        'cursor': 'pointer',
                        'transition': 'all 0.3s ease',
                    }),
                    style={'marginBottom': '15px'},
                    multiple=False
                ),
                html.Div(id='upload-status', style={'fontSize': '13px', 'color': COLORS['text_secondary'], 'marginTop': '10px'}),
            ]),
            
            # Dataset summary metrics
            html.Div(style=CARD_STYLE, className='dashboard-card', children=[
                html.Div('Dataset Summary', style=SECTION_TITLE_STYLE),
                html.Div(id='dataset-summary', children=[
                    html.Div([
                        html.Div('--', id='total-laps-value', style=METRIC_VALUE_STYLE),
                        html.Div('Total Laps', style=METRIC_LABEL_STYLE),
                    ], style=METRIC_STYLE),
                    html.Div([
                        html.Div('--', id='drivers-count-value', style=METRIC_VALUE_STYLE),
                        html.Div('Drivers', style=METRIC_LABEL_STYLE),
                    ], style=METRIC_STYLE),
                    html.Div([
                        html.Div('--', id='fastest-lap-value', style={**METRIC_VALUE_STYLE, 'fontSize': '14px'}),
                        html.Div('Fastest Lap', style=METRIC_LABEL_STYLE),
                    ], style=METRIC_STYLE),
                ]),
            ]),
            
            # Lap overview chart
            html.Div(children=[
                html.Div(style=CARD_STYLE, className='dashboard-card', children=[
                html.Div('Lap Overview', style=SECTION_TITLE_STYLE),
                    html.Div(className='chart-container', style={'height': '250px'}, children=[dcc.Graph(id='lap-times-chart', config={'displayModeBar': False})]),
                ]),
                html.Div(style=CARD_STYLE, className='dashboard-card', children=[
                html.Div('Lap Times Table', style=SECTION_TITLE_STYLE),
                    html.Div(id='lap-times-table-container'),
                ]),
            ]),
        ]),
        
        # Data preview
        html.Div(style=CARD_STYLE, className='dashboard-card', children=[
            html.Div('Data Preview', style=SECTION_TITLE_STYLE),
            html.Div(id='data-preview-container'),
        ]),
        
        # Lap detail section
        html.Div(style=CARD_STYLE, className='dashboard-card no-hover', children=[
            html.Div('Lap Detail View', style=SECTION_TITLE_STYLE),
            html.Div(style={'display': 'grid', 'gridTemplateColumns': '1fr 1fr', 'gap': '15px', 'marginBottom': '20px'}, children=[
                html.Div([
                    html.Label('Select Driver', style={'fontSize': '12px', 'color': COLORS['text_secondary'], 'marginBottom': '8px', 'display': 'block', 'fontWeight': '600'}),
                    dcc.Dropdown(id='driver-select', className=DROPDOWN_CLASSNAME, placeholder='Select a driver...'),
                ]),
                html.Div([
                    html.Label('Select Lap', style={'fontSize': '12px', 'color': COLORS['text_secondary'], 'marginBottom': '8px', 'display': 'block', 'fontWeight': '600'}),
                    dcc.Dropdown(id='lap-select', className=DROPDOWN_CLASSNAME, placeholder='Select a lap...'),
                ]),
            ]),
            html.Div(style={'display': 'grid', 'gridTemplateColumns': '1fr 1fr', 'gap': '15px'}, children=[
                html.Div(className='chart-container', children=[dcc.Graph(id='speed-trace-chart', config={'displayModeBar': False})]),
                html.Div(children=[
                    html.Div(className='chart-container', style={'height': '180px'}, children=[dcc.Graph(id='throttle-trace-chart', config={'displayModeBar': False})]),
                    html.Div(className='chart-container', style={'height': '180px'}, children=[dcc.Graph(id='brake-trace-chart', config={'displayModeBar': False})]),
                ]),
            ]),
            html.Div(className='chart-container', children=[dcc.Graph(id='rpm-trace-chart', config={'displayModeBar': False})]),
        ]),
        
        # Bottom band: Lap comparison + Insights
        html.Div(style={'display': 'grid', 'gridTemplateColumns': '60% 40%', 'gap': '20px'}, children=[
            
            # Lap comparison
            html.Div(style=CARD_STYLE, className='dashboard-card no-hover', children=[
                html.Div('Lap Comparison', style=SECTION_TITLE_STYLE),
                html.Div(style={'display': 'flex', 'gap': '15px', 'marginBottom': '25px', 'alignItems': 'flex-end'}, children=[
                    html.Div(style={'flex': '1'}, children=[
                        html.Label('Driver', style={'fontSize': '12px', 'color': COLORS['text_secondary'], 'marginBottom': '8px', 'display': 'block', 'fontWeight': '600'}),
                        dcc.Dropdown(id='comparison-driver-select', className=DROPDOWN_CLASSNAME, placeholder='Select driver...'),
                    ]),
                    html.Div(style={'flex': '1'}, children=[
                        html.Label('Lap A', style={'fontSize': '12px', 'color': COLORS['text_secondary'], 'marginBottom': '8px', 'display': 'block', 'fontWeight': '600'}),
                        dcc.Dropdown(id='lap-a-select', className=DROPDOWN_CLASSNAME, placeholder='Select lap A...'),
                    ]),
                    html.Div(style={'flex': '1'}, children=[
                        html.Label('Lap B', style={'fontSize': '12px', 'color': COLORS['text_secondary'], 'marginBottom': '8px', 'display': 'block', 'fontWeight': '600'}),
                        dcc.Dropdown(id='lap-b-select', className=DROPDOWN_CLASSNAME, placeholder='Select lap B...'),
                    ]),
                ]),
                html.Div(className='chart-container', style={'height': '450px'}, children=[dcc.Graph(id='lap-comparison-chart', config={'displayModeBar': False})]),
            ]),
            
            # Insights and sectors
            html.Div(children=[
                html.Div(style=CARD_STYLE, className='dashboard-card', children=[
                    html.Div('Session Insights', style=SECTION_TITLE_STYLE),
                    html.Div(id='insights-content'),
                ]),
                html.Div(style=CARD_STYLE, className='dashboard-card', children=[
                    html.Div('Sector Heatmap', style=SECTION_TITLE_STYLE),
                    html.Div(className='chart-container', style={'height': '250px'}, children=[dcc.Graph(id='sector-heatmap', config={'displayModeBar': False})]),
                ]),
            ]),
        ]),
        
        # Track Map & Lap Delta Analysis Section
        html.Div(style=CARD_STYLE, className='dashboard-card no-hover', children=[
            html.Div('Track Map & Lap Delta Analysis', style=SECTION_TITLE_STYLE),
            html.Div(style={'display': 'grid', 'gridTemplateColumns': '60% 40%', 'gap': '20px'}, children=[
                
                # Track Map Section
                html.Div(children=[
                    html.Div(style={'marginBottom': '15px'}, children=[
                        html.Label('Track Map Controls', style={'fontSize': '12px', 'color': COLORS['text_secondary'], 'marginBottom': '8px', 'display': 'block', 'fontWeight': '600'}),
                        html.Div(style={'display': 'flex', 'gap': '10px', 'alignItems': 'center'}, children=[
                            html.Button([icons.get_icon('play', size=16), ' Play'], id='animation-play-btn', className='button-primary', n_clicks=0, style={
                                'color': '#ffffff',
                                'border': 'none',
                                'padding': '8px 16px',
                                'borderRadius': '6px',
                                'cursor': 'pointer',
                                'fontSize': '12px',
                                'fontWeight': '600',
                                'display': 'flex', 'alignItems': 'center', 'gap': '6px'
                            }),
                            html.Button([icons.get_icon('pause', size=16), ' Pause'], id='animation-pause-btn', className='button-secondary', n_clicks=0, style={
                                'color': COLORS['text_primary'],
                                'border': f'1px solid {COLORS["border"]}',
                                'padding': '8px 16px',
                                'borderRadius': '6px',
                                'cursor': 'pointer',
                                'fontSize': '12px',
                                'fontWeight': '600',
                                'display': 'flex', 'alignItems': 'center', 'gap': '6px'
                            }),
                        ]),
                    ]),
                    html.Div(className='chart-container', style={'height': '500px'}, children=[dcc.Graph(id='track-map-chart', config={'displayModeBar': False})]),
                    html.Div(style={'marginTop': '15px'}, children=[
                        html.Label('Distance Along Lap', style={'fontSize': '11px', 'color': COLORS['text_secondary'], 'marginBottom': '8px', 'display': 'block'}),
                        dcc.Slider(
                            id='distance-slider',
                            min=0,
                            max=100,
                            value=0,
                            marks={i: f'{i}%' for i in range(0, 101, 20)},
                            tooltip={'placement': 'bottom', 'always_visible': False},
                            updatemode='drag'
                        ),
                    ]),
                    dcc.Interval(id='animation-interval', interval=100, disabled=True, n_intervals=0),
                ]),
                
                # Lap Delta Section
                html.Div(children=[
                    html.Div(style={'marginBottom': '15px'}, children=[
                        html.Label('Lap Delta Analysis', style={'fontSize': '12px', 'color': COLORS['text_secondary'], 'marginBottom': '8px', 'display': 'block', 'fontWeight': '600'}),
                        html.Div(style={'display': 'grid', 'gridTemplateColumns': '1fr 1fr', 'gap': '10px'}, children=[
                            html.Div([
                                html.Label('Reference Lap', style={'fontSize': '11px', 'color': COLORS['text_secondary'], 'marginBottom': '5px', 'display': 'block'}),
                                dcc.Dropdown(id='delta-lap-a-select', className=DROPDOWN_CLASSNAME, placeholder='Lap A...'),
                            ]),
                            html.Div([
                                html.Label('Compare Lap', style={'fontSize': '11px', 'color': COLORS['text_secondary'], 'marginBottom': '5px', 'display': 'block'}),
                                dcc.Dropdown(id='delta-lap-b-select', className=DROPDOWN_CLASSNAME, placeholder='Lap B...'),
                            ]),
                        ]),
                    ]),
                    html.Div(className='chart-container', style={'height': '300px'}, children=[dcc.Graph(id='delta-plot-chart', config={'displayModeBar': False})]),
                    html.Div(id='corner-stats-card', style={'marginTop': '15px'}),
                    html.Div(id='delta-summary-card', style={'marginTop': '15px'}),
                ]),
            ]),
        ]),

        # ================================================================
        # 📊 ANALYTICS LAB — Data Science Widgets
        # ================================================================
        html.Div(style={'marginTop': '40px', 'marginBottom': '50px'}, children=[
            
            # Section Header
            html.Div(style={
                'display': 'flex', 'alignItems': 'center', 'justifyContent': 'space-between',
                'marginBottom': '30px', 'paddingBottom': '15px',
                'borderBottom': f'2px solid {COLORS["f1_cyan"]}',
            }, children=[
                html.Div(style={'display': 'flex', 'alignItems': 'center', 'gap': '15px'}, children=[
                    html.H2('📊 ANALYTICS LAB', style={
                        'fontFamily': 'Orbitron, sans-serif', 'fontSize': '24px',
                        'fontWeight': '700', 'color': COLORS['f1_cyan'],
                        'letterSpacing': '0.1em', 'margin': '0',
                    }),
                    html.Span('ADVANCED TELEMETRY ANALYSIS', style={
                        'fontSize': '12px', 'color': COLORS['text_secondary'],
                        'letterSpacing': '0.2em', 'textTransform': 'uppercase',
                        'fontWeight': '600', 'marginTop': '4px',
                        'borderLeft': f'1px solid {COLORS["border"]}',
                        'paddingLeft': '15px'
                    }),
                ]),
                html.Div(style={'fontSize': '11px', 'color': COLORS['text_muted'], 'fontStyle': 'italic'}, 
                         children='Statistical insights derived from full session data')
            ]),

            # Row 1: Correlation Heatmap + Consistency Metrics
            html.Div(style={'display': 'grid', 'gridTemplateColumns': '50% 50%', 'gap': '20px', 'marginBottom': '20px'}, children=[

                # Correlation Heatmap
                html.Div(style=CARD_STYLE, className='dashboard-card', children=[
                    html.Div('Telemetry Correlation Matrix', style=SECTION_TITLE_STYLE),
                    html.P('Pearson correlation between telemetry channels', style={
                        'fontSize': '11px', 'color': COLORS['text_muted'], 'marginBottom': '15px',
                    }),
                    html.Div(
                        className='chart-container', style={'height': '380px'},
                        children=[dcc.Graph(id='correlation-heatmap', config={'displayModeBar': False})],
                    ),
                ]),

                # Consistency Metrics
                html.Div(style=CARD_STYLE, className='dashboard-card', children=[
                    html.Div('Driver Consistency Analysis', style=SECTION_TITLE_STYLE),
                    html.P('Lap-time variability per driver (lower CoV = more consistent)', style={
                        'fontSize': '11px', 'color': COLORS['text_muted'], 'marginBottom': '15px',
                    }),
                    html.Div(id='consistency-metric-cards', style={
                        'display': 'flex', 'gap': '12px', 'marginBottom': '18px', 'flexWrap': 'wrap',
                    }),
                    html.Div(
                        className='chart-container', style={'height': '280px'},
                        children=[dcc.Graph(id='consistency-chart', config={'displayModeBar': False})],
                    ),
                ]),
            ]),

            # Row 2: Performance Distribution (full width)
            html.Div(style=CARD_STYLE, className='dashboard-card no-hover', children=[
                html.Div(style={'display': 'flex', 'justifyContent': 'space-between', 'alignItems': 'center', 'marginBottom': '15px'}, children=[
                    html.Div(children=[
                        html.Div('Performance Distributions', style=SECTION_TITLE_STYLE),
                        html.P('Per-driver distribution of telemetry metrics (violin + box)', style={
                            'fontSize': '11px', 'color': COLORS['text_muted'], 'marginTop': '4px',
                        }),
                    ]),
                    html.Div(style={'width': '200px'}, children=[
                        html.Label('Metric', style={
                            'fontSize': '11px', 'color': COLORS['text_secondary'],
                            'display': 'block', 'marginBottom': '5px', 'fontWeight': '600',
                        }),
                        dcc.Dropdown(
                            id='distribution-column-select',
                            options=[{'label': c.replace('_', ' ').title(), 'value': c} for c in NUMERIC_TELEMETRY_COLS],
                            value='speed_kph',
                            clearable=False,
                            style={'backgroundColor': COLORS['card_bg']},
                        ),
                    ]),
                ]),
                html.Div(
                    className='chart-container', style={'height': '400px'},
                    children=[dcc.Graph(id='distribution-chart', config={'displayModeBar': False})],
                ),
            ]),

            # Row 3: Rolling Stats + Percentile Radar
            html.Div(style={'display': 'grid', 'gridTemplateColumns': '60% 40%', 'gap': '20px', 'marginBottom': '20px'}, children=[

                # Rolling Stats
                html.Div(style=CARD_STYLE, className='dashboard-card', children=[
                    html.Div(style={'display': 'flex', 'justifyContent': 'space-between', 'alignItems': 'center', 'marginBottom': '15px'}, children=[
                        html.Div(children=[
                            html.Div('Rolling Averages', style=SECTION_TITLE_STYLE),
                            html.P('Moving-window smoothing of telemetry traces', style={
                                'fontSize': '11px', 'color': COLORS['text_muted'], 'marginTop': '4px',
                            }),
                        ]),
                        html.Div(style={'width': '150px'}, children=[
                            html.Label('Window Size', style={
                                'fontSize': '11px', 'color': COLORS['text_secondary'],
                                'display': 'block', 'marginBottom': '5px', 'fontWeight': '600',
                            }),
                            dcc.Slider(
                                id='rolling-window-slider', min=5, max=50, step=5,
                                value=20, marks={5: '5', 20: '20', 50: '50'},
                                tooltip={'placement': 'bottom'},
                            ),
                        ]),
                    ]),
                    html.Div(
                        className='chart-container', style={'height': '380px'},
                        children=[dcc.Graph(id='rolling-stats-chart', config={'displayModeBar': False})],
                    ),
                ]),

                # Percentile Radar
                html.Div(style=CARD_STYLE, className='dashboard-card', children=[
                    html.Div('Driver Percentile Profile', style=SECTION_TITLE_STYLE),
                    html.P('How does this driver rank vs. all drivers?', style={
                        'fontSize': '11px', 'color': COLORS['text_muted'], 'marginBottom': '12px',
                    }),
                    html.Div(style={'width': '180px', 'marginBottom': '12px'}, children=[
                        html.Label('Driver', style={
                            'fontSize': '11px', 'color': COLORS['text_secondary'],
                            'display': 'block', 'marginBottom': '5px', 'fontWeight': '600',
                        }),
                        dcc.Dropdown(
                            id='percentile-driver-select',
                            placeholder='Select driver...',
                            style={'backgroundColor': COLORS['card_bg']},
                        ),
                    ]),
                    html.Div(
                        className='chart-container', style={'height': '340px'},
                        children=[dcc.Graph(id='percentile-radar', config={'displayModeBar': False})],
                    ),
                ]),
            ]),
        ]),
    ]),
])


# ============================================================================
# CALLBACKS
# ============================================================================

# File upload callback
@app.callback(
    [Output('stored-data', 'data'),
     Output('upload-status', 'children')],
    Input('upload-data', 'contents'),
    State('upload-data', 'filename')
)
def upload_file(contents, filename):
    if contents is None:
        raise PreventUpdate
    
    df, error = parse_upload_contents(contents, filename)
    
    if error:
        return None, html.Div(f'❌ {error}', style={'color': COLORS['header_gradient_start']})
    
    is_valid, message = validate_dataframe(df)
    if not is_valid:
        return None, html.Div(f'❌ {message}', style={'color': COLORS['header_gradient_start']})
    
    return df.to_json(date_format='iso', orient='split'), html.Div(f'✅ Loaded: {filename}', style={'color': '#7eff7a'})



# Dataset Metrics Callback
@app.callback(
    [Output('total-laps-value', 'children'),
     Output('drivers-count-value', 'children'),
     Output('fastest-lap-value', 'children')],
    Input('stored-data', 'data')
)
def update_metrics(stored_data):
    if not stored_data:
        return '--', '--', '--'
    
    df = pd.read_json(io.StringIO(stored_data), orient='split')
    summary = get_dataset_summary(df)
    
    return summary['total_laps'], summary['drivers_count'], summary['fastest_lap']



# Data preview callback
@app.callback(
    Output('data-preview-container', 'children'),
    Input('stored-data', 'data')
)
def update_data_preview(stored_data):
    if not stored_data:
        return html.Div('No data loaded', style={'color': COLORS['text_secondary'], 'textAlign': 'center', 'padding': '20px'})
    
    df = pd.read_json(io.StringIO(stored_data), orient='split')
    preview_df = df.head(10)
    
    return dash_table.DataTable(
        data=preview_df.to_dict('records'),
        columns=[{'name': col, 'id': col} for col in preview_df.columns],
        style_table={'overflowX': 'auto'},
        style_cell={
            'backgroundColor': COLORS['card_bg'],
            'color': COLORS['text_primary'],
            'border': f'1px solid {COLORS["border"]}',
            'textAlign': 'left',
            'padding': '10px',
            'fontSize': '12px',
        },
        style_header={
            'backgroundColor': COLORS['table_header'],
            'fontWeight': '700',
            'textTransform': 'uppercase',
            'fontSize': '11px',
            'letterSpacing': '0.05em',
        },
        style_data_conditional=[
            {
                'if': {'row_index': 'odd'},
                'backgroundColor': COLORS['table_row_odd'],
            },
            {
                'if': {'row_index': 'even'},
                'backgroundColor': COLORS['table_row_even'],
            },
        ],
    )


# Lap times chart and table callback
@app.callback(
    [Output('lap-times-chart', 'figure'),
     Output('lap-times-table-container', 'children')],
    Input('stored-data', 'data')
)
def update_lap_overview(stored_data):
    if not stored_data:
        empty_fig = go.Figure()
        empty_fig.update_layout(
            template='plotly_dark',
            paper_bgcolor=COLORS['card_bg'],
            plot_bgcolor=COLORS['card_bg'],
            xaxis={'visible': False},
            yaxis={'visible': False},
            annotations=[{
                'text': 'No data available',
                'xref': 'paper',
                'yref': 'paper',
                'showarrow': False,
                'font': {'size': 14, 'color': COLORS['text_secondary']}
            }]
        )
        return empty_fig, html.Div('No data', style={'color': COLORS['text_secondary']})
    
    df = pd.read_json(io.StringIO(stored_data), orient='split')
    df = compute_lap_times(df)
    
    # Get lap times summary
    lap_summary = df.groupby(['driver', 'lap'])['lap_time_ms'].first().reset_index()
    lap_summary['lap_time_s'] = lap_summary['lap_time_ms'] / 1000
    
    # Create bar chart
    fig = go.Figure()
    
    for i, driver in enumerate(lap_summary['driver'].unique()):
        driver_data = lap_summary[lap_summary['driver'] == driver]
        fig.add_trace(go.Bar(
            x=driver_data['lap'],
            y=driver_data['lap_time_s'],
            name=driver,
            marker_color=COLORS['series'][i % len(COLORS['series'])],
            hovertemplate='<b>%{fullData.name}</b><br>Lap %{x}<br>Time: %{y:.3f}s<extra></extra>',
        ))
    
    fig.update_layout(
        template='plotly_dark',
        paper_bgcolor=COLORS['card_bg'],
        plot_bgcolor=COLORS['card_bg'],
        font={'color': COLORS['text_secondary'], 'size': 11},
        xaxis={'title': 'Lap Number', 'gridcolor': COLORS['grid_line']},
        yaxis={'title': 'Lap Time (s)', 'gridcolor': COLORS['grid_line']},
        legend={'orientation': 'h', 'yanchor': 'bottom', 'y': 1.02, 'xanchor': 'right', 'x': 1},
        margin={'l': 50, 'r': 20, 't': 40, 'b': 50},
        barmode='group',
        hovermode='closest',
    )
    
    # Create table
    table = dash_table.DataTable(
        data=lap_summary.to_dict('records'),
        columns=[
            {'name': 'Driver', 'id': 'driver'},
            {'name': 'Lap', 'id': 'lap'},
            {'name': 'Time (s)', 'id': 'lap_time_s', 'type': 'numeric', 'format': {'specifier': '.3f'}},
        ],
        style_table={'overflowY': 'auto', 'maxHeight': '200px'},
        style_cell={
            'backgroundColor': COLORS['card_bg'],
            'color': COLORS['text_primary'],
            'border': f'1px solid {COLORS["border"]}',
            'textAlign': 'center',
            'padding': '8px',
            'fontSize': '12px',
        },
        style_header={
            'backgroundColor': COLORS['table_header'],
            'fontWeight': '700',
            'fontSize': '11px',
        },
        style_data_conditional=[
            {'if': {'row_index': 'odd'}, 'backgroundColor': COLORS['table_row_odd']},
            {'if': {'row_index': 'even'}, 'backgroundColor': COLORS['table_row_even']},
        ],
    )
    
    return fig, table


# Driver dropdown callback
@app.callback(
    [Output('driver-select', 'options'),
     Output('comparison-driver-select', 'options')],
    Input('stored-data', 'data')
)
def update_driver_dropdowns(stored_data):
    if not stored_data:
        return [], []
    
    df = pd.read_json(io.StringIO(stored_data), orient='split')
    drivers = sorted(df['driver'].unique())
    options = [{'label': driver, 'value': driver} for driver in drivers]
    
    return options, options


# Lap dropdown callback (for detail view)
@app.callback(
    Output('lap-select', 'options'),
    [Input('stored-data', 'data'),
     Input('driver-select', 'value')]
)
def update_lap_dropdown(stored_data, selected_driver):
    if not stored_data or not selected_driver:
        return []
    
    df = pd.read_json(io.StringIO(stored_data), orient='split')
    laps = sorted(df[df['driver'] == selected_driver]['lap'].unique())
    
    return [{'label': f'Lap {lap}', 'value': lap} for lap in laps]


# Lap detail charts callback
@app.callback(
    [Output('speed-trace-chart', 'figure'),
     Output('throttle-trace-chart', 'figure'),
     Output('brake-trace-chart', 'figure'),
     Output('rpm-trace-chart', 'figure')],
    [Input('stored-data', 'data'),
     Input('driver-select', 'value'),
     Input('lap-select', 'value')]
)
def update_lap_detail_charts(stored_data, selected_driver, selected_lap):
    empty_fig = go.Figure()
    empty_fig.update_layout(
        template='plotly_dark',
        paper_bgcolor=COLORS['card_bg'],
        plot_bgcolor=COLORS['card_bg'],
        xaxis={'visible': False},
        yaxis={'visible': False},
        annotations=[{
            'text': 'Waiting for data...',
            'xref': 'paper',
            'yref': 'paper',
            'showarrow': False,
            'font': {'size': 12, 'color': COLORS['text_secondary']}
        }]
    )
    
    # Check for valid selection
    if not stored_data or not selected_driver or selected_lap is None:
        return empty_fig, empty_fig, empty_fig, empty_fig
    
    df = pd.read_json(io.StringIO(stored_data), orient='split')
    lap_data = df[(df['driver'] == selected_driver) & (df['lap'] == selected_lap)].sort_values('time_stamp')
    
    if lap_data.empty:
        return empty_fig, empty_fig, empty_fig, empty_fig
    
    # Speed trace
    speed_fig = go.Figure()
    if 'speed_kph' in lap_data.columns:
        speed_fig.add_trace(go.Scatter(
            x=lap_data['time_stamp'],
            y=lap_data['speed_kph'],
            mode='lines',
            name='Speed',
            line={'color': COLORS['series'][0], 'width': 2},
            fill='tozeroy',
            fillcolor=f'rgba(255, 70, 84, 0.2)',
        ))
        speed_fig.update_layout(
            template='plotly_dark',
            paper_bgcolor=COLORS['card_bg'],
            plot_bgcolor=COLORS['card_bg'],
            font={'color': COLORS['text_secondary'], 'size': 10},
            title={'text': 'Speed (km/h)', 'font': {'size': 12}},
            xaxis={'title': 'Time (s)', 'gridcolor': COLORS['grid_line']},
            yaxis={'title': 'Speed', 'gridcolor': COLORS['grid_line'], 'range': [0, 360], 'fixedrange': True},
            margin={'l': 50, 'r': 20, 't': 40, 'b': 40},
            height=380,
        )
    else:
        # Placeholder for missing speed data
        speed_fig.update_layout(
            template='plotly_dark',
            paper_bgcolor=COLORS['card_bg'],
            plot_bgcolor=COLORS['card_bg'],
            xaxis={'visible': False},
            yaxis={'visible': False},
            annotations=[{
                'text': 'Speed data not available',
                'xref': 'paper',
                'yref': 'paper',
                'showarrow': False,
                'font': {'size': 12, 'color': COLORS['text_secondary']}
            }],
            height=380
        )
    
    # Throttle trace
    throttle_fig = go.Figure()
    if 'throttle_pct' in lap_data.columns:
        throttle_fig.add_trace(go.Scatter(
            x=lap_data['time_stamp'],
            y=lap_data['throttle_pct'],
            mode='lines',
            name='Throttle',
            line={'color': COLORS['series'][2], 'width': 2},
            fill='tozeroy',
            fillcolor=f'rgba(255, 181, 71, 0.2)',
        ))
    throttle_fig.update_layout(
        template='plotly_dark',
        paper_bgcolor=COLORS['card_bg'],
        plot_bgcolor=COLORS['card_bg'],
        font={'color': COLORS['text_secondary'], 'size': 10},
        title={'text': 'Throttle (%)', 'font': {'size': 12}},
        xaxis={'title': 'Time (s)', 'gridcolor': COLORS['grid_line']},
        yaxis={'title': 'Throttle', 'gridcolor': COLORS['grid_line'], 'range': [0, 105], 'fixedrange': True},
        margin={'l': 50, 'r': 20, 't': 40, 'b': 40},
    )
    
    # Brake trace
    brake_fig = go.Figure()
    if 'brake_pct' in lap_data.columns:
        brake_fig.add_trace(go.Scatter(
            x=lap_data['time_stamp'],
            y=lap_data['brake_pct'],
            mode='lines',
            name='Brake',
            line={'color': COLORS['series'][0], 'width': 2},
            fill='tozeroy',
            fillcolor=f'rgba(255, 70, 84, 0.2)',
        ))
    brake_fig.update_layout(
        template='plotly_dark',
        paper_bgcolor=COLORS['card_bg'],
        plot_bgcolor=COLORS['card_bg'],
        font={'color': COLORS['text_secondary'], 'size': 10},
        title={'text': 'Brake (%)', 'font': {'size': 12}},
        xaxis={'title': 'Time (s)', 'gridcolor': COLORS['grid_line']},
        yaxis={'title': 'Brake', 'gridcolor': COLORS['grid_line'], 'range': [0, 105], 'fixedrange': True},
        margin={'l': 50, 'r': 20, 't': 40, 'b': 40},
    )
    
    # RPM trace
    rpm_fig = go.Figure()
    if 'rpm' in lap_data.columns:
        rpm_fig.add_trace(go.Scatter(
            x=lap_data['time_stamp'],
            y=lap_data['rpm'],
            mode='lines',
            name='RPM',
            line={'color': COLORS['series'][1], 'width': 2},
        ))
    rpm_fig.update_layout(
        template='plotly_dark',
        paper_bgcolor=COLORS['card_bg'],
        plot_bgcolor=COLORS['card_bg'],
        font={'color': COLORS['text_secondary'], 'size': 10},
        title={'text': 'RPM', 'font': {'size': 12}},
        xaxis={'title': 'Time (s)', 'gridcolor': COLORS['grid_line']},
        yaxis={'title': 'RPM', 'gridcolor': COLORS['grid_line'], 'range': [5000, 14000], 'fixedrange': True},
        margin={'l': 50, 'r': 20, 't': 40, 'b': 40},
        height=200,
    )
    
    return speed_fig, throttle_fig, brake_fig, rpm_fig


# Lap comparison dropdowns callback
@app.callback(
    [Output('lap-a-select', 'options'),
     Output('lap-b-select', 'options')],
    [Input('stored-data', 'data'),
     Input('comparison-driver-select', 'value')]
)
def update_comparison_lap_dropdowns(stored_data, selected_driver):
    if not stored_data or not selected_driver:
        return [], []
    
    df = pd.read_json(io.StringIO(stored_data), orient='split')
    laps = sorted(df[df['driver'] == selected_driver]['lap'].unique())
    options = [{'label': f'Lap {lap}', 'value': lap} for lap in laps]
    
    return options, options


# Lap comparison chart callback
@app.callback(
    Output('lap-comparison-chart', 'figure'),
    [Input('stored-data', 'data'),
     Input('comparison-driver-select', 'value'),
     Input('lap-a-select', 'value'),
     Input('lap-b-select', 'value')]
)
def update_lap_comparison(stored_data, selected_driver, lap_a, lap_b):
    empty_fig = go.Figure()
    empty_fig.update_layout(
        template='plotly_dark',
        paper_bgcolor=COLORS['card_bg'],
        plot_bgcolor=COLORS['card_bg'],
        xaxis={'visible': False},
        yaxis={'visible': False},
        annotations=[{
            'text': 'Select driver and two laps to compare',
            'xref': 'paper',
            'yref': 'paper',
            'showarrow': False,
            'font': {'size': 14, 'color': COLORS['text_secondary']}
        }]
    )
    
    if not stored_data or not selected_driver or lap_a is None or lap_b is None:
        return empty_fig
    
    df = pd.read_json(io.StringIO(stored_data), orient='split')
    
    lap_a_data = df[(df['driver'] == selected_driver) & (df['lap'] == lap_a)].sort_values('time_stamp').copy()
    lap_b_data = df[(df['driver'] == selected_driver) & (df['lap'] == lap_b)].sort_values('time_stamp').copy()
    
    if lap_a_data.empty or lap_b_data.empty:
        return empty_fig
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=lap_a_data['time_stamp'],
        y=lap_a_data['speed_kph'],
        mode='lines',
        name=f'Lap {lap_a}',
        line={'color': COLORS['series'][0], 'width': 3},
    ))
    
    fig.add_trace(go.Scatter(
        x=lap_b_data['time_stamp'],
        y=lap_b_data['speed_kph'],
        mode='lines',
        name=f'Lap {lap_b}',
        line={'color': COLORS['series'][1], 'width': 3, 'dash': 'dash'},
    ))
    
    fig.update_layout(
        template='plotly_dark',
        paper_bgcolor=COLORS['card_bg'],
        plot_bgcolor=COLORS['card_bg'],
        font={'color': COLORS['text_secondary'], 'size': 11},
        title={'text': f'{selected_driver} - Speed Comparison', 'font': {'size': 14}},
        xaxis={'title': 'Time (s)', 'gridcolor': COLORS['grid_line']},
        yaxis={'title': 'Speed (km/h)', 'gridcolor': COLORS['grid_line'], 'range': [0, 360], 'fixedrange': True},
        legend={'orientation': 'h', 'yanchor': 'bottom', 'y': 1.02, 'xanchor': 'right', 'x': 1},
        margin={'l': 50, 'r': 20, 't': 60, 'b': 50},
        height=400,
        hovermode='x unified',
    )
    
    return fig


# Insights callback
@app.callback(
    Output('insights-content', 'children'),
    Input('stored-data', 'data')
)
def update_insights(stored_data):
    if not stored_data:
        return html.Div('No data available', style={'color': COLORS['text_secondary'], 'textAlign': 'center'})
    
    df = pd.read_json(io.StringIO(stored_data), orient='split')
    summary = get_dataset_summary(df)
    
    return html.Div([
        html.Div([
            icons.get_icon('trophy', size=32, color=COLORS['f1_gold']),
            html.Div(summary['fastest_lap'], style={'fontSize': '13px', 'color': COLORS['text_accent'], 'fontWeight': '600'}),
            html.Div('Fastest Lap', style={'fontSize': '11px', 'color': COLORS['text_secondary'], 'marginTop': '3px'}),
        ], style={'textAlign': 'center', 'marginBottom': '15px', 'padding': '10px', 'backgroundColor': 'rgba(71, 215, 255, 0.05)', 'borderRadius': '8px'}),
        
        html.Div([
            icons.get_icon('chart', size=32, color=COLORS['f1_cyan']),
            html.Div(summary['avg_lap_time'], style={'fontSize': '13px', 'color': COLORS['text_accent'], 'fontWeight': '600'}),
            html.Div('Average Lap Time', style={'fontSize': '11px', 'color': COLORS['text_secondary'], 'marginTop': '3px'}),
        ], style={'textAlign': 'center', 'marginBottom': '15px', 'padding': '10px', 'backgroundColor': 'rgba(71, 215, 255, 0.05)', 'borderRadius': '8px'}),
        
        html.Div([
            icons.get_icon('timer', size=32, color=COLORS['f1_red']),
            html.Div(summary['session_duration'], style={'fontSize': '13px', 'color': COLORS['text_accent'], 'fontWeight': '600'}),
            html.Div('Session Duration', style={'fontSize': '11px', 'color': COLORS['text_secondary'], 'marginTop': '3px'}),
        ], style={'textAlign': 'center', 'padding': '10px', 'backgroundColor': 'rgba(71, 215, 255, 0.05)', 'borderRadius': '8px'}),
    ])


# Sector heatmap callback
@app.callback(
    Output('sector-heatmap', 'figure'),
    Input('stored-data', 'data')
)
def update_sector_heatmap(stored_data):
    empty_fig = go.Figure()
    empty_fig.update_layout(
        template='plotly_dark',
        paper_bgcolor=COLORS['card_bg'],
        plot_bgcolor=COLORS['card_bg'],
        xaxis={'visible': False},
        yaxis={'visible': False},
        annotations=[{
            'text': 'No sector data available',
            'xref': 'paper',
            'yref': 'paper',
            'showarrow': False,
            'font': {'size': 12, 'color': COLORS['text_secondary']}
        }]
    )
    
    if not stored_data:
        return empty_fig
    
    df = pd.read_json(io.StringIO(stored_data), orient='split')
    
    if 'sector' not in df.columns:
        return empty_fig
    
    # Compute sector times
    sector_data = []
    for (driver, lap, sector), group in df.groupby(['driver', 'lap', 'sector']):
        sector_time = (group['time_stamp'].max() - group['time_stamp'].min()) * 1000
        sector_data.append({
            'driver': driver,
            'lap': lap,
            'sector': sector,
            'sector_time_ms': sector_time
        })
    
    sector_df = pd.DataFrame(sector_data)
    
    if sector_df.empty:
        return empty_fig
    
    # Create pivot table for heatmap
    pivot = sector_df.pivot_table(
        values='sector_time_ms',
        index='lap',
        columns='sector',
        aggfunc='mean'
    )
    
    fig = go.Figure(data=go.Heatmap(
        z=pivot.values,
        x=[f'S{int(col)}' for col in pivot.columns],
        y=pivot.index,
        colorscale=[[0, '#003b8f'], [0.5, '#00c853'], [1, '#ff6d00']],
        hovertemplate='Lap %{y}<br>%{x}<br>Time: %{z:.0f}ms<extra></extra>',
    ))
    
    fig.update_layout(
        template='plotly_dark',
        paper_bgcolor=COLORS['card_bg'],
        plot_bgcolor=COLORS['card_bg'],
        font={'color': COLORS['text_secondary'], 'size': 10},
        xaxis={'title': 'Sector', 'side': 'bottom'},
        yaxis={'title': 'Lap'},
        margin={'l': 50, 'r': 20, 't': 20, 'b': 50},
    )
    
    return fig




# ============================================================================
# TRACK MAP & LAP DELTA CALLBACKS
# ============================================================================

# Lap dropdown population for delta analysis
@app.callback(
    [Output('delta-lap-a-select', 'options'),
     Output('delta-lap-b-select', 'options')],
    [Input('stored-data', 'data'),
     Input('comparison-driver-select', 'value')]
)
def update_delta_lap_dropdowns(stored_data, selected_driver):
    if not stored_data or not selected_driver:
        return [], []
    
    df = pd.read_json(io.StringIO(stored_data), orient='split')
    laps = sorted(df[df['driver'] == selected_driver]['lap'].unique())
    options = [{'label': f'Lap {lap}', 'value': lap} for lap in laps]
    
    return options, options


# Track map generation callback
@app.callback(
    Output('track-map-chart', 'figure'),
    [Input('stored-data', 'data'),
     Input('driver-select', 'value'),
     Input('lap-select', 'value'),
     Input('distance-slider', 'value')]
)
def update_track_map(stored_data, selected_driver, selected_lap, slider_value):
    empty_fig = go.Figure()
    empty_fig.update_layout(
        template='plotly_dark',
        paper_bgcolor=COLORS['card_bg'],
        plot_bgcolor=COLORS['card_bg'],
        xaxis={'visible': False},
        yaxis={'visible': False},
        annotations=[{
            'text': 'Select driver and lap to view track map',
            'xref': 'paper',
            'yref': 'paper',
            'showarrow': False,
            'font': {'size': 14, 'color': COLORS['text_secondary']}
        }]
    )
    
    
    if not stored_data or not selected_driver or selected_lap is None:
        return empty_fig

    # Optimize: If Live Mode is active, we STILL need the track map as background.
    # But if we knew for sure the track map hasn't changed...
    # For now, we proceed to load it, but we could cache it.
    
    # Parse Data
    try:
        # Avoid full parse if possible? No, need coords.
        df = pd.read_json(io.StringIO(stored_data), orient='split')
        lap_data = df[(df['driver'] == selected_driver) & (df['lap'] == selected_lap)].sort_values('time_stamp').copy()
    except Exception:
         return empty_fig

    if lap_data.empty:
        return empty_fig
    
    # Check if GPS coordinates or Speed (for distance calc) are available
    # If speed is missing, compute_distance_along_lap returns df without dist_along_lap, 
    # and normalize_track_coordinates might fail or return just x_coord/y_coord if GPS exists.
    
    use_gps = 'lat' in lap_data.columns and 'long' in lap_data.columns
    
    # helper function attempts to use distance if GPS missing
    try:
        lap_data = tu.normalize_track_coordinates(lap_data, use_gps=use_gps)
    except Exception:
        # Fallback if normalization fails (e.g. no distance and no GPS)
        pass
    
    if 'x_coord' not in lap_data.columns:
        empty_fig.layout.annotations[0]['text'] = 'No GPS or Speed data available for track map'
        return empty_fig
    fig = go.Figure()
    
    # Add track line
    fig.add_trace(go.Scatter(
        x=lap_data['x_coord'],
        y=lap_data['y_coord'],
        mode='lines',
        name='Track',
        line={'color': COLORS['text_secondary'], 'width': 3},
        hoverinfo='skip'
    ))
    
    # Add car marker
    current_x, current_y, speed_val = 0, 0, 0
    show_marker = False
    
    # Static mode - use slider value
    if slider_value is not None and not lap_data.empty:
        max_idx = len(lap_data) - 1
        current_idx = int((slider_value / 100) * max_idx)
        current_point = lap_data.iloc[current_idx]
        current_x = current_point['x_coord']
        current_y = current_point['y_coord']
        speed_val = current_point.get("speed_kph", 0)
        show_marker = True
    
    # Add current position marker
    if show_marker:
        fig.add_trace(go.Scatter(
            x=[current_x],
            y=[current_y],
            mode='markers',
            name='Car Position',
            marker={
                'size': 15,
                'color': COLORS['header_gradient_start'],
                'symbol': 'circle',
                'line': {'width': 2, 'color': '#ffffff'}
            },
            hovertemplate=f'Speed: {speed_val:.1f} km/h<extra></extra>'
        ))

    
    fig.update_layout(
        template='plotly_dark',
        paper_bgcolor=COLORS['card_bg'],
        plot_bgcolor=COLORS['card_bg'],
        font={'color': COLORS['text_secondary'], 'size': 11},
        title={'text': f'{selected_driver} - Lap {selected_lap} Track Map', 'font': {'size': 14}},
        xaxis={
            'title': '',
            'showgrid': False,
            'zeroline': False,
            'showticklabels': False,
            'scaleanchor': 'y',
            'scaleratio': 1
        },
        yaxis={
            'title': '',
            'showgrid': False,
            'zeroline': False,
            'showticklabels': False
        },
        showlegend=False,
        margin={'l': 20, 'r': 20, 't': 40, 'b': 20},
        hovermode='closest'
    )
    
    return fig


# Animation control callbacks
@app.callback(
    Output('animation-interval', 'disabled'),
    [Input('animation-play-btn', 'n_clicks'),
     Input('animation-pause-btn', 'n_clicks')],
    [State('animation-interval', 'disabled')]
)
def control_animation(play_clicks, pause_clicks, current_state):
    if not play_clicks and not pause_clicks:
        raise PreventUpdate
    
    # Determine which button was clicked
    ctx = dash.callback_context
    if not ctx.triggered:
        raise PreventUpdate
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if button_id == 'animation-play-btn':
        return False  # Enable interval (start animation)
    elif button_id == 'animation-pause-btn':
        return True  # Disable interval (pause animation)
    
    return current_state


@app.callback(
    Output('distance-slider', 'value'),
    [Input('animation-interval', 'n_intervals')],
    [State('distance-slider', 'value'),
     State('animation-interval', 'disabled')]
)
def animate_slider(n_intervals, current_value, is_paused):
    if is_paused or n_intervals is None:
        raise PreventUpdate
    
    # Increment slider by 1% each interval
    new_value = (current_value + 1) % 101
    return new_value


# Lap delta computation callback
@app.callback(
    Output('delta-plot-chart', 'figure'),
    [Input('stored-data', 'data'),
     Input('comparison-driver-select', 'value'),
     Input('delta-lap-a-select', 'value'),
     Input('delta-lap-b-select', 'value')]
)
def update_delta_plot(stored_data, selected_driver, lap_a, lap_b):
    empty_fig = go.Figure()
    empty_fig.update_layout(
        template='plotly_dark',
        paper_bgcolor=COLORS['card_bg'],
        plot_bgcolor=COLORS['card_bg'],
        xaxis={'visible': False},
        yaxis={'visible': False},
        annotations=[{
            'text': 'Select driver and two laps for delta analysis',
            'xref': 'paper',
            'yref': 'paper',
            'showarrow': False,
            'font': {'size': 12, 'color': COLORS['text_secondary']}
        }]
    )
    
    if not stored_data or not selected_driver or lap_a is None or lap_b is None:
        return empty_fig
    
    if lap_a == lap_b:
        empty_fig.layout.annotations[0]['text'] = 'Please select two different laps'
        return empty_fig
    
    df = pd.read_json(io.StringIO(stored_data), orient='split')
    
    lap_a_data = df[(df['driver'] == selected_driver) & (df['lap'] == lap_a)].sort_values('time_stamp').copy()
    lap_b_data = df[(df['driver'] == selected_driver) & (df['lap'] == lap_b)].sort_values('time_stamp').copy()
    
    if lap_a_data.empty or lap_b_data.empty:
        return empty_fig
    
    # Compute lap delta
    delta_df = tu.compute_lap_delta(lap_a_data, lap_b_data, num_points=200)
    
    if delta_df.empty:
        empty_fig.layout.annotations[0]['text'] = 'Unable to compute delta'
        return empty_fig
    
    # Create delta plot with color coding
    fig = go.Figure()
    
    # Add delta line
    fig.add_trace(go.Scatter(
        x=delta_df['distance'],
        y=delta_df['delta_ms'],
        mode='lines',
        name='Delta',
        line={'color': COLORS['text_accent'], 'width': 2},
        fill='tozeroy',
        fillcolor='rgba(71, 215, 255, 0.2)',
        hovertemplate='Distance: %{x:.0f}m<br>Delta: %{y:.0f}ms<extra></extra>'
    ))
    
    # Add zero line
    fig.add_hline(
        y=0,
        line_dash='dash',
        line_color=COLORS['text_secondary'],
        line_width=1,
        annotation_text='No difference',
        annotation_position='right'
    )
    
    # Color-code regions
    for i in range(len(delta_df) - 1):
        color = '#7eff7a' if delta_df.iloc[i]['delta_ms'] < 0 else '#ff4654'
        fig.add_shape(
            type='rect',
            x0=delta_df.iloc[i]['distance'],
            x1=delta_df.iloc[i + 1]['distance'],
            y0=0,
            y1=delta_df.iloc[i]['delta_ms'],
            fillcolor=color,
            opacity=0.3,
            line_width=0
        )
    
    fig.update_layout(
        template='plotly_dark',
        paper_bgcolor=COLORS['card_bg'],
        plot_bgcolor=COLORS['card_bg'],
        font={'color': COLORS['text_secondary'], 'size': 10},
        title={
            'text': f'Lap {lap_b} vs Lap {lap_a} - Time Delta',
            'font': {'size': 12}
        },
        xaxis={
            'title': 'Distance (m)',
            'gridcolor': COLORS['grid_line']
        },
        yaxis={
            'title': 'Delta (ms)',
            'gridcolor': COLORS['grid_line'],
            'zeroline': True,
            'zerolinecolor': COLORS['text_secondary']
        },
        margin={'l': 50, 'r': 20, 't': 40, 'b': 40},
        hovermode='x unified'
    )
    
    return fig


# Delta summary callback
@app.callback(
    Output('delta-summary-card', 'children'),
    [Input('stored-data', 'data'),
     Input('comparison-driver-select', 'value'),
     Input('delta-lap-a-select', 'value'),
     Input('delta-lap-b-select', 'value')]
)
def update_delta_summary(stored_data, selected_driver, lap_a, lap_b):
    if not stored_data or not selected_driver or lap_a is None or lap_b is None or lap_a == lap_b:
        return html.Div()
    
    df = pd.read_json(io.StringIO(stored_data), orient='split')
    
    lap_a_data = df[(df['driver'] == selected_driver) & (df['lap'] == lap_a)].sort_values('time_stamp').copy()
    lap_b_data = df[(df['driver'] == selected_driver) & (df['lap'] == lap_b)].sort_values('time_stamp').copy()
    
    if lap_a_data.empty or lap_b_data.empty:
        return html.Div()
    
    # Compute total lap time difference
    lap_a_time = lap_a_data['time_stamp'].max() - lap_a_data['time_stamp'].min()
    lap_b_time = lap_b_data['time_stamp'].max() - lap_b_data['time_stamp'].min()
    total_delta = (lap_b_time - lap_a_time) * 1000  # in ms
    
    # Determine if gain or loss
    delta_type = 'Faster' if total_delta < 0 else 'Slower'
    delta_color = '#7eff7a' if total_delta < 0 else '#ff4654'
    
    return html.Div(style={
        'backgroundColor': 'rgba(71, 215, 255, 0.05)',
        'borderRadius': '8px',
        'padding': '15px',
        'textAlign': 'center'
    }, children=[
        html.Div('Total Lap Delta', style={
            'fontSize': '11px',
            'color': COLORS['text_secondary'],
            'marginBottom': '8px',
            'textTransform': 'uppercase',
            'letterSpacing': '0.05em'
        }),
        html.Div(f'{abs(total_delta):.0f} ms', style={
            'fontSize': '24px',
            'fontWeight': '700',
            'color': delta_color,
            'fontFamily': 'Orbitron, sans-serif'
        }),
        html.Div(f'Lap {lap_b} is {delta_type}', style={
            'fontSize': '12px',
            'color': COLORS['text_secondary'],
            'marginTop': '5px'
        })
    ])


# Corner statistics callback
@app.callback(
    Output('corner-stats-card', 'children'),
    [Input('stored-data', 'data'),
     Input('comparison-driver-select', 'value'),
     Input('delta-lap-a-select', 'value'),
     Input('delta-lap-b-select', 'value')]
)
def update_corner_stats(stored_data, selected_driver, lap_a, lap_b):
    if not stored_data or not selected_driver or lap_a is None or lap_b is None or lap_a == lap_b:
        return html.Div()
    
    df = pd.read_json(io.StringIO(stored_data), orient='split')
    
    lap_a_data = df[(df['driver'] == selected_driver) & (df['lap'] == lap_a)].sort_values('time_stamp').copy()
    lap_b_data = df[(df['driver'] == selected_driver) & (df['lap'] == lap_b)].sort_values('time_stamp').copy()
    
    if lap_a_data.empty or lap_b_data.empty:
        return html.Div()
    
    # Auto-detect corners
    corners = tu.find_corner_zones(lap_a_data, speed_threshold=200, min_duration=1.0)
    
    if not corners:
        return html.Div('No corners detected', style={
            'fontSize': '11px',
            'color': COLORS['text_secondary'],
            'textAlign': 'center',
            'padding': '10px'
        })
    
    # Compute delta
    delta_df = tu.compute_lap_delta(lap_a_data, lap_b_data, num_points=200)
    
    if delta_df.empty:
        return html.Div()
    
    # Compute corner deltas
    corner_deltas = tu.compute_corner_deltas(delta_df, corners)
    
    # Sort by magnitude
    corner_deltas.sort(key=lambda x: abs(x['delta_ms']), reverse=True)
    
    # Get top 3
    top_corners = corner_deltas[:3]
    
    return html.Div(style={
        'backgroundColor': 'rgba(71, 215, 255, 0.05)',
        'borderRadius': '8px',
        'padding': '12px'
    }, children=[
        html.Div('Top Corner Deltas', style={
            'fontSize': '11px',
            'color': COLORS['text_secondary'],
            'marginBottom': '10px',
            'textTransform': 'uppercase',
            'letterSpacing': '0.05em',
            'fontWeight': '600'
        }),
        html.Div([
            html.Div(style={
                'display': 'flex',
                'justifyContent': 'space-between',
                'alignItems': 'center',
                'padding': '8px',
                'marginBottom': '5px',
                'backgroundColor': COLORS['card_bg'],
                'borderRadius': '6px',
                'borderLeft': f'3px solid {"#7eff7a" if c["type"] == "gain" else "#ff4654"}'
            }, children=[
                html.Div(c['name'], style={
                    'fontSize': '12px',
                    'color': COLORS['text_primary'],
                    'fontWeight': '600'
                }),
                html.Div(f'{abs(c["delta_ms"]):.0f} ms', style={
                    'fontSize': '12px',
                    'color': '#7eff7a' if c['type'] == 'gain' else '#ff4654',
                    'fontWeight': '700'
                })
            ]) for c in top_corners
        ])
    ])


# ============================================================================
# ANALYTICS LAB CALLBACKS
# ============================================================================

# Populate percentile driver dropdown (reuse data from stored-data)
@app.callback(
    Output('percentile-driver-select', 'options'),
    Input('stored-data', 'data')
)
def update_percentile_driver_options(stored_data):
    if not stored_data:
        return []
    df = pd.read_json(io.StringIO(stored_data), orient='split')
    drivers = sorted(df['driver'].unique())
    return [{'label': d, 'value': d} for d in drivers]


# 1. Correlation Heatmap
@app.callback(
    Output('correlation-heatmap', 'figure'),
    Input('stored-data', 'data')
)
def update_correlation_heatmap(stored_data):
    fig = go.Figure()
    base_layout = dict(
        template='plotly_dark',
        paper_bgcolor=COLORS['card_bg'],
        plot_bgcolor=COLORS['card_bg'],
        font={'color': COLORS['text_secondary'], 'size': 10},
        margin={'l': 60, 'r': 20, 't': 20, 'b': 60},
    )

    if not stored_data:
        fig.update_layout(**base_layout)
        return fig

    df = pd.read_json(io.StringIO(stored_data), orient='split')
    corr = compute_correlation_matrix(df)
    if corr.empty:
        fig.update_layout(**base_layout)
        return fig

    # Readable labels
    labels = [c.replace('_', ' ').title() for c in corr.columns]

    fig = go.Figure(data=go.Heatmap(
        z=corr.values,
        x=labels,
        y=labels,
        colorscale=[
            [0.0, '#E10600'],   # F1 Red (Negative)
            [0.2, '#8a1c19'],
            [0.5, '#15151e'],   # Neutral (Dark)
            [0.8, '#009081'],
            [1.0, '#00D2BE'],   # F1 Cyan (Positive)
        ],
        zmin=-1, zmax=1,
        text=corr.values.round(2),
        texttemplate='%{text}',
        textfont={'size': 11, 'color': '#ffffff', 'family': 'Fira Code, monospace'},
        hovertemplate='<b>%{x}</b> vs <b>%{y}</b><br>Correlation: %{z:.3f}<extra></extra>',
        xgap=1, ygap=1,  # Pro Max: Add distinct cell separation
        colorbar=dict(
            title='Correlation', titlefont={'size': 10}, titleside='right', thickness=10,
            tickfont={'color': COLORS['text_secondary'], 'size': 9},
            len=0.7, y=0.5, yanchor='middle',  # Pro Max:Centered and compact
        ),
    ))
    fig.update_layout(**base_layout, height=370, title={'text': 'Pearson Correlation', 'font': {'size': 12}})
    return fig


# 2. Consistency Metrics
@app.callback(
    [Output('consistency-chart', 'figure'),
     Output('consistency-metric-cards', 'children')],
    Input('stored-data', 'data')
)
def update_consistency_metrics(stored_data):
    empty_fig = go.Figure()
    empty_fig.update_layout(
        template='plotly_dark',
        paper_bgcolor=COLORS['card_bg'],
        plot_bgcolor=COLORS['card_bg'],
    )
    if not stored_data:
        return empty_fig, []

    df = pd.read_json(io.StringIO(stored_data), orient='split')
    stats = compute_consistency_scores(df)
    if stats.empty:
        return empty_fig, []

    # Metric cards
    cards = []
    for _, row in stats.iterrows():
        score = row['consistency_score']
        # Color logic: 90+ Cyan, 80+ Green, <80 Red/Orange
        if score >= 90:
            color = COLORS['f1_cyan'] 
        elif score >= 80:
            color = '#2ecc71'
        else:
            color = '#e10600'
            
        cards.append(html.Div(style={
            'backgroundColor': '#1a1a1a', 
            'borderRadius': '6px', 
            'padding': '12px',
            'flex': '1', 
            'minWidth': '100px', 
            'textAlign': 'center',
            'borderTop': f'2px solid {color}',
            'boxShadow': '0 4px 6px rgba(0,0,0,0.3)'
        }, children=[
            html.Div(row['driver'], style={
                'fontSize': '14px', 'fontWeight': '700', 'color': '#ffffff',
                'fontFamily': 'Orbitron, sans-serif', 'marginBottom': '4px',
            }),
            html.Div(f'{score:.1f}', style={
                'fontSize': '24px', 'fontWeight': '700', 'color': color, 'lineHeight': '1.1',
            }),
            html.Div('SCORE', style={
                'fontSize': '9px', 'color': COLORS['text_muted'],
                'fontWeight': '600', 'marginTop': '4px',
            }),
        ]))

    # Bar chart — coefficient of variation
    fig = go.Figure()
    bar_colors = [COLORS['f1_cyan'] if s >= 90 else ('#2ecc71' if s >= 80 else '#e10600')
                  for s in stats['consistency_score']]
                  
    fig.add_trace(go.Bar(
        x=stats['driver'],
        y=stats['cv_pct'],
        marker_color=bar_colors,
        text=stats['cv_pct'].apply(lambda v: f'{v:.2f}%'),
        textposition='auto',
        textfont={'color': '#ffffff', 'size': 10},
        hovertemplate='<b>%{x}</b><br>CoV: %{y:.2f}%<br>Score: %{customdata:.1f}<extra></extra>',
        customdata=stats['consistency_score']
    ))
    # Pro Max: Reference line for "Elite" consistency
    fig.add_shape(
        type='line', x0=-0.5, x1=len(stats['driver'])-0.5, y0=90, y1=90,
        line=dict(color='rgba(0, 210, 190, 0.5)', width=1, dash='dash'),
        name='Elite Threshold'
    )
    fig.add_annotation(
        x=len(stats['driver'])-0.5, y=90, text='ELITE', showarrow=False,
        xanchor='right', yanchor='bottom', font=dict(color='rgba(0, 210, 190, 0.5)', size=9)
    )

    fig.update_layout(
        template='plotly_dark',
        paper_bgcolor=COLORS['card_bg'],
        plot_bgcolor=COLORS['card_bg'],
        font={'color': COLORS['text_secondary'], 'size': 10},
        xaxis={'title': '', 'gridcolor': 'rgba(255,255,255,0.05)', 'tickfont': {'size': 11, 'family': 'Orbitron'}},
        yaxis={'title': 'Consistency Score', 'gridcolor': 'rgba(255,255,255,0.05)', 'zeroline': False, 'range': [0, 105]},
        margin={'l': 50, 'r': 20, 't': 10, 'b': 30},
        height=270,
        bargap=0.4,
    )
    return fig, cards


# 3. Distribution Chart (Violin + Box)
@app.callback(
    Output('distribution-chart', 'figure'),
    [Input('stored-data', 'data'),
     Input('distribution-column-select', 'value')]
)
def update_distribution_chart(stored_data, column):
    fig = go.Figure()
    base_layout = dict(
        template='plotly_dark',
        paper_bgcolor=COLORS['card_bg'],
        plot_bgcolor=COLORS['card_bg'],
        font={'color': COLORS['text_secondary'], 'size': 10},
        margin={'l': 50, 'r': 30, 't': 30, 'b': 50},
        height=390,
    )
    if not stored_data or not column:
        fig.update_layout(**base_layout)
        return fig

    df = pd.read_json(io.StringIO(stored_data), orient='split')
    if column not in df.columns:
        fig.update_layout(**base_layout)
        return fig

    drivers = sorted(df['driver'].unique())
    colors = COLORS['series']

    for i, driver in enumerate(drivers):
        series = df.loc[df['driver'] == driver, column].dropna()
        color = colors[i % len(colors)]
        fig.add_trace(go.Violin(
            y=series,
            name=driver,
            box_visible=True,
            meanline_visible=True,
            line_color=color,
            fillcolor=f'rgba{tuple(list(int(color.lstrip("#")[j:j+2], 16) for j in (0, 2, 4)) + [0.15])}',
            points='outliers',
            marker={'color': color, 'size': 3},
            hoverinfo='y+name',
        ))

    label = column.replace('_', ' ').title()
    fig.update_layout(
        **base_layout,
        title={'text': f'{label} Distribution', 'font': {'size': 12}},
        yaxis={'title': label, 'gridcolor': COLORS['grid_line'], 'zerolinecolor': COLORS['grid_line']},
        xaxis={'title': '', 'gridcolor': COLORS['grid_line']},
        showlegend=False,
        violinmode='group',
        violingap=0.3,
    )
    return fig


# 4. Rolling Stats
@app.callback(
    Output('rolling-stats-chart', 'figure'),
    [Input('stored-data', 'data'),
     Input('driver-select', 'value'),
     Input('lap-select', 'value'),
     Input('rolling-window-slider', 'value')]
)
def update_rolling_stats(stored_data, driver, lap, window):
    fig = go.Figure()
    base_layout = dict(
        template='plotly_dark',
        paper_bgcolor=COLORS['card_bg'],
        plot_bgcolor=COLORS['card_bg'],
        font={'color': COLORS['text_secondary'], 'size': 10},
        margin={'l': 50, 'r': 20, 't': 30, 'b': 50},
        height=370,
    )
    if not stored_data or not driver:
        fig.update_layout(**base_layout)
        return fig

    df = pd.read_json(io.StringIO(stored_data), orient='split')
    rolled = compute_rolling_stats(df, driver, lap, window or 20)
    if rolled.empty:
        fig.update_layout(**base_layout)
        return fig

    channels = [
        ('speed_kph', 'Speed (km/h)', COLORS['series'][0]),
        ('throttle_pct', 'Throttle (%)', COLORS['series'][2]),
        ('brake_pct', 'Brake (%)', COLORS['series'][1]),
    ]

    for col, label, color in channels:
        if col not in rolled.columns:
            continue
        # Raw (faint)
        fig.add_trace(go.Scatter(
            x=rolled['time_stamp'], y=rolled[col],
            mode='lines', name=f'{label} (raw)',
            line={'color': color, 'width': 1},
            opacity=0.15, showlegend=False,
            hoverinfo='skip'
        ))
        # Moving average (bold)
        ma_col = f'{col}_ma'
        if ma_col in rolled.columns:
            fig.add_trace(go.Scatter(
                x=rolled['time_stamp'], y=rolled[ma_col],
                mode='lines', name=label,
                line={'color': color, 'width': 2},
                hovertemplate=f'{label}: %{{y:.1f}}<extra></extra>'
            ))

    fig.update_layout(
        **base_layout,
        title={'text': f'{driver} — Moving Average (window={window})', 'font': {'size': 12}},
        xaxis={
            'title': 'Time (seconds)', 
            'gridcolor': 'rgba(255,255,255,0.05)', 'zerolinecolor': 'rgba(255,255,255,0.05)',
            'rangeslider': {'visible': False}, # Pro Max: Clean look, rely on zoom
        },
        yaxis={'gridcolor': 'rgba(255,255,255,0.05)', 'zerolinecolor': 'rgba(255,255,255,0.05)'},
        legend={'orientation': 'h', 'y': 1.02, 'x': 1, 'xanchor': 'right', 'bgcolor': 'rgba(0,0,0,0)',
                'font': {'size': 9, 'color': COLORS['text_secondary']}},
        hovermode='x unified',
    )
    return fig


# 5. Percentile Radar
@app.callback(
    Output('percentile-radar', 'figure'),
    [Input('stored-data', 'data'),
     Input('percentile-driver-select', 'value')]
)
def update_percentile_radar(stored_data, driver):
    fig = go.Figure()
    base_layout = dict(
        template='plotly_dark',
        paper_bgcolor=COLORS['card_bg'],
        plot_bgcolor=COLORS['card_bg'],
        font={'color': COLORS['text_secondary'], 'size': 10},
        margin={'l': 50, 'r': 50, 't': 30, 'b': 30},
        height=330,
    )
    if not stored_data or not driver:
        fig.update_layout(**base_layout)
        return fig

    df = pd.read_json(io.StringIO(stored_data), orient='split')
    profile = compute_percentile_profile(df, driver)
    if not profile:
        fig.update_layout(**base_layout)
        return fig

    labels = [k.replace('_', ' ').title() for k in profile.keys()]
    values = list(profile.values())
    # Close the polygon
    labels += [labels[0]]
    values += [values[0]]

    fig.add_trace(go.Scatterpolar(
        r=values,
        theta=labels,
        fill='toself',
        fillcolor=f'rgba(0, 210, 190, 0.2)',
        line={'color': COLORS['f1_cyan'], 'width': 2.5},
        marker={'size': 5, 'color': '#ffffff', 'line': {'color': COLORS['f1_cyan'], 'width': 1}},
        name=driver,
        hovertemplate='<b>%{theta}</b><br>Percentile: %{r:.0f}<extra></extra>',
    ))

    fig.update_layout(
        **base_layout,
        title={'text': f'{driver} Performance Profile', 'font': {'size': 12}},
        polar=dict(
            bgcolor=COLORS['card_bg'],
            radialaxis=dict(
                visible=True, range=[0, 100],
                gridcolor='rgba(255,255,255,0.08)',
                linecolor='rgba(0,0,0,0)', # Hide axis line, keep grid
                tickfont={'size': 8, 'color': COLORS['text_muted']},
                ticks='', # Clean ticks
            ),
            angularaxis=dict(
                gridcolor='rgba(255,255,255,0.15)', # Brighter angular grid
                linecolor='rgba(255,255,255,0.15)',
                tickfont={'size': 9, 'color': COLORS['text_primary'], 'family': 'Orbitron', 'weight': 700},
                rotation=0, # Rotate to align
            ),
        ),
        showlegend=False,
    )
    return fig


# ============================================================================
# RUN APP
# ============================================================================

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=8050)


