"""
Enhanced F1 Telemetry Data Generator
Creates realistic telemetry data based on actual F1 racing patterns
Simulates Monza circuit characteristics
"""

import pandas as pd
import numpy as np

# Set random seed for reproducibility
np.random.seed(42)

# Configuration
drivers = {
    'VER': {'skill': 1.00, 'consistency': 0.98},  # Verstappen - most consistent
    'HAM': {'skill': 0.99, 'consistency': 0.96},  # Hamilton
    'LEC': {'skill': 0.98, 'consistency': 0.94},  # Leclerc - slightly less consistent
}

laps_per_driver = 10
base_lap_time = 81.5  # Monza lap time in seconds (~1:21.5)

# Monza circuit profile (simplified but realistic duration)
# Famous for long straights and chicanes
# Total duration should be ~80-82 seconds
circuit_profile = [
    # (duration_s, type, target_speed, description)
    (12.0, 'accel', 340, 'Start/Finish straight - longest in F1'),
    (5.5, 'brake', 120, 'Turn 1 - Variante del Rettifilo (chicane)'),
    (9.0, 'accel', 310, 'Exit T1 to Curva Grande'),
    (4.0, 'brake', 180, 'Turn 4 - Curva Grande (fast right)'),
    (13.5, 'accel', 335, 'Lesmo straight'),
    (4.5, 'brake', 140, 'Turns 6-7 - Variante Ascari (chicane complex)'),
    (10.5, 'accel', 320, 'Exit Ascari to Parabolica'),
    (6.0, 'brake', 160, 'Turn 11 - Curva Parabolica (long corner)'),
    (15.0, 'accel', 345, 'Parabolica exit to finish line'),
]

def generate_corner_telemetry(time_start, duration, corner_type, target_speed, current_speed, driver_skill):
    """Generate realistic telemetry for a corner or straight"""
    samples = int(duration * 2)  # 0.5s intervals
    telemetry = []
    
    for i in range(samples):
        t = time_start + (i * 0.5)
        progress = i / max(samples - 1, 1)
        
        if corner_type == 'accel':
            # Acceleration phase
            speed = current_speed + (target_speed - current_speed) * (1 - np.exp(-3 * progress))
            speed += np.random.uniform(-2, 2)  # Small variations
            
            throttle = min(100, 85 + 15 * progress + np.random.uniform(-5, 5))
            brake = 0
            
            # DRS active on long straights at high speed
            drs = 1 if speed > 280 and duration > 3.0 and progress > 0.3 else 0
            
        elif corner_type == 'brake':
            # Braking and corner phase
            if progress < 0.4:  # Initial braking
                speed = current_speed - (current_speed - target_speed) * (progress / 0.4)
                throttle = max(0, 100 - (progress / 0.4) * 100)
                brake = min(100, (progress / 0.4) * 100)
            elif progress < 0.7:  # Apex
                speed = target_speed + np.random.uniform(-5, 5)
                throttle = 30 + np.random.uniform(-10, 10)
                brake = max(0, 40 - (progress - 0.4) * 100)
            else:  # Exit
                speed = target_speed + (target_speed * 0.5) * ((progress - 0.7) / 0.3)
                throttle = 50 + ((progress - 0.7) / 0.3) * 50
                brake = 0
            
            drs = 0
        else:
            speed = current_speed
            throttle = 50
            brake = 0
            drs = 0
        
        # Apply driver skill variation
        speed *= (1 + np.random.uniform(-0.01, 0.01) * (1 - driver_skill))
        
        # Calculate RPM based on speed and gear
        gear = min(8, max(2, int(speed / 45) + 1))
        rpm = int(6000 + (speed / 345) * 7500 + np.random.uniform(-200, 200))
        rpm = max(5500, min(13500, rpm))
        
        telemetry.append({
            'time': t,
            'speed': max(80, min(350, speed)),
            'throttle': max(0, min(100, throttle)),
            'brake': max(0, min(100, brake)),
            'rpm': rpm,
            'gear': gear,
            'drs': drs
        })
    
    return telemetry, telemetry[-1]['speed'] if telemetry else current_speed


