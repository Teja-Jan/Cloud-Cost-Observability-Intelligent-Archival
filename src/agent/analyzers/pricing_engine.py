class PricingEngine:
    """
    Handles dynamic cost calculations based on usage.
    Supports adjusting base rates and applying discounts (concessions, negotiated pricing).
    """
    def __init__(self, config=None):
        self.config = config or {}
        
        # Default Base Rates
        self.base_rates = {
            "Snowflake": {"compute": 3.0, "storage": 0.023, "transfer": 0.12},
            "Databricks": {"compute": 2.0, "storage": 0.023, "transfer": 0.09},
            "BigQuery": {"compute": 4.0, "storage": 0.020, "transfer": 0.12},
            "AWS": {"compute": 3.2, "storage": 0.023, "transfer": 0.09},
            "Azure": {"compute": 3.1, "storage": 0.022, "transfer": 0.08},
            "Google Cloud Platform": {"compute": 3.5, "storage": 0.020, "transfer": 0.11},
            "Oracle Cloud Infrastructure": {"compute": 2.8, "storage": 0.021, "transfer": 0.08},
            "IBM Cloud": {"compute": 2.9, "storage": 0.022, "transfer": 0.09}
        }
        
        # Default Multipliers (1.0 = no discount, 0.8 = 20% discount)
        self.multipliers = {
            "Snowflake": {"compute": 1.0, "storage": 1.0, "transfer": 1.0},
            "Databricks": {"compute": 1.0, "storage": 1.0, "transfer": 1.0},
            "BigQuery": {"compute": 1.0, "storage": 1.0, "transfer": 1.0},
            "AWS": {"compute": 1.0, "storage": 1.0, "transfer": 1.0},
            "Azure": {"compute": 1.0, "storage": 1.0, "transfer": 1.0},
            "Google Cloud Platform": {"compute": 1.0, "storage": 1.0, "transfer": 1.0},
            "Oracle Cloud Infrastructure": {"compute": 1.0, "storage": 1.0, "transfer": 1.0},
            "IBM Cloud": {"compute": 1.0, "storage": 1.0, "transfer": 1.0}
        }

    def set_multiplier(self, platform: str, resource_type: str, multiplier: float):
        """Update the discount multiplier for a specific platform and resource."""
        if platform in self.multipliers and resource_type in self.multipliers[platform]:
            self.multipliers[platform][resource_type] = multiplier

    def calculate_cost(self, platform: str, compute_units: float, storage_gb: float, transfer_gb: float) -> dict:
        """Calculate the total cost given raw usage units and current pricing logic."""
        if platform not in self.base_rates:
            return {"compute": 0, "storage": 0, "transfer": 0, "total": 0}
        
        rates = self.base_rates[platform]
        mults = self.multipliers[platform]
        
        compute_cost = compute_units * rates["compute"] * mults["compute"]
        storage_cost = storage_gb * rates["storage"] * mults["storage"]
        transfer_cost = transfer_gb * rates["transfer"] * mults["transfer"]
        
        return {
            "compute": round(compute_cost, 2),
            "storage": round(storage_cost, 2),
            "transfer": round(transfer_cost, 2),
            "total": round(compute_cost + storage_cost + transfer_cost, 2)
        }
