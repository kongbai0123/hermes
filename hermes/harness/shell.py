import hashlib
import secrets
import shlex
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional

from hermes.core.types import ToolResult


@dataclass
class ShellCommandProposal:
    id: str
    command: str
    args: list[str]
    cwd: str
    reason: str
    risk_level: str = "requires_user_approval"
    status: str = "pending"
    created_at: float = field(default_factory=time.time)


class ShellApprovalManager:
    def __init__(self, expiration_seconds: int = 300):
        self.pending_actions: Dict[str, ShellCommandProposal] = {}
        self.tokens: Dict[str, Dict] = {}
        self.expiration_seconds = expiration_seconds

    def register(self, proposal: ShellCommandProposal) -> None:
        self.pending_actions[proposal.id] = proposal

    def approve(self, proposal_id: str) -> Optional[str]:
        proposal = self.pending_actions.get(proposal_id)
        if not proposal:
            return None
        token = secrets.token_hex(16)
        self.tokens[token] = {
            "proposal_id": proposal_id,
            "proposal_hash": self._hash_proposal(proposal),
            "expires_at": time.time() + self.expiration_seconds,
        }
        proposal.status = "approved"
        return token

    def validate(self, proposal_id: str, token: str) -> bool:
        record = self.tokens.get(token)
        proposal = self.pending_actions.get(proposal_id)
        if not record or not proposal:
            return False
        if record["proposal_id"] != proposal_id:
            return False
        if time.time() > record["expires_at"]:
            return False
        return record["proposal_hash"] == self._hash_proposal(proposal)

    def _hash_proposal(self, proposal: ShellCommandProposal) -> str:
        data = "|".join([proposal.id, proposal.command, proposal.cwd, proposal.reason, *proposal.args])
        return hashlib.sha256(data.encode("utf-8")).hexdigest()


class GovernedShellExecutor:
    BLOCKED_TOKENS = {
        "rm",
        "del",
        "erase",
        "rmdir",
        "format",
        "shutdown",
        "restart-computer",
        "set-executionpolicy",
        "reg",
    }

    ALLOWED_COMMANDS = {
        "git",
        "python",
        "py",
        "npm",
        "node",
        "ollama",
    }

    def __init__(self, constraints, approval_manager: ShellApprovalManager | None = None):
        self.constraints = constraints
        self.approval_manager = approval_manager or ShellApprovalManager()

    def propose(self, command: str, reason: str, cwd: str = ".") -> ToolResult:
        args = self._parse(command)
        if not args:
            return ToolResult(ok=False, tool="propose_shell_command", summary="Blocked shell command", error="Command is empty.")

        allowed, error = self._validate_args(args)
        if not allowed:
            return ToolResult(ok=False, tool="propose_shell_command", summary="Blocked shell command", error=error)

        is_safe, target_cwd = self.constraints.validate_path(cwd)
        if not is_safe:
            return ToolResult(ok=False, tool="propose_shell_command", summary="Blocked shell command", error=target_cwd)

        proposal_id = "shell-" + hashlib.sha1(f"{time.time()}|{command}".encode("utf-8")).hexdigest()[:12]
        proposal = ShellCommandProposal(
            id=proposal_id,
            command=command,
            args=args,
            cwd=target_cwd,
            reason=reason or "User requested governed shell execution.",
        )
        self.approval_manager.register(proposal)
        return ToolResult(
            ok=True,
            tool="propose_shell_command",
            summary="Shell command pending approval",
            content=f"Proposed shell command:\n{command}\n\nReason:\n{proposal.reason}",
            metadata={
                "proposal_id": proposal_id,
                "command": command,
                "cwd": target_cwd,
                "risk_level": proposal.risk_level,
                "status": proposal.status,
            },
        )

    def execute(self, proposal_id: str, approval_token: str, timeout_seconds: int = 120) -> ToolResult:
        if not self.approval_manager.validate(proposal_id, approval_token):
            return ToolResult(ok=False, tool="execute_approved_shell", summary="Unauthorized", error="Invalid or expired shell approval token.")

        proposal = self.approval_manager.pending_actions[proposal_id]
        allowed, error = self._validate_args(proposal.args)
        if not allowed:
            return ToolResult(ok=False, tool="execute_approved_shell", summary="Blocked shell command", error=error)

        try:
            completed = subprocess.run(
                proposal.args,
                cwd=proposal.cwd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout_seconds,
                shell=False,
            )
            proposal.status = "executed" if completed.returncode == 0 else "failed"
            output = "\n".join(part for part in [completed.stdout.strip(), completed.stderr.strip()] if part)
            return ToolResult(
                ok=completed.returncode == 0,
                tool="execute_approved_shell",
                summary="Shell command executed" if completed.returncode == 0 else "Shell command failed",
                content=output,
                error=None if completed.returncode == 0 else output,
                metadata={
                    "proposal_id": proposal_id,
                    "command": proposal.command,
                    "cwd": proposal.cwd,
                    "returncode": completed.returncode,
                    "status": proposal.status,
                },
            )
        except Exception as exc:
            proposal.status = "failed"
            return ToolResult(ok=False, tool="execute_approved_shell", summary="Shell execution failed", error=str(exc), metadata={"proposal_id": proposal_id})

    def _parse(self, command: str) -> list[str]:
        return shlex.split(command or "", posix=False)

    def _validate_args(self, args: list[str]) -> tuple[bool, str]:
        command_name = Path(args[0]).name.lower()
        stem = Path(command_name).stem.lower()
        if stem not in self.ALLOWED_COMMANDS and command_name not in self.ALLOWED_COMMANDS:
            return False, f"Command is not in governed shell allowlist: {args[0]}"

        lowered = [arg.lower() for arg in args]
        if any(token in self.BLOCKED_TOKENS for token in lowered):
            return False, "Command contains blocked destructive token."
        joined = " ".join(lowered)
        if "|" in joined or "&&" in joined or ";" in joined or ">" in joined or "<" in joined:
            return False, "Shell control operators are blocked."
        return True, ""
