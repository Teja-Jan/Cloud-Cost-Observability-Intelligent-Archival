import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from db import database as db

class GovernanceService:
    """
    Manages the lifecycle of Cloud Intelligence governance requests.
    """
    
    @staticmethod
    def submit_archival_request(asset_name: str, platform: str, projected_savings: float) -> int:
        """Submit a new request to the governance inbox."""
        notes = f"System identified {asset_name} as hoarded data. Recommend archival to Cold Storage."
        return db.create_governance_request(asset_name, platform, 'ARCHIVE', projected_savings, notes)
        
    @staticmethod
    def get_pending_requests() -> list:
        return db.get_governance_requests(status='PENDING')
        
    @staticmethod
    def get_all_requests() -> list:
        return db.get_governance_requests()
        
    @staticmethod
    def approve_request(request_id: int):
        db.update_governance_request_status(request_id, 'APPROVED', "Approved by Governance Team.")
        
    @staticmethod
    def reject_request(request_id: int, reason: str):
        db.update_governance_request_status(request_id, 'REJECTED', f"Rejected: {reason}")
