"""
Mock UDP Sender for F1 24 Telemetry
Replays data from CSV file to simulate realistic game traffic.
"""
import socket
import struct
import time
import pandas as pd
import numpy as np
import os

# Configuration
UDP_IP = "127.0.0.1"
UDP_PORT = 20777
CSV_FILE = os.path.join("data", "example_telemetry.csv")
REPLAY_SPEED = 1.0  # 1.0 = Realtime
UPDATE_RATE = 0.05  # 20Hz (50ms)

# Packet IDs
PACKET_ID_LAP_DATA = 2
PACKET_ID_CAR_TELEMETRY = 6

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

def load_telemetry_data():
    """Load and preprocess CSV data"""
    if not os.path.exists(CSV_FILE):
        print(f"❌ Error: {CSV_FILE} not found!")
        return None
    
    print(f"📥 Loading {CSV_FILE}...")
    df = pd.read_csv(CSV_FILE)
    
    # Ensure required columns exist
    required = ['time_stamp', 'speed_kph', 'rpm', 'throttle_pct', 'brake_pct', 'gear', 'lat', 'long']
    if not all(col in df.columns for col in required):
        print("❌ Error: CSV missing required columns!")
        return None
        
    # Sort by time
    df = df.sort_values('time_stamp')
    return df

def create_header(packet_id, frame_id, time_val):
    # Pack Header (F1 2024 spec)
    # HBBBBQfIIBB (28 bytes)
    # Format, Maj, Min, Ver, ID, SessionUID, Time, Frame, OverallFrame, PlayerIdx, SecondaryIdx
    return struct.pack('<HBBBBQfIIBB', 
        2024, 1, 0, 1, packet_id, 123456789, time_val, frame_id, frame_id, 0, 255
    )

def interpolate_packet(df, current_time):
    """Get interpolated values for current timestamp"""
    # Find data rows before and after current_time
    # This is a simple logic: get nearest or interpolate
    # For performance, we can use searchsorted
    
    # Find index where time_stamp >= current_time
    idx = np.searchsorted(df['time_stamp'], current_time)
    
    if idx == 0:
        return df.iloc[0]
    if idx >= len(df):
        return df.iloc[-1]
        
    # Valid interval found
    row_next = df.iloc[idx]
    row_prev = df.iloc[idx - 1]
    
    t_next = row_next['time_stamp']
    t_prev = row_prev['time_stamp']
    
    if t_next == t_prev:
        return row_prev
        
    # Linear interpolation factor
    alpha = (current_time - t_prev) / (t_next - t_prev)
    
    # Interpolate numeric fields
    # We only care about specific fields for the packet
    interp_data = {}
    cols = ['speed_kph', 'rpm', 'throttle_pct', 'brake_pct', 'lat', 'long', 'sector_time_ms', 'lap']
    
    for col in cols:
        if col in df.columns:
            val_prev = row_prev[col]
            val_next = row_next[col]
            interp_data[col] = val_prev + (alpha * (val_next - val_prev))
            
    interp_data['gear'] = int(row_prev['gear']) # Gear usually maintains until switch
    interp_data['drs'] = int(row_prev.get('drs', 0))
    interp_data['lap'] = int(row_prev.get('lap', 1))
    interp_data['sector'] = int(row_prev.get('sector', 1))
    
    # Calculate lap distance from speed integration (meters)
    # distance = speed (km/h) * (1000 m/km) / (3600 s/h) * time_elapsed (s)
    if current_time > df['time_stamp'].min():
        # Simplified: use average speed over interval
        lap_start_time = df[df['lap'] == interp_data['lap']]['time_stamp'].min()
        time_in_lap = current_time - lap_start_time
        avg_speed_kph = interp_data['speed_kph']
        # Rough estimate: distance = avg_speed * time
        interp_data['lap_distance'] = avg_speed_kph * (1000/3600) * time_in_lap
        interp_data['total_distance'] = current_time * avg_speed_kph * (1000/3600)  # Rough total
    else:
        interp_data['lap_distance'] = 0.0
        interp_data['total_distance'] = 0.0
    
    return interp_data

