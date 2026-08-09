from __future__ import annotations

import inspect
import json
from collections.abc import Callable, Mapping, Sequence
from dataclasses import replace
from typing import Any

import numpy as np
import pandas as pd
import pytest

import deapack.models.additive as additive_module
import deapack.models.directional as directional_module
import deapack.models.sbm as sbm_module
from deapack import (
    BAM,
    DDF,
    ERG,
    RAM,
    RDM,
    SBM,
    AdditiveDEA,
    BCCInput,
    BCCOutput,
    ByProductionDirectionalDistanceDEA,
    CCRInput,
    CCROutput,
    DEAData,
    DirectionalDistanceDEA,
    GeneralizedDistanceDEA,
    InputOrientedSlacksBasedDEA,
    InputRussell,
    InputSBM,
    OutputOrientedSlacksBasedDEA,
    OutputRussell,
    OutputSBM,
    PeerEligibility,
    PeerEligibilityProvenance,
    RangeAdjustedDEA,
    ReferenceSpec,
    SlacksBasedDEA,
    WeightedAdditiveDEA,
)
from deapack.exceptions import ModelSpecificationError
from deapack.technology import build_reference_plan

ModelConstructor = Callable[..., Any]


class _FailIfCalledSolver:
    name = "must-not-be-called"

    def __init__(self) -> None:
        self.calls = 0

    @property
    def effective_primal_feasibility_tolerance(self) -> float:
        return 1e-7

    @property
    def effective_dual_feasibility_tolerance(self) -> float:
        return 1e-7

    def solve(self, problem):  # type: ignore[no-untyped-def]
        self.calls += 1
        raise AssertionError(f"solver called unexpectedly for {problem.name}")


def _provenance() -> PeerEligibilityProvenance:
    return PeerEligibilityProvenance(
        rule_name="declared institutional comparability",
        source="approved study-design ledger v1",
        comparison_population="eligible service organizations",
        decision_owner="study steering committee",
        validity_period="2020-2024",
    )


def _dominance_data() -> DEAData:
    return DEAData.from_frame(
        pd.DataFrame(
            {
                "dmu": ["A", "B", "C", "D"],
                "input": [1.0, 2.0, 3.0, 4.0],
                "output": [4.0, 3.0, 2.0, 1.0],
            }
        ),
        dmu="dmu",
        inputs="input",
        outputs="output",
    )


def _panel_data() -> DEAData:
    return DEAData.from_frame(
        pd.DataFrame(
            {
                "dmu": ["A", "B", "A", "B", "A", "B"],
                "year": [2020, 2020, 2021, 2021, 2024, 2024],
                "input": [1.0, 2.0, 1.5, 3.0, 2.0, 4.0],
                "output": [1.0] * 6,
            }
        ),
        dmu="dmu",
        period="year",
        inputs="input",
        outputs="output",
    )


def _eligibility(
    candidates: Mapping[str, Sequence[str]],
) -> PeerEligibility:
    return PeerEligibility.by_key(candidates, provenance=_provenance())


def _all_to_all(data: DEAData) -> PeerEligibility:
    identifiers = tuple(str(identifier) for identifier in data.dmu_ids)
    return _eligibility({identifier: identifiers for identifier in identifiers})


def _focal_frame(frame: pd.DataFrame, dmu_id: str) -> pd.DataFrame:
    if "dmu_id" not in frame.columns:
        return frame.copy().reset_index(drop=True)
    focal = frame.loc[frame["dmu_id"] == dmu_id].copy()
    candidates = (
        "phase",
        "role",
        "constraint_role",
        "variable",
        "reference_dmu_id",
        "reference_period",
        "selection_status",
    )
    sort_columns = [column for column in candidates if column in focal.columns]
    if sort_columns:
        focal = focal.sort_values(sort_columns, kind="stable")
    return focal.reset_index(drop=True)


def _assert_focal_semantic_tables_equal(
    left: Any,
    right: Any,
    dmu_id: str,
) -> None:
    for attribute in ("slacks", "targets", "intensities", "duals"):
        pd.testing.assert_frame_equal(
            _focal_frame(getattr(left, attribute), dmu_id),
            _focal_frame(getattr(right, attribute), dmu_id),
            check_exact=False,
            rtol=0.0,
            atol=1e-10,
        )


