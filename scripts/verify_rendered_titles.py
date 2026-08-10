#!/usr/bin/env python3
"""Verify the package Documentation identity and legal-notice route."""

from __future__ import annotations

import argparse
import re
from html.parser import HTMLParser
from pathlib import Path

_NOTICE_MARKERS = (
    "Third-Party Notices",
    "Sphinx 9.1.0",
    "PyData Sphinx Theme 0.19.0",
    "Font Awesome Free 7.2.0",
)


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        self.parts.append(data)


def _page_text(path: Path) -> str:
    if not path.is_file():
        raise RuntimeError(f"rendered page is missing: {path}")
    parser = _TextExtractor()
    parser.feed(path.read_text(encoding="utf-8"))
    return re.sub(r"\s+", " ", " ".join(parser.parts)).strip()


def verify(site_root: Path) -> None:
    """Reject a stale site identity or an omitted legal-notice route."""

    site_root = site_root.resolve()
    pages = {
        site_root / "index.html": ("DEAPack Documentation",),
        site_root / "user-guide" / "citing.html": ("Citing DEAPack",),
        site_root / "legal" / "third-party-notices.html": _NOTICE_MARKERS,
    }
    failures: list[str] = []
    for path, required in pages.items():
        text = _page_text(path)
        missing = [phrase for phrase in required if phrase not in text]
        if missing:
            failures.append(
                f"{path}: missing {', '.join(repr(item) for item in missing)}"
            )
    if failures:
        raise RuntimeError(
            "rendered Documentation verification failed: " + "; ".join(failures)
        )
    print(f"verified Documentation identity and notices: {site_root}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("site_root", type=Path)
    arguments = parser.parse_args()
    verify(arguments.site_root)


if __name__ == "__main__":
    main()
