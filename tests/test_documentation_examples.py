from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path
from types import ModuleType

import pytest

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
        if sequence.setup_from is not None:
            assert sequence.setup_from in by_path
            assert by_path[sequence.setup_from].setup_from is None


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

    # Reading my_data.csv deliberately requires a reader-supplied file.
    assert tuple(index for index, _code in selected) == (0, 2, 3, 4, 5)
    for index, code in selected:
        namespace = {"__name__": "__deapack_data_schema_example__"}
        filename = f"{sequence.path}::python-fence-{index + 1}"
        exec(compile(code, filename, "exec"), namespace)


def test_documentation_page_filter_runs_only_requested_sequences() -> None:
    runner = _runner()
    paths = ("docs/user-guide/data.md", "docs/getting-started/quickstart.md")
    selected = runner.select_sequences(paths)
    assert [sequence.path for sequence in selected] == list(reversed(paths))
    assert runner.select_sequences(()) == ()
    assert runner.select_sequences() == runner.SEQUENCES
    with pytest.raises(ValueError, match="unreviewed documentation page"):
        runner.select_sequences(("docs/misspelled-page.md",))


def test_documentation_setup_and_selected_page_share_one_session(monkeypatch) -> None:
    runner = _runner()
    setup = runner.DocumentSequence("docs/setup.md", 1, (0,))
    page = runner.DocumentSequence("docs/page.md", 1, (0,), setup_from="docs/setup.md")
    monkeypatch.setattr(runner, "SEQUENCES", (setup, page))
    calls = []

    def execute(sequence, namespace, *, include_visualization):
        calls.append(sequence.path)
        if sequence.path == setup.path:
            namespace["prepared"] = True
        else:
            assert namespace["prepared"] is True
        return 1

    monkeypatch.setattr(runner, "_execute_blocks", execute)
    runner._run_sequences(include_visualization=False, pages=(page.path,))
    assert calls == [setup.path, page.path]


def test_dynamic_sbm_example_matches_current_data_and_printed_table() -> None:
    runner = _runner()
    path = ROOT / "docs/models/tone-tsutsui-dynamic-sbm.md"
    namespace = {"__name__": "__dynamic_documentation_example__"}
    exec(compile(runner.python_fences(path)[0], str(path), "exec"), namespace)
    frame = namespace["frame"]
    assert len(frame) == 12
    assert frame["period"].nunique() == 3
    assert set(frame["unit_id"]) == {"path_01", "path_02", "path_03", "path_04"}

    summary = namespace["result"].summary().set_index("dmu_id")
    assert summary["score_valid"].all()
    rows = re.findall(
        r"^\| (path_\d+) \| ([0-9.]+) \| ([0-9.]+) \|$",
        path.read_text(encoding="utf-8"),
        re.MULTILINE,
    )
    assert len(rows) == 4
    for dmu, adjusted, base in rows:
        assert summary.loc[dmu, "efficiency"] == pytest.approx(
            float(adjusted), abs=5e-7
        )
        assert summary.loc[dmu, "optimization_efficiency"] == pytest.approx(
            float(base), abs=5e-7
        )


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