AUTHORIZED_PUBLIC_CONSTRUCTORS = (
    CCRInput,
    CCROutput,
    BCCInput,
    BCCOutput,
    AdditiveDEA,
    WeightedAdditiveDEA,
    RangeAdjustedDEA,
    RAM,
    SlacksBasedDEA,
    SBM,
    ERG,
    InputOrientedSlacksBasedDEA,
    InputSBM,
    InputRussell,
    OutputOrientedSlacksBasedDEA,
    OutputSBM,
    OutputRussell,
    DirectionalDistanceDEA,
    DDF,
)

CLASSICAL_MOTHER_CONSTRUCTORS = (
    AdditiveDEA,
    RangeAdjustedDEA,
    SlacksBasedDEA,
    InputOrientedSlacksBasedDEA,
    OutputOrientedSlacksBasedDEA,
    DirectionalDistanceDEA,
)


@pytest.mark.parametrize(
    "constructor",
    AUTHORIZED_PUBLIC_CONSTRUCTORS,
    ids=lambda constructor: constructor.__name__,
)
def test_authorized_public_constructors_expose_peer_eligibility(
    constructor: ModelConstructor,
) -> None:
    eligibility = _all_to_all(_dominance_data())

    assert "peer_eligibility" in inspect.signature(constructor).parameters
    assert constructor(peer_eligibility=eligibility).peer_eligibility is eligibility


@pytest.mark.parametrize(
    "constructor",
    (
        CCRInput,
        CCROutput,
        BCCInput,
        BCCOutput,
        AdditiveDEA,
        RangeAdjustedDEA,
        SlacksBasedDEA,
        InputOrientedSlacksBasedDEA,
        OutputOrientedSlacksBasedDEA,
        DirectionalDistanceDEA,
    ),
    ids=lambda constructor: constructor.__name__,
)
def test_classical_core_constructors_reject_noneligibility_objects(
    constructor: ModelConstructor,
) -> None:
    with pytest.raises(TypeError, match=r"peer_eligibility.*PeerEligibility"):
        constructor(peer_eligibility=object())


@pytest.mark.parametrize(
    "constructor",
    (
        ByProductionDirectionalDistanceDEA,
        BAM,
        RDM,
        GeneralizedDistanceDEA,
    ),
    ids=lambda constructor: constructor.__name__,
)
def test_unauthorized_environmental_and_specialist_neighbors_reject_keyword(
    constructor: ModelConstructor,
) -> None:
    with pytest.raises(TypeError, match=r"unexpected keyword argument"):
        constructor(peer_eligibility=_all_to_all(_dominance_data()))


def test_inherited_specialist_neighbors_fail_closed_after_attribute_mutation() -> None:
    data = _dominance_data()
    eligibility = _all_to_all(data)
    cases = (
        (BAM(), data, r"not supported by BoundedAdjustedDEA"),
        (RDM(), data, r"not supported by RangeDirectionalDEA"),
    )

    for model, fit_data, message in cases:
        model.peer_eligibility = eligibility
        with pytest.raises(ModelSpecificationError, match=message):
            model.fit(fit_data)


@pytest.mark.parametrize(
    "constructor",
    CLASSICAL_MOTHER_CONSTRUCTORS,
    ids=lambda constructor: constructor.__name__,
)
def test_all_candidate_policy_preserves_classical_core_results(
    constructor: ModelConstructor,
) -> None:
    data = _dominance_data()
    eligibility = _all_to_all(data)

    baseline = constructor().fit(data)
    conditioned = constructor(peer_eligibility=eligibility).fit(data)

    for attribute in ("summary_frame", "slacks", "targets", "intensities", "duals"):
        pd.testing.assert_frame_equal(
            getattr(baseline, attribute),
            getattr(conditioned, attribute),
        )
    assert "peer_eligibility" not in baseline.metadata
    assert conditioned.metadata["peer_eligibility"]["effective_edge_count"] == 16


