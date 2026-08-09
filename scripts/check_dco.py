#!/usr/bin/env python3
"""Require a valid DCO Signed-off-by trailer on every commit in a range."""

from __future__ import annotations

import argparse
import re
import subprocess
from pathlib import Path

_SHA = re.compile(r"[0-9a-f]{40}\Z")
_SIGNOFF = re.compile(
    r"Signed-off-by:\s+[^<>\r\n]+\s+<[^<>\s@]+@[^<>\s@]+>\s*\Z",
    flags=re.IGNORECASE,
)


def _git(
    *arguments: str,
    cwd: Path | None = None,
    input_text: str | None = None,
) -> str:
    """Run one read-only Git command and return its standard output."""

    return subprocess.run(
        ["git", *arguments],
        cwd=cwd,
        input=input_text,
        text=True,
        check=True,
        capture_output=True,
    ).stdout


def signed_off_by_trailers(message: str, *, cwd: Path | None = None) -> tuple[str, ...]:
    """Return valid sign-offs from Git's parsed final trailer block only."""

    parsed = _git("interpret-trailers", "--parse", cwd=cwd, input_text=message)
    return tuple(line for line in parsed.splitlines() if _SIGNOFF.fullmatch(line))


def check_commit_range(base: str, head: str, *, cwd: Path | None = None) -> int:
    """Check every commit in ``base..head`` and return the checked count."""

    if _SHA.fullmatch(base) is None or _SHA.fullmatch(head) is None:
        raise RuntimeError("pull-request commit identifiers are invalid")
    subprocess.run(
        ["git", "merge-base", "--is-ancestor", base, head],
        cwd=cwd,
        check=True,
        capture_output=True,
    )
    commits = _git("rev-list", "--reverse", f"{base}..{head}", cwd=cwd).splitlines()
    if not commits:
        raise RuntimeError("pull request contains no reviewable commits")

    missing: list[str] = []
    for commit in commits:
        message = _git("show", "-s", "--format=%B", commit, cwd=cwd)
        if not signed_off_by_trailers(message, cwd=cwd):
            missing.append(commit)
    if missing:
        rendered = "\n".join(f"  - {commit}" for commit in missing)
        raise RuntimeError(
            "DCO Signed-off-by trailer missing from commit(s):\n" + rendered
        )
    return len(commits)


def main(argv: list[str] | None = None) -> int:
    """Run the DCO range check from the command line."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", required=True)
    parser.add_argument("--head", required=True)
    arguments = parser.parse_args(argv)
    try:
        count = check_commit_range(arguments.base, arguments.head)
    except (RuntimeError, subprocess.CalledProcessError) as error:
        parser.exit(1, f"{error}\n")
    print(f"DCO check passed for {count} pull-request commit(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
