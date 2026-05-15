import json
import sys

from hermes.mcp_server.bridge import HermesAPIBridge
from hermes.mcp_server.schemas import SERVER_INFO, make_text_result
from hermes.mcp_server.tools import TOOLS, tool_names


class HermesMCPServer:
    def __init__(self, bridge: HermesAPIBridge | None = None):
        self.bridge = bridge or HermesAPIBridge()

    def handle(self, method: str, params: dict) -> dict:
        if method == "initialize":
            return {
                "serverInfo": SERVER_INFO,
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
        if name not in tool_names():
            raise ValueError(f"Unknown tool: {name}")
        if name == "hermes.run_task":
            task = arguments.get("task")
            if not task:
                raise ValueError("hermes.run_task requires a task argument")
            payload, is_error = self.bridge.run_task(task)
            return make_text_result(payload, is_error=is_error)
        if name == "hermes.get_status":
            payload, is_error = self.bridge.get_status()
            return make_text_result(payload, is_error=is_error)
        if name == "hermes.get_trace":
            payload, is_error = self.bridge.get_trace()
            return make_text_result(payload, is_error=is_error)
        raise ValueError(f"Unknown tool: {name}")


def respond(message_id, result=None, error=None):
    payload = {"jsonrpc": "2.0", "id": message_id}
    if error:
        payload["error"] = {"code": -32000, "message": error}
    else:
        payload["result"] = result or {}
    sys.stdout.buffer.write((json.dumps(payload, ensure_ascii=False) + "\n").encode("utf-8"))
    sys.stdout.buffer.flush()


def main():
    server = HermesMCPServer()
    for line in sys.stdin:
        try:
            request = json.loads(line)
            result = server.handle(request.get("method", ""), request.get("params") or {})
            respond(request.get("id"), result=result)
        except Exception as exc:
            respond(request.get("id") if "request" in locals() else None, error=str(exc))


if __name__ == "__main__":
    main()
