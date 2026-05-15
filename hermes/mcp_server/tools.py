from hermes.mcp_server.schemas import EMPTY_INPUT_SCHEMA, RUN_TASK_INPUT_SCHEMA


TOOLS = [
    {
        "name": "hermes.run_task",
        "description": "Submit a task to the governed Hermes runtime through its HTTP API.",
        "inputSchema": RUN_TASK_INPUT_SCHEMA,
    },
    {
        "name": "hermes.get_status",
        "description": "Return the current Hermes runtime status from the configured Hermes API.",
        "inputSchema": EMPTY_INPUT_SCHEMA,
    },
    {
        "name": "hermes.get_trace",
        "description": "Return the trace/log entries exposed by the current Hermes API.",
        "inputSchema": EMPTY_INPUT_SCHEMA,
    },
]


def tool_names() -> set[str]:
    return {tool["name"] for tool in TOOLS}

