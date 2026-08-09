from __future__ import annotations

from dataclasses import replace

import numpy as np
import pandas as pd
import pytest

from deapack._registry import EXPANDED_SPEC_AXES
from deapack.enums import SolverStatus
from deapack.exceptions import DataValidationError, ModelSpecificationError
from deapack.network.data import NetworkData
from deapack.network.sequential import LewisSextonSequentialNetworkDEA
from deapack.network.specs import LinkSpec, NetworkSpec, ProcessSpec
from deapack.solvers import LPSolution, SciPyHiGHSSolver


def _paper_data(*, reversed_declarations: bool = False) -> NetworkData:
    """Lewis--Sexton (2004), Figure 2 and Tables 1--2."""
    processes = (
        ProcessSpec("p1", "x1", "y1"),
        ProcessSpec("p2", "x2", "y2"),
        ProcessSpec("p3", ("y1", "y2"), "z1"),
    )
    links = (
        LinkSpec("p1_to_p3", "p1", "p3", "y1"),
        LinkSpec("p2_to_p3", "p2", "p3", "y2"),
    )
    if reversed_declarations:
        processes = (
            ProcessSpec("p3", ("y2", "y1"), "z1"),
            ProcessSpec("p2", "x2", "y2"),
            ProcessSpec("p1", "x1", "y1"),
        )
        links = tuple(reversed(links))
    frame = pd.DataFrame(
        {
            "dmu": ["A", "B"],
            "x1": [1.0, 1.0],
            "x2": [1.0, 1.0],
            "y1": [5.0, 10.0],
            "y2": [10.0, 5.0],
            "z1": [20.0, 20.0],
        }
    )
    return NetworkData.from_frame(
        frame,
        dmu="dmu",
        spec=NetworkSpec(processes=processes, links=links),
    )


def _fork_join_data() -> NetworkData:
    spec = NetworkSpec(
        processes=(
            ProcessSpec("acquire", "x", ("z_a", "z_b")),
            ProcessSpec("branch_a", "z_a", "w_a"),
            ProcessSpec("branch_b", "z_b", "w_b"),
            ProcessSpec("finish", ("w_a", "w_b"), "y"),
        ),
        links=(
            LinkSpec("to_a", "acquire", "branch_a", "z_a"),
            LinkSpec("to_b", "acquire", "branch_b", "z_b"),
            LinkSpec("a_to_finish", "branch_a", "finish", "w_a"),
            LinkSpec("b_to_finish", "branch_b", "finish", "w_b"),
        ),
    )
    return NetworkData.from_frame(
        pd.DataFrame(
            {
                "dmu": ["A", "B", "C"],
                "x": [1.0, 2.0, 3.0],
                "z_a": [1.0, 3.0, 2.0],
                "z_b": [2.0, 2.0, 4.0],
                "w_a": [1.0, 3.0, 2.0],
                "w_b": [2.0, 2.0, 4.0],
                "y": [1.0, 3.0, 4.0],
            }
        ),
        dmu="dmu",
        spec=spec,
    )


def test_reproduces_lewis_sexton_figure_2_and_tables_1_2() -> None:
    result = LewisSextonSequentialNetworkDEA(
        orientation="output",
        returns_to_scale="crs",
    ).fit(_paper_data())

    summary = result.summary().set_index("dmu_id")
    np.testing.assert_allclose(
        summary["organizational_factor"],
        [4.0 / 3.0, 4.0 / 3.0],
        atol=2e-10,
        rtol=0,
    )
    np.testing.assert_allclose(
        summary["system_efficiency"],
        [0.75, 0.75],
        atol=2e-10,
        rtol=0,
    )

    initial = (
        result.components.query("phase == 'initial'")
        .pivot(index="dmu_id", columns="process_id", values="radial_factor")
        .loc[["A", "B"], ["p1", "p2", "p3"]]
    )
    np.testing.assert_allclose(
        initial,
        [[2.0, 1.0, 1.0], [1.0, 2.0, 1.0]],
        atol=2e-10,
        rtol=0,
    )
    assert summary["is_efficient"].isna().all()
    assert not bool(summary["is_sequentially_efficient"].any())
    assert summary["is_measure_efficient"].equals(summary["is_sequentially_efficient"])
    assert result.metadata["method_id"] == (
        "network.sequential.lewis_sexton_2004.forward_radial"
    )


