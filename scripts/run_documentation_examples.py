#!/usr/bin/env python3
"""Execute the reviewed standalone examples in package Documentation.

Most documentation fences are fragments, failure demonstrations, or
continuations that intentionally depend on reader-created objects.  This
runner names complete teaching sequences explicitly and refuses to continue
if their fence inventory changes without a corresponding review.
"""

from __future__ import annotations

import argparse
import os
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYTHON_FENCE = re.compile(
    r"^```python\s*\n(?P<code>.*?)^```\s*$", re.MULTILINE | re.DOTALL
)


@dataclass(frozen=True)
class DocumentSequence:
    path: str
    expected_fences: int
    core_indices: tuple[int, ...]
    visualization_indices: tuple[int, ...] = ()


SEQUENCES = (
    DocumentSequence(
        path="docs/getting-started/quickstart.md",
        expected_fences=3,
        core_indices=(0, 1, 2),
    ),
    DocumentSequence(
        path="docs/getting-started/migration.md",
        expected_fences=2,
        core_indices=(0, 1),
    ),
    DocumentSequence(
        path="docs/user-guide/data.md",
        expected_fences=4,
        core_indices=(0, 1, 2, 3),
    ),
    DocumentSequence(
        path="docs/analysis/reference-frequency.md",
        expected_fences=4,
        core_indices=(0, 1, 2),
        visualization_indices=(3,),
    ),
    DocumentSequence(
        path="docs/analysis/local-returns-to-scale.md",
        expected_fences=1,
        core_indices=(0,),
    ),
    DocumentSequence(
        path="docs/analysis/metafrontier.md",
        expected_fences=8,
        core_indices=(0, 1, 2, 3, 4),
        visualization_indices=(5, 7),
    ),
    DocumentSequence(
        path="docs/user-guide/reference-sets.md",
        expected_fences=4,
        core_indices=(3,),
    ),
    DocumentSequence(
        path="docs/models/ebm.md",
        expected_fences=1,
        core_indices=(0,),
    ),
    DocumentSequence(
        path="docs/api/network.md",
        expected_fences=3,
        core_indices=(0, 1, 2),
    ),
    DocumentSequence(
        path="docs/models/fare-grosskopf-network-radial.md",
        expected_fences=2,
        core_indices=(0, 1),
    ),
    DocumentSequence(
        path="docs/models/kao-hwang-network.md",
        expected_fences=3,
        core_indices=(0, 1, 2),
    ),
    DocumentSequence(
        path="docs/models/chen-additive-network.md",
        expected_fences=2,
        core_indices=(0, 1),
    ),
)


def python_fences(path: Path) -> tuple[str, ...]:
    """Return ordinary Python fences in source order."""

    return tuple(
        match.group("code")
        for match in PYTHON_FENCE.finditer(path.read_text(encoding="utf-8"))
    )


def selected_blocks(
    sequence: DocumentSequence,
    *,
    include_visualization: bool,
) -> tuple[tuple[int, str], ...]:
    """Select reviewed blocks and enforce the reviewed fence inventory."""

    path = ROOT / sequence.path
    blocks = python_fences(path)
    if len(blocks) != sequence.expected_fences:
        raise RuntimeError(
            f"{sequence.path} contains {len(blocks)} Python fences; "
            f"the reviewed manifest expects {sequence.expected_fences}"
        )
    indices = sequence.core_indices
    if include_visualization:
        indices = tuple(sorted((*indices, *sequence.visualization_indices)))
    return tuple((index, blocks[index]) for index in indices)


def _run_sequences(*, include_visualization: bool) -> None:
    """Execute each selected document as one stateful reader session."""

    for sequence in SEQUENCES:
        namespace = {"__name__": "__deapack_documentation_example__"}
        selected = selected_blocks(
            sequence,
            include_visualization=include_visualization,
        )
        for index, code in selected:
            filename = f"{sequence.path}::python-fence-{index + 1}"
            exec(compile(code, filename, "exec"), namespace)
        print(f"executed {sequence.path}: {len(selected)} reviewed blocks")


def run(*, include_visualization: bool) -> None:
    """Execute the reviewed package-Documentation sessions."""

    os.environ.setdefault("MPLBACKEND", "Agg")
    os.environ.setdefault("MPL_IGNORE_SYSTEM_FONTS", "1")
    os.environ.setdefault(
        "MPLCONFIGDIR",
        str(Path(tempfile.gettempdir()) / "deapack-matplotlib-doc-examples"),
    )
    with tempfile.TemporaryDirectory(prefix="deapack-doc-examples-") as directory:
        previous = Path.cwd()
        os.chdir(directory)
        try:
            _run_sequences(include_visualization=include_visualization)
        finally:
            os.chdir(previous)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--include-visualization",
        action="store_true",
        help="also execute reviewed Matplotlib-backed example blocks",
    )
    arguments = parser.parse_args()
    run(include_visualization=arguments.include_visualization)


if __name__ == "__main__":
    main()
