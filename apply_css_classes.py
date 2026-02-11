# Script to add CSS classes to app.py components for fluid UI

import re

# Read the current app.py
with open(r'c:\Users\sunrise\Desktop\pfojects\f1\f1-telemetry-dashboard\app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Define replacements for adding className to components
replacements = [
    # Upload card
    (
        r"html\.Div\(style=CARD_STYLE, children=\[\s*html\.Div\('Upload & Summary'",
        "html.Div(style=CARD_STYLE, className='dashboard-card', children=[\n                html.Div('Upload & Summary'"
    ),
    # Dataset summary card
    (
        r"html\.Div\(style=CARD_STYLE, children=\[\s*html\.Div\('Dataset Summary'",
        "html.Div(style=CARD_STYLE, className='dashboard-card', children=[\n                html.Div('Dataset Summary'"
    ),
    # Lap overview card  
    (
        r"html\.Div\(style=CARD_STYLE, children=\[\s*html\.Div\('Lap Overview'",
        "html.Div(style=CARD_STYLE, className='dashboard-card', children=[\n                html.Div('Lap Overview'"
    ),
    # Lap times table card
    (
        r"html\.Div\(style=CARD_STYLE, children=\[\s*html\.Div\('Lap Times Table'",
        "html.Div(style=CARD_STYLE, className='dashboard-card', children=[\n                html.Div('Lap Times Table'"
    ),
    # Data preview card
    (
        r"html\.Div\(style=CARD_STYLE, children=\[\s*html\.Div\('Data Preview'",
        "html.Div(style=CARD_STYLE, className='dashboard-card', children=[\n            html.Div('Data Preview'"
    ),
    # Lap detail card
    (
        r"html\.Div\(style=CARD_STYLE, children=\[\s*html\.Div\('Lap Detail View'",
        "html.Div(style=CARD_STYLE, className='dashboard-card no-hover', children=[\n            html.Div('Lap Detail View'"
    ),
    # Lap comparison card
    (
        r"html\.Div\(style=CARD_STYLE, children=\[\s*html\.Div\('Lap Comparison'",
        "html.Div(style=CARD_STYLE, className='dashboard-card no-hover', children=[\n                html.Div('Lap Comparison'"
    ),
    # Session insights card
    (
        r"html\.Div\(style=CARD_STYLE, children=\[\s*html\.Div\('Session Insights'",
        "html.Div(style=CARD_STYLE, className='dashboard-card', children=[\n                    html.Div('Session Insights'"
    ),
    # Sector heatmap card
    (
        r"html\.Div\(style=CARD_STYLE, children=\[\s*html\.Div\('Sector Heatmap'",
        "html.Div(style=CARD_STYLE, className='dashboard-card', children=[\n                    html.Div('Sector Heatmap'"
    ),
    # Track map card
    (
        r"html\.Div\(style=CARD_STYLE, children=\[\s*html\.Div\('Track Map & Lap Delta Analysis'",
        "html.Div(style=CARD_STYLE, className='dashboard-card no-hover', children=[\n            html.Div('Track Map & Lap Delta Analysis'"
    ),
    # Play button
    (
        r"html\.Button\('▶️ Play', id='animation-play-btn'",
        "html.Button('▶️ Play', id='animation-play-btn', className='button-primary'"
    ),
    # Pause button
    (
        r"html\.Button\('⏸️ Pause', id='animation-pause-btn'",
        "html.Button('⏸️ Pause', id='animation-pause-btn', className='button-secondary'"
    ),
]

# Apply replacements
for pattern, replacement in replacements:
    content = re.sub(pattern, replacement, content, flags=re.MULTILINE)

# Wrap dcc.Graph components in chart-container divs
# This is more complex, so we'll do it with a more targeted approach
graph_pattern = r'(dcc\.Graph\(id=\'[^\']+\', config=\{\'displayModeBar\': False\})'
content = re.sub(
    graph_pattern,
    r"html.Div(className='chart-container', children=[\1])",
    content
)

# Write back
with open(r'c:\Users\sunrise\Desktop\pfojects\f1\f1-telemetry-dashboard\app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✓ Successfully added CSS classes to app.py components")
print("  - Added 'dashboard-card' to all card components")
print("  - Added 'button-primary' and 'button-secondary' to buttons")
print("  - Wrapped graphs in 'chart-container' divs")
