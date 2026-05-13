import json
import sys


TOOLS = [
    {
        "name": "read_note",
        "description": "Read a note",
        "inputSchema": {
            "type": "object",
            "properties": {"path": {"type": "string"}},
        },
    },
    {
        "name": "delete_note",
        "description": "Delete a note",
        "inputSchema": {"type": "object"},
    },
]


def respond(message_id, result=None, error=None):
    payload = {"jsonrpc": "2.0", "id": message_id}
    if error:
        payload["error"] = {"code": -32000, "message": error}
    else:
        payload["result"] = result or {}
    sys.stdout.write(json.dumps(payload) + "\n")
    sys.stdout.flush()


for line in sys.stdin:
    request = json.loads(line)
    method = request.get("method")
    params = request.get("params") or {}
    message_id = request.get("id")

    if method == "initialize":
        respond(message_id, {"serverInfo": {"name": "echo-mcp"}, "capabilities": {"tools": {}}})
    elif method == "tools/list":
        respond(message_id, {"tools": TOOLS})
    elif method == "tools/call":
        name = params.get("name")
        arguments = params.get("arguments") or {}
        if name == "fail":
            respond(message_id, error="forced failure")
        else:
            respond(message_id, {"content": [{"type": "text", "text": f"{name}:{arguments}"}]})
    else:
        respond(message_id, error=f"unknown method: {method}")
