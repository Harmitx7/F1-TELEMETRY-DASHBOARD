"""
Analytics Engine — Statistical computations for the F1 Telemetry Dashboard.

Pure computation module. No layout or callback code.
All functions accept a pandas DataFrame and return computed results.
"""
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional


# Columns eligible for statistical analysis
NUMERIC_TELEMETRY_COLS = [
    'speed_kph', 'rpm', 'throttle_pct', 'brake_pct', 'gear', 'drs'
]


def _get_numeric_cols(df: pd.DataFrame) -> list[str]:
    """Return telemetry columns that exist in the DataFrame."""
    return [c for c in NUMERIC_TELEMETRY_COLS if c in df.columns]


# ── 1. Correlation Matrix ────────────────────────────────────────────────────

def compute_correlation_matrix(df: pd.DataFrame) -> pd.DataFrame:
    """
    Pearson correlation between numeric telemetry columns.

    Returns:
        Square DataFrame of correlation coefficients (−1 … +1).
    """
    cols = _get_numeric_cols(df)
    if len(cols) < 2:
        return pd.DataFrame()
    return df[cols].corr(method='pearson').round(3)


# ── 2. Distribution Statistics ───────────────────────────────────────────────

def compute_distributions(
    df: pd.DataFrame,
    column: str
) -> Dict[str, Dict[str, float]]:
    """
    Per-driver distribution stats for a given column.

    Returns dict keyed by driver with mean, std, min, q25, median, q75, max.
    """
    if column not in df.columns:
        return {}

    result: Dict[str, Dict[str, float]] = {}
    for driver, group in df.groupby('driver'):
        series = group[column].dropna()
        if series.empty:
            continue
        result[str(driver)] = {
            'mean': float(series.mean()),
            'std': float(series.std()),
            'min': float(series.min()),
            'q25': float(series.quantile(0.25)),
            'median': float(series.median()),
            'q75': float(series.quantile(0.75)),
            'max': float(series.max()),
            'count': int(len(series)),
        }
    return result


# ── 3. Consistency Scores ────────────────────────────────────────────────────

def compute_consistency_scores(df: pd.DataFrame) -> pd.DataFrame:
    """
    Lap-time consistency per driver: mean, std, coefficient of variation (CV),
    and a 0-100 consistency score (lower CV → higher score).

    Requires 'time_stamp' and 'lap' columns.
    """
    if 'time_stamp' not in df.columns or 'lap' not in df.columns:
        return pd.DataFrame()

    # Compute lap durations
    lap_times = (
        df.groupby(['driver', 'lap'])['time_stamp']
        .agg(duration=lambda s: s.max() - s.min())
        .reset_index()
    )

    stats = (
        lap_times.groupby('driver')['duration']
        .agg(
            mean_lap='mean',
            std_lap='std',
            min_lap='min',
            max_lap='max',
            lap_count='count',
        )
        .reset_index()
    )

    # Coefficient of Variation (%)
    stats['cv_pct'] = (stats['std_lap'] / stats['mean_lap'] * 100).round(2)
    # Consistency score: 100 minus CV (clamped 0-100)
    stats['consistency_score'] = (100 - stats['cv_pct']).clip(0, 100).round(1)

    return stats.sort_values('consistency_score', ascending=False)


# ── 4. Rolling Statistics ────────────────────────────────────────────────────

def compute_rolling_stats(
    df: pd.DataFrame,
    driver: str,
    lap: Optional[int] = None,
    window: int = 20
) -> pd.DataFrame:
    """
    Moving average + smoothed series for speed, throttle, brake.

    Args:
        df: Full telemetry DataFrame
        driver: Driver code
        lap: Optional specific lap (all laps if None)
        window: Rolling window size (number of samples)

    Returns:
        DataFrame with original + _ma (moving-average) columns.
    """
    mask = df['driver'] == driver
    if lap is not None:
        mask &= df['lap'] == lap
    subset = df.loc[mask].sort_values('time_stamp').copy()

    if subset.empty:
        return pd.DataFrame()

    for col in ['speed_kph', 'throttle_pct', 'brake_pct']:
        if col in subset.columns:
            subset[f'{col}_ma'] = (
                subset[col]
                .rolling(window=window, min_periods=1, center=True)
                .mean()
                .round(2)
            )
    return subset


# ── 5. Percentile Profile ────────────────────────────────────────────────────

def compute_percentile_profile(
    df: pd.DataFrame,
    driver: str
) -> Dict[str, float]:
    """
    Percentile rank of *driver* for each metric relative to all drivers.

    A value of 90 means the driver's average is higher than 90 % of drivers.
    Returns dict mapping metric name → percentile (0-100).
    """
    cols = _get_numeric_cols(df)
    if not cols or driver not in df['driver'].values:
        return {}

    driver_means = df.groupby('driver')[cols].mean()
    target = driver_means.loc[driver]

    profile: Dict[str, float] = {}
    for col in cols:
        series = driver_means[col]
        # percentile rank: fraction of drivers with value <= target
        rank = (series <= target[col]).sum() / len(series) * 100
        profile[col] = round(rank, 1)

    return profile
