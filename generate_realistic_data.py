import pandas as pd
import numpy as np
import os
import math

# Configuration
OUTPUT_FILE = 'data/example_telemetry.csv'
DRIVERS = ['VER', 'NOR', 'HAM', 'LEC', 'PIA']
LAPS_PER_DRIVER = 12
TRACK_LENGTH_M = 5300
DT = 0.2 # Time step in seconds (50Hz simulated -> downsampled to 5Hz for CSV)

# Physics / Track Constants
TOP_SPEED_KPH = 340
MIN_SPEED_KPH = 60
ACCEL_G = 1.6
BRAKE_G = 4.5
DRS_ZONES = [(500, 1200), (2500, 3200)] # Distances in meters

# Track Map Generator (Simple complex loop)
def get_track_coords(dist_m):
    # Normalized distance 0..1
    t = (dist_m % TRACK_LENGTH_M) / TRACK_LENGTH_M
    # Lissajous-style shape for realistic-looking circuit
    angle = 2 * np.pi * t
    
    # Monza-ish shape (long straights, chicanes)
    # Simple parametric eq for a track shape
    x = 1000 * np.sin(angle) + 500 * np.sin(2 * angle)
    y = 1200 * np.cos(angle) + 200 * np.sin(3 * angle)
    
    # Add coordinate offset to center roughly on a "real" location if needed, 
    # but for relative track map, centered at 0,0 is fine.
    # Let's map to Monza GPS roughly for realism if viewed on map
    lat_base = 45.620
    lon_base = 9.280
    
    # Scale x/y to lat/lon degrees (approx)
    lat = lat_base + (y / 111000)
    lon = lon_base + (x / 78000)
    
    return lat, lon

# Speed Profile Generator
def generate_base_lap():
    """Generates a velocity profile for one lap based on track geometry curvature."""
    dists = np.arange(0, TRACK_LENGTH_M, 10) # 10m chunks
    speeds = []
    
    for d in dists:
        # Generate curvature based on the track shape derivatives
        # Simplified: varying speed sinusoidally + straights
        t = (d / TRACK_LENGTH_M) * 2 * np.pi
        
        # Track complexity: Straights are where curvature is low
        # Sinusoidal "difficulty":
        curvature = abs(np.sin(t) + 0.5 * np.sin(3*t))
        
        # Speed is inverse to curvature (tighter turn = slower)
        # Add broad straights
        target_speed = MIN_SPEED_KPH + (TOP_SPEED_KPH - MIN_SPEED_KPH) * (1 - curvature * 0.8)
        
        # Add DRS boost on straights
        in_drs = any(start <= d <= end for start, end in DRS_ZONES)
        if in_drs:
            target_speed += 15
            
        speeds.append(target_speed)
        
    return dists, np.array(speeds)

BASE_DISTS, BASE_SPEEDS = generate_base_lap()

def get_speed_at_dist(dist):
    idx = int((dist % TRACK_LENGTH_M) / 10)
    if idx >= len(BASE_SPEEDS): idx = len(BASE_SPEEDS) - 1
    return BASE_SPEEDS[idx]

