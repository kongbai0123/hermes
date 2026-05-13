from pathlib import Path
from typing import Any


ALLOWED_EXTENSIONS = {
    ".py",
    ".md",
    ".txt",
    ".json",
    ".yaml",
    ".yml",
    ".html",
    ".css",
    ".js",
    ".ts",
    ".toml",
    ".ini",
    ".bat",
    ".sh",
}
ALLOWED_FILENAMES = {".gitignore", "LICENSE"}
FORBIDDEN_SEGMENTS = {".env", ".git", ".venv", "node_modules", "__pycache__", "secrets", ".vscode", ".idea"}
MAX_FILE_BYTES = 512 * 1024


def api_error(code: str, message: str, status: int = 400, details: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "ok": False,
        "data": None,
        "error": {
            "code": code,
            "message": message,
            "status": status,
            "details": details or {},
        },
    }


def _safe_resolve(workspace_root: str | Path, path: str) -> tuple[Path | None, dict[str, Any] | None]:
    root = Path(workspace_root).resolve()
    raw_path = path or "."
    candidate = Path(raw_path)
    target = candidate.resolve() if candidate.is_absolute() else (root / candidate).resolve()

    try:
        target.relative_to(root)
    except ValueError:
        return None, api_error(
            "PATH_DENIED",
            f"Path '{raw_path}' is outside workspace boundary.",
            status=403,
            details={"path": raw_path, "workspace": str(root)},
        )

    if any(part in FORBIDDEN_SEGMENTS for part in target.parts) or target.name in FORBIDDEN_SEGMENTS:
        return None, api_error(
            "PATH_DENIED",
            f"Path '{raw_path}' contains a forbidden segment.",
            status=403,
            details={"path": raw_path},
        )

    return target, None


def _relative_path(workspace_root: str | Path, target: Path) -> str:
    return str(target.resolve().relative_to(Path(workspace_root).resolve())).replace("\\", "/")


def list_workspace_files(workspace_root: str | Path, path: str = ".") -> dict[str, Any]:
    target, error = _safe_resolve(workspace_root, path)
    if error:
        return error
    if target is None or not target.exists():
        return api_error("NOT_FOUND", f"Path '{path}' does not exist.", status=404, details={"path": path})
    if not target.is_dir():
        return api_error("NOT_DIRECTORY", f"Path '{path}' is not a directory.", status=400, details={"path": path})

    items = []
    for item in target.iterdir():
        if item.name in FORBIDDEN_SEGMENTS or (item.name.startswith(".") and item.name != ".gitignore"):
            continue
        try:
            item.relative_to(Path(workspace_root).resolve())
        except ValueError:
            continue
        items.append(
            {
                "name": item.name,
                "path": _relative_path(workspace_root, item),
                "type": "directory" if item.is_dir() else "file",
                "size": item.stat().st_size if item.is_file() else 0,
            }
        )

    items.sort(key=lambda entry: (entry["type"] != "directory", entry["name"].lower()))
    return {"ok": True, "root": path, "items": items}


def read_workspace_file(workspace_root: str | Path, path: str, max_bytes: int = MAX_FILE_BYTES) -> dict[str, Any]:
    target, error = _safe_resolve(workspace_root, path)
    if error:
        return error
    if target is None or not target.exists():
        return api_error("NOT_FOUND", f"Path '{path}' does not exist.", status=404, details={"path": path})
    if not target.is_file():
        return api_error("NOT_FILE", f"Path '{path}' is not a file.", status=400, details={"path": path})

    suffix = target.suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS and target.name not in ALLOWED_FILENAMES:
        return api_error(
            "UNSUPPORTED_FILE_TYPE",
            f"Path '{path}' is not a supported text file.",
            status=415,
            details={"path": path, "extension": suffix},
        )

    size = target.stat().st_size
    if size > max_bytes:
        return api_error(
            "FILE_TOO_LARGE",
            f"Path '{path}' exceeds the {max_bytes} byte preview limit.",
            status=413,
            details={"path": path, "size": size, "max_bytes": max_bytes},
        )

    content = target.read_text(encoding="utf-8", errors="replace")
    return {
        "ok": True,
        "path": _relative_path(workspace_root, target),
        "content": content,
        "size": size,
        "lines": content.count("\n") + (0 if content.endswith("\n") or not content else 1),
    }


def status_from_result(result: dict[str, Any]) -> int:
    if result.get("ok"):
        return 200
    return int(result.get("error", {}).get("status", 400))
