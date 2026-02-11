"""
Telemetry Utilities for F1 Dashboard
Provides helper functions for track map generation and lap delta analysis
"""

import pandas as pd
import numpy as np
from scipy.interpolate import interp1d


def compute_distance_along_lap(df):
    """
    Compute cumulative distance along lap from speed and timestamps.
    
    Formula: distance = Σ (speed_kph * 1000/3600 * Δt)
    
    Args:
        df: DataFrame with columns ['driver', 'lap', 'time_stamp', 'speed_kph']
    
    Returns:
        DataFrame with added 'dist_along_lap' column (if speed_kph available)
    """
    if 'dist_along_lap' in df.columns:
        return df
        
    # RELAXED VALIDATION: If speed_kph is missing, we cannot compute distance
    if 'speed_kph' not in df.columns:
        return df
    
    df = df.sort_values(['driver', 'lap', 'time_stamp']).copy()
    
    def calc_distance(group):
        """Calculate distance for a single lap"""
        group = group.sort_values('time_stamp').copy()
        
        # Calculate time differences
        time_diff = group['time_stamp'].diff().fillna(0)
        
        # Convert speed from km/h to m/s and multiply by time
        speed_ms = group['speed_kph'] * 1000 / 3600
        distance_increment = speed_ms * time_diff
        
        # Cumulative sum
        group['dist_along_lap'] = distance_increment.cumsum()
        
        return group
    
    df = df.groupby(['driver', 'lap'], group_keys=False).apply(calc_distance)
    
    return df


def normalize_track_coordinates(df, use_gps=True):
    """
    Convert telemetry data to normalized (x, y) track coordinates.
    
    Args:
        df: DataFrame with either ['lat', 'long'] or ['dist_along_lap']
        use_gps: If True, use GPS coordinates; if False, generate from distance
    
    Returns:
        DataFrame with added 'x_coord' and 'y_coord' columns
    """
    df = df.copy()
    
    if use_gps and 'lat' in df.columns and 'long' in df.columns:
        # Use GPS coordinates directly
        df['x_coord'] = df['long']
        df['y_coord'] = df['lat']
        
        # Center coordinates
        x_center = df['x_coord'].mean()
        y_center = df['y_coord'].mean()
        df['x_coord'] = df['x_coord'] - x_center
        df['y_coord'] = df['y_coord'] - y_center
        
        # Scale to reasonable range (preserve aspect ratio)
        max_range = max(df['x_coord'].abs().max(), df['y_coord'].abs().max())
        if max_range > 0:
            df['x_coord'] = df['x_coord'] / max_range
            df['y_coord'] = df['y_coord'] / max_range
    
    else:
        # Generate pseudo-coordinates from distance
        if 'dist_along_lap' not in df.columns:
            df = compute_distance_along_lap(df)
        
        # Get max distance for normalization
        max_dist = df.groupby(['driver', 'lap'])['dist_along_lap'].max().max()
        
        if max_dist > 0:
            # Create parametric track shape (oval-ish with straights)
            # Normalize distance to 0-2π range
            theta = (df['dist_along_lap'] / max_dist) * 2 * np.pi
            
            # Generate track shape with straights and curves
            # Using a modified circle with elongated sections
            df['x_coord'] = 1.5 * np.sin(theta) + 0.3 * np.sin(3 * theta)
            df['y_coord'] = np.cos(theta) + 0.2 * np.cos(2 * theta)
        else:
            df['x_coord'] = 0
            df['y_coord'] = 0
    
    return df


def interpolate_lap_by_distance(lap_data, distance_grid=None, num_points=200):
    """
    Interpolate lap telemetry at uniform distance intervals.
    
    Args:
        lap_data: DataFrame for a single lap with 'dist_along_lap' and 'time_stamp'
        distance_grid: Optional array of distance points; if None, creates uniform grid
        num_points: Number of interpolation points if distance_grid not provided
    
    Returns:
        DataFrame with interpolated values at uniform distances
    """
    lap_data = lap_data.sort_values('dist_along_lap').copy()
    
    # Ensure we have distance data
    if 'dist_along_lap' not in lap_data.columns:
        raise ValueError("lap_data must contain 'dist_along_lap' column")
    
    # Create distance grid if not provided
    if distance_grid is None:
        min_dist = lap_data['dist_along_lap'].min()
        max_dist = lap_data['dist_along_lap'].max()
        distance_grid = np.linspace(min_dist, max_dist, num_points)
    
    # Interpolate time as function of distance
    try:
        time_interp = interp1d(
            lap_data['dist_along_lap'], 
            lap_data['time_stamp'],
            kind='linear',
            bounds_error=False,
            fill_value='extrapolate'
        )
        
        interpolated_time = time_interp(distance_grid)
        
        # Create result DataFrame
        result = pd.DataFrame({
            'dist_along_lap': distance_grid,
            'time_stamp': interpolated_time
        })
        
        # Interpolate other columns if present
        for col in ['speed_kph', 'throttle_pct', 'brake_pct', 'rpm']:
            if col in lap_data.columns:
                col_interp = interp1d(
                    lap_data['dist_along_lap'],
                    lap_data[col],
                    kind='linear',
                    bounds_error=False,
                    fill_value='extrapolate'
                )
                result[col] = col_interp(distance_grid)
        
        return result
    
    except Exception as e:
        print(f"Interpolation error: {e}")
        return pd.DataFrame()