@pytest.mark.parametrize(
    "constructor",
    (
        AdditiveDEA,
        SlacksBasedDEA,
        InputOrientedSlacksBasedDEA,
        OutputOrientedSlacksBasedDEA,
        DirectionalDistanceDEA,
    ),
    ids=lambda constructor: constructor.__name__,
)
def test_observation_specific_fit_matches_independent_custom_fits_for_each_mother(
    constructor: ModelConstructor,
) -> None:
    data = _dominance_data()
    candidates = {
        "A": ("A",),
        "B": ("A",),
        "C": ("A", "B"),
        "D": ("B", "C"),
    }
    rows = {
        "A": (0,),
        "B": (0,),
        "C": (0, 1),
        "D": (1, 2),
    }

    joint = constructor(peer_eligibility=_eligibility(candidates)).fit(data)
    for dmu_id, reference_rows in rows.items():
        independent = constructor(
            reference=ReferenceSpec("custom", custom_rows=reference_rows)
        ).fit(data)
        excluded_summary_fields = ["base_reference_size", "failure_reason"]
        joint_summary = (
            joint.summary()
            .set_index("dmu_id")
            .loc[dmu_id]
            .drop(excluded_summary_fields, errors="ignore")
        )
        independent_summary = (
            independent.summary()
            .set_index("dmu_id")
            .loc[dmu_id]
            .drop(excluded_summary_fields, errors="ignore")
        )
        pd.testing.assert_series_equal(
            joint_summary,
            independent_summary,
            check_exact=False,
            rtol=0.0,
            atol=1e-10,
        )
        _assert_focal_semantic_tables_equal(joint, independent, dmu_id)


def test_ram_uses_full_data_ranges_before_eligibility_and_matches_additive_oracle() -> (
    None
):
    frame = pd.DataFrame(
        {
            "dmu": ["A", "B", "C", "D"],
            "x1": [7.0, 1.0, 1.5, 10.0],
            "x2": [8.0, 2.0, 1.5, 10.0],
            "y": [20.0, 5.0, 1.0, 1.0],
        }
    )
    data = DEAData.from_frame(
        frame,
        dmu="dmu",
        inputs=["x1", "x2"],
        outputs="y",
    )
    candidates = {
        "A": ("A", "B"),
        "B": ("A", "B"),
        "C": ("C",),
        "D": ("B", "C"),
    }
    positions = {
        identifier: tuple(
            position
            for position, candidate in enumerate(frame["dmu"])
            if candidate in allowed
        )
        for identifier, allowed in candidates.items()
    }
    dimensions = data.n_inputs + data.n_outputs
    input_ranges = np.ptp(data.inputs, axis=0)
    output_ranges = np.ptp(data.outputs, axis=0)
    input_weights = {
        name: float(1.0 / (dimensions * coordinate_range))
        for name, coordinate_range in zip(data.input_names, input_ranges, strict=True)
    }
    output_weights = {
        name: float(1.0 / (dimensions * coordinate_range))
        for name, coordinate_range in zip(data.output_names, output_ranges, strict=True)
    }

    result = RAM(peer_eligibility=_eligibility(candidates)).fit(data)

    assert result.metadata["range_population"] == (
        "base_global_data_before_peer_eligibility"
    )
    assert dict(result.metadata["input_weights"]) == pytest.approx(input_weights)
    assert dict(result.metadata["output_weights"]) == pytest.approx(output_weights)
    assert result.metadata["source_profile"] == "deapack_ram_extension"
    assert result.metadata["source_profile_mismatches"] == (
        "reference_is_not_the_full_self_inclusive_sample",
    )

    for dmu_id, reference_rows in positions.items():
        oracle = AdditiveDEA(
            returns_to_scale="vrs",
            input_weights=input_weights,
            output_weights=output_weights,
            reference=ReferenceSpec("custom", custom_rows=reference_rows),
        ).fit(data)
        ram_row = result.summary().set_index("dmu_id").loc[dmu_id]
        additive_row = oracle.summary().set_index("dmu_id").loc[dmu_id]
        assert ram_row["distance"] == pytest.approx(additive_row["distance"], abs=1e-10)
        assert ram_row["score"] == pytest.approx(
            1.0 - additive_row["distance"], abs=1e-10
        )
        assert ram_row["reference_size"] == len(reference_rows)
        assert ram_row["base_reference_size"] == data.n_dmus
        _assert_focal_semantic_tables_equal(result, oracle, dmu_id)


