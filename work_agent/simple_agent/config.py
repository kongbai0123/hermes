from __future__ import annotations

import json
import sys
from pathlib import Path


DEFAULT_CONFIG = {
    "model": "gemma4:latest",
    "ollama_url": "http://localhost:11434/api/chat",
    "workspace": "workspace",
    "max_steps": 6,
    "max_replans": 2,
    "max_tool_failures": 2,
    "max_same_action_repeat": 1,
    "default_capability": "controlled_autonomous",
    "allowed_commands": [
        "python --version",
        "python -m pytest",
        "pytest",
        "rg",
    ],
    "allowed_proxy_domains": [],
    "allowed_browser_domains": [
        "youtube.com"
    ],
    "external_chat_bridge": {
        "enabled": True,
        "mode": "windows_clipboard",
        "window_title": "Google Chrome",
        "wait_seconds": 20
    },
    "gui_runner": {
        "enabled": True,
        "mode": "windows",
        "screenshot_dir": "trace/gui"
    },
}


def app_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[1]


ROOT = app_root()
CONFIG_PATH = ROOT / "config.json"


def load_config() -> dict:
    if not CONFIG_PATH.exists():
        CONFIG_PATH.write_text(
            json.dumps(DEFAULT_CONFIG, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    with CONFIG_PATH.open("r", encoding="utf-8") as f:
        data = json.load(f)
    data["root"] = str(ROOT)
    data["workspace_path"] = str((ROOT / data.get("workspace", "workspace")).resolve())
    return data
