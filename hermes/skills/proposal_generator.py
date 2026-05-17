import json
from datetime import datetime
from typing import Dict, Any

class ProposalGenerator:
    """
    負責將 Skill Curator 的分析結果轉換為標準化的 Patch Proposal 格式。
    """
    
    def generate(self, target_file: str, reason: str, patch_content: str, risk_level: str = "medium") -> Dict[str, Any]:
        """
        生成結構化的提案字典。
        """
        timestamp = int(datetime.now().timestamp())
        proposal_id = f"prop-{timestamp}"
        
        return {
            "id": proposal_id,
            "type": "skill_update",
            "target_file": target_file,
            "reason": reason,
            "patch": patch_content,
            "risk_level": risk_level,
            "requires_approval": True,
            "status": "pending_approval",
            "created_at": datetime.now().isoformat()
        }