def compute_lap_delta(lap_a_data, lap_b_data, num_points=200):
    """
    Compute time delta between two laps using distance-based alignment.
    
    Delta = time_B(distance) - time_A(distance)
    Positive delta means Lap B is slower (time loss)
    Negative delta means Lap B is faster (time gain)
    
    Args:
        lap_a_data: DataFrame for reference lap (Lap A)
        lap_b_data: DataFrame for comparison lap (Lap B)
        num_points: Number of points for delta calculation
    
    Returns:
        DataFrame with columns: ['distance', 'delta_ms', 'delta_color', 'cumulative_delta']
    """
    # Ensure both laps have distance data
    if 'dist_along_lap' not in lap_a_data.columns:
        lap_a_data = compute_distance_along_lap(lap_a_data)
    if 'dist_along_lap' not in lap_b_data.columns:
        lap_b_data = compute_distance_along_lap(lap_b_data)
    
    # SAFETY CHECK: If distance calculation failed (e.g. no speed data), return empty
    if 'dist_along_lap' not in lap_a_data.columns or 'dist_along_lap' not in lap_b_data.columns:
        return pd.DataFrame()

    # Find common distance range
    min_dist = max(lap_a_data['dist_along_lap'].min(), lap_b_data['dist_along_lap'].min())
    max_dist = min(lap_a_data['dist_along_lap'].max(), lap_b_data['dist_along_lap'].max())
    
    if min_dist >= max_dist:
        return pd.DataFrame()
    
    # Create uniform distance grid
    distance_grid = np.linspace(min_dist, max_dist, num_points)
    
    # Interpolate both laps
    lap_a_interp = interpolate_lap_by_distance(lap_a_data, distance_grid)
    lap_b_interp = interpolate_lap_by_distance(lap_b_data, distance_grid)
    
    if lap_a_interp.empty or lap_b_interp.empty:
        return pd.DataFrame()
    
    # Compute delta in milliseconds
    delta_seconds = lap_b_interp['time_stamp'].values - lap_a_interp['time_stamp'].values
    delta_ms = delta_seconds * 1000
    
    # Determine color based on delta (green = gain, red = loss)
    # Negative delta = Lap B faster = green
    # Positive delta = Lap B slower = red
    delta_colors = ['#7eff7a' if d < 0 else '#ff4654' for d in delta_ms]
    
    # Create result DataFrame
    result = pd.DataFrame({
        'distance': distance_grid,
        'delta_ms': delta_ms,
        'delta_color': delta_colors,
        'cumulative_delta': np.cumsum(delta_ms)
    })
    
    return result


def find_corner_zones(lap_data, speed_threshold=200, min_duration=1.0):
    """
    Auto-detect corner zones from speed and brake data.
    
    Args:
        lap_data: DataFrame for a single lap
        speed_threshold: Speed below which is considered a corner (km/h)
        min_duration: Minimum duration for a corner zone (seconds)
    
    Returns:
        List of dicts with corner information: [{'name', 'start_dist', 'end_dist', 'min_speed'}]
    """
    if 'dist_along_lap' not in lap_data.columns:
        lap_data = compute_distance_along_lap(lap_data)
    
    lap_data = lap_data.sort_values('time_stamp').copy()
    
    # Identify low-speed zones
    lap_data['is_corner'] = lap_data['speed_kph'] < speed_threshold
    
    # Find corner segments
    corners = []
    in_corner = False
    corner_start_idx = None
    
    for idx, row in lap_data.iterrows():
        if row['is_corner'] and not in_corner:
            # Corner starts
            in_corner = True
            corner_start_idx = idx
        elif not row['is_corner'] and in_corner:
            # Corner ends
            in_corner = False
            corner_segment = lap_data.loc[corner_start_idx:idx]
            
            # Check duration
            duration = corner_segment['time_stamp'].max() - corner_segment['time_stamp'].min()
            if duration >= min_duration:
                corners.append({
                    'name': f'Corner {len(corners) + 1}',
                    'start_dist': corner_segment['dist_along_lap'].iloc[0],
                    'end_dist': corner_segment['dist_along_lap'].iloc[-1],
                    'min_speed': corner_segment['speed_kph'].min()
                })
    
    return corners


def compute_corner_deltas(delta_df, corners):
    """
    Compute delta time for each corner zone.
    
    Args:
        delta_df: DataFrame from compute_lap_delta()
        corners: List of corner dicts from find_corner_zones()
    
    Returns:
        List of dicts with corner delta info: [{'name', 'delta_ms', 'type'}]
    """
    corner_deltas = []
    
    for corner in corners:
        # Find delta points within corner range
        corner_delta = delta_df[
            (delta_df['distance'] >= corner['start_dist']) &
            (delta_df['distance'] <= corner['end_dist'])
        ]
        
        if not corner_delta.empty:
            # Calculate delta across corner
            delta_change = corner_delta['delta_ms'].iloc[-1] - corner_delta['delta_ms'].iloc[0]
            
            corner_deltas.append({
                'name': corner['name'],
                'delta_ms': delta_change,
                'type': 'gain' if delta_change < 0 else 'loss'
            })
    
    return corner_deltas
