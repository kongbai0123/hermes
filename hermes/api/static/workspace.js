(() => {
    function fileIcon(item) {
        if (!item) return "📄";
        return item.type === "directory" ? "📁" : "📄";
    }

    function normalizeFileListPayload(payload) {
        if (!payload) return [];
        return Array.isArray(payload.items) ? payload.items : [];
    }

    window.HermesWorkspace = {
        fileIcon,
        normalizeFileListPayload
    };
})();
