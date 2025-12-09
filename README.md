# 🏁 F1 Telemetry Analysis Dashboard

A Python + Dash application for uploading, analyzing, and visualizing Formula 1 telemetry data. Built purely out of passion for F1, performance metrics, and motorsport engineering.

![F1 Dashboard](https://img.shields.io/badge/F1-Telemetry%20Dashboard-e3262f?style=for-the-badge&logo=f1&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.8+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Dash](https://img.shields.io/badge/Dash-Plotly-00c0ff?style=for-the-badge)

---

## 🚦 Overview

This dashboard lets you ingest telemetry CSV files, parse performance traces, visualize laps, compare speed curves, and extract F1-style driver insights — all from your browser.

Perfect for sim racers, data nerds, and anyone who screams at sector times on Sundays.

---

## 🏎️ Features

### 📤 Upload & Validate
- Drag-and-drop CSV upload with instant validation  
- Required columns auto-checked: `driver`, `lap`, `time_stamp`, `speed_kph`
- CSV preview table (first 10 rows)  
- Upload status with colored indicators (✅ / ❌)

### 📊 Lap Time Overview
- Grouped bar graph of lap times per driver  
- Automatic lap time computation if missing  
- F1-themed color palette  
- Sortable table with 3-decimal precision

### 🔍 Detailed Lap Telemetry
Four synchronized charts with a dark F1 UI theme:
- **Speed Trace** (0–350 km/h)
- **Throttle %**, **Brake %**
- **RPM** (6000–14000 typical)

Time axis stays in sync across all charts.

### ⚖️ Lap Comparison
- Pick a driver → compare Lap A vs Lap B  
- Solid vs dashed traces for clarity  
- Unified hover with both lap data

### 🎯 Session Insights
- Fastest lap & driver
- Average lap time
- Total session duration
- Driver and lap counts
- Stylish info cards: trophy, timer, charts

### 🟩 Sector Analysis
- Heatmap showing sector performance  
- Blue → fast, Orange/Red → slow  
- Great for spotting weak corners

---

## 🎨 Design Language

- Dark F1 pit-wall aesthetic `#050913`  
- Cinematic gradient header `#e3262f → #0070ff`  
- Fonts: **Orbitron** (headers) + **Rajdhani** (body)  
- Glassmorphism cards, carbon fiber textures  
- Animated interactions & custom scrollbars  
- Fully responsive layout (max-width 1800px)

---

## 🛠 Tech Stack

| Component | Technology |
|----------|------------|
| Language | Python 3.8+ |
| Framework | Dash 2.14+ (Plotly) |
| Charts | Plotly 5.18+ |
| Data Layer | Pandas 2.0+, NumPy |

---

## 📋 Required Data Format (CSV)

### Mandatory columns
| Column | Type | Example |
|-------|------|---------|
| `driver` | string | VER |
| `lap` | int | 5 |
| `time_stamp` | float | 32.75 |
| `speed_kph` | float | 289.5 |

### Optional telemetry channels
`rpm`, `throttle_pct`, `brake_pct`, `gear`, `drs`, `sector`, `sector_time_ms`, `lat`, `long`

If `lap_time_ms` is missing, it’s computed automatically.

---

## 🚀 Run the Application

```bash
git clone <repository-url>
cd f1-telemetry-dashboard
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py

### 📂 Project Layout
f1-telemetry-dashboard/
├── app.py                  # Main Dash app with callbacks
├── requirements.txt
├── README.md
├── generate_sample_data.py
└── data/
    └── example_telemetry.csv

🧪 Sample Data Highlights

Drivers: VER, HAM, LEC

8 laps each → 24 laps total

~4000 telemetry samples (@0.5s intervals)

Realistic RPM, throttle, brake, DRS + GPS channels

Generate fresh data:

python generate_sample_data.py

🔧 Customization
Add more drivers
drivers = ['VER', 'HAM', 'LEC', 'NOR', 'SAI']

Change theme colors

COLORS in app.py

Modify chart style

Plotly layout settings in callback functions

🐛 Troubleshooting
Issue	Fix
Missing columns	Ensure CSV has required headers
Dark text in dropdowns	Clear cache, refresh
Charts not visible	Verify numeric values, no NaN
Startup issues	Check Python version & dependencies
Slow data	Downsample rows or limit laps
