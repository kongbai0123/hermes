(() => {
    function latest(logs, action) {
        return [...(logs || [])].reverse().find(log => log.action === action)?.data || {};
    }

    function summarizeManagement(logs) {
        const executive = latest(logs, "EXECUTIVE_DECISION");
        const strategy = latest(logs, "STRATEGY_PLAN");
        const auditor = latest(logs, "AUDITOR_VERIFICATION");
        const toolCount = (logs || []).filter(log => String(log.action || "").includes("TOOL")).length;
        return {
            executive,
            strategy,
            auditor,
            toolCount
        };
    }

    window.HermesManagement = {
        latest,
        summarizeManagement
    };
})();