def test_forward_propagation_reports_selected_targets_and_reuses_sources() -> None:
    result = LewisSextonSequentialNetworkDEA().fit(_paper_data())
    propagated = result.targets.query(
        "dmu_id == 'A' and phase == 'propagated'"
    ).set_index(["process_id", "variable"])
    components = result.components.query(
        "dmu_id == 'A' and phase == 'propagated'"
    ).set_index("process_id")

    assert propagated.loc[("p1", "y1"), "target"] == pytest.approx(10.0)
    assert propagated.loc[("p2", "y2"), "target"] == pytest.approx(10.0)
    assert propagated.loc[("p3", "z1"), "target"] == pytest.approx(80.0 / 3.0)
    assert components.loc["p3", "radial_factor"] == pytest.approx(4.0 / 3.0)
    assert bool(components.loc["p1", "solve_reused"])
    assert bool(components.loc["p2", "solve_reused"])
    assert not bool(components.loc["p3", "solve_reused"])
    assert result.summary()["primary_programmes"].eq(4).all()
    assert result.metadata["total_primary_programmes"] == 8
    assert result.summary()["targets_may_be_nonunique"].all()
    assert result.metadata["target_selection"]["uniqueness"] == "not_tested"


def test_organizational_factor_uses_source_min_and_max_endpoint_ratios() -> None:
    output_data = NetworkData.from_frame(
        pd.DataFrame(
            {
                "dmu": ["A", "B"],
                "x": [1.0, 1.0],
                "y_1": [1.0, 2.0],
                "y_2": [1.0, 4.0],
            }
        ),
        dmu="dmu",
        spec=NetworkSpec(
            processes=(ProcessSpec("organization", "x", ("y_1", "y_2")),),
            links=(),
        ),
    )
    output_result = LewisSextonSequentialNetworkDEA(orientation="output").fit(
        output_data
    )
    output_targets = output_result.targets.query(
        "dmu_id == 'A' and phase == 'propagated' and role == 'external_output'"
    ).set_index("variable")
    output_ratios = output_targets["target"] / output_targets["observed"]
    output_factor = (
        output_result.summary().set_index("dmu_id").loc["A", "organizational_factor"]
    )

    np.testing.assert_allclose(
        output_ratios.loc[["y_1", "y_2"]],
        [2.0, 4.0],
        atol=1e-11,
        rtol=0,
    )
    assert output_factor == pytest.approx(output_ratios.min())
    assert (
        output_result.metadata["expanded_spec"]["performance"][
            "organizational_factor_formula"
        ]
        == "min_r_sum_s_target_output_over_sum_s_observed_output"
    )

    input_data = NetworkData.from_frame(
        pd.DataFrame(
            {
                "dmu": ["A", "B"],
                "x_1": [2.0, 1.0],
                "x_2": [4.0, 1.0],
                "y": [1.0, 1.0],
            }
        ),
        dmu="dmu",
        spec=NetworkSpec(
            processes=(ProcessSpec("organization", ("x_1", "x_2"), "y"),),
            links=(),
        ),
    )
    input_result = LewisSextonSequentialNetworkDEA(orientation="input").fit(input_data)
    input_targets = input_result.targets.query(
        "dmu_id == 'A' and phase == 'propagated' and role == 'external_input'"
    ).set_index("variable")
    input_ratios = input_targets["target"] / input_targets["observed"]
    input_factor = (
        input_result.summary().set_index("dmu_id").loc["A", "organizational_factor"]
    )

    np.testing.assert_allclose(
        input_ratios.loc[["x_1", "x_2"]],
        [0.5, 0.25],
        atol=1e-11,
        rtol=0,
    )
    assert input_factor == pytest.approx(input_ratios.max())
    assert (
        input_result.metadata["expanded_spec"]["performance"][
            "organizational_factor_formula"
        ]
        == "max_i_sum_s_target_input_over_sum_s_observed_input"
    )