@pytest.mark.parametrize(
    "reference",
    (
        ReferenceSpec("contemporaneous"),
        ReferenceSpec("sequential"),
        ReferenceSpec("custom", custom_rows=(0, 1, 2, 3)),
    ),
    ids=("contemporaneous", "sequential", "custom"),
)
@pytest.mark.parametrize(
    "constructor",
    (AdditiveDEA, SlacksBasedDEA, DirectionalDistanceDEA),
    ids=lambda constructor: constructor.__name__,
)
def test_compatible_models_forward_exact_temporal_and_custom_intersections(
    constructor: ModelConstructor,
    reference: ReferenceSpec,
) -> None:
    data = _panel_data()
    keys = tuple(zip(data.dmu_ids, data.periods, strict=True))
    eligibility = PeerEligibility.by_key(
        {
            evaluatee: tuple(
                candidate for candidate in keys if candidate[0] == evaluatee[0]
            )
            for evaluatee in keys
        },
        provenance=_provenance(),
    )
    plan = build_reference_plan(
        data,
        reference,
        peer_eligibility=eligibility,
    )

    result = constructor(
        reference=reference,
        peer_eligibility=eligibility,
    ).fit(data)

    assert result.summary()["reference_size"].tolist() == [
        len(plan.rows_for(observation)) for observation in range(data.n_dmus)
    ]
    assert result.summary()["base_reference_size"].tolist() == (
        plan.base_size_by_observation.tolist()
    )
    assert result.metadata["compiled_reference_sets"] == plan.unique_reference_sets
    assert result.metadata["peer_eligibility"]["composition"] == "intersection"


def test_ram_retains_global_only_base_reference_boundary() -> None:
    data = _dominance_data()
    eligibility = _all_to_all(data)

    for reference in (
        ReferenceSpec("contemporaneous"),
        ReferenceSpec("custom", custom_rows=(0, 1, 2, 3)),
    ):
        with pytest.raises(
            ModelSpecificationError,
            match=r"requires one global range and global reference technology",
        ):
            RAM(reference=reference, peer_eligibility=eligibility).fit(data)


def test_empty_intersection_fails_before_nonradial_solver_call() -> None:
    data = _panel_data()
    eligibility = PeerEligibility.by_row(
        [[2], [1], [2], [3], [4], [5]],
        provenance=_provenance(),
    )
    solver = _FailIfCalledSolver()

    with pytest.raises(ModelSpecificationError, match=r"empty intersection.*row 0"):
        AdditiveDEA(
            reference="contemporaneous",
            peer_eligibility=eligibility,
            solver=solver,
        ).fit(data)

    assert solver.calls == 0


def test_external_additive_membership_survives_published_target_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = additive_module._certify_additive_account
    calls = 0

    def fail_published_quantity(**kwargs):  # type: ignore[no-untyped-def]
        nonlocal calls
        calls += 1
        certificate = original(**kwargs)
        if calls % 2 == 0:
            return replace(
                certificate,
                quantity_certified=False,
                reason="injected_published_quantity_failure",
                resource_violation=np.inf,
            )
        return certificate

    monkeypatch.setattr(
        additive_module,
        "_certify_additive_account",
        fail_published_quantity,
    )
    result = AdditiveDEA(
        peer_eligibility=_eligibility(
            {
                "A": ("A",),
                "B": ("A",),
                "C": ("A",),
                "D": ("B",),
            }
        )
    ).fit(_dominance_data())
    summary = result.summary().set_index("dmu_id")
    external = summary.loc[["B", "C", "D"]]

    assert external["score_valid"].astype(bool).all()
    assert not external["target_valid"].astype(bool).any()
    assert not external["peer_valid"].astype(bool).any()
    assert external["dual_valid"].astype(bool).all()
    assert external["is_within_reference_technology"].astype(bool).all()
    assert not external["self_in_reference"].astype(bool).any()
    assert set(external["membership_status"]) == {"certified_by_raw_additive_balance"}
    assert set(external["target_status"]) == {
        "unavailable_uncertified_published_quantity_account"
    }
    assert result.targets.empty
    assert result.intensities.empty
    assert not result.duals.empty


