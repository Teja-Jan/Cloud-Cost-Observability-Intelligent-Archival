class PricingEngine:
    """
    Handles dynamic cost calculations based on native platform pricing methodologies.
    Supports adjusting base rates and applying discounts (concessions, negotiated pricing).
    """
    def __init__(self, config=None):
        self.config = config or {}
        
        # Advanced Base Rates mimicking native platform tiers
        self.base_rates = {
            "Snowflake": {
                "compute": 3.00,       # per Snowflake Credit (Enterprise)
                "storage": 23.00 / 1000, # $23 per TB -> $0.023 per GB (Active compressed)
                "transfer": 0.12
            },
            "Databricks": {
                "compute": 0.40,       # per DBU (Premium Job Compute)
                "storage": 0.023,      # Underlying AWS S3 equivalent
                "transfer": 0.09
            },
            "BigQuery": {
                "compute": 6.25 / 1000, # $6.25 per TB processed -> $0.00625 per GB
                "storage": 0.020,      # Active logical storage per GB
                "long_term_storage": 0.010, # Long term (90+ days) per GB
                "transfer": 0.12
            },
            "AWS": {
                "compute": 0.10,       # Blended vCPU hour (e.g., m5 series avg)
                "storage": 0.023,      # S3 Standard per GB
                "glacier_storage": 0.0036, # S3 Glacier Flexible per GB
                "transfer": 0.09
            },
            "Azure": {
                "compute": 0.096,      # Blended VM hour
                "storage": 0.0184,     # Blob Hot per GB
                "archive_storage": 0.00099, # Blob Archive
                "transfer": 0.08
            },
            "Google Cloud Platform": {
                "compute": 0.10,
                "storage": 0.020,
                "archive_storage": 0.0012,
                "transfer": 0.11
            },
            "Oracle Cloud Infrastructure": {
                "compute": 0.09,
                "storage": 0.0255,
                "transfer": 0.08
            },
            "IBM Cloud": {
                "compute": 0.10,
                "storage": 0.022,
                "transfer": 0.09
            }
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

    def calculate_cost(self, platform: str, compute_units: float, storage_gb: float, transfer_gb: float, inactive_storage_gb: float = 0.0) -> dict:
        """
        Calculate the total cost given raw usage units and current pricing logic.
        Validates against native capabilities:
        - BigQuery uses long-term storage for inactive assets.
        - AWS/Azure/GCP use Archive/Glacier for inactive assets.
        """
        if platform not in self.base_rates:
            return {"compute": 0, "storage": 0, "transfer": 0, "total": 0}
        
        rates = self.base_rates[platform]
        mults = self.multipliers[platform]
        
        compute_cost = compute_units * rates["compute"] * mults["compute"]
        
        active_storage_gb = max(0, storage_gb - inactive_storage_gb)
        
        if platform == "BigQuery":
            storage_cost = (active_storage_gb * rates["storage"] * mults["storage"]) + \
                           (inactive_storage_gb * rates["long_term_storage"] * mults["storage"])
        elif platform == "AWS":
            storage_cost = (active_storage_gb * rates["storage"] * mults["storage"]) + \
                           (inactive_storage_gb * rates["glacier_storage"] * mults["storage"])
        elif platform == "Azure":
            storage_cost = (active_storage_gb * rates["storage"] * mults["storage"]) + \
                           (inactive_storage_gb * rates["archive_storage"] * mults["storage"])
        elif platform == "Google Cloud Platform":
            storage_cost = (active_storage_gb * rates["storage"] * mults["storage"]) + \
                           (inactive_storage_gb * rates["archive_storage"] * mults["storage"])
        else:
            # Snowflake, Databricks generally use flat blended storage unless specifically external tables
            storage_cost = storage_gb * rates["storage"] * mults["storage"]
            
        transfer_cost = transfer_gb * rates["transfer"] * mults["transfer"]
        
        return {
            "compute": round(compute_cost, 2),
            "storage": round(storage_cost, 2),
            "transfer": round(transfer_cost, 2),
            "total": round(compute_cost + storage_cost + transfer_cost, 2)
        }