def simulate_driver_lap(driver, lap_num):
    data = []
    
    # Driver attributes
    consistency = 0.98 if driver == 'VER' else (0.95 if driver in ['HAM', 'NOR'] else 0.92)
    aggressiveness = 1.05 if driver in ['VER', 'LEC'] else 1.0
    
    # Lap time variation (random + tire deg)
    lap_variation = np.random.normal(0, 0.5 * (1 - consistency)) 
    tire_deg_factor = 1.0 - (lap_num * 0.002) # Tires get older -> slightly slower or different grip
    
    current_dist = 0
    current_time = 0
    
    while current_dist < TRACK_LENGTH_M:
        # 1. Calculate Target Speed
        base_speed = get_speed_at_dist(current_dist)
        
        # Apply driver style
        # Aggressive drivers brake later (carry more speed into entry) but might have lower min speed
        noise = np.random.normal(0, 2)
        speed_kph = base_speed * aggressiveness * tire_deg_factor + noise
        
        # Clamp
        speed_kph = max(MIN_SPEED_KPH, min(TOP_SPEED_KPH, speed_kph))
        
        # 2. Derive Telemetry
        speed_ms = speed_kph / 3.6
        
        # Gear (1-8)
        gear = min(8, max(1, int(speed_kph / 42)))
        
        # RPM (approx linear map within gear)
        # Power band 10000 - 12000
        gear_min_speed = (gear - 1) * 40
        gear_max_speed = gear * 45
        rpm_norm = (speed_kph - gear_min_speed) / (gear_max_speed - gear_min_speed + 1e-3)
        rpm = 10000 + (rpm_norm * 2000) + np.random.randint(-100, 100)
        rpm = min(12500, max(9500, rpm))
        
        # Throttle / Brake
        # If accelerating (speed increasing relative to previous), high throttle
        # We need "previous" speed, but here we just infer from "potential" speed
        # Simplified: High speed = Throttle, Low speed = Brake? No, depends on delta.
        # Let's map to static map:
        # Near top speed or increasing base profile = Throttle
        # Near low speed valleys = Brake
        
        # Look ahead 50m
        next_dist = current_dist + 50
        next_val = get_speed_at_dist(next_dist)
        
        delta = next_val - (speed_kph/aggressiveness) # Correct for driver offset
        
        if delta > 5: # Accelerating zone
            throttle = min(100, 80 + delta * 2)
            brake = 0
        elif delta < -5: # Braking zone
            throttle = 0
            brake = min(100, abs(delta) * 4)
        else: # Cruising / Cornering
            throttle = 40 + np.random.randint(0, 20)
            brake = 0
            
        # DRS
        drs = 1 if any(start <= current_dist <= end for start, end in DRS_ZONES) and lap_num > 1 else 0
        
        # Sector
        if current_dist < TRACK_LENGTH_M / 3:
            sector = 1
        elif current_dist < 2 * TRACK_LENGTH_M / 3:
            sector = 2
        else:
            sector = 3
            
        # Coords
        lat, lon = get_track_coords(current_dist)
        
        # Append
        data.append({
            'driver': driver,
            'lap': lap_num,
            'time_stamp': round(current_time, 3),
            'speed_kph': round(speed_kph, 1),
            'rpm': int(rpm),
            'gear': int(gear),
            'throttle_pct': int(throttle),
            'brake_pct': int(brake),
            'drs': int(drs),
            'sector': sector,
            'lat': lat,
            'long': lon
        })
        
        # Update state
        dist_step = speed_ms * DT
        current_dist += dist_step
        current_time += DT

    return pd.DataFrame(data)

def main():
    if not os.path.exists('data'):
        os.makedirs('data')
        
    print(f"Generatign data for {len(DRIVERS)} drivers, {LAPS_PER_DRIVER} laps each...")
    
    all_dfs = []
    
    for driver in DRIVERS:
        print(f"  Simulating {driver}...")
        for lap in range(1, LAPS_PER_DRIVER + 1):
            lap_df = simulate_driver_lap(driver, lap)
            all_dfs.append(lap_df)
            
    final_df = pd.concat(all_dfs, ignore_index=True)
    
    # Calculate sector times (post-process)
    # This is a bit complex to do perfectly row-by-row, but we can aggregate 
    # expected sector times if needed. Since the dashboard calculates corner stats
    # dynamically, we might just leave 'sector' column as is.
    # The app calculates 'sector_time_ms' if present, or we can omit it.
    # Let's add dummy sector_time_ms to match schema
    final_df['sector_time_ms'] = 0 # Placeholder
    
    final_df.to_csv(OUTPUT_FILE, index=False)
    print(f"Done! {len(final_df)} rows written to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
