# F1 Telemetry Analysis Dashboard

A Python + Dash web application to upload and analyze Formula 1 telemetry data, visualize laps, and compare performance traces. Built for the love of F1, the obsession with data, and the joy of motorsport.

![F1 Dashboard](https://img.shields.io/badge/F1-Telemetry%20Dashboard-e3262f?style=for-the-badge&logo=f1&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.8+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Dash](https://img.shields.io/badge/Dash-Plotly-00c0ff?style=for-the-badge)

## 🏎️ Features

### Core Functionality
- **📤 Upload & Validate**: 
  - Drag-and-drop CSV file upload interface with racing car icon
  - Automatic validation of required columns (`driver`, `lap`, `time_stamp`, `speed_kph`)
  - Real-time error messages for invalid files or missing columns
  - Visual confirmation (✅/❌) of upload status with colored feedback
  - Data preview table showing first 10 rows with all columns
  - Client-side data storage for fast interactions

- **📊 Lap Time Overview**: 
  - Interactive grouped bar chart showing lap times per driver
  - Color-coded by driver using F1-inspired palette (red, cyan, orange, green, purple)
  - Sortable data table with lap times displayed in seconds (3 decimal precision)
  - Automatic lap time computation from `time_stamp` if `lap_time_ms` not provided
  - Hover tooltips with detailed lap information (driver, lap number, time)
  - Responsive legend with horizontal orientation

- **🔍 Detailed Lap View**: 
  - Cascading driver and lap selection dropdowns with improved visibility
  - Four synchronized telemetry charts with dark theme:
    - **Speed Trace**: Line chart with area fill showing speed over time (0-350 km/h)
    - **Throttle Trace**: Percentage-based chart with orange fill (0-100%)
    - **Brake Trace**: Percentage-based chart with red fill (0-100%)
    - **RPM Trace**: Engine RPM visualization (6000-14000 RPM typical range)
  - Conditional rendering - charts gracefully hide if data columns are missing
  - Interactive hover with synchronized time axis across all charts
  - Grid lines for easy value reading

- **⚖️ Lap Comparison**: 
  - Side-by-side comparison of two laps for the same driver
  - Overlaid speed traces with different line styles for easy distinction
  - Solid line for Lap A, dashed line for Lap B
  - Different colors (red vs cyan) for clear visual separation
  - Unified hover tooltips showing both laps simultaneously
  - Large 450px chart height for detailed analysis
  - Improved flexbox layout with better spacing

- **🎯 Sector Analysis**: 
  - Color-coded heatmap of sector performance across all laps
  - Blue (fast) → Green (medium) → Orange/Red (slow) color scale
  - Automatic sector time computation from telemetry time ranges
  - Lap × Sector matrix visualization for pattern identification
  - Interactive hover showing exact sector times in milliseconds
  - Helps identify consistent strong/weak track sections

- **💡 Session Insights**: 
  - **Fastest Lap**: Shows driver code, lap number, and time
  - **Average Lap Time**: Mean lap time across all laps in session
  - **Session Duration**: Total time span from first to last sample
  - **Driver Count**: Number of unique drivers in dataset
  - **Total Laps**: Complete lap count across all drivers
  - Visual cards with trophy, chart, and timer icons
  - Accent-colored backgrounds with subtle transparency

### Design & User Experience
- **🎨 Premium F1 Theme**: 
  - Dark motorsport-inspired UI with deep space blue background (#050913)
  - Red-to-blue gradient header (#e3262f → #0070ff) matching F1 branding
  - Custom Google Fonts: Orbitron (headers) and Rajdhani (body text)
  - Glassmorphism card effects with subtle shadows and borders
  - Racing aesthetics with carbon fiber texture references
  - Checkered flag table border accents
  - Smooth hover transitions and micro-animations
  - **Custom styled dropdowns** with visible white text on dark background
  - Cyan accent color (#47d7ff) for hover states
  - Responsive grid layout optimized for large screens (1800px max width)
  - Custom scrollbar styling matching dark theme

## 🛠️ Tech Stack

- **Python 3.8+** - Core programming language
- **Dash 2.14+** - Interactive web framework built on Flask
- **Plotly 5.18+** - Advanced charting and data visualizations
- **Pandas 2.0+** - Data manipulation and analysis
- **NumPy** - Numerical computing (via Pandas dependency)

## 📋 Data Format

The dashboard expects CSV files with the following columns:

### Required Columns
- `driver` (string) - Driver identifier (e.g., "VER", "HAM", "LEC")
- `lap` (integer) - Lap number (1, 2, 3, ...)
- `time_stamp` (float) - Time in seconds relative to lap/session start
- `speed_kph` (float) - Speed in kilometers per hour

### Optional Columns
- `rpm` (integer) - Engine RPM (revolutions per minute)
- `throttle_pct` (float) - Throttle position percentage (0-100%)
- `brake_pct` (float) - Brake pressure percentage (0-100%)
- `gear` (integer) - Current gear (1-8 for modern F1)
- `drs` (integer) - DRS (Drag Reduction System) status (0=off, 1=on)
- `sector` (integer) - Track sector number (1, 2, or 3)
- `sector_time_ms` (integer) - Sector time in milliseconds
- `lat` (float) - GPS latitude coordinate
- `long` (float) - GPS longitude coordinate

**Note**: If `lap_time_ms` is not provided, it will be automatically calculated from the `time_stamp` column.

## 🚀 How to Run

### 1. Clone the Repository
```bash
git clone <repository-url>
cd f1-telemetry-dashboard
```

### 2. Create Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the Application
```bash
python app.py
```

### 5. Open in Browser
Navigate to: **http://127.0.0.1:8050**

The application will start in debug mode by default. You should see:
```
Dash is running on http://127.0.0.1:8050/
 * Serving Flask app 'app'
 * Debug mode: on
```

## 📖 Usage Guide

### Step 1: Upload Data
- Click the upload area (with racing car icon 🏎️) or drag and drop a CSV file
- The dashboard will automatically validate the file structure
- Look for the green checkmark (✅) confirming successful upload
- Dataset summary metrics will update automatically in real-time
- Preview table shows the first 10 rows of your data

### Step 2: Explore Lap Times
- View the **Lap Overview** bar chart to see lap times for all drivers
- Each driver is color-coded for easy identification
- Hover over bars to see exact lap times
- Check the **Lap Times Table** below for sortable detailed numbers
- Identify fastest laps and performance trends

### Step 3: Analyze Individual Laps
- Select a **driver** from the dropdown (VER, HAM, LEC, etc.)
- Choose a specific **lap** to view from the filtered lap list
- Examine the four detailed telemetry traces:
  - **Speed vs Time**: See acceleration, braking, and top speed
  - **Throttle vs Time**: Analyze throttle application patterns
  - **Brake vs Time**: Identify braking zones and intensity
  - **RPM vs Time**: View engine usage and gear shifts
- All charts share the same time axis for easy correlation

### Step 4: Compare Laps
- In the **Lap Comparison** section, select a driver
- Choose **Lap A** (solid line) and **Lap B** (dashed line) to compare
- The speed traces will overlay showing exactly where time is gained or lost
- Use unified hover to see both lap values at the same time point
- Analyze differences in braking points, acceleration, and corner speeds

### Step 5: Review Insights & Sectors
- Check **Session Insights** for:
  - Fastest lap (driver and time)
  - Average lap time across session
  - Total session duration
- View the **Sector Heatmap** to identify:
  - Consistently fast sectors (blue)
  - Problematic sectors (orange/red)
  - Lap-to-lap sector performance patterns

## 📁 Project Structure

```
f1-telemetry-dashboard/
├── app.py                      # Main Dash application (980+ lines)
│   ├── Helper functions (validation, lap time computation)
│   ├── Styling constants (colors, card styles, fonts)
│   ├── Layout definition (all UI components)
│   └── 11 reactive callbacks for interactivity
├── requirements.txt            # Python dependencies
├── README.md                   # This file
├── generate_sample_data.py     # Script to generate realistic sample data
└── data/
    └── example_telemetry.csv   # Sample telemetry data (3,969 rows)
```

## 🎨 Design Features

- **Dark Theme**: Motorsport-inspired dark UI (#050913 background)
- **F1 Gradient Header**: Red-to-blue gradient (#e3262f → #0070ff)
- **Custom Fonts**: Orbitron (headers) and Rajdhani (body) via Google Fonts
- **Racing Aesthetics**: Carbon fiber textures, checkered flag accents
- **Responsive Charts**: Interactive Plotly visualizations with hover details
- **Premium Cards**: Glassmorphism effects with subtle shadows
- **Visible Dropdowns**: Custom CSS ensuring white text on dark backgrounds
- **Color Palette**: Red (#ff4654), Cyan (#00c0ff), Orange (#ffb547), Green (#7eff7a), Purple (#b66bff)

## 🧪 Sample Data

The project includes a realistic sample dataset with:
- **3 Drivers**: VER (Verstappen), HAM (Hamilton), LEC (Leclerc)
- **8 Laps per driver** (24 total laps)
- **~4,000 telemetry samples** (165 samples per lap at 0.5s intervals)
- **Realistic lap times**: 82-84 seconds (typical F1 lap duration)
- **All telemetry channels**: speed, RPM, throttle, brake, gear, DRS, sectors, GPS
- **Realistic patterns**: Acceleration zones, braking zones, DRS activation on straights

To regenerate sample data:
```bash
python generate_sample_data.py
```

## 🔧 Customization

### Adding More Drivers
Edit `generate_sample_data.py` and add to the `drivers` list:
```python
drivers = ['VER', 'HAM', 'LEC', 'NOR', 'SAI']
lap_base_times = {
    'VER': 82.5,
    'HAM': 82.8,
    'LEC': 83.1,
    'NOR': 83.0,
    'SAI': 83.2
}
```

### Changing Theme Colors
Modify the `COLORS` dictionary in `app.py`:
```python
COLORS = {
    'background': '#050913',
    'card_bg': '#0c101c',
    'header_gradient_start': '#e3262f',
    'header_gradient_end': '#0070ff',
    'text_primary': '#ffffff',
    'text_accent': '#47d7ff',
    # ... more colors
}
```

### Adjusting Chart Styles
Update Plotly figure layouts in the callback functions within `app.py`:
```python
fig.update_layout(
    template='plotly_dark',
    paper_bgcolor=COLORS['card_bg'],
    plot_bgcolor=COLORS['card_bg'],
    # ... more styling
)
```

## 🐛 Troubleshooting

### Issue: "Missing required columns" error
**Solution**: Ensure your CSV has `driver`, `lap`, `time_stamp`, and `speed_kph` columns with correct spelling.

### Issue: Dropdown text not visible
**Solution**: This has been fixed with custom CSS. If still an issue, clear browser cache and refresh.

### Issue: Charts not displaying
**Solution**: 
- Check that your data has numeric values in telemetry columns
- Ensure no NaN values in critical fields (`driver`, `lap`, `time_stamp`, `speed_kph`)
- Verify CSV is properly formatted with headers

### Issue: Application won't start
**Solution**: 
1. Verify Python 3.8+ is installed: `python --version`
2. Ensure all dependencies are installed: `pip install -r requirements.txt`
3. Check port 8050 is not in use: `netstat -ano | findstr :8050` (Windows)
4. Try a different port by editing `app.py`: `app.run(port=8051)`

### Issue: Slow performance with large datasets
**Solution**: 
- Consider downsampling telemetry data (e.g., every 1s instead of 0.5s)
- Filter to specific laps or drivers before upload
- The dashboard is optimized for datasets under 100k rows

## 📊 Performance Notes

- The dashboard handles datasets with thousands of rows efficiently
- For very large datasets (>100k rows), consider downsampling telemetry data
- All processing happens in-browser using Dash's client-side storage (`dcc.Store`)
- No server-side sessions required - fully stateless architecture
- Charts render using WebGL for smooth interactions

## 🚀 Future Enhancements

Potential features for future versions:

- [ ] **Track Map Visualization**: Plot GPS coordinates on circuit layout
- [ ] **Delta Time Analysis**: Show time gained/lost per corner
- [ ] **Tire Degradation**: Track lap time degradation over stint
- [ ] **Export Reports**: Generate PDF comparison reports
- [ ] **Multi-Driver Comparison**: Compare 3+ drivers simultaneously
- [ ] **Real-Time Streaming**: Support live telemetry data feeds
- [ ] **Gear Shift Analysis**: Visualize optimal shift points
- [ ] **Weather Integration**: Correlate performance with track conditions
- [ ] **Historical Comparison**: Compare current session with previous races

## 📄 License

This project is open source, but it was built to satisfy the inner noises and dreaming of the pit wall. It exists for the love for F1, the obsession with data, and joy of cars and motorsport. This is not a production-ready application. This code is for you.

## 👤 Author

**Harmit Kalal**

Built with passion for Formula 1 and data engineering.

---

**Enjoy analyzing F1 telemetry! 🏁**
