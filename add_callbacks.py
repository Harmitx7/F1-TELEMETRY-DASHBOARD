# Script to add callbacks for track map and lap delta features

callbacks_code = '''

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
    
    df = pd.read_json(stored_data, orient='split')
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
    
    df = pd.read_json(stored_data, orient='split')
    lap_data = df[(df['driver'] == selected_driver) & (df['lap'] == selected_lap)].sort_values('time_stamp').copy()
    
    if lap_data.empty:
        return empty_fig
    
    # Check if GPS coordinates are available
    use_gps = 'lat' in lap_data.columns and 'long' in lap_data.columns
    
    # Normalize coordinates
    lap_data = tu.normalize_track_coordinates(lap_data, use_gps=use_gps)
    
    # Create track map
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
    
    # Add car marker at current position
    if slider_value is not None and not lap_data.empty:
        # Calculate position based on slider (0-100%)
        max_idx = len(lap_data) - 1
        current_idx = int((slider_value / 100) * max_idx)
        current_point = lap_data.iloc[current_idx]
        
        fig.add_trace(go.Scatter(
            x=[current_point['x_coord']],
            y=[current_point['y_coord']],
            mode='markers',
            name='Car Position',
            marker={
                'size': 15,
                'color': COLORS['header_gradient_start'],
                'symbol': 'circle',
                'line': {'width': 2, 'color': '#ffffff'}
            },
            hovertemplate=f'<b>Position: {slider_value:.1f}%</b><br>Speed: {current_point.get("speed_kph", 0):.1f} km/h<extra></extra>'
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
    
    df = pd.read_json(stored_data, orient='split')
    
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
    
    df = pd.read_json(stored_data, orient='split')
    
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
    
    df = pd.read_json(stored_data, orient='split')
    
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

'''

# Read the current app.py
with open(r'c:\Users\sunrise\Desktop\pfojects\f1\f1-telemetry-dashboard\app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the position to insert (before "# RUN APP" section)
insert_marker = '# ============================================================================\n# RUN APP\n# ============================================================================'
insert_pos = content.find(insert_marker)

if insert_pos == -1:
    print("❌ Could not find insertion point")
else:
    # Insert the callbacks
    new_content = content[:insert_pos] + callbacks_code + '\n' + content[insert_pos:]
    
    # Write back
    with open(r'c:\Users\sunrise\Desktop\pfojects\f1\f1-telemetry-dashboard\app.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("✓ Successfully added all track map and lap delta callbacks to app.py")
