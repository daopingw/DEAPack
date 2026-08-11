from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

ROOT = Path(__file__).resolve().parents[1]


def _runner() -> ModuleType:
    name = "deapack_documentation_example_runner_test"
    specification = importlib.util.spec_from_file_location(
        name,
        ROOT / "scripts" / "run_documentation_examples.py",
    )
    assert specification is not None and specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    sys.modules[name] = module
    specification.loader.exec_module(module)
    return module


def test_reviewed_sequences_are_bounded_to_package_documentation() -> None:
    runner = _runner()
    sequences = runner.SEQUENCES
    by_path = {sequence.path: sequence for sequence in sequences}

    assert sequences
    assert len(by_path) == len(sequences)
    assert all(path.startswith("docs/") for path in by_path)
    assert all("book/" not in path.casefold() for path in by_path)

    for path, sequence in by_path.items():
        blocks = runner.python_fences(ROOT / path)
        assert len(blocks) == sequence.expected_fences

        core = sequence.core_indices
        visualization = sequence.visualization_indices
        assert len(set(core)) == len(core)
        assert len(set(visualization)) == len(visualization)
        assert set(core).isdisjoint(visualization)
        assert set((*core, *visualization)) <= set(range(sequence.expected_fences))


def test_documentation_example_selection_preserves_reviewed_source_order() -> None:
    runner = _runner()

    for sequence in runner.SEQUENCES:
        core = runner.selected_blocks(sequence, include_visualization=False)
        all_reviewed = runner.selected_blocks(sequence, include_visualization=True)

        assert tuple(index for index, _code in core) == tuple(sequence.core_indices)
        assert tuple(index for index, _code in all_reviewed) == tuple(
            sorted((*sequence.core_indices, *sequence.visualization_indices))
        )
        assert all(code.strip() for _index, code in all_reviewed)


def test_data_schema_examples_run_independently() -> None:
    runner = _runner()
    sequence = next(
        sequence
        for sequence in runner.SEQUENCES
        if sequence.path == "docs/user-guide/data.md"
    )
    selected = runner.selected_blocks(sequence, include_visualization=False)

    assert tuple(index for index, _code in selected) == tuple(
        range(sequence.expected_fences)
    )
    for index, code in selected:
        namespace = {"__name__": "__deapack_data_schema_example__"}
        filename = f"{sequence.path}::python-fence-{index + 1}"
        exec(compile(code, filename, "exec"), namespace)


def test_repaired_frame_examples_run_independently() -> None:
    runner = _runner()
    cases = {
        "docs/getting-started/migration.md": (0,),
        "docs/analysis/local-returns-to-scale.md": (0,),
        "docs/analysis/metafrontier.md": (1,),
    }

    for path, indices in cases.items():
        blocks = runner.python_fences(ROOT / path)
        for index in indices:
            namespace = {"__name__": "__deapack_documentation_example__"}
            filename = f"{path}::python-fence-{index + 1}"
            exec(compile(blocks[index], filename, "exec"), namespace)
