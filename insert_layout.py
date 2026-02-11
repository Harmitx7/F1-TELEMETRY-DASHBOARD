# Script to add track map and lap delta section to app.py

# Read the original file
with open(r'c:\Users\sunrise\Desktop\pfojects\f1\f1-telemetry-dashboard\app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# New section to insert
new_section = '''        
        # Track Map & Lap Delta Analysis Section
        html.Div(style=CARD_STYLE, children=[
            html.Div('Track Map & Lap Delta Analysis', style=SECTION_TITLE_STYLE),
            html.Div(style={'display': 'grid', 'gridTemplateColumns': '60% 40%', 'gap': '20px'}, children=[
                
                # Track Map Section
                html.Div(children=[
                    html.Div(style={'marginBottom': '15px'}, children=[
                        html.Label('Track Map Controls', style={'fontSize': '12px', 'color': COLORS['text_secondary'], 'marginBottom': '8px', 'display': 'block', 'fontWeight': '600'}),
                        html.Div(style={'display': 'flex', 'gap': '10px', 'alignItems': 'center'}, children=[
                            html.Button('▶️ Play', id='animation-play-btn', n_clicks=0, style={
                                'backgroundColor': COLORS['header_gradient_start'],
                                'color': '#ffffff',
                                'border': 'none',
                                'padding': '8px 16px',
                                'borderRadius': '6px',
                                'cursor': 'pointer',
                                'fontSize': '12px',
                                'fontWeight': '600'
                            }),
                            html.Button('⏸️ Pause', id='animation-pause-btn', n_clicks=0, style={
                                'backgroundColor': COLORS['card_bg'],
                                'color': COLORS['text_primary'],
                                'border': f'1px solid {COLORS["border"]}',
                                'padding': '8px 16px',
                                'borderRadius': '6px',
                                'cursor': 'pointer',
                                'fontSize': '12px',
                                'fontWeight': '600'
                            }),
                        ]),
                    ]),
                    dcc.Graph(id='track-map-chart', config={'displayModeBar': False}, style={'height': '500px'}),
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
                    dcc.Graph(id='delta-plot-chart', config={'displayModeBar': False}, style={'height': '300px'}),
                    html.Div(id='corner-stats-card', style={'marginTop': '15px'}),
                    html.Div(id='delta-summary-card', style={'marginTop': '15px'}),
                ]),
            ]),
        ]),
'''

# Insert after line 434 (index 434)
new_lines = lines[:435] + [new_section] + lines[435:]

# Write back
with open(r'c:\Users\sunrise\Desktop\pfojects\f1\f1-telemetry-dashboard\app.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print("✓ Successfully added track map and lap delta section to app.py")
