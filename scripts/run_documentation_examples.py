#!/usr/bin/env python3
"""Execute a deliberately curated set of code blocks from package docs.

Most documentation fences are API fragments, failure demonstrations, or
continuations that intentionally depend on reader-created objects.  Treating
all of them as standalone programs would give a false signal.  This runner
instead names complete teaching sequences explicitly and refuses to continue
if their fence inventory changes without a corresponding review here.
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
        path="docs/analysis/reference-frequency.md",
        expected_fences=4,
        core_indices=(0, 1, 2),
        visualization_indices=(3,),
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
)


# Every ordinary Python fence in the active English Handbook is classified
# here.  A chapter is executed as one stateful reader session, so later blocks
# can reuse objects introduced earlier in that chapter.  Blocks that call the
# optional plotting layer are kept out of the core-only gate and added by
# ``--include-visualization``.  The explicit fence counts make an editorial
# change fail closed until somebody reviews the new reader session.
HANDBOOK_SEQUENCES = (
    DocumentSequence(
        path="book/citing.md",
        expected_fences=1,
        core_indices=(0,),
    ),
    DocumentSequence(
        path="book/chapters/01-foundations/01-efficiency-productivity.md",
        expected_fences=3,
        core_indices=(0, 1, 2),
    ),
    DocumentSequence(
        path="book/chapters/01-foundations/02-study-design.md",
        expected_fences=3,
        core_indices=(0, 1, 2),
    ),
    DocumentSequence(
        path="book/chapters/02-classical/03-classical-radial.md",
        expected_fences=3,
        core_indices=(0, 1),
        visualization_indices=(2,),
    ),
    DocumentSequence(
        path="book/chapters/02-classical/04-sbm.md",
        expected_fences=4,
        core_indices=(0, 1, 3),
        visualization_indices=(2,),
    ),
    DocumentSequence(
        path="book/chapters/02-classical/community-hospital-capstone.md",
        expected_fences=8,
        core_indices=(0, 1, 2, 3, 4, 5, 6),
        visualization_indices=(7,),
    ),
    DocumentSequence(
        path="book/chapters/02-classical/05-directional-distance.md",
        expected_fences=4,
        core_indices=(0, 1, 3),
        visualization_indices=(2,),
    ),
    DocumentSequence(
        path=("book/chapters/02-classical/economic-efficiency-under-prices.md"),
        expected_fences=1,
        core_indices=(0,),
    ),
    DocumentSequence(
        path="book/chapters/02-classical/scale-performance-management.md",
        expected_fences=2,
        core_indices=(1,),
        visualization_indices=(0,),
    ),
    DocumentSequence(
        path=("book/chapters/03-environmental/06-undesirable-outputs-ddf.md"),
        expected_fences=3,
        core_indices=(0, 1),
        visualization_indices=(2,),
    ),
    DocumentSequence(
        path=("book/chapters/03-environmental/07-undesirable-output-sbm.md"),
        expected_fences=1,
        core_indices=(),
        visualization_indices=(0,),
    ),
    DocumentSequence(
        path="book/chapters/04-productivity/12-luenberger.md",
        expected_fences=1,
        core_indices=(),
        visualization_indices=(0,),
    ),
    DocumentSequence(
        path="book/chapters/04-productivity/17-hicks-moorsteen.md",
        expected_fences=1,
        core_indices=(),
        visualization_indices=(0,),
    ),
    DocumentSequence(
        path=(
            "book/chapters/04-productivity/"
            "environmental-productivity-ml-common-reference.md"
        ),
        expected_fences=5,
        core_indices=(0, 2, 3),
        visualization_indices=(1, 4),
    ),
    DocumentSequence(
        path=(
            "book/chapters/04-productivity/"
            "malmquist-productivity-reference-information.md"
        ),
        expected_fences=4,
        core_indices=(0, 1, 3),
        visualization_indices=(2,),
    ),
    DocumentSequence(
        path="book/chapters/05-network/20-network-sbm.md",
        expected_fences=1,
        core_indices=(),
        visualization_indices=(0,),
    ),
    DocumentSequence(
        path=(
            "book/chapters/05-network/network-dea-organizations-links-responsibility.md"
        ),
        expected_fences=3,
        core_indices=(0, 2),
        visualization_indices=(1,),
    ),
    DocumentSequence(
        path=("book/chapters/06-dynamic/dynamic-dea-carryovers-trajectories.md"),
        expected_fences=4,
        core_indices=(0, 2),
        visualization_indices=(1, 3),
    ),
    DocumentSequence(
        path="book/chapters/07-heterogeneity/23-metafrontier.md",
        expected_fences=1,
        core_indices=(),
        visualization_indices=(0,),
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
        # A document is one stateful reader session.  Optional plotting blocks
        # must therefore return to their source positions instead of running
        # after every core block, because a later example may deliberately
        # reuse names such as ``result`` for a different dataset.
        indices = tuple(sorted((*indices, *sequence.visualization_indices)))
    return tuple((index, blocks[index]) for index in indices)


def _run_sequences(
    sequences: tuple[DocumentSequence, ...],
    *,
    include_visualization: bool,
) -> None:
    """Execute each selected document as one stateful reader session."""

    for sequence in sequences:
        namespace = {"__name__": "__deapack_documentation_example__"}
        selected = selected_blocks(
            sequence,
            include_visualization=include_visualization,
        )
        for index, code in selected:
            filename = f"{sequence.path}::python-fence-{index + 1}"
            exec(compile(code, filename, "exec"), namespace)
        print(f"executed {sequence.path}: {len(selected)} reviewed blocks")


def run(*, include_visualization: bool, include_handbook: bool = False) -> None:
    """Execute reviewed documentation and optional Handbook reader sessions."""

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
            _run_sequences(
                SEQUENCES,
                include_visualization=include_visualization,
            )
            if include_handbook:
                _run_sequences(
                    HANDBOOK_SEQUENCES,
                    include_visualization=include_visualization,
                )
        finally:
            os.chdir(previous)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--include-visualization",
        action="store_true",
        help="also execute reviewed Matplotlib-backed example blocks",
    )
    parser.add_argument(
        "--include-handbook",
        action="store_true",
        help="also execute every reviewed Python fence in the English Handbook",
    )
    arguments = parser.parse_args()
    run(
        include_visualization=arguments.include_visualization,
        include_handbook=arguments.include_handbook,
    )


if __name__ == "__main__":
    main()
