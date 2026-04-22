"""
Tests for telemetry_utils module.

Covers: distance computation, track normalization, interpolation,
lap delta, corner detection, and timestamp sanitization.
"""
import sys
import os
import pytest
import pandas as pd
import numpy as np

# Ensure project root is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from telemetry_utils import (
    compute_distance_along_lap,
    normalize_track_coordinates,
    interpolate_lap_by_distance,
    compute_lap_delta,
    find_corner_zones,
    compute_corner_deltas,
)


# ── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def single_lap_df():
    """Single driver, single lap with realistic speed profile."""
    n = 100
    time = np.linspace(0, 90, n)
    speed = 200 + 50 * np.sin(time * 0.1)  # oscillating speed
    return pd.DataFrame({
        'driver': 'VER',
        'lap': 1,
        'time_stamp': time,
        'speed_kph': speed,
    })


@pytest.fixture
def two_lap_df(single_lap_df):
    """Same driver, two laps for delta comparison."""
    lap1 = single_lap_df.copy()
    lap2 = single_lap_df.copy()
    lap2['lap'] = 2
    lap2['time_stamp'] = lap2['time_stamp'] + 100
    # Slightly faster on lap 2
    lap2['speed_kph'] = lap2['speed_kph'] + 5
    return pd.concat([lap1, lap2], ignore_index=True)


@pytest.fixture
def multi_driver_df():
    """Two drivers, one lap each."""
    rows = []
    for driver in ['VER', 'HAM']:
        for t in np.linspace(0, 90, 80):
            rows.append({
                'driver': driver,
                'lap': 1,
                'time_stamp': t,
                'speed_kph': 180 + np.random.normal(0, 30),
            })
    return pd.DataFrame(rows)


# ── compute_distance_along_lap ────────────────────────────────────────────

class TestComputeDistance:
    def test_adds_column(self, single_lap_df):
        result = compute_distance_along_lap(single_lap_df)
        assert 'dist_along_lap' in result.columns

    def test_monotonically_increasing(self, single_lap_df):
        result = compute_distance_along_lap(single_lap_df)
        dists = result['dist_along_lap'].values
        assert all(dists[i] <= dists[i+1] for i in range(len(dists) - 1))

    def test_starts_at_zero(self, single_lap_df):
        result = compute_distance_along_lap(single_lap_df)
        assert result['dist_along_lap'].iloc[0] == pytest.approx(0.0)

    def test_idempotent(self, single_lap_df):
        first = compute_distance_along_lap(single_lap_df)
        second = compute_distance_along_lap(first)
        pd.testing.assert_frame_equal(first, second)

    def test_skips_if_no_speed(self):
        df = pd.DataFrame({
            'driver': ['VER'] * 10,
            'lap': [1] * 10,
            'time_stamp': range(10),
        })
        result = compute_distance_along_lap(df)
        assert 'dist_along_lap' not in result.columns

    def test_handles_duplicate_timestamps(self, single_lap_df):
        """Duplicate timestamps should be dropped, not cause errors."""
        dup = single_lap_df.copy()
        # Insert duplicate row
        dup = pd.concat([dup, dup.iloc[[5]]], ignore_index=True)
        result = compute_distance_along_lap(dup)
        assert 'dist_along_lap' in result.columns
        # No NaN values
        assert not result['dist_along_lap'].isna().any()

    def test_handles_nonmonotonic_timestamps(self):
        """Non-monotonic timestamps should clamp to 0 delta, not negative distance."""
        df = pd.DataFrame({
            'driver': ['VER'] * 5,
            'lap': [1] * 5,
            'time_stamp': [0, 1, 0.5, 2, 3],  # 0.5 is out of order
            'speed_kph': [100, 100, 100, 100, 100],
        })
        result = compute_distance_along_lap(df)
        assert 'dist_along_lap' in result.columns
        dists = result['dist_along_lap'].values
        assert all(dists[i] <= dists[i+1] for i in range(len(dists) - 1))

    def test_multi_driver(self, multi_driver_df):
        """Each driver's distance should reset independently."""
        result = compute_distance_along_lap(multi_driver_df)
        for driver in ['VER', 'HAM']:
            driver_data = result[result['driver'] == driver]
            assert driver_data['dist_along_lap'].iloc[0] == pytest.approx(0.0)


