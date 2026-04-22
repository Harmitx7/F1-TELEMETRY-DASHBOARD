"""
Tests for app.features.analytics module.

Covers: correlation matrix, distributions, consistency scores,
rolling stats, and percentile profile.
"""
import sys
import os
import pytest
import pandas as pd
import numpy as np

# Ensure project root is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.features.analytics import (
    compute_correlation_matrix,
    compute_distributions,
    compute_consistency_scores,
    compute_rolling_stats,
    compute_percentile_profile,
    NUMERIC_TELEMETRY_COLS,
)


# ── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def sample_df():
    """Minimal realistic telemetry DataFrame for 2 drivers, 3 laps each."""
    np.random.seed(42)
    rows = []
    for driver in ['VER', 'HAM']:
        for lap in [1, 2, 3]:
            for t in np.linspace(0, 90, 50):
                rows.append({
                    'driver': driver,
                    'lap': lap,
                    'time_stamp': t + (lap - 1) * 100,
                    'speed_kph': 200 + np.random.normal(0, 20),
                    'rpm': 10000 + np.random.normal(0, 500),
                    'throttle_pct': max(0, min(100, 70 + np.random.normal(0, 15))),
                    'brake_pct': max(0, min(100, 10 + np.random.normal(0, 8))),
                    'gear': np.random.choice([5, 6, 7, 8]),
                    'drs': np.random.choice([0, 1]),
                })
    return pd.DataFrame(rows)


@pytest.fixture
def empty_df():
    """Empty DataFrame with correct columns."""
    return pd.DataFrame(columns=['driver', 'lap', 'time_stamp', 'speed_kph'])


# ── 1. Correlation Matrix ────────────────────────────────────────────────────

class TestCorrelationMatrix:
    def test_returns_square_df(self, sample_df):
        corr = compute_correlation_matrix(sample_df)
        assert not corr.empty
        assert corr.shape[0] == corr.shape[1]

    def test_diagonal_is_one(self, sample_df):
        corr = compute_correlation_matrix(sample_df)
        for col in corr.columns:
            assert corr.loc[col, col] == pytest.approx(1.0, abs=0.001)

    def test_values_in_range(self, sample_df):
        corr = compute_correlation_matrix(sample_df)
        assert (corr.values >= -1).all()
        assert (corr.values <= 1).all()

    def test_empty_input(self, empty_df):
        corr = compute_correlation_matrix(empty_df)
        assert corr.empty

    def test_single_numeric_col(self):
        df = pd.DataFrame({'speed_kph': [100, 200, 300]})
        corr = compute_correlation_matrix(df)
        assert corr.empty  # needs at least 2 columns


# ── 2. Distributions ─────────────────────────────────────────────────────────

class TestDistributions:
    def test_returns_per_driver(self, sample_df):
        dist = compute_distributions(sample_df, 'speed_kph')
        assert 'VER' in dist
        assert 'HAM' in dist

    def test_stats_keys(self, sample_df):
        dist = compute_distributions(sample_df, 'speed_kph')
        expected_keys = {'mean', 'std', 'min', 'q25', 'median', 'q75', 'max', 'count'}
        for driver_stats in dist.values():
            assert expected_keys <= set(driver_stats.keys())

    def test_missing_column(self, sample_df):
        dist = compute_distributions(sample_df, 'nonexistent_col')
        assert dist == {}

    def test_median_between_q25_q75(self, sample_df):
        dist = compute_distributions(sample_df, 'speed_kph')
        for stats in dist.values():
            assert stats['q25'] <= stats['median'] <= stats['q75']


# ── 3. Consistency Scores ────────────────────────────────────────────────────

class TestConsistencyScores:
    def test_returns_all_drivers(self, sample_df):
        stats = compute_consistency_scores(sample_df)
        assert set(stats['driver'].tolist()) == {'VER', 'HAM'}

    def test_score_range(self, sample_df):
        stats = compute_consistency_scores(sample_df)
        assert (stats['consistency_score'] >= 0).all()
        assert (stats['consistency_score'] <= 100).all()

    def test_cv_nonnegative(self, sample_df):
        stats = compute_consistency_scores(sample_df)
        assert (stats['cv_pct'] >= 0).all()

    def test_missing_columns(self):
        df = pd.DataFrame({'driver': ['VER'], 'speed_kph': [200]})
        stats = compute_consistency_scores(df)
        assert stats.empty

    def test_sorted_by_score(self, sample_df):
        stats = compute_consistency_scores(sample_df)
        scores = stats['consistency_score'].tolist()
        assert scores == sorted(scores, reverse=True)


# ── 4. Rolling Stats ─────────────────────────────────────────────────────────

class TestRollingStats:
    def test_returns_ma_columns(self, sample_df):
        rolled = compute_rolling_stats(sample_df, 'VER', lap=1, window=5)
        assert not rolled.empty
        assert 'speed_kph_ma' in rolled.columns

    def test_ma_is_smoother(self, sample_df):
        rolled = compute_rolling_stats(sample_df, 'VER', lap=1, window=10)
        raw_std = rolled['speed_kph'].std()
        ma_std = rolled['speed_kph_ma'].std()
        assert ma_std < raw_std  # moving average should be smoother

    def test_nonexistent_driver(self, sample_df):
        rolled = compute_rolling_stats(sample_df, 'NOBODY', lap=1)
        assert rolled.empty

    def test_all_laps(self, sample_df):
        rolled = compute_rolling_stats(sample_df, 'VER', lap=None, window=5)
        assert not rolled.empty
        assert len(rolled) > 50  # multiple laps combined


# ── 5. Percentile Profile ────────────────────────────────────────────────────

class TestPercentileProfile:
    def test_returns_dict(self, sample_df):
        profile = compute_percentile_profile(sample_df, 'VER')
        assert isinstance(profile, dict)
        assert len(profile) > 0

    def test_values_0_to_100(self, sample_df):
        profile = compute_percentile_profile(sample_df, 'VER')
        for val in profile.values():
            assert 0 <= val <= 100

    def test_nonexistent_driver(self, sample_df):
        profile = compute_percentile_profile(sample_df, 'NOBODY')
        assert profile == {}

    def test_single_driver(self):
        """Single driver should always be at 100th percentile."""
        df = pd.DataFrame({
            'driver': ['VER'] * 10,
            'speed_kph': np.random.normal(200, 10, 10),
            'rpm': np.random.normal(10000, 500, 10),
        })
        profile = compute_percentile_profile(df, 'VER')
        for val in profile.values():
            assert val == 100.0
