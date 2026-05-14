import os
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def project_root() -> Path:
    return PROJECT_ROOT


def workspace_root() -> Path:
    configured = os.getenv("HERMES_WORKSPACE")
    return Path(configured).resolve() if configured else PROJECT_ROOT


def optimization_dir() -> Path:
    return workspace_root() / "optimization"


def optimization_file(name: str) -> str:
    return str(optimization_dir() / name)
