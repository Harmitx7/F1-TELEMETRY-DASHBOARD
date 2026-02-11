"""
Utility Helper Functions
Common utilities for data processing and UI generation.
"""
from functools import lru_cache
from typing import Any, Dict, Optional
import pandas as pd
from config import Config
import plotly.graph_objects as go


@lru_cache(maxsize=Config.CACHE_SIZE)
def validate_dataframe(df_json: str) -> tuple[bool, str]:
    """
    Validate that the uploaded DataFrame has required columns.
    Cached for performance.
    
    Args:
        df_json: JSON string of DataFrame
        
    Returns:
        Tuple of (is_valid, message)
    """
    try:
        df = pd.read_json(df_json, orient='split')
        required_columns = Config.REQUIRED_COLUMNS
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            return False, f"Missing required columns: {', '.join(missing_columns)}"
        return True, "Valid"
    except Exception as e:
        return False, f"Validation error: {str(e)}"


@lru_cache(maxsize=Config.CACHE_SIZE)
def compute_lap_times_cached(df_json: str) -> str:
    """
    Compute lap times from time_stamp if lap_time_ms is missing.
    Cached version for performance.
    
    Args:
        df_json: JSON string of DataFrame
        
    Returns:
        JSON string of DataFrame with lap times computed
    """
    df = pd.read_json(df_json, orient='split')
    
    if 'lap_time_ms' in df.columns:
        return df.to_json(date_format='iso', orient='split')
    
    # Vectorized computation - much faster than iterative approach
    lap_times = df.groupby(['driver', 'lap'], as_index=False).agg({
        'time_stamp': ['min', 'max']
    })
    lap_times.columns = ['driver', 'lap', 'min_time', 'max_time']
    lap_times['lap_time_ms'] = ((lap_times['max_time'] - lap_times['min_time']) * 1000).astype(int)
    lap_times = lap_times[['driver', 'lap', 'lap_time_ms']]
    
    # Merge back to original dataframe
    df = df.merge(lap_times, on=['driver', 'lap'], how='left')
    return df.to_json(date_format='iso', orient='split')


def compute_lap_times(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute lap times from time_stamp if lap_time_ms is missing.
    Non-cached version for direct DataFrame usage.
    
    Args:
        df: Input DataFrame
        
    Returns:
        DataFrame with lap times computed
    """
    if 'lap_time_ms' in df.columns:
        return df
    
    # Vectorized computation
    lap_times = df.groupby(['driver', 'lap'], as_index=False).agg({
        'time_stamp': ['min', 'max']
    })
    lap_times.columns = ['driver', 'lap', 'min_time', 'max_time']
    lap_times['lap_time_ms'] = ((lap_times['max_time'] - lap_times['min_time']) * 1000).astype(int)
    lap_times = lap_times[['driver', 'lap', 'lap_time_ms']]
    
    # Merge back
    df = df.merge(lap_times, on=['driver', 'lap'], how='left')
    return df


@lru_cache(maxsize=Config.CACHE_SIZE)
def get_dataset_summary_cached(df_json: str) -> Dict[str, Any]:
    """
    Generate summary statistics for the dataset (cached).
    
    Args:
        df_json: JSON string of DataFrame
        
    Returns:
        Dictionary containing summary statistics
    """
    df = pd.read_json(df_json, orient='split')
    return get_dataset_summary(df)


def get_dataset_summary(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Generate summary statistics for the dataset.
    
    Args:
        df: Input DataFrame
        
    Returns:
        Dictionary containing summary statistics
    """
    if df is None or df.empty:
        return {}
    
    total_laps = df.groupby(['driver', 'lap']).ngroups
    drivers = df['driver'].unique().tolist()
    
    # Compute lap times if needed
    df_with_times = compute_lap_times(df.copy())
    lap_summary = df_with_times.groupby(['driver', 'lap'])['lap_time_ms'].first().reset_index()
    
    if not lap_summary.empty:
        fastest_lap_row = lap_summary.loc[lap_summary['lap_time_ms'].idxmin()]
        fastest_lap = f"{fastest_lap_row['driver']} - Lap {fastest_lap_row['lap']} ({fastest_lap_row['lap_time_ms']/1000:.3f}s)"
        avg_lap_time = f"{lap_summary['lap_time_ms'].mean()/1000:.3f}s"
    else:
        fastest_lap = "N/A"
        avg_lap_time = "N/A"
    
    session_duration = f"{df['time_stamp'].max():.1f}s"
    
    return {
        'total_laps': total_laps,
        'drivers': ', '.join(drivers),
        'drivers_count': len(drivers),
        'fastest_lap': fastest_lap,
        'avg_lap_time': avg_lap_time,
        'session_duration': session_duration,
        'total_rows': len(df)
    }


def create_disabled_figure(title: str, message: str) -> go.Figure:
    """
    Create a placeholder figure for disabled features.
    
    Args:
        title: Figure title
        message: Message to display
        
    Returns:
        Plotly Figure object
    """
    fig = go.Figure()
    layout = Config.get_chart_layout_base()
    layout.update({
        'xaxis': {'visible': False},
        'yaxis': {'visible': False},
        'annotations': [{
            'text': f'<b>{title}</b><br><br>{message}',
            'xref': 'paper',
            'yref': 'paper',
            'x': 0.5,
            'y': 0.5,
            'showarrow': False,
            'font': {'size': 14, 'color': Config.COLORS['text_secondary']},
            'align': 'center'
        }],
    })
    fig.update_layout(layout)
    return fig


def downsample_dataframe(df: pd.DataFrame, max_points: int = Config.CHART_MAX_POINTS) -> pd.DataFrame:
    """
    Downsample DataFrame to maximum number of points for chart performance.
    Uses stratified sampling to maintain data distribution.
    
    Args:
        df: Input DataFrame
        max_points: Maximum number of points to keep
        
    Returns:
        Downsampled DataFrame
    """
    if len(df) <= max_points:
        return df
    
    # Calculate sampling rate
    sample_rate = max_points / len(df)
    
    # Stratified sampling - sample evenly across the dataset
    return df.sample(frac=sample_rate, random_state=42).sort_index()
