"""
F1 Telemetry Dashboard
A Dash web application for analyzing Formula 1 telemetry data
"""

import base64
import io
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from dash import Dash, dcc, html, Input, Output, State, dash_table
from dash.exceptions import PreventUpdate

# Initialize the Dash app
app = Dash(__name__, suppress_callback_exceptions=True)
app.title = "F1 Telemetry Dashboard"

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def validate_dataframe(df):
    """Validate that the uploaded DataFrame has required columns"""
    required_columns = ['driver', 'lap', 'time_stamp', 'speed_kph']
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


# ============================================================================
# STYLING
# ============================================================================

# F1 Dark Theme Colors
COLORS = {
    'background': '#050913',
    'card_bg': '#0c101c',
    'header_gradient_start': '#e3262f',
    'header_gradient_end': '#0070ff',
    'text_primary': '#ffffff',
    'text_secondary': '#b3bedc',
    'text_accent': '#47d7ff',
    'grid_line': '#1b2538',
    'border': '#1c2840',
    'series': ['#ff4654', '#00c0ff', '#ffb547', '#7eff7a', '#b66bff'],
    'table_header': '#121829',
    'table_row_even': '#0a0f1a',
    'table_row_odd': '#050913',
    'table_hover': '#151e31',
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
                background-color: #050913;
                color: #ffffff;
                margin: 0;
                padding: 0;
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
                background: #0c101c;
            }
            
            ::-webkit-scrollbar-thumb {
                background: #1c2840;
                border-radius: 5px;
            }
            
            ::-webkit-scrollbar-thumb:hover {
                background: #2a3a5a;
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

METRIC_STYLE = {
    'textAlign': 'center',
    'padding': '15px',
}

METRIC_VALUE_STYLE = {
    'fontSize': '28px',
    'fontWeight': '700',
    'color': COLORS['text_accent'],
    'fontFamily': 'Orbitron, sans-serif',
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
    dcc.Store(id='stored-data'),
    
    # Header
    html.Div(style={
        'background': f'linear-gradient(90deg, {COLORS["header_gradient_start"]} 0%, {COLORS["header_gradient_end"]} 100%)',
        'height': '90px',
        'display': 'flex',
        'alignItems': 'center',
        'justifyContent': 'center',
        'marginBottom': '30px',
        'boxShadow': '0 4px 12px rgba(227, 38, 47, 0.3)',
    }, children=[
        html.Div(children=[
            html.H1('F1 TELEMETRY DASHBOARD', style={
                'fontSize': '32px',
                'fontWeight': '900',
                'color': '#ffffff',
                'margin': '0',
                'fontFamily': 'Orbitron, sans-serif',
                'letterSpacing': '0.1em',
            }),
            html.P('Upload telemetry and explore laps, sectors, and performance', style={
                'fontSize': '14px',
                'color': '#c0d4ff',
                'margin': '5px 0 0 0',
                'fontWeight': '300',
            }),
        ]),
    ]),
    
    # Main container
    html.Div(style={'padding': '0 30px 30px 30px', 'maxWidth': '1800px', 'margin': '0 auto'}, children=[
        
        # Top band: Upload + Summary + Lap Overview
        html.Div(style={'display': 'grid', 'gridTemplateColumns': '32% 22% 46%', 'gap': '20px', 'marginBottom': '20px'}, children=[
            
            # Upload card
            html.Div(style=CARD_STYLE, children=[
                html.Div('Upload & Summary', style=SECTION_TITLE_STYLE),
                dcc.Upload(
                    id='upload-data',
                    children=html.Div([
                        html.Div('🏎️', style={'fontSize': '48px', 'marginBottom': '10px'}),
                        html.Div('Drag and Drop or ', style={'fontSize': '14px'}),
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
            html.Div(style=CARD_STYLE, children=[
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
                html.Div(style=CARD_STYLE, children=[
                    html.Div('Lap Overview', style=SECTION_TITLE_STYLE),
                    dcc.Graph(id='lap-times-chart', config={'displayModeBar': False}, style={'height': '250px'}),
                ]),
                html.Div(style=CARD_STYLE, children=[
                    html.Div('Lap Times Table', style=SECTION_TITLE_STYLE),
                    html.Div(id='lap-times-table-container'),
                ]),
            ]),
        ]),
        
        # Data preview
        html.Div(style=CARD_STYLE, children=[
            html.Div('Data Preview', style=SECTION_TITLE_STYLE),
            html.Div(id='data-preview-container'),
        ]),
        
        # Lap detail section
        html.Div(style=CARD_STYLE, children=[
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
                dcc.Graph(id='speed-trace-chart', config={'displayModeBar': False}),
                html.Div(children=[
                    dcc.Graph(id='throttle-trace-chart', config={'displayModeBar': False}, style={'height': '180px'}),
                    dcc.Graph(id='brake-trace-chart', config={'displayModeBar': False}, style={'height': '180px'}),
                ]),
            ]),
            dcc.Graph(id='rpm-trace-chart', config={'displayModeBar': False}),
        ]),
        
        # Bottom band: Lap comparison + Insights
        html.Div(style={'display': 'grid', 'gridTemplateColumns': '60% 40%', 'gap': '20px'}, children=[
            
            # Lap comparison
            html.Div(style=CARD_STYLE, children=[
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
                dcc.Graph(id='lap-comparison-chart', config={'displayModeBar': False}, style={'height': '450px'}),
            ]),
            
            # Insights and sectors
            html.Div(children=[
                html.Div(style=CARD_STYLE, children=[
                    html.Div('Session Insights', style=SECTION_TITLE_STYLE),
                    html.Div(id='insights-content'),
                ]),
                html.Div(style=CARD_STYLE, children=[
                    html.Div('Sector Heatmap', style=SECTION_TITLE_STYLE),
                    dcc.Graph(id='sector-heatmap', config={'displayModeBar': False}, style={'height': '250px'}),
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


# Dataset summary callback
@app.callback(
    [Output('total-laps-value', 'children'),
     Output('drivers-count-value', 'children'),
     Output('fastest-lap-value', 'children')],
    Input('stored-data', 'data')
)
def update_summary(stored_data):
    if not stored_data:
        return '--', '--', '--'
    
    df = pd.read_json(stored_data, orient='split')
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
    
    df = pd.read_json(stored_data, orient='split')
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
    
    df = pd.read_json(stored_data, orient='split')
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
    
    df = pd.read_json(stored_data, orient='split')
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
    
    df = pd.read_json(stored_data, orient='split')
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
            'text': 'Select driver and lap',
            'xref': 'paper',
            'yref': 'paper',
            'showarrow': False,
            'font': {'size': 12, 'color': COLORS['text_secondary']}
        }]
    )
    
    if not stored_data or not selected_driver or selected_lap is None:
        return empty_fig, empty_fig, empty_fig, empty_fig
    
    df = pd.read_json(stored_data, orient='split')
    lap_data = df[(df['driver'] == selected_driver) & (df['lap'] == selected_lap)].sort_values('time_stamp')
    
    if lap_data.empty:
        return empty_fig, empty_fig, empty_fig, empty_fig
    
    # Speed trace
    speed_fig = go.Figure()
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
        yaxis={'title': 'Speed', 'gridcolor': COLORS['grid_line']},
        margin={'l': 50, 'r': 20, 't': 40, 'b': 40},
        height=380,
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
        yaxis={'title': 'Throttle', 'gridcolor': COLORS['grid_line'], 'range': [0, 100]},
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
        yaxis={'title': 'Brake', 'gridcolor': COLORS['grid_line'], 'range': [0, 100]},
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
        yaxis={'title': 'RPM', 'gridcolor': COLORS['grid_line']},
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
    
    df = pd.read_json(stored_data, orient='split')
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
    
    df = pd.read_json(stored_data, orient='split')
    
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
        yaxis={'title': 'Speed (km/h)', 'gridcolor': COLORS['grid_line']},
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
    
    df = pd.read_json(stored_data, orient='split')
    summary = get_dataset_summary(df)
    
    return html.Div([
        html.Div([
            html.Div('🏆', style={'fontSize': '24px', 'marginBottom': '5px'}),
            html.Div(summary['fastest_lap'], style={'fontSize': '13px', 'color': COLORS['text_accent'], 'fontWeight': '600'}),
            html.Div('Fastest Lap', style={'fontSize': '11px', 'color': COLORS['text_secondary'], 'marginTop': '3px'}),
        ], style={'textAlign': 'center', 'marginBottom': '15px', 'padding': '10px', 'backgroundColor': 'rgba(71, 215, 255, 0.05)', 'borderRadius': '8px'}),
        
        html.Div([
            html.Div('📊', style={'fontSize': '24px', 'marginBottom': '5px'}),
            html.Div(summary['avg_lap_time'], style={'fontSize': '13px', 'color': COLORS['text_accent'], 'fontWeight': '600'}),
            html.Div('Average Lap Time', style={'fontSize': '11px', 'color': COLORS['text_secondary'], 'marginTop': '3px'}),
        ], style={'textAlign': 'center', 'marginBottom': '15px', 'padding': '10px', 'backgroundColor': 'rgba(71, 215, 255, 0.05)', 'borderRadius': '8px'}),
        
        html.Div([
            html.Div('⏱️', style={'fontSize': '24px', 'marginBottom': '5px'}),
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
    
    df = pd.read_json(stored_data, orient='split')
    
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
# RUN APP
# ============================================================================

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=8050)

