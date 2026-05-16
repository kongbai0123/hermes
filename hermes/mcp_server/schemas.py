import json


SERVER_INFO = {"name": "hermes-mcp-server", "version": "0.1.0"}


RUN_TASK_INPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "task": {"type": "string"},
        "provider": {"type": "string"},
        "model": {"type": "string"},
        "base_url": {"type": "string"},
        "temperature": {"type": "number"}
    },
    "required": ["task"],
}

EMPTY_INPUT_SCHEMA = {
    "type": "object",
    "properties": {},
}


def make_text_result(payload, is_error: bool = False) -> dict:
    return {
        "content": [
            {
                "type": "text",
                "text": json.dumps(payload, ensure_ascii=False),
            }
        ],
        "isError": is_error,
    }

