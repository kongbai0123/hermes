import json
import os
import logging
from typing import List, Dict, Any
from .proposal_generator import ProposalGenerator

class SkillCurator:
    """
    Hermes Skill Curator
    負責分析過去的執行軌跡 (Traces)，並產生改進提案 (Proposals)。
    嚴格遵守 Proposal-only 原則，絕不直接套用修改。
    """
    def __init__(self, workspace_path: str = "/workspace"):
        self.workspace_path = workspace_path
        self.proposals_dir = os.path.join(workspace_path, "proposals")
        self.generator = ProposalGenerator()
        self.logger = logging.getLogger(__name__)
        
        # 確保提案儲存目錄存在
        os.makedirs(self.proposals_dir, exist_ok=True)

    def analyze_traces(self, traces: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        分析錯誤軌跡並生成改進提案。
        """
        generated_proposals = []
        
        for trace in traces:
            # 尋找工具執行失敗或觸發退避的紀錄
            if trace.get("status") == "FAILED" or "error" in trace:
                failed_tool = trace.get("tool", "unknown_tool")
                error_msg = trace.get("error_msg", "Unknown error")
                
                # 這裡可以串接 LLM 來進行深度根因分析 (RCA)，目前以簡單規則展示
                reason = f"Observation: Tool '{failed_tool}' repeatedly failed with error: '{error_msg}'. Suggesting a policy clarification."
                
                proposal = self.generator.generate(
                    target_file="docs/autonomy_policy.md",
                    reason=reason,
                    patch_content="<!-- Add specific clarification for this tool usage here -->",
                    risk_level="medium"
                )
                
                self._save_proposal(proposal)
                generated_proposals.append(proposal)
                self.logger.info(f"[SkillCurator] Generated proposal {proposal['id']} for failed tool {failed_tool}.")
                
        return generated_proposals

    def _save_proposal(self, proposal: Dict[str, Any]) -> None:
        """
        將提案實體寫入檔案系統，等待人類審查。
        """
        file_path = os.path.join(self.proposals_dir, f"{proposal['id']}.json")
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(proposal, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"[SkillCurator] Failed to save proposal {proposal['id']}: {e}")
