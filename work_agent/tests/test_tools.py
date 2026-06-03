from pathlib import Path

from simple_agent.tools import ToolBox


def test_rejects_path_outside_workspace(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    tools = ToolBox(str(workspace), ["python --version"])

    result = tools.read_file("../secret.txt")

    assert result.ok is False
    assert "workspace 外" in result.content


def test_list_files_inside_workspace(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "hello.txt").write_text("hello", encoding="utf-8")
    tools = ToolBox(str(workspace), ["python --version"])

    result = tools.list_files(".")

    assert result.ok is True
    assert "hello.txt" in result.content


def test_proxy_fetch_requires_allowed_domain(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    tools = ToolBox(str(workspace), ["python --version"])

    result = tools.proxy_fetch("https://example.com")

    assert result.ok is False
    assert "allowlist" in result.content


def test_proxy_fetch_rejects_localhost_even_when_allowlisted(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    tools = ToolBox(str(workspace), ["python --version"], allowed_proxy_domains=["localhost"])

    result = tools.proxy_fetch("http://localhost:11434/api/tags")

    assert result.ok is False
    assert "內網" in result.content


def test_proxy_fetch_uses_registered_fetcher_for_allowlisted_domain(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"

    def fake_fetcher(url: str, timeout: int, max_bytes: int) -> str:
        assert url == "https://example.com/status"
        assert timeout == 10
        assert max_bytes == 4096
        return "proxy ok"

    tools = ToolBox(
        str(workspace),
        ["python --version"],
        allowed_proxy_domains=["example.com"],
        proxy_fetcher=fake_fetcher,
    )

    result = tools.proxy_fetch("https://example.com/status", timeout=10, max_bytes=4096)

    assert result.ok is True
    assert result.content == "proxy ok"


def test_proxy_fetch_execute_reports_invalid_numeric_args(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    tools = ToolBox(str(workspace), ["python --version"], allowed_proxy_domains=["example.com"])

    result = tools.execute("proxy_fetch", url="https://example.com", timeout="slow")

    assert result.ok is False
    assert "timeout" in result.content


def test_open_browser_uses_registered_opener_for_allowlisted_domain(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    opened: list[tuple[str, str]] = []

    def fake_opener(url: str, browser: str) -> None:
        opened.append((url, browser))

    tools = ToolBox(
        str(workspace),
        ["python --version"],
        allowed_browser_domains=["youtube.com"],
        browser_opener=fake_opener,
    )

    result = tools.open_browser("https://www.youtube.com", browser="chrome")

    assert result.ok is True
    assert opened == [("https://www.youtube.com", "chrome")]
    assert "chrome" in result.content.lower()


def test_open_browser_rejects_localhost_even_when_allowlisted(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    tools = ToolBox(str(workspace), ["python --version"], allowed_browser_domains=["localhost"])

    result = tools.open_browser("http://localhost:3000", browser="chrome")

    assert result.ok is False
    assert "內網" in result.content
