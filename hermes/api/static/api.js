(() => {
    function describeApiError(resp, data) {
        const error = data && data.error ? data.error : {};
        const status = error.status || (resp && resp.status) || "ERR";
        const code = error.code || (data && data.detail) || "REQUEST_FAILED";
        const message = error.message || (data && data.detail) || (resp ? resp.statusText : "Unknown error");
        return `${status} ${code}: ${message}`;
    }

    async function fetchJson(url, options = {}) {
        const resp = await fetch(url, options);
        const contentType = resp.headers.get("content-type") || "";
        if (!contentType.toLowerCase().includes("application/json")) {
            const text = await resp.text();
            const preview = text.trim().slice(0, 80).replace(/\s+/g, " ");
            throw new Error(`${resp.status || "ERR"} API returned HTML or non-JSON response. Check that ${url} is served by the Hermes API, then restart Hermes. Preview: ${preview}`);
        }
        const data = await resp.json();
        if (!resp.ok || data.ok === false) {
            throw new Error(describeApiError(resp, data));
        }
        return data;
    }

    window.HermesApi = {
        describeApiError,
        fetchJson,
        listFiles(path = ".") {
            return fetchJson(`/api/files/list?path=${encodeURIComponent(path)}`);
        },
        readFile(path) {
            return fetchJson(`/api/files/read?path=${encodeURIComponent(path)}`);
        },
        fetchLogs() {
            return fetchJson("/api/logs");
        }
    };
})();
