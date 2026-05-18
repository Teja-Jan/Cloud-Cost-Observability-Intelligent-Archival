import pandas as pd
from datetime import datetime
from .pricing_engine import PricingEngine

class HoardingAnalyzer:
    """
    Identifies unused or low-utilization data assets (Data Hoarding).
    Calculates accumulated storage cost and potential archival savings.
    """
    def __init__(self, assets_df: pd.DataFrame, pricing_engine: PricingEngine):
        self.df = assets_df.copy()
        self.df['last_queried_date'] = pd.to_datetime(self.df['last_queried_date'])
        self.pricing_engine = pricing_engine
        
    def analyze_hoarding(self, inactivity_threshold_days: int = 365) -> pd.DataFrame:
        """
        Scan assets to find items older than threshold.
        Calculate cost savings assuming moving from Standard to Archive tier (approx 90% cheaper).
        """
        now = datetime.now()
        
        # Calculate days inactive
        self.df['days_inactive'] = (now - self.df['last_queried_date']).dt.days
        
        # Identify Hoarded Assets
        hoarded_df = self.df[self.df['days_inactive'] > inactivity_threshold_days].copy()
        
        if hoarded_df.empty:
            return pd.DataFrame()
            
        # Calculate costs and savings
        def calc_savings(row):
            # Calculate standard cost per month
            standard_cost = self.pricing_engine.calculate_cost(
                row['platform'], compute_units=0, storage_gb=row['size_gb'], transfer_gb=0
            )['storage']
            
            # Archive tier assumption: 10% of standard cost
            archive_cost = standard_cost * 0.10
            
            monthly_savings = standard_cost - archive_cost
            five_year_savings = monthly_savings * 12 * 5
            
            return pd.Series({
                'current_monthly_cost': standard_cost,
                'archive_monthly_cost': archive_cost,
                'monthly_savings': monthly_savings,
                'five_year_savings': five_year_savings
            })
            
        savings_df = hoarded_df.apply(calc_savings, axis=1)
        result_df = pd.concat([hoarded_df, savings_df], axis=1)
        
        # Sort by biggest savings
        result_df = result_df.sort_values('five_year_savings', ascending=False)
        return result_df