def test_metadata_uses_the_standard_eleven_axis_registry_contract() -> None:
    result = LewisSextonSequentialNetworkDEA().fit(_paper_data())
    expanded = result.metadata["expanded_spec"]

    assert result.metadata["registry_schema_version"] == 2
    assert tuple(expanded) == EXPANDED_SPEC_AXES
    assert expanded["graph"]["kind"] == "directed_acyclic"
    assert expanded["data_roles"]["representation"]["flow_type"] == "forward_only"
    assert (
        expanded["performance"]["endpoint_aggregation_contract"]
        == "paper_sum_over_processes_collapses_to_one_declared_owner_per_"
        "endpoint_type"
    )
    with pytest.raises(TypeError, match="immutable"):
        expanded["performance"]["orientation"] = "changed"


def test_input_orientation_propagates_requirements_backward() -> None:
    result = LewisSextonSequentialNetworkDEA(orientation="input").fit(_paper_data())
    propagated = result.components.query("dmu_id == 'A' and phase == 'propagated'")

    assert propagated["process_id"].tolist() == ["p3", "p2", "p1"]
    assert bool(propagated.set_index("process_id").loc["p3", "solve_reused"])
    assert result.metadata["propagation_direction"] == "backward"
    assert result.metadata["propagation_order"] == ["p3", "p2", "p1"]
    assert result.summary()["primary_programmes"].eq(5).all()
    assert (result.links["balance_residual"] >= -1e-10).all()
    assert result.links["propagation_direction"].eq("backward").all()


def test_series_fork_and_join_graph_is_supported() -> None:
    data = _fork_join_data()
    result = LewisSextonSequentialNetworkDEA().fit(data)

    assert result.summary()["score_status"].eq("defined").all()
    assert result.summary()["process_count"].eq(4).all()
    assert result.summary()["primary_programmes"].eq(7).all()
    assert set(result.links["link_id"]) == {
        "to_a",
        "to_b",
        "a_to_finish",
        "b_to_finish",
    }
    assert result.links.groupby("dmu_id").size().eq(4).all()
    assert (result.links["disposable_surplus"] >= -1e-10).all()
    assert result.metadata["process_order"] == [
        "acquire",
        "branch_a",
        "branch_b",
        "finish",
    ]


def test_process_and_variable_declaration_order_do_not_change_results() -> None:
    first_data = _paper_data()
    reversed_data = _paper_data(reversed_declarations=True)
    first = LewisSextonSequentialNetworkDEA().fit(first_data)
    second = LewisSextonSequentialNetworkDEA().fit(reversed_data)

    np.testing.assert_allclose(
        first.summary()["organizational_factor"],
        second.summary()["organizational_factor"],
        atol=1e-11,
        rtol=1e-11,
    )
    target_key = ["dmu_id", "phase", "process_id", "role", "variable"]
    first_targets = first.targets.sort_values(target_key).reset_index(drop=True)
    second_targets = second.targets.sort_values(target_key).reset_index(drop=True)
    assert first_targets[target_key].equals(second_targets[target_key])
    np.testing.assert_allclose(
        first_targets["target"],
        second_targets["target"],
        atol=1e-10,
        rtol=1e-10,
    )
    assert first_data.graph_fingerprint == reversed_data.graph_fingerprint


class _RecordingSolver:
    name = "recording-scipy-highs"

    def __init__(self) -> None:
        self.delegate = SciPyHiGHSSolver()
        self.problems = []

    def solve(self, problem):  # type: ignore[no-untyped-def]
        self.problems.append(problem)
        return self.delegate.solve(problem)


