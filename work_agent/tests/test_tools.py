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

