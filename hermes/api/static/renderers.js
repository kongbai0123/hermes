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
        const serverEvents = mcpLogs.filter(log => ["MCP_SERVER_READY", "MCP_SERVER_FAILED"].includes(log.action));
        const toolEvents = mcpLogs.filter(log => log.action === "MCP_TOOL_REGISTERED");
        const callEvents = mcpLogs.filter(log => ["MCP_TOOL_CALL", "MCP_TOOL_RESULT", "MCP_TOOL_DENIED"].includes(log.action));

        const serverRows = serverEvents.length
            ? serverEvents.map(log => `
                <div class="mcp-row">
                    <span class="mcp-row-name">${escapeHtml(log.data?.server || "local_workspace")}</span>
                    <span class="mcp-pill">${log.action === "MCP_SERVER_READY" ? "READY" : "ERROR"}</span>
                </div>
            `).join("")
            : `<div class="mcp-row"><span class="mcp-row-name">local_workspace</span><span class="mcp-pill">READY</span></div>`;

        const toolRows = toolEvents.length
            ? toolEvents.map(log => `
                <div class="mcp-row">
                    <span class="mcp-row-name">mcp.${escapeHtml(log.data?.server || "server")}.${escapeHtml(log.data?.tool || "tool")}</span>
                    <span class="mcp-pill">${escapeHtml(log.data?.permission || "read")}</span>
                </div>
            `).join("")
            : `<div class="mcp-row"><span class="mcp-row-name">mcp.local_workspace.read_file</span><span class="mcp-pill">read</span></div>`;

        const callRows = callEvents.length
            ? callEvents.slice(-6).map(log => `
                <div class="mcp-row">
                    <span class="mcp-row-name">${escapeHtml(log.action)} · ${escapeHtml(log.data?.tool || "")}</span>
                    <span class="mcp-pill">${log.data?.ok === false ? "failed" : "ok"}</span>
                </div>
            `).join("")
            : `<div class="mcp-empty">No MCP calls in this session yet.</div>`;

        target.innerHTML = `
            <div class="mcp-dashboard">
                <div class="mcp-status-card ready">
                    <div class="mcp-card-title">Connected MCP Servers <span class="mcp-pill">GOVERNED</span></div>
                    <div id="mcp-server-list" class="mcp-list">${serverRows}</div>
                </div>
                <div class="mcp-status-card">
                    <div class="mcp-card-title">Imported MCP Tools <span class="mcp-card-meta">${toolEvents.length || 1} tools</span></div>
                    <div id="mcp-tool-list" class="mcp-list">${toolRows}</div>
                </div>
                <div class="mcp-status-card">
                    <div class="mcp-card-title">Recent MCP Calls</div>
                    <div id="mcp-call-list" class="mcp-list">${callRows}</div>
                </div>
            </div>
        `;
    }

    function escapeHtml(unsafe) {
        return String(unsafe ?? "").replace(/[&<>"']/g, m => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;" }[m]));
    }

    window.HermesRenderers = {
        renderTraceTimeline,
        renderToolResultPreview,
        renderMcpEvents
    };
})();