def generate_lap(driver, lap_num, driver_stats):
    """Generate a complete lap of telemetry data"""
    lap_data = []
    
    # Lap time variation based on consistency
    lap_variation = np.random.uniform(-0.3, 0.5) * (1 - driver_stats['consistency'])
    
    # First lap is slower (out lap or traffic)
    if lap_num == 1:
        lap_variation += 1.2
    
    # Add some lap-to-lap variation
    lap_variation += np.random.uniform(-0.2, 0.3)
    
    current_time = 0.0
    current_speed = 280.0  # Starting speed
    sector = 1
    sector_start_time = 0.0
    
    for segment_idx, (duration, seg_type, target_speed, description) in enumerate(circuit_profile):
        # Adjust duration based on lap variation
        adjusted_duration = duration * (1 + lap_variation * 0.01)
        
        # Generate telemetry for this segment
        segment_telemetry, current_speed = generate_corner_telemetry(
            current_time, adjusted_duration, seg_type, target_speed, 
            current_speed, driver_stats['skill']
        )
        
        # Determine sector (divide circuit into 3 roughly equal parts)
        if segment_idx < 3:
            sector = 1
        elif segment_idx < 6:
            if sector == 1:
                sector_start_time = current_time
            sector = 2
        else:
            if sector == 2:
                sector_start_time = current_time
            sector = 3
        
        # Add sector information
        for sample in segment_telemetry:
            sample['sector'] = sector
            sample['sector_time_ms'] = 0  # Will be filled at sector end
        
        lap_data.extend(segment_telemetry)
        current_time += adjusted_duration
    
    # Calculate sector times
    sector_times = {}
    for s in [1, 2, 3]:
        sector_samples = [d for d in lap_data if d['sector'] == s]
        if sector_samples:
            sector_time = (sector_samples[-1]['time'] - sector_samples[0]['time']) * 1000
            sector_times[s] = int(sector_time)
            # Mark last sample of each sector
            sector_samples[-1]['sector_time_ms'] = int(sector_time)
    
    # Add GPS coordinates (simplified Monza layout)
    monza_center_lat = 45.6156
    monza_center_lon = 9.2811
    
    for i, sample in enumerate(lap_data):
        progress = i / len(lap_data)
        # Simplified oval-ish track shape
        angle = progress * 2 * np.pi
        sample['lat'] = monza_center_lat + 0.008 * np.cos(angle) + np.random.uniform(-0.0001, 0.0001)
        sample['long'] = monza_center_lon + 0.015 * np.sin(angle) + np.random.uniform(-0.0001, 0.0001)
    
    return lap_data


# Generate all data
all_data = []

print("Generating realistic F1 telemetry data...")
print(f"Circuit: Monza (simplified)")
print(f"Drivers: {', '.join(drivers.keys())}")
print(f"Laps per driver: {laps_per_driver}")
print()

for driver, stats in drivers.items():
    print(f"Generating data for {driver}...")
    
    for lap_num in range(1, laps_per_driver + 1):
        lap_telemetry = generate_lap(driver, lap_num, stats)
        
        # Convert to final format
        for sample in lap_telemetry:
            all_data.append({
                'driver': driver,
                'lap': lap_num,
                'time_stamp': round(sample['time'], 1),
                'speed_kph': round(sample['speed'], 1),
                'rpm': sample['rpm'],
                'throttle_pct': round(sample['throttle'], 1),
                'brake_pct': round(sample['brake'], 1),
                'gear': sample['gear'],
                'drs': sample['drs'],
                'sector': sample['sector'],
                'sector_time_ms': sample['sector_time_ms'],
                'lat': round(sample['lat'], 6),
                'long': round(sample['long'], 6)
            })
        
        lap_time = lap_telemetry[-1]['time']
        print(f"  Lap {lap_num}: {lap_time:.3f}s ({len(lap_telemetry)} samples)")

# Create DataFrame and save
df = pd.DataFrame(all_data)
df.to_csv('data/example_telemetry.csv', index=False)

print()
print(f"✅ Generated {len(df)} telemetry samples")
print(f"📊 Total laps: {len(drivers) * laps_per_driver}")
print(f"💾 Saved to: data/example_telemetry.csv")
print()

# Print summary statistics
print("Summary Statistics:")
print(f"  Speed range: {df['speed_kph'].min():.1f} - {df['speed_kph'].max():.1f} km/h")
print(f"  RPM range: {df['rpm'].min()} - {df['rpm'].max()}")
print(f"  Average lap time: {df.groupby(['driver', 'lap'])['time_stamp'].max().mean():.3f}s")
print()

# Show fastest lap per driver
print("Fastest laps:")
lap_times = df.groupby(['driver', 'lap'])['time_stamp'].max().reset_index()
lap_times.columns = ['driver', 'lap', 'lap_time']
for driver in drivers.keys():
    driver_laps = lap_times[lap_times['driver'] == driver]
    fastest = driver_laps.loc[driver_laps['lap_time'].idxmin()]
    print(f"  {driver}: Lap {fastest['lap']} - {fastest['lap_time']:.3f}s")