def send_replay_loop(df):
    print(f"🏎️ Starting Replay (20Hz) to {UDP_IP}:{UDP_PORT}")
    print("Press Ctrl+C to stop")
    
    start_wall_time = time.time()
    max_sim_time = df['time_stamp'].max()
    min_sim_time = df['time_stamp'].min()
    frame_id = 0
    
    try:
        while True:
            # Calculate simulation time
            elapsed_wall = (time.time() - start_wall_time) * REPLAY_SPEED
            current_sim_time = min_sim_time + (elapsed_wall % max_sim_time) # Loop
            
            # Get data
            data = interpolate_packet(df, current_sim_time)
            
            # ---------------------------------------------------------
            # 1. Car Telemetry Packet (ID 6)
            # ---------------------------------------------------------
            packet_id = PACKET_ID_CAR_TELEMETRY
            header = create_header(packet_id, frame_id, float(current_sim_time))
            
            # Pack Car Data
            # Format: <HfffBbHBBHHHHHBBBBBBBBHffffBBBB (60 bytes)
            # speed, throttle, steer, brake, clutch, gear, rpm, drs, rev%, revBit...
            
            speed = float(data['speed_kph'])
            throttle = float(data['throttle_pct']) / 100.0
            brake = float(data['brake_pct']) / 100.0
            rpm = int(data['rpm'])
            gear = int(data['gear'])
            drs = int(data.get('drs', 0))
            
            car_struct = struct.pack('<HfffBbHBBHHHHHBBBBBBBBHffffBBBB',
                int(speed),     # Speed (H)
                throttle,       # Throttle
                0.0,            # Steer
                brake,          # Brake
                0,              # Clutch
                gear,           # Gear
                rpm,            # RPM
                drs,            # DRS
                int(rpm/12000 * 100), # Rev lights %
                0,              # Rev lights bits
                500, 500, 500, 500, # Brakes temp
                90, 90, 90, 90, # Tyre Surf
                80, 80, 80, 80, # Tyre Inner
                90,             # Engine Temp
                23.5, 23.5, 23.5, 23.5, # Pressures
                0, 0, 0, 0 # Surface
            )
            
            # Fill remaining 21 cars with empty data
            dummy_car = b'\x00' * 60
            payload = car_struct + (dummy_car * 21)
            
            sock.sendto(header + payload, (UDP_IP, UDP_PORT))
            
            # ---------------------------------------------------------
            # 2. Lap Data Packet (ID 2)
            # ---------------------------------------------------------
            packet_id = PACKET_ID_LAP_DATA
            header = create_header(packet_id, frame_id, float(current_sim_time))
            
            # Format: <IIHHfffBBBBBBBBBBBBBBHHB (43 bytes)
            # LastLap, CurLap, S1, S2, Dist, Tot, SC...
            
            current_lap_time = int(current_sim_time * 1000) # ms
            lap_num = int(data['lap'])
            sector = int(data.get('sector', 1))
            
            lap_struct = struct.pack('<IIHHfffBBBBBBBBBBBBBBHHB',
                83000,          # Last Lap ms
                current_lap_time, # Current Lap ms
                25000, 28000,   # Sectors
                float(interp_data.get('lap_distance', 0)),  # Lap Distance (calculated below)
                float(interp_data.get('total_distance', 0)),  # Total Distance
                0.0,            # Safety Car
                1,              # Car Position
                lap_num,        # Current Lap
                0,              # Pit Status
                0,              # Num Pit Stops
                sector,         # Sector
                0,              # Current Lap Invalid
                0,              # Penalties
                0,              # Warnings
                0,              # Unserved Drive Through
                0,              # Unserved Stop Go
                1,              # Grid Position
                4,              # Driver Status (On Track)
                2,              # Result Status (Active)
                0,              # Pit Lane Timer Active
                0,              # Pit Lane Time
                0,              # Pit Stop Timer
                0,              # Pit Stop Should Serve Pen
            )
            
            # Fill remaining 21 cars
            dummy_lap = b'\x00' * 43
            payload = lap_struct + (dummy_lap * 21)
            
            sock.sendto(header + payload, (UDP_IP, UDP_PORT))
            
            # Loop control
            frame_id += 1
            time.sleep(UPDATE_RATE)
            
    except KeyboardInterrupt:
        print("\n🛑 Replay Stopped")

if __name__ == "__main__":
    df = load_telemetry_data()
    if df is not None:
        send_replay_loop(df)
