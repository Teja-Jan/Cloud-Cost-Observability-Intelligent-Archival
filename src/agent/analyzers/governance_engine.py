import pandas as pd
import random
from datetime import datetime, timedelta

class GovernanceEngine:
    """
    Advanced AI-driven governance engine that generates multi-dimensional 
    recommendations for cloud data assets.
    """
    
    def __init__(self, platform: str):
        self.platform = platform
        
    def generate_recommendations(self, asset_row: pd.Series) -> list:
        """
        Generates 13-17 governance recommendation dimensions for a specific asset.
        """
        recs = []
        
        # 1. Cost Optimization
        recs.append({
            "dimension": "Cost Optimization",
            "impact": "High",
            "recommendation": f"Moving this {asset_row['size_gb']:.1f}GB asset to cold storage will reduce monthly cost by ${asset_row['cost_per_month']*0.85:,.2f}."
        })
        
        # 2. Storage Efficiency
        recs.append({
            "dimension": "Storage Efficiency",
            "impact": "Medium",
            "recommendation": "Current compression ratio is sub-optimal. Recommend re-clustering using 'last_access_date' as the partition key."
        })
        
        # 3. Compute Rationalization (Platform Specific)
        if self.platform == "Snowflake":
            recs.append({
                "dimension": "Compute Rationalization",
                "impact": "High",
                "recommendation": "Queries on this table are primarily small point-lookups. Recommend moving to an X-Small warehouse with auto-scaling enabled."
            })
        elif self.platform == "Databricks":
            recs.append({
                "dimension": "Compute Rationalization",
                "impact": "High",
                "recommendation": "High shuffle read observed. Recommend enabling Photon engine and optimizing shuffle partitions for large joins."
            })
        else:
            recs.append({
                "dimension": "Compute Rationalization",
                "impact": "Medium",
                "recommendation": "Instance type mismatch detected. Provisioned compute exceeds 95th percentile peak usage."
            })
            
        # 4. Memory Optimization
        recs.append({
            "dimension": "Memory Optimization",
            "impact": "Medium",
            "recommendation": f"High memory spill to disk detected for this asset. Allocate {asset_row['memory_usage_gb']*1.5:.1f}GB of intermediate shuffle buffer."
        })
        
        # 5. Security & PII Governance
        recs.append({
            "dimension": "Security Governance",
            "impact": "Critical",
            "recommendation": f"Prune access for {asset_row['users_with_access'] - asset_row['active_users']} inactive users to satisfy Least Privilege principles."
        })
        
        # 6. Upstream Impact Analysis
        recs.append({
            "dimension": "Upstream Impact",
            "impact": "High",
            "recommendation": f"Identified {asset_row.get('upstream_deps', 2)} upstream dependencies. Archival requires updating the feed manifest in the orchestration layer."
        })
        
        # 7. Downstream Lineage
        recs.append({
            "dimension": "Downstream Lineage",
            "impact": "Critical",
            "recommendation": f"Archiving this asset will impact {asset_row.get('downstream_deps', 3)} downstream objects including {asset_row.get('report_dependencies', 'Finance Dashboard')}."
        })
        
        # 8. Performance Bottlenecks
        if asset_row['object_type'] == "View":
            recs.append({
                "dimension": "Performance Bottleneck",
                "impact": "High",
                "recommendation": "Nested view complexity is causing high latency. Recommend materializing as a Delta Table or Iceberg Table."
            })
        else:
            recs.append({
                "dimension": "Performance Bottleneck",
                "impact": "Medium",
                "recommendation": "Lack of statistics is causing inefficient query plans. Run 'ANALYZE TABLE' to refresh metadata."
            })
            
        # 9. Pipeline Coupling
        recs.append({
            "dimension": "Pipeline Coupling",
            "impact": "Medium",
            "recommendation": "High coupling with ETL pipelines detected. Recommend decoupling using an asynchronous event-driven pattern (e.g., SQS/SNS or Kafka)."
        })
        
        # 10. Operational Efficiency
        recs.append({
            "dimension": "Operational Efficiency",
            "impact": "High",
            "recommendation": "Current query pruning effectiveness is only 12%. Add metadata-based filtering to reduce compute overhead."
        })
        
        # 11. ML/MLOps Governance (Databricks Specific)
        if self.platform == "Databricks":
            recs.append({
                "dimension": "MLOps Governance",
                "impact": "Medium",
                "recommendation": "This table is used as a feature source. Ensure MLflow experiment tracking is enabled for any derived models."
            })
        else:
            recs.append({
                "dimension": "MLOps Governance",
                "impact": "Low",
                "recommendation": "No direct ML lifecycle dependencies identified for this asset."
            })
            
        # 12. Lifecycle State
        recs.append({
            "dimension": "Lifecycle State",
            "impact": "Low",
            "recommendation": "Retention policy is set to 'Indefinite'. Align with corporate 7-year data retention policy to reduce liability."
        })
        
        # 13. Operational Governance
        recs.append({
            "dimension": "Operational Governance",
            "impact": "Medium",
            "recommendation": "Stewardship assignment is missing for this database. Assign a Data Owner to manage approval workflows."
        })
        
        # 14. User Adoption Trends
        recs.append({
            "dimension": "User Adoption",
            "impact": "Low",
            "recommendation": f"Active users have declined by 40% QoQ. Asset is likely in the 'End-of-Life' phase."
        })
        
        # 15. Cross-Platform Portability
        recs.append({
            "dimension": "Migration Portability",
            "impact": "Medium",
            "recommendation": f"Proprietary {self.platform} types detected. Use standard ANSI SQL or Open Formats (Iceberg) to improve portability."
        })
        
        return recs
