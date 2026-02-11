# 🏎️ F1 Telemetry Dashboard Pro

![Version](https://img.shields.io/badge/version-2.1-e10600?style=for-the-badge&logo=formula1&logoColor=white)
![Python](https://img.shields.io/badge/python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Status](https://img.shields.io/badge/features-Pro%20Max-00D2BE?style=for-the-badge)

A high-fidelity F1 telemetry analysis tool with broadcast-grade visualizations, realistic data simulation, and advanced statistical analytics.

![Dashboard Preview](https://via.placeholder.com/800x400.png?text=F1+Telemetry+Dashboard+Pro)

## ✨ Key Features (v2.1)

### 📊 Analytics Lab
Advanced statistical widgets for deep dive analysis:
- **Correlation Heatmap**: F1-branded Red/Cyan correlation matrix to spot mechanical relationships.
- **Driver Consistency**: Coefficient of Variation (CV) scoring (90+ score = Elite).
- **Performance Distribution**: Violin plots showing the spread of speed, throttle, and braking.
- **Race Pace**: Rolling average analysis with interactive zoom for stint analysis.
- **Percentile Radar**: Tactical scope visualization comparing driver metrics.

### 🎨 UI/UX Pro Max
- **Cinematic Design**: Dark asphalt backgrounds (`#15151e`), neon cyan accents, and glassmorphism cards.
- **Tactical Grids**: Custom radar scopes and reference lines (e.g., "Elite Threshold").
- **Responsive**: Precision formatting with Orbitron headers and Fira Code data fonts.

### 🏎️ Realistic Simulation
- **Physics Engine**: Includes `generate_realistic_data.py` to simulate 2024 season data.
- **High Fidelity**: Generates accurate speed, gear, RPM, and GPS traces for 5 drivers (VER, NOR, HAM, LEC, PIA).

## 🚀 Quick Start

### 1. Installation
Clone the repo and install dependencies:
```bash
git clone https://github.com/Harmitx7/F1-TELEMETRY-DASHBOARD.git
cd F1-TELEMETRY-DASHBOARD
pip install -r requirements.txt
```

### 2. Run Locally
Start the Dash server:
```bash
python app.py
```
Open your browser at `http://127.0.0.1:8050`.

### 3. Generate New Data (Optional)
Simulate a fresh 60-lap session:
```bash
python generate_realistic_data.py
```

## ☁️ Deployment
Ready for production.
- **Vercel**: `vercel.json` included for one-click Python deployment.
- **Heroku/Render**: `Procfile` included (`web: gunicorn app:server`).

## 🛠️ Tech Stack
- **Frontend**: Dash, Plotly, HTML5/CSS3 (Glassmorphism)
- **Backend**: Python, Pandas, Numpy, Scipy
- **Sim**: Custom Physics Generator

---
*Built for speed. Engineered for precision.*