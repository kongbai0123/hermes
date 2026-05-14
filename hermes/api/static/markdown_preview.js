(() => {
    function escapeHtml(value) {
        return String(value || "").replace(/[&<>"']/g, match => ({
            "&": "&amp;",
            "<": "&lt;",
            ">": "&gt;",
            '"': "&quot;",
            "'": "&#039;"
        }[match]));
    }

    function extractFrontmatter(markdown) {
        const match = String(markdown || "").match(/^---\r?\n([\s\S]*?)\r?\n---\r?\n?/);
        if (!match) return { frontmatter: "", body: markdown || "" };
        return { frontmatter: match[1], body: markdown.slice(match[0].length) };
    }

    function extractMarkdownToc(markdown) {
        return String(markdown || "")
            .split(/\r?\n/)
            .map((line, index) => {
                const match = line.match(/^(#{1,6})\s+(.+)$/);
                if (!match) return null;
                const text = match[2].replace(/[#*_`]/g, "").trim();
                return {
                    level: match[1].length,
                    text,
                    id: `md-heading-${index}`,
                    line: index + 1
                };
            })
            .filter(Boolean);
    }

    function renderFrontmatter(frontmatter) {
        if (!frontmatter) return "";
        const rows = frontmatter.split(/\r?\n/).filter(Boolean).map(line => {
            const [key, ...rest] = line.split(":");
            return `<tr><th>${escapeHtml(key.trim())}</th><td>${escapeHtml(rest.join(":").trim())}</td></tr>`;
        }).join("");
        return `<section class="markdown-frontmatter"><table>${rows}</table></section>`;
    }

    function renderMarkdownTable(lines, startIndex) {
        const header = lines[startIndex];
        const divider = lines[startIndex + 1] || "";
        if (!header.includes("|") || !/^\s*\|?\s*:?-{3,}/.test(divider)) return null;
        const rows = [];
        let index = startIndex;
        while (index < lines.length && lines[index].includes("|")) {
            rows.push(lines[index]);
            index += 1;
        }
        const cells = row => row.trim().replace(/^\||\|$/g, "").split("|").map(cell => cell.trim());
        const head = cells(rows[0]).map(cell => `<th>${escapeHtml(cell)}</th>`).join("");
        const body = rows.slice(2).map(row => `<tr>${cells(row).map(cell => `<td>${escapeHtml(cell)}</td>`).join("")}</tr>`).join("");
        return {
            html: `<table class="markdown-table"><thead><tr>${head}</tr></thead><tbody>${body}</tbody></table>`,
            nextIndex: index
        };
    }

    function renderInline(text) {
        return escapeHtml(text)
            .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
            .replace(/\*(.*?)\*/g, "<em>$1</em>")
            .replace(/`([^`]+)`/g, "<code>$1</code>");
    }

    function renderMarkdownPreview(markdown, options = {}) {
        const { frontmatter, body } = extractFrontmatter(markdown || "");
        const toc = extractMarkdownToc(body);
        const lines = body.split(/\r?\n/);
        const html = [];
        let inCode = false;
        let code = [];
        let codeLang = "";
        for (let i = 0; i < lines.length; i += 1) {
            const line = lines[i];
            const fence = line.match(/^```(.*)$/);
            if (fence) {
                if (inCode) {
                    html.push(`<pre class="markdown-code"><code data-lang="${escapeHtml(codeLang)}">${escapeHtml(code.join("\n"))}</code></pre>`);
                    code = [];
                    codeLang = "";
                    inCode = false;
                } else {
                    inCode = true;
                    codeLang = fence[1].trim();
                }
                continue;
            }
            if (inCode) {
                code.push(line);
                continue;
            }
            const table = renderMarkdownTable(lines, i);
            if (table) {
                html.push(table.html);
                i = table.nextIndex - 1;
                continue;
            }
            const heading = line.match(/^(#{1,6})\s+(.+)$/);
            if (heading) {
                const tocItem = toc.find(item => item.line === i + 1);
                html.push(`<h${heading[1].length} id="${tocItem?.id || ""}">${renderInline(heading[2])}</h${heading[1].length}>`);
            } else if (/^\s*[-*]\s+/.test(line)) {
                html.push(`<ul><li>${renderInline(line.replace(/^\s*[-*]\s+/, ""))}</li></ul>`);
            } else if (line.trim()) {
                html.push(`<p>${renderInline(line)}</p>`);
            }
        }
        const rendered = `${renderFrontmatter(frontmatter)}${html.join("\n")}`;
        return {
            html: highlightMarkdownMatches(rendered, options.query || ""),
            toc
        };
    }

    function highlightMarkdownMatches(html, query) {
        const q = String(query || "").trim();
        if (!q) return html;
        const escaped = q.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
        return html.replace(new RegExp(escaped, "gi"), match => `<mark>${match}</mark>`);
    }

    window.HermesMarkdownPreview = {
        extractMarkdownToc,
        renderMarkdownPreview,
        renderFrontmatter,
        renderMarkdownTable,
        highlightMarkdownMatches
    };
})();
