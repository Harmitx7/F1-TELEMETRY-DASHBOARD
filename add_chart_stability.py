# Script to add stable chart dimensions and axis ranges

import re

# Read the current app.py
with open(r'c:\Users\sunrise\Desktop\pfojects\f1\f1-telemetry-dashboard\app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find and update chart configurations for stability
# We'll add fixedrange and consistent ranges to key charts

# Speed chart - set range 0-360
speed_chart_updates = [
    (
        r"yaxis=\{'title': 'Speed', 'gridcolor': COLORS\['grid_line'\]\}",
        "yaxis={'title': 'Speed', 'gridcolor': COLORS['grid_line'], 'range': [0, 360], 'fixedrange': True}"
    ),
    (
        r"yaxis=\{'title': 'Speed \(km/h\)', 'gridcolor': COLORS\['grid_line'\]\}",
        "yaxis={'title': 'Speed (km/h)', 'gridcolor': COLORS['grid_line'], 'range': [0, 360], 'fixedrange': True}"
    ),
]

# Throttle/Brake charts - set range 0-105
throttle_brake_updates = [
    (
        r"yaxis=\{'title': 'Throttle', 'gridcolor': COLORS\['grid_line'\], 'range': \[0, 100\]\}",
        "yaxis={'title': 'Throttle', 'gridcolor': COLORS['grid_line'], 'range': [0, 105], 'fixedrange': True}"
    ),
    (
        r"yaxis=\{'title': 'Brake', 'gridcolor': COLORS\['grid_line'\], 'range': \[0, 100\]\}",
        "yaxis={'title': 'Brake', 'gridcolor': COLORS['grid_line'], 'range': [0, 105], 'fixedrange': True}"
    ),
]

# RPM chart - set range 5000-14000
rpm_updates = [
    (
        r"yaxis=\{'title': 'RPM', 'gridcolor': COLORS\['grid_line'\]\}",
        "yaxis={'title': 'RPM', 'gridcolor': COLORS['grid_line'], 'range': [5000, 14000], 'fixedrange': True}"
    ),
]

# Apply all updates
all_updates = speed_chart_updates + throttle_brake_updates + rpm_updates

for pattern, replacement in all_updates:
    content = re.sub(pattern, replacement, content)

# Add explicit heights to charts that don't have them
# Find chart style definitions and ensure they have height
chart_height_pattern = r"style=\{'height': '(\d+)px'\}"

# Write back
with open(r'c:\Users\sunrise\Desktop\pfojects\f1\f1-telemetry-dashboard\app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✓ Successfully added stable chart configurations")
print("  - Speed charts: range [0, 360], fixedrange=True")
print("  - Throttle/Brake: range [0, 105], fixedrange=True")
print("  - RPM charts: range [5000, 14000], fixedrange=True")