# ── normalize_track_coordinates ───────────────────────────────────────────

class TestNormalizeTrackCoordinates:
    def test_generates_coords_from_distance(self, single_lap_df):
        df = compute_distance_along_lap(single_lap_df)
        result = normalize_track_coordinates(df, use_gps=False)
        assert 'x_coord' in result.columns
        assert 'y_coord' in result.columns

    def test_gps_coords(self):
        df = pd.DataFrame({
            'driver': ['VER'] * 5,
            'lap': [1] * 5,
            'time_stamp': range(5),
            'lat': [51.0, 51.001, 51.002, 51.001, 51.0],
            'long': [-1.0, -1.001, -1.0, -0.999, -1.0],
        })
        result = normalize_track_coordinates(df, use_gps=True)
        assert 'x_coord' in result.columns
        assert 'y_coord' in result.columns
        # Centered: mean should be ~0
        assert result['x_coord'].mean() == pytest.approx(0.0, abs=0.01)


# ── interpolate_lap_by_distance ──────────────────────────────────────────

class TestInterpolateLap:
    def test_returns_correct_num_points(self, single_lap_df):
        df = compute_distance_along_lap(single_lap_df)
        result = interpolate_lap_by_distance(df, num_points=50)
        assert len(result) == 50

    def test_raises_without_distance(self, single_lap_df):
        with pytest.raises((ValueError, KeyError)):
            interpolate_lap_by_distance(single_lap_df, num_points=10)


# ── compute_lap_delta ────────────────────────────────────────────────────

class TestComputeLapDelta:
    def test_returns_delta_columns(self, two_lap_df):
        lap1 = two_lap_df[two_lap_df['lap'] == 1].copy()
        lap2 = two_lap_df[two_lap_df['lap'] == 2].copy()
        delta = compute_lap_delta(lap1, lap2, num_points=50)
        assert not delta.empty
        assert 'delta_ms' in delta.columns
        assert 'distance' in delta.columns

    def test_same_lap_zero_delta(self, single_lap_df):
        delta = compute_lap_delta(single_lap_df, single_lap_df.copy(), num_points=50)
        if not delta.empty:
            assert delta['delta_ms'].abs().max() < 1  # essentially zero


# ── find_corner_zones ────────────────────────────────────────────────────

class TestFindCornerZones:
    def test_detects_corners(self):
        """Create data with a clear low-speed zone."""
        n = 200
        time = np.linspace(0, 100, n)
        speed = np.full(n, 250.0)
        # Insert a corner: low speed from t=40 to t=60
        corner_mask = (time >= 40) & (time <= 60)
        speed[corner_mask] = 120  # below default 200 threshold
        df = pd.DataFrame({
            'driver': 'VER', 'lap': 1,
            'time_stamp': time, 'speed_kph': speed,
        })
        corners = find_corner_zones(df, speed_threshold=200, min_duration=1.0)
        assert len(corners) >= 1
        assert corners[0]['min_speed'] == pytest.approx(120.0)

    def test_no_speed_column(self):
        df = pd.DataFrame({'driver': ['VER'], 'lap': [1], 'time_stamp': [0]})
        corners = find_corner_zones(df)
        assert corners == []

    def test_no_corners(self, single_lap_df):
        """If speed never drops below threshold, no corners detected."""
        df = single_lap_df.copy()
        df['speed_kph'] = 300  # always above 200
        corners = find_corner_zones(df, speed_threshold=200)
        assert corners == []
