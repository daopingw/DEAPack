#!/usr/bin/env python3
"""Prepare Sphinx's temporary LaTeX tree for PDF compilation."""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
from pathlib import Path

SVG_REFERENCE = re.compile(r"(?P<prefix>\{\{[^{}]+\})\.svg(?P<suffix>\})")


def prepare(latex_directory: Path, *, converter: str = "rsvg-convert") -> int:
    """Convert copied SVG assets to PDF and rewrite generated TeX references."""

    latex_directory = latex_directory.resolve()
    if not latex_directory.is_dir():
        raise RuntimeError(f"LaTeX build directory does not exist: {latex_directory}")
    executable = shutil.which(converter)
    if executable is None:
        raise RuntimeError(
            f"{converter!r} is required for book PDF images; "
            "install librsvg2-bin (Linux) before running this target"
        )

    svg_paths = sorted(latex_directory.glob("*.svg"))
    if not svg_paths:
        raise RuntimeError(f"no copied SVG assets found in {latex_directory}")
    for source in svg_paths:
        destination = source.with_suffix(".pdf")
        subprocess.run(
            [executable, "--format=pdf", f"--output={destination}", str(source)],
            check=True,
        )
        if (
            not destination.is_file()
            or destination.stat().st_size < 256
            or destination.read_bytes()[:5] != b"%PDF-"
        ):
            raise RuntimeError(
                f"SVG converter did not create a valid vector PDF for {source.name}"
            )

    replacements = 0
    tex_paths = sorted(latex_directory.glob("*.tex"))
    if not tex_paths:
        raise RuntimeError(f"no generated TeX source found in {latex_directory}")
    for path in tex_paths:
        source = path.read_text(encoding="utf-8")
        prepared, count = SVG_REFERENCE.subn(r"\g<prefix>.pdf\g<suffix>", source)
        if count:
            path.write_text(prepared, encoding="utf-8", newline="\n")
            replacements += count

    if replacements == 0:
        raise RuntimeError("generated TeX contains no SVG image references to rewrite")
    unresolved = [
        path.name
        for path in tex_paths
        if SVG_REFERENCE.search(path.read_text(encoding="utf-8"))
    ]
    if unresolved:
        raise RuntimeError(
            f"unresolved SVG references remain in: {', '.join(unresolved)}"
        )
    print(
        f"prepared {len(svg_paths)} SVG assets and {replacements} TeX references "
        f"in {latex_directory}"
    )
    return replacements


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("latex_directory", type=Path)
    arguments = parser.parse_args()
    prepare(arguments.latex_directory)


if __name__ == "__main__":
    main()
