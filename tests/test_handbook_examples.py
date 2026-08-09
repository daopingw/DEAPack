from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

ROOT = Path(__file__).resolve().parents[1]


def _runner() -> ModuleType:
    name = "deapack_handbook_example_runner_test"
    specification = importlib.util.spec_from_file_location(
        name,
        ROOT / "scripts" / "run_documentation_examples.py",
    )
    assert specification is not None and specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    sys.modules[name] = module
    specification.loader.exec_module(module)
    return module


def _active_handbook_markdown() -> tuple[Path, ...]:
    book = ROOT / "book"
    return tuple(
        sorted(book.glob("*.md"))
        + sorted(book.glob("chapters/**/*.md"))
        + sorted(book.glob("appendices/*.md"))
    )


def test_every_active_handbook_python_fence_has_one_reviewed_classification() -> None:
    runner = _runner()
    sequences = runner.HANDBOOK_SEQUENCES
    by_path = {sequence.path: sequence for sequence in sequences}
    assert len(by_path) == len(sequences)

    fenced_paths = {
        path.relative_to(ROOT).as_posix()
        for path in _active_handbook_markdown()
        if runner.python_fences(path)
    }
    assert set(by_path) == fenced_paths

    for path, sequence in by_path.items():
        blocks = runner.python_fences(ROOT / path)
        assert len(blocks) == sequence.expected_fences
        core = set(sequence.core_indices)
        visualization = set(sequence.visualization_indices)
        assert core.isdisjoint(visualization)
        assert core | visualization == set(range(sequence.expected_fences))

        selected = runner.selected_blocks(
            sequence,
            include_visualization=True,
        )
        assert tuple(index for index, _code in selected) == tuple(range(len(blocks)))
        assert all(code.strip() for _index, code in selected)


def test_handbook_core_only_selection_preserves_source_order() -> None:
    runner = _runner()
    for sequence in runner.HANDBOOK_SEQUENCES:
        selected = runner.selected_blocks(
            sequence,
            include_visualization=False,
        )
        indices = tuple(index for index, _code in selected)
        assert indices == tuple(sorted(sequence.core_indices))