def test_each_process_can_select_one_of_the_four_source_rts_assumptions() -> None:
    data = _fork_join_data()
    solver = _RecordingSolver()
    rts = {
        "acquire": "crs",
        "branch_a": "vrs",
        "branch_b": "nirs",
        "finish": "ndrs",
    }
    result = LewisSextonSequentialNetworkDEA(
        returns_to_scale=rts,
        solver=solver,
    ).fit(data)

    assert result.summary()["score_status"].eq("defined").all()
    assert result.metadata["returns_to_scale_by_process"] == rts
    initial = {
        problem.name.split(":")[-3]: problem
        for problem in solver.problems
        if ":initial:" in problem.name
    }
    assert initial["acquire"].a_eq is None
    assert initial["branch_a"].a_eq is not None
    assert initial["branch_a"].a_eq.shape[0] == 1

    n = data.n_dmus
    nirs = initial["branch_b"]
    np.testing.assert_allclose(nirs.a_ub.toarray()[-1, :n], 1.0)
    assert nirs.b_ub[-1] == pytest.approx(1.0)
    ndrs = initial["finish"]
    np.testing.assert_allclose(ndrs.a_ub.toarray()[-1, :n], -1.0)
    assert ndrs.b_ub[-1] == pytest.approx(-1.0)


class _AlwaysFailSolver:
    name = "always-fail"

    def solve(self, problem):  # type: ignore[no-untyped-def]
        del problem
        return LPSolution(
            status=SolverStatus.FAILED,
            objective=None,
            primal=None,
            message="injected failure",
            iterations=None,
        )


class _NoCertificateSolver:
    name = "no-certificate"

    def __init__(self) -> None:
        self.delegate = SciPyHiGHSSolver()

    def solve(self, problem):  # type: ignore[no-untyped-def]
        return replace(
            self.delegate.solve(problem),
            inequality_marginals=None,
            equality_marginals=None,
        )


@pytest.mark.parametrize(
    "solver",
    [_AlwaysFailSolver(), _NoCertificateSolver()],
)
def test_solver_or_certificate_failure_closes_all_result_accounts(
    solver: object,
) -> None:
    result = LewisSextonSequentialNetworkDEA(
        solver=solver,  # type: ignore[arg-type]
    ).fit(_paper_data())

    assert result.summary()["system_efficiency"].isna().all()
    assert result.summary()["is_efficient"].isna().all()
    assert result.targets.empty
    assert result.intensities.empty
    assert result.components.empty
    assert result.links.empty
    assert result.diagnostics["certification_status"].eq("failed").all()


def test_domain_link_policy_and_complete_process_rts_are_enforced() -> None:
    frame = pd.DataFrame(
        {
            "dmu": ["A"],
            "x": [1.0],
            "z": [-1.0],
            "y": [1.0],
        }
    )
    negative = NetworkData.from_frame(
        frame,
        dmu="dmu",
        spec=NetworkSpec(
            processes=(
                ProcessSpec("one", "x", "z"),
                ProcessSpec("two", "z", "y"),
            ),
            links=(LinkSpec("flow", "one", "two", "z"),),
        ),
    )
    with pytest.raises(DataValidationError, match="nonnegative quantities"):
        LewisSextonSequentialNetworkDEA().fit(negative)

    shared_intensity = NetworkData.from_frame(
        pd.DataFrame({"dmu": ["A"], "x": [1.0], "z": [1.0], "y": [1.0]}),
        dmu="dmu",
        spec=NetworkSpec(
            processes=(
                ProcessSpec("one", "x", "z"),
                ProcessSpec("two", "z", "y"),
            ),
            links=(
                LinkSpec(
                    "flow",
                    "one",
                    "two",
                    "z",
                    intensity_policy="shared",
                ),
            ),
        ),
    )
    with pytest.raises(
        ModelSpecificationError,
        match="process-specific reference intensities",
    ):
        LewisSextonSequentialNetworkDEA().fit(shared_intensity)

    with pytest.raises(ValueError, match="contain every network process"):
        LewisSextonSequentialNetworkDEA(
            returns_to_scale={"p1": "crs"},
        ).fit(_paper_data())
