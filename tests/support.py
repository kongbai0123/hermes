from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent


def repo_root() -> Path:
    return REPO_ROOT


def test_workspace(name: str) -> Path:
    return REPO_ROOT / "tests" / name
