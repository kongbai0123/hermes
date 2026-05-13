(() => {
    function renderTraceTimeline(target, logs) {
        if (!target) return;
        target.textContent = logs && logs.length
            ? logs.map(log => `${log.state || ""} ${log.action || ""}`).join("\n")
            : "No Runtime Trace";
    }

    function renderToolResultPreview(target, logs) {
        if (!target) return;
        const toolLogs = (logs || []).filter(log => String(log.action || "").includes("TOOL_RESULT"));
        target.textContent = toolLogs.length
            ? JSON.stringify(toolLogs.slice(-3), null, 2)
            : "No tool results yet.";
    }

    function renderMcpEvents(target, logs) {
        if (!target) return;
        const mcpLogs = (logs || []).filter(log => String(log.action || "").startsWith("MCP_"));
        target.textContent = mcpLogs.length
            ? mcpLogs.map(log => `${log.action}: ${JSON.stringify(log.data || {})}`).join("\n")
            : "MCP_SERVER_READY\nMCP_TOOL_REGISTERED\nNo MCP calls in this session yet.";
    }

    window.HermesRenderers = {
        renderTraceTimeline,
        renderToolResultPreview,
        renderMcpEvents
    };
})();