@pytest.mark.parametrize(
    "constructor",
    (
        BCCInput,
        AdditiveDEA,
        RangeAdjustedDEA,
        SlacksBasedDEA,
        InputOrientedSlacksBasedDEA,
        OutputOrientedSlacksBasedDEA,
        DirectionalDistanceDEA,
    ),
    ids=lambda constructor: constructor.__name__,
)
def test_common_result_fields_compact_provenance_and_mixed_appraisal(
    constructor: ModelConstructor,
) -> None:
    data = _dominance_data()
    candidates = {
        "A": ("A",),
        "B": ("A",),
        "C": ("A",),
        "D": ("B",),
    }
    result = constructor(peer_eligibility=_eligibility(candidates)).fit(data)
    summary = result.summary()

    assert summary["base_reference_size"].tolist() == [4, 4, 4, 4]
    assert summary["reference_size"].tolist() == [1, 1, 1, 1]
    assert summary["self_in_reference"].tolist() == [True, False, False, False]
    assert result.metadata["expanded_spec"]["evaluation_protocol"]["kind"] == (
        "mixed_self_and_external_reference_appraisal"
    )
    audit = result.metadata["peer_eligibility"]
    assert json.loads(json.dumps(audit)) == json.loads(
        json.dumps(result.metadata["expanded_spec"]["reference"]["peer_eligibility"])
    )
    assert audit["schema"] == "deapack.peer-eligibility-plan.v1"
    assert audit["categorical_interpretation"] == "not_claimed"
    assert audit["provenance"] == _provenance().metadata()
    assert audit["base_unique_reference_sets"] == 1
    assert audit["effective_unique_reference_sets"] == 2
    serialized = json.dumps(audit)
    assert "rows_by_observation" not in serialized
    assert "reference_dmu_id" not in serialized

    allowed = {identifier: set(values) for identifier, values in candidates.items()}
    for intensity in result.intensities.itertuples(index=False):
        assert intensity.reference_dmu_id in allowed[intensity.dmu_id]


@pytest.mark.parametrize(
    "constructor",
    (
        BCCInput,
        AdditiveDEA,
        RangeAdjustedDEA,
        SlacksBasedDEA,
        InputOrientedSlacksBasedDEA,
        OutputOrientedSlacksBasedDEA,
        DirectionalDistanceDEA,
    ),
    ids=lambda constructor: constructor.__name__,
)
def test_fully_self_excluded_population_is_external_appraisal(
    constructor: ModelConstructor,
) -> None:
    data = DEAData.from_frame(
        pd.DataFrame(
            {
                "dmu": ["A", "B"],
                "input": [1.0, 1.0],
                "output": [1.0, 1.0],
            }
        ),
        dmu="dmu",
        inputs="input",
        outputs="output",
    )
    eligibility = _eligibility({"A": ("B",), "B": ("A",)})

    result = constructor(peer_eligibility=eligibility).fit(data)

    assert result.summary()["score_valid"].astype(bool).all()
    assert not result.summary()["self_in_reference"].astype(bool).any()
    assert result.metadata["expanded_spec"]["evaluation_protocol"]["kind"] == (
        "external_reference_appraisal"
    )
    assert set(result.intensities["reference_dmu_id"]) == {"A", "B"}
    assert not any(
        row.dmu_id == row.reference_dmu_id
        for row in result.intensities.itertuples(index=False)
    )


@pytest.mark.parametrize(
    "constructor",
    CLASSICAL_MOTHER_CONSTRUCTORS,
    ids=lambda constructor: constructor.__name__,
)
def test_external_infeasibility_has_declared_status_and_withholds_claims(
    constructor: ModelConstructor,
) -> None:
    data = DEAData.from_frame(
        pd.DataFrame(
            {
                "dmu": ["A", "B"],
                "input": [1.0, 2.0],
                "output": [2.0, 1.0],
            }
        ),
        dmu="dmu",
        inputs="input",
        outputs="output",
    )
    eligibility = _eligibility({"A": ("B",), "B": ("B",)})

    result = constructor(peer_eligibility=eligibility).fit(data)
    evaluated = result.summary().set_index("dmu_id").loc["A"]

    assert not bool(evaluated["score_valid"])
    assert evaluated["score_status"] == "outside_reference_technology"
    assert not bool(evaluated["is_within_reference_technology"])
    assert not bool(evaluated["self_in_reference"])
    assert evaluated["membership_status"] == "outside_reference_technology"
    assert pd.isna(evaluated["score"])
    for attribute in ("slacks", "targets", "intensities", "duals"):
        assert _focal_frame(getattr(result, attribute), "A").empty


