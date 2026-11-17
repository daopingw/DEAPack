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
    setup_from: str | None = None


SEQUENCES = (
    DocumentSequence(
        path="docs/getting-started/quickstart.md",
        expected_fences=5,
        core_indices=(0, 1, 2, 3, 4),
    ),
    DocumentSequence(
        path="docs/getting-started/migration.md",
        expected_fences=2,
        core_indices=(0, 1),
    ),
    DocumentSequence(
        path="docs/user-guide/data.md",
        expected_fences=6,
        # Fence 1 reads the reader's own CSV; the other examples are standalone.
        core_indices=(0, 2, 3, 4, 5),
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
        expected_fences=7,
        core_indices=(0, 1, 2, 3, 4),
        visualization_indices=(5, 6),
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
    DocumentSequence("docs/index.md", 1, (0,)),
    DocumentSequence("docs/getting-started/installation.md", 2, (0, 1)),
    DocumentSequence("docs/user-guide/datasets.md", 21, tuple(range(21))),
    DocumentSequence("docs/user-guide/method-catalog.md", 2, (0,)),
    DocumentSequence(
        "docs/user-guide/results.md",
        7,
        (0, 1, 2, 3, 4, 6),
        setup_from="docs/getting-started/quickstart.md",
    ),
    DocumentSequence(
        "docs/user-guide/visualization.md",
        19,
        (2,),
        visualization_indices=(0, 1, 7, 8, 9, 10, 11, 12, 13, 16),
        setup_from="docs/getting-started/quickstart.md",
    ),
    DocumentSequence(
        "docs/user-guide/reporting.md",
        10,
        (0, 1, 2, 3, 5, 8, 9),
        visualization_indices=(6, 7),
        setup_from="docs/getting-started/quickstart.md",
    ),
    DocumentSequence("docs/models/cost.md", 1, (0,)),
    DocumentSequence("docs/models/revenue.md", 1, (0,)),
    DocumentSequence("docs/models/profit.md", 1, (0,)),
    DocumentSequence("docs/models/nerlovian.md", 2, (0, 1)),
    DocumentSequence(
        "docs/models/directional.md",
        6,
        (0, 1, 2, 3, 4),
        visualization_indices=(5,),
    ),
    DocumentSequence(
        "docs/models/environmental-directional.md",
        4,
        (0, 1),
        visualization_indices=(2,),
    ),
    DocumentSequence(
        "docs/analysis/global-malmquist.md",
        5,
        (0, 1, 3, 4),
        visualization_indices=(2,),
    ),
    DocumentSequence("docs/analysis/malmquist-luenberger.md", 1, (0,)),
    DocumentSequence("docs/analysis/malmquist.md", 7, tuple(range(7))),
    DocumentSequence("docs/analysis/scale-efficiency.md", 1, (0,)),
    DocumentSequence("docs/models/tone-tsutsui-dynamic-network-sbm.md", 3, (0, 1, 2)),
    DocumentSequence(
        "docs/models/tone-tsutsui-dynamic-sbm.md",
        4,
        (0, 1, 3),
        visualization_indices=(2,),
    ),
    DocumentSequence(
        "docs/models/tone-tsutsui-network-sbm.md",
        4,
        (0, 1, 2),
        visualization_indices=(3,),
    ),
    DocumentSequence("docs/panel/multiperiod-aggregative.md", 1, (0,)),
    DocumentSequence(
        "docs/models/radial.md",
        6,
        (0, 1, 2, 3, 5),
        visualization_indices=(4,),
    ),
    DocumentSequence(
        "docs/models/sbm.md",
        10,
        tuple(range(9)),
        visualization_indices=(9,),
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


def select_sequences(
    pages: tuple[str, ...] | None = None,
) -> tuple[DocumentSequence, ...]:
    """Select named pages, rejecting typos instead of silently skipping checks."""

    if pages is None:
        return SEQUENCES
    requested = set(pages)
    known = {sequence.path for sequence in SEQUENCES}
    unknown = requested - known
    if unknown:
        raise ValueError(
            f"unreviewed documentation page(s): {', '.join(sorted(unknown))}"
        )
    return tuple(sequence for sequence in SEQUENCES if sequence.path in requested)


def _execute_blocks(
    sequence: DocumentSequence,
    namespace: dict[str, object],
    *,
    include_visualization: bool,
) -> int:
    selected = selected_blocks(sequence, include_visualization=include_visualization)
    for index, code in selected:
        filename = f"{sequence.path}::python-fence-{index + 1}"
        exec(compile(code, filename, "exec"), namespace)
    return len(selected)


def _run_sequences(
    *, include_visualization: bool, pages: tuple[str, ...] | None = None
) -> None:
    """Execute each selected document as one stateful reader session."""

    for sequence in select_sequences(pages):
        namespace = {"__name__": "__deapack_documentation_example__"}
        if sequence.setup_from is not None:
            setup = select_sequences((sequence.setup_from,))[0]
            if setup.setup_from is not None:
                raise ValueError("documentation setup sequences must be standalone")
            _execute_blocks(setup, namespace, include_visualization=False)
        count = _execute_blocks(
            sequence,
            namespace,
            include_visualization=include_visualization,
        )
        print(f"executed {sequence.path}: {count} reviewed blocks")
        if include_visualization:
            import matplotlib.pyplot as plt

            plt.close("all")


def run(*, include_visualization: bool, pages: tuple[str, ...] | None = None) -> None:
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
            _run_sequences(include_visualization=include_visualization, pages=pages)
        finally:
            os.chdir(previous)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--page",
        action="append",
        help="run only this reviewed docs/...md page; repeat for multiple pages",
    )
    parser.add_argument(
        "--include-visualization",
        action="store_true",
        help="also execute reviewed Matplotlib-backed example blocks",
    )
    arguments = parser.parse_args()
    run(
        include_visualization=arguments.include_visualization,
        pages=None if arguments.page is None else tuple(arguments.page),
    )


if __name__ == "__main__":
    main()
