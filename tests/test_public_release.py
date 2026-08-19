from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]


def test_public_repository_audit() -> None:
    subprocess.run(
        [sys.executable, str(ROOT / "scripts/check_public_repo.py"), str(ROOT)],
        check=True,
        capture_output=True,
        text=True,
    )


def test_notification_dependency_is_absent() -> None:
    forbidden_import = "slack" + "web"
    for path in (ROOT / "src").rglob("*.py"):
        assert forbidden_import not in path.read_text(encoding="utf-8").lower()
