#!/usr/bin/env python3
"""Verify canonical titles and third-party notices in rendered websites."""

from __future__ import annotations

import argparse
import re
from html.parser import HTMLParser
from pathlib import Path

_BOOK_TITLE = "Data Envelopment Analysis"
_BOOK_SUBTITLE = "Efficiency, Productivity, and Environmental Performance with Python"
_BOOK_STRAPLINE = "A Unified Handbook of Theory, Methods, and Practice"
_BOOK_METADATA_TITLE = f"{_BOOK_TITLE}: {_BOOK_SUBTITLE}"
_EN_NOTICE_MARKERS = (
    "Third-Party Notices",
    "Sphinx 9.1.0",
    "PyData Sphinx Theme 0.19.0",
    "Font Awesome Free 7.2.0",
    "LPPL Version 1.3c",
    "Bitstream Vera Fonts Copyright",
)
_ZH_NOTICE_MARKERS = (
    "第三方声明",
    "经审计的构建产物清单",
    "Sphinx 9.1.0",
    "Font Awesome Free 7.2.0",
    "LPPL Version 1.3c",
    "Bitstream Vera Fonts Copyright",
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
    """Reject stale publication identity or an omitted legal-notice route."""

    site_root = site_root.resolve()
    pages = {
        site_root / "book" / "en" / "index.html": (
            _BOOK_TITLE,
            _BOOK_SUBTITLE,
            _BOOK_STRAPLINE,
            _BOOK_METADATA_TITLE,
        ),
        site_root / "docs" / "en" / "user-guide" / "citing.html": (
            _BOOK_METADATA_TITLE,
        ),
        site_root / "docs" / "en" / "legal" / "third-party-notices.html": (
            *_EN_NOTICE_MARKERS,
        ),
        site_root / "book" / "en" / "legal-notices.html": (*_EN_NOTICE_MARKERS,),
        site_root / "book" / "zh_CN" / "legal-notices.html": (*_ZH_NOTICE_MARKERS,),
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
        raise RuntimeError("rendered title verification failed: " + "; ".join(failures))
    print(f"verified rendered titles and third-party notices: {site_root}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("site_root", type=Path)
    arguments = parser.parse_args()
    verify(arguments.site_root)


if __name__ == "__main__":
    main()
