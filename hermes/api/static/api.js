(() => {
    const API_ENDPOINTS = {
        filesList: ["/api/files/list", "/files/list"],
        filesRead: ["/api/files/read", "/files/read"],
        logs: ["/api/logs", "/logs"],
        task: ["/api/task", "/task"]
    };

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

    async function requestFirstJson(urls, makeUrl = url => url, options = {}) {
        const errors = [];
        for (const url of urls) {
            try {
                return await fetchJson(makeUrl(url), options);
            } catch (error) {
                errors.push(error.message || String(error));
            }
        }
        throw new Error(errors.join(" | "));
    }

    window.HermesApi = {
        API_ENDPOINTS,
        describeApiError,
        fetchJson,
        requestFirstJson,
        listFiles(path = ".") {
            return requestFirstJson(API_ENDPOINTS.filesList, url => `${url}?path=${encodeURIComponent(path)}`);
        },
        readFile(path) {
            return requestFirstJson(API_ENDPOINTS.filesRead, url => `${url}?path=${encodeURIComponent(path)}`);
        },
        fetchLogs() {
            return requestFirstJson(API_ENDPOINTS.logs);
        },
        sendTask(payload) {
            return requestFirstJson(API_ENDPOINTS.task, url => url, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });
        }
    };
})();
