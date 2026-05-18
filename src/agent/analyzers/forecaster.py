"""
Linear Trend Forecaster
-----------------------
Forecasting Model: Ordinary Least Squares (OLS) Linear Regression via np.polyfit.

Model Justification:
  - Historical usage data shows steady, monotonic growth trends with low seasonality.
  - Linear Regression provides mathematically explainable and auditable projections.
  - Appropriate for 1-to-5 year enterprise budget planning horizons.
  - For datasets with strong weekly/yearly seasonality, Prophet would be preferred.

Accuracy Approach:
  - Baseline is computed as the mean of the last 30 days to reduce short-term noise.
  - All WoW/MoM/YoY percentages are calculated relative to this 30-day mean baseline.
  - Projections use the OLS trendline evaluated at the exact future day number.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from .pricing_engine import PricingEngine


class Forecaster:
    """
    Analyzes historical cloud usage data to generate WoW, MoM, YoY, 1-Year,
    and 5-Year projections using a Linear Regression trend model.
    """

    METRICS = ['storage_gb', 'compute_units', 'data_transfer_gb', 'memory_usage_gb']

    def __init__(self, usage_df: pd.DataFrame, pricing_engine: PricingEngine):
        self.df = usage_df.copy()
        self.df['usage_date'] = pd.to_datetime(self.df['usage_date'])
        self.pricing_engine = pricing_engine

    # ── Internal helpers ────────────────────────────────────────────────────

    def _build_daily(self, platform: str) -> pd.DataFrame:
        """Aggregate usage to daily level for a given platform."""
        plat_df = self.df[self.df['platform'] == platform]
        if plat_df.empty:
            return pd.DataFrame()
        daily = (
            plat_df
            .groupby('usage_date')[self.METRICS]
            .sum()
            .reset_index()
            .sort_values('usage_date')
        )
        start = daily['usage_date'].min()
        daily['day_num'] = (daily['usage_date'] - start).dt.days
        return daily

    def _fit_models(self, daily_df: pd.DataFrame) -> dict:
        """Fit a linear model (slope, intercept) for each metric."""
        return {
            m: np.polyfit(daily_df['day_num'], daily_df[m], 1)
            for m in self.METRICS
        }

    def _project_at(self, models: dict, future_day_num: int) -> dict:
        """Project all metrics at a given future day number."""
        result = {}
        for m, (slope, intercept) in models.items():
            result[m] = max(0.0, slope * future_day_num + intercept)
        return result

    def _add_cost(self, platform: str, metrics: dict) -> dict:
        """Attach cost breakdown to a metrics dict (in-place, returns dict)."""
        cost = self.pricing_engine.calculate_cost(
            platform,
            metrics['compute_units'],
            metrics['storage_gb'],
            metrics['data_transfer_gb'],
        )
        metrics['total_cost']    = cost['total']
        metrics['compute_cost']  = cost['compute']
        metrics['storage_cost']  = cost['storage']
        metrics['transfer_cost'] = cost['transfer']
        return metrics

    # ── Public API ──────────────────────────────────────────────────────────

    def generate_projections(self, platform: str) -> dict:
        """
        Generate Current, WoW, MoM, YoY, 1-Year, and 5-Year projections.

        Baseline (Current): mean of the last 30 days of recorded data.
        All % changes are relative to this 30-day mean baseline.
        """
        daily = self._build_daily(platform)
        if daily.empty:
            return {}

        models = self._fit_models(daily)
        start_date = daily['usage_date'].min()
        last_date  = daily['usage_date'].max()

        # ── Baseline: 30-day mean (robust, less noisy than last-7) ──
        last_30 = daily.tail(30).mean(numeric_only=True)
        current = {m: float(last_30[m]) for m in self.METRICS}
        current = self._add_cost(platform, current)

        # ── Projection horizons ──
        horizons = {
            'WoW':    last_date + timedelta(days=7),
            'MoM':    last_date + relativedelta(months=1),
            'YoY':    last_date + relativedelta(years=1),
            '1_Year': last_date + relativedelta(years=1),
            '5_Year': last_date + relativedelta(years=5),
        }

        projections = {'Current': current}
        for label, future_date in horizons.items():
            future_day = (future_date - start_date).days
            proj = self._project_at(models, future_day)
            proj = self._add_cost(platform, proj)
            projections[label] = proj

        # ── Insight / Rationalization ──
        # Use cost slope from OLS fit across entire history
        cost_series = [
            self.pricing_engine.calculate_cost(
                platform, r['compute_units'], r['storage_gb'], r['data_transfer_gb']
            )['total']
            for _, r in daily.iterrows()
        ]
        cost_slope = np.polyfit(daily['day_num'], cost_series, 1)[0]

        if cost_slope > 0.05:
            reason = (
                "Steady organic growth in data ingestion and compute-intensive "
                "workloads is driving a consistent upward cost trajectory. "
                "Archiving inactive assets and right-sizing compute clusters "
                "are recommended priority actions."
            )
        elif cost_slope < -0.05:
            reason = (
                "Ongoing optimization initiatives and archival workflows are "
                "successfully reducing the platform's resource footprint. "
                "Continue monitoring to sustain the downward trend."
            )
        else:
            reason = (
                "Usage patterns are stable with minimal variance across the "
                "observed period. Workload demand is predictable, making this "
                "platform a low-risk candidate for budget planning."
            )

        projections['Insight'] = {
            'reason':         reason,
            'model':          'Linear Trend Analysis (OLS)',
            'baseline_days':  30,
            'cost_slope':     cost_slope,
            'storage_slope':  models['storage_gb'][0],
            'compute_slope':  models['compute_units'][0],
            'memory_slope':   models['memory_usage_gb'][0],
        }

        return projections

    def generate_timeline(self, platform: str, years: int = 5) -> pd.DataFrame:
        """
        Generate a monthly timeline DataFrame for plotting.
        Returns columns: usage_date, platform, type, storage_gb, compute_units,
                         data_transfer_gb, memory_usage_gb, total_cost.
        """
        daily = self._build_daily(platform)
        if daily.empty:
            return pd.DataFrame()

        models    = self._fit_models(daily)
        start_date = daily['usage_date'].min()
        last_date  = daily['usage_date'].max()
        end_date   = last_date + relativedelta(years=years)

        future_dates = pd.date_range(
            start=last_date + relativedelta(months=1),
            end=end_date,
            freq='ME',
        )

        rows = []
        for d in future_dates:
            day_num = (d - start_date).days
            row = {'usage_date': d, 'platform': platform, 'type': 'Forecast'}
            for m, (slope, intercept) in models.items():
                row[m] = max(0.0, slope * day_num + intercept)
            cost = self.pricing_engine.calculate_cost(
                platform, row['compute_units'], row['storage_gb'], row['data_transfer_gb']
            )
            row['total_cost'] = cost['total']
            rows.append(row)

        return pd.DataFrame(rows)

    def generate_historical(self, platform: str) -> pd.DataFrame:
        """Return the aggregated historical usage DataFrame for plotting."""
        daily = self._build_daily(platform)
        if daily.empty:
            return pd.DataFrame()
        daily['type'] = 'Historical'
        cost_col = [
            self.pricing_engine.calculate_cost(
                platform, r['compute_units'], r['storage_gb'], r['data_transfer_gb']
            )['total']
            for _, r in daily.iterrows()
        ]
        daily['total_cost'] = cost_col
        return daily
