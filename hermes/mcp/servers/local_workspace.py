import json
import sys
from pathlib import Path

from hermes.harness.constraints import ConstraintValidator


TOOLS = [
    {
        "name": "list_files",
        "description": "List files inside the Hermes workspace.",
        "inputSchema": {
            "type": "object",
            "properties": {"path": {"type": "string"}},
        },
    },
    {
        "name": "read_file",
        "description": "Read a text file inside the Hermes workspace.",
        "inputSchema": {
            "type": "object",
            "properties": {"path": {"type": "string"}},
            "required": ["path"],
        },
    },
    {
        "name": "search_files",
        "description": "Search text files inside the Hermes workspace.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "path": {"type": "string"},
            },
            "required": ["query"],
        },
    },
]


class LocalWorkspaceMCPServer:
    def __init__(self):
        self.constraints = ConstraintValidator()

    def handle(self, method: str, params: dict) -> dict:
        if method == "initialize":
            return {
                "serverInfo": {"name": "hermes-local-workspace", "version": "0.1.0"},
                "capabilities": {"tools": {}},
            }
        if method == "tools/list":
            return {"tools": TOOLS}
        if method == "tools/call":
            name = params.get("name")
            arguments = params.get("arguments") or {}
            return self.call_tool(name, arguments)
        raise ValueError(f"unknown method: {method}")

    def call_tool(self, name: str, arguments: dict) -> dict:
        if name == "list_files":
            return self._text(self._list_files(arguments.get("path") or "."))
        if name == "read_file":
            return self._text(self._read_file(arguments.get("path") or ""))
        if name == "search_files":
            return self._text(self._search_files(arguments.get("query") or "", arguments.get("path") or "."))
        return self._text(f"Unknown tool: {name}")

    def _list_files(self, path: str) -> str:
        is_safe, target = self.constraints.validate_path(path)
        if not is_safe:
            return target
        root = Path(target)
        if not root.is_dir():
            return "Target is not a directory."
        items = []
        for item in sorted(root.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower())):
            if item.name in self.constraints.forbidden_segments:
                continue
            items.append(f"{'[D]' if item.is_dir() else '[F]'} {item.name}")
        return "\n".join(items)

    def _read_file(self, path: str) -> str:
        is_safe, target = self.constraints.validate_path(path)
        if not is_safe:
            return target
        target_path = Path(target)
        if not target_path.is_file():
            return "Target is not a file."
        return target_path.read_text(encoding="utf-8", errors="replace")[:12000]

    def _search_files(self, query: str, path: str) -> str:
        if not query:
            return "Query is required."
        is_safe, target = self.constraints.validate_path(path)
        if not is_safe:
            return target
        root = Path(target)
        if not root.is_dir():
            return "Target is not a directory."
        matches = []
        for file_path in root.rglob("*"):
            if any(part in self.constraints.forbidden_segments for part in file_path.parts):
                continue
            if not file_path.is_file() or file_path.suffix.lower() not in self.constraints.allowed_extensions:
                continue
            try:
                for line_number, line in enumerate(file_path.read_text(encoding="utf-8", errors="replace").splitlines(), start=1):
                    if query.lower() in line.lower():
                        matches.append(f"{file_path.relative_to(root)}:{line_number}: {line.strip()}")
                    if len(matches) >= 100:
                        return "\n".join(matches)
            except OSError:
                continue
        return "\n".join(matches)

    def _text(self, text: str) -> dict:
        return {"content": [{"type": "text", "text": text}]}


def respond(message_id, result=None, error=None):
    payload = {"jsonrpc": "2.0", "id": message_id}
    if error:
        payload["error"] = {"code": -32000, "message": error}
    else:
        payload["result"] = result or {}
    sys.stdout.buffer.write((json.dumps(payload, ensure_ascii=False) + "\n").encode("utf-8"))
    sys.stdout.buffer.flush()


def main():
    server = LocalWorkspaceMCPServer()
    for line in sys.stdin:
        try:
            request = json.loads(line)
            result = server.handle(request.get("method", ""), request.get("params") or {})
            respond(request.get("id"), result=result)
        except Exception as exc:
            respond(request.get("id") if "request" in locals() else None, error=str(exc))


if __name__ == "__main__":
    main()
