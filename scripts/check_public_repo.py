#!/usr/bin/env python3
"""Fail on common secrets, personal absolute paths, or oversized tracked files."""

from __future__ import annotations

import argparse
from pathlib import Path
import re


TEXT_SUFFIXES = {".py", ".md", ".toml", ".txt", ".yml", ".yaml", ".json", ".cff"}
FORBIDDEN = {
    "Slack webhook": re.compile(r"hooks\.slack\.com/services/", re.IGNORECASE),
    "private home path": re.compile(r"/home/(?:saeki|aci18648qz)/"),
    "generic API key": re.compile(r"(?:api[_-]?key|token|secret)\s*[=:]\s*['\"][^'\"]+", re.IGNORECASE),
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", nargs="?", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    failures: list[str] = []
    for path in args.root.rglob("*"):
        if not path.is_file() or ".git" in path.parts:
            continue
        if path.resolve() == Path(__file__).resolve():
            continue
        relative = path.relative_to(args.root)
        if path.stat().st_size > 50 * 1024 * 1024:
            failures.append(f"oversized file: {relative}")
        if path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for label, pattern in FORBIDDEN.items():
            if pattern.search(text):
                failures.append(f"{label}: {relative}")
    if failures:
        raise SystemExit("Public-repository audit failed:\n" + "\n".join(failures))
    print("Public-repository audit passed.")


if __name__ == "__main__":
    main()