def test_negative_ddf_distance_is_retained_as_valid_external_evidence() -> None:
    data = DEAData.from_frame(
        pd.DataFrame(
            {
                "dmu": ["A", "B"],
                "input": [1.0, 2.0],
                "output": [2.0, 1.0],
            }
        ),
        dmu="dmu",
        inputs="input",
        outputs="output",
    )
    eligibility = _eligibility({"A": ("B",), "B": ("B",)})

    result = DDF(
        peer_eligibility=eligibility,
        allow_negative_distance=True,
        compute_slacks=False,
    ).fit(data)
    evaluated = result.summary().set_index("dmu_id").loc["A"]

    assert bool(evaluated["score_valid"])
    assert evaluated["score_status"] == "defined"
    assert evaluated["score"] == pytest.approx(-1.0, abs=1e-12)
    assert evaluated["distance"] == pytest.approx(-1.0, abs=1e-12)
    assert not bool(evaluated["is_within_reference_technology"])
    assert evaluated["membership_status"] == "outside_reference_technology"
    peers = result.intensities.loc[result.intensities["dmu_id"] == "A"]
    assert peers["reference_dmu_id"].tolist() == ["B"]
    assert peers["lambda"].tolist() == pytest.approx([1.0], abs=1e-12)


@pytest.mark.parametrize(
    "constructor",
    CLASSICAL_MOTHER_CONSTRUCTORS,
    ids=lambda constructor: constructor.__name__,
)
def test_reference_frequency_remains_fail_closed_for_classical_core(
    constructor: ModelConstructor,
) -> None:
    result = constructor(peer_eligibility=_all_to_all(_dominance_data())).fit(
        _dominance_data()
    )

    with pytest.raises(
        ModelSpecificationError,
        match=(
            r"eligibility-conditioned fitted results has not been independently "
            r"audited"
        ),
    ):
        result.reference_frequency()


@pytest.mark.parametrize(
    ("module", "constructor"),
    (
        (additive_module, AdditiveDEA),
        (additive_module, RangeAdjustedDEA),
        (sbm_module, SlacksBasedDEA),
        (sbm_module, InputOrientedSlacksBasedDEA),
        (sbm_module, OutputOrientedSlacksBasedDEA),
        (directional_module, DirectionalDistanceDEA),
    ),
    ids=("additive", "ram", "sbm", "input-sbm", "output-sbm", "ddf"),
)
def test_repeated_effective_populations_compile_k_blocks_and_solve_n_programs(
    module: Any,
    constructor: ModelConstructor,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    data = _dominance_data()
    eligibility = _eligibility(
        {
            "A": ("A", "B"),
            "B": ("A", "B"),
            "C": ("C", "D"),
            "D": ("C", "D"),
        }
    )
    compile_calls: list[tuple[int, ...]] = []
    production_compiler = module.compile_reference

    def counted_compiler(data: DEAData, rows: np.ndarray):
        compile_calls.append(tuple(int(row) for row in rows))
        return production_compiler(data, rows)

    monkeypatch.setattr(module, "compile_reference", counted_compiler)
    model_kwargs = (
        {"compute_slacks": False} if constructor is DirectionalDistanceDEA else {}
    )

    result = constructor(
        peer_eligibility=eligibility,
        **model_kwargs,
    ).fit(data)

    assert compile_calls == [(0, 1), (2, 3)]
    assert result.metadata["compiled_reference_sets"] == 2
    assert result.metadata["solver_calls"] == data.n_dmus
    assert result.summary()["score_valid"].astype(bool).all()
