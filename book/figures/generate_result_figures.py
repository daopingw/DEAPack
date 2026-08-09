"""Generate package-native result figures used inside the English case studies."""

from __future__ import annotations

from functools import lru_cache
from itertools import pairwise
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import FancyBboxPatch, Rectangle
from matplotlib.text import Text

from deapack import (
    BCC,
    DDF,
    RAM,
    SBM,
    AdditiveDEA,
    BCCInput,
    CarryOverSpec,
    CommonFactorWeakDisposalDDF,
    DEAData,
    DynamicData,
    DynamicSBM,
    DynamicSBMSpec,
    FareGrosskopfNetworkRadialDEA,
    FGNZMalmquist,
    GlobalMalmquistDEA,
    HicksMoorsteenDEA,
    LinkSpec,
    LuenbergerProductivityIndicator,
    MalmquistLuenbergerDEA,
    MetafrontierDEA,
    NetworkData,
    NetworkSBM,
    NetworkSpec,
    PeriodProductionSpec,
    PriceData,
    ProcessSpec,
    RadialDEA,
    ReturnToDollarEfficiency,
    TwoStageSeriesSpec,
    UndesirableSBM,
    dataset_info,
    load_dataset,
    scale_efficiency,
)
from deapack.visualization import prepare_directional_ddf_improvement_data

OUTPUT = Path(__file__).resolve().parents[1] / "_static" / "figures"
matplotlib.rcParams["svg.hashsalt"] = "deapack-book-result-figures"
matplotlib.rcParams["svg.fonttype"] = "none"


def _save(figure: object, filename: str, title: str) -> None:
    path = OUTPUT / filename
    figure.savefig(  # type: ignore[attr-defined]
        path,
        format="svg",
        bbox_inches="tight",
        metadata={"Title": title, "Date": None},
    )
    plt.close(figure)


def _use_reader_facing_text(
    figure: object,
    replacements: tuple[tuple[str, str], ...],
    *,
    context: str,
) -> object:
    """Rewrite visible book labels without changing the fitted result or plot API."""

    findobj = getattr(figure, "findobj", None)
    if findobj is None:
        raise RuntimeError(f"the {context} figure does not expose Matplotlib text")
    artists = tuple(findobj(match=Text))
    for source, target in replacements:
        if not source or source == target:
            raise ValueError(
                "reader-label replacements must be non-empty and different"
            )
        matches = [
            (artist, artist.get_text().count(source))
            for artist in artists
            if source in artist.get_text()
        ]
        occurrence_count = sum(count for _, count in matches)
        if occurrence_count != 1:
            raise RuntimeError(
                f"the {context} figure exposes {occurrence_count} occurrences "
                f"of reader-label anchor {source!r}"
            )
        artist = next(artist for artist, count in matches if count)
        artist.set_text(artist.get_text().replace(source, target, 1))
    return figure


def _use_reader_facing_text_block(
    figure: object,
    *,
    marker: str,
    text: str,
    context: str,
) -> object:
    """Replace one complete visible note while retaining the generated plot."""

    findobj = getattr(figure, "findobj", None)
    if findobj is None:
        raise RuntimeError(f"the {context} figure does not expose Matplotlib text")
    matches = [artist for artist in findobj(match=Text) if marker in artist.get_text()]
    if len(matches) != 1:
        raise RuntimeError(
            f"the {context} figure exposes {len(matches)} notes containing {marker!r}"
        )
    matches[0].set_text(text)
    return figure


def directional_distance_figure() -> None:
    """Render one certified resource-saving and service-expansion account."""

    frame = load_dataset("slacks_2x2")
    data = DEAData.from_frame(
        frame,
        dmu="dmu",
        inputs=("labor", "capital"),
        outputs=("service", "quality"),
    )
    result = DDF(
        input_direction="observed",
        output_direction="observed",
        returns_to_scale="vrs",
    ).fit(data)
    focus = "E"

    # The public discovery contract must identify this as an improvement
    # account before the book inspects or renders it.  The remaining checks
    # freeze the economic case rather than trusting a successful solver flag
    # or a visually plausible chart.
    if "improvement" not in {plot.kind for plot in result.available_plots()}:
        raise RuntimeError(
            "the certified ordinary DDF result did not expose improvement"
        )

    summary = result.summary()
    required_summary = {
        "dmu_id",
        "solver_status",
        "score",
        "distance",
        "score_valid",
        "score_status",
        "primary_solver_status",
        "completion_solver_status",
        "completion_valid",
        "completion_status",
        "target_valid",
        "target_status",
        "returns_to_scale",
        "max_slack",
        "max_scaled_slack",
    }
    missing_summary = required_summary.difference(summary.columns)
    if missing_summary:
        raise RuntimeError("the ordinary DDF public release row is incomplete")
    selected_summary = summary.loc[summary["dmu_id"] == focus]
    if len(selected_summary) != 1:
        raise RuntimeError(
            "the ordinary DDF result omitted its unique public release row"
        )
    row = selected_summary.iloc[0]
    valid_claims = ("score_valid", "completion_valid", "target_valid")
    if any(not (pd.notna(row[field]) and bool(row[field])) for field in valid_claims):
        raise RuntimeError("the ordinary DDF result withheld its selected plan")
    expected_statuses = {
        "solver_status": "optimal",
        "primary_solver_status": "optimal",
        "score_status": "defined",
        "completion_solver_status": "optimal",
        "completion_status": "certified",
        "target_status": "certified_slack_completion",
        "returns_to_scale": "vrs",
    }
    if any(
        str(row[field]) != expected for field, expected in expected_statuses.items()
    ):
        raise RuntimeError("the ordinary DDF result changed its certified account")

    metadata = result.metadata
    expanded_spec = metadata.get("expanded_spec", {})
    context = expanded_spec.get("context", {})
    graph = expanded_spec.get("graph", {})
    data_roles = expanded_spec.get("data_roles", {})
    technology = expanded_spec.get("technology", {})
    estimator = expanded_spec.get("estimator", {})
    performance = expanded_spec.get("performance", {})
    evaluation = expanded_spec.get("evaluation_protocol", {})
    if not (
        metadata.get("method_id") == "static.directional_distance"
        and metadata.get("model_family") == "directional_distance"
        and metadata.get("orientation") == "input_contraction_output_expansion"
        and metadata.get("reference_kind") == "global"
        and metadata.get("returns_to_scale") == "vrs"
        and metadata.get("native_score") == "beta"
        and metadata.get("input_direction") == "observed"
        and metadata.get("output_direction") == "observed"
        and metadata.get("direction_sign_convention")
        == {"input": "contract", "output": "expand"}
        and metadata.get("compute_slacks") is True
        and metadata.get("target_completion_id")
        == "evaluation.target_completion.pareto_koopmans"
        and metadata.get("target_completion_scale_anchor") == "evaluated_observation"
        and metadata.get("slack_phase") == "maximize_row_scaled_sum"
        and metadata.get("slack_target_unit_invariant") is True
        and metadata.get("allow_negative_distance") is False
        and metadata.get("additional_solver_calls") == 0
        and metadata.get("phase_one_solver_calls") == len(summary)
        and metadata.get("phase_two_solver_calls") == len(summary)
        and metadata.get("solver_calls") == 2 * len(summary)
        and context
        == {
            "purpose": "declared_operating_improvement_programme",
            "sample": "cross_section",
        }
        and graph.get("kind") == "black_box"
        and data_roles.get("inputs") == "resources_to_contract"
        and data_roles.get("outputs") == "services_to_expand"
        and data_roles.get("bad_outputs") == "excluded"
        and data_roles.get("variables")
        == {
            "inputs": ("labor", "capital"),
            "outputs": ("service", "quality"),
            "bad_outputs": (),
            "polluting_inputs": (),
        }
        and technology
        == {
            "family": "convex_envelopment",
            "returns_to_scale": "vrs",
            "disposal": "ordinary_free",
        }
        and estimator
        == {
            "estimator_id": "estimator.full.dea",
            "kind": "full_frontier",
            "family": "dea_envelopment",
        }
        and performance
        == {
            "family": "directional_distance",
            "input_direction": {"kind": "observed"},
            "output_direction": {"kind": "observed"},
            "negative_distance": False,
        }
        and evaluation.get("kind") == "self_appraisal"
        and evaluation.get("target_completion_id")
        == "evaluation.target_completion.pareto_koopmans"
        and evaluation.get("target_completion_scale_anchor") == "evaluated_observation"
        and evaluation.get("target_uniqueness") == "not_assessed"
        and evaluation.get("secondary_objective") == "maximize_row_scaled_slacks"
    ):
        raise RuntimeError(
            "the ordinary DDF case no longer represents the declared technology"
        )

    all_diagnostics = result.diagnostics
    required_certificates = (
        "lp_postsolve_certified",
        "postsolve_certified",
        "raw_economic_postsolve_certified",
        "published_output_account_certified",
        "economic_postsolve_certified",
    )
    missing_diagnostics = {
        "dmu_id",
        "phase",
        "solver_status",
        *required_certificates,
    }.difference(all_diagnostics.columns)
    if missing_diagnostics:
        raise RuntimeError("the ordinary DDF diagnostic ledger is incomplete")
    diagnostics = all_diagnostics.loc[all_diagnostics["dmu_id"] == focus].copy()
    if (
        len(diagnostics) != 2
        or sorted(diagnostics["phase"].tolist()) != [1, 2]
        or not diagnostics["solver_status"].eq("optimal").all()
        or not diagnostics.loc[:, list(required_certificates)].eq(True).all(axis=None)
    ):
        raise RuntimeError(
            "both ordinary DDF solves and quantity accounts must be certified"
        )

    beta = float(row["score"])
    if not (
        np.isfinite(beta)
        and np.isclose(beta, float(row["distance"]), atol=1e-12, rtol=0.0)
        and np.isclose(beta, 0.2472527472527472, atol=1e-12, rtol=0.0)
    ):
        raise RuntimeError("organization E's directional programme changed")

    targets = result.targets_for(focus).copy()
    all_slacks = result.slacks
    target_fields = {
        "role",
        "variable",
        "observed",
        "target",
        "direction",
        "directional_change",
    }
    slack_fields = {
        "dmu_id",
        "role",
        "variable",
        "slack",
        "slack_scale",
        "scaled_slack",
    }
    if target_fields.difference(targets.columns) or slack_fields.difference(
        all_slacks.columns
    ):
        raise RuntimeError("the public ordinary DDF quantity ledger is incomplete")
    slacks = all_slacks.loc[all_slacks["dmu_id"] == focus].copy()

    # Each tuple records observed quantity, declared direction, beta*g change,
    # target after the declared programme, extra slack, and completed target.
    expected_plan = {
        ("input", "labor"): (
            2.0,
            2.0,
            0.4945054945054944,
            1.5054945054945055,
            0.0,
            1.5054945054945055,
        ),
        ("input", "capital"): (
            2.8,
            2.8,
            0.6923076923076922,
            2.1076923076923078,
            0.0,
            2.1076923076923078,
        ),
        ("output", "service"): (
            1.3,
            1.3,
            0.3214285714285714,
            1.6214285714285714,
            0.031318681318681346,
            1.6527472527472529,
        ),
        ("output", "quality"): (
            0.62,
            0.62,
            0.15329670329670328,
            0.7732967032967033,
            0.05725274725274716,
            0.8305494505494505,
        ),
    }
    if (
        targets.duplicated(["role", "variable"]).any()
        or slacks.duplicated(["role", "variable"]).any()
        or len(targets) != len(expected_plan)
        or len(slacks) != len(expected_plan)
    ):
        raise RuntimeError("the public ordinary DDF ledgers are not one-to-one")

    slack_lookup: dict[tuple[str, str], tuple[float, float, float]] = {}
    for slack_row in slacks.itertuples(index=False):
        key = (str(slack_row.role), str(slack_row.variable))
        slack = float(slack_row.slack)
        slack_scale = float(slack_row.slack_scale)
        scaled_slack = float(slack_row.scaled_slack)
        if not (
            np.isfinite(slack)
            and np.isfinite(slack_scale)
            and np.isfinite(scaled_slack)
            and slack >= 0.0
            and slack_scale > 0.0
            and scaled_slack >= 0.0
            and np.isclose(
                scaled_slack,
                slack / slack_scale,
                atol=1e-12,
                rtol=0.0,
            )
        ):
            raise RuntimeError("the public ordinary DDF slack ledger is invalid")
        slack_lookup[key] = (slack, slack_scale, scaled_slack)

    actual_keys: set[tuple[str, str]] = set()
    for target_row in targets.itertuples(index=False):
        key = (str(target_row.role), str(target_row.variable))
        actual_keys.add(key)
        if key not in expected_plan or key not in slack_lookup:
            raise RuntimeError("the ordinary DDF case exposed an undeclared variable")
        observed = float(target_row.observed)
        direction = float(target_row.direction)
        directional_change = float(target_row.directional_change)
        target = float(target_row.target)
        slack, _, _ = slack_lookup[key]
        values = np.asarray(
            (observed, direction, directional_change, target, slack),
            dtype=np.float64,
        )
        if not (
            np.isfinite(values).all()
            and direction > 0.0
            and np.isclose(
                directional_change,
                beta * direction,
                atol=1e-9,
                rtol=0.0,
            )
        ):
            raise RuntimeError("beta times direction did not reconstruct")
        sign = -1.0 if key[0] == "input" else 1.0
        directional_target = observed + sign * directional_change
        reconstructed_target = directional_target + sign * slack
        if not np.isclose(target, reconstructed_target, atol=1e-9, rtol=0.0):
            raise RuntimeError("the public ordinary DDF target account did not close")
        if not np.allclose(
            (
                observed,
                direction,
                directional_change,
                directional_target,
                slack,
                target,
            ),
            expected_plan[key],
            atol=1e-9,
            rtol=0.0,
        ):
            raise RuntimeError("organization E's public quantities changed")

    if actual_keys != set(expected_plan) or set(slack_lookup) != set(expected_plan):
        raise RuntimeError("the ordinary DDF target and slack ledgers do not align")
    if not (
        np.isclose(
            float(row["max_slack"]),
            max(slack for slack, _, _ in slack_lookup.values()),
            atol=1e-12,
            rtol=0.0,
        )
        and np.isclose(
            float(row["max_scaled_slack"]),
            max(scaled for _, _, scaled in slack_lookup.values()),
            atol=1e-12,
            rtol=0.0,
        )
        and np.isclose(
            float(row["max_slack"]),
            0.05725274725274716,
            atol=1e-12,
            rtol=0.0,
        )
        and np.isclose(
            float(row["max_scaled_slack"]),
            0.06090717792845443,
            atol=1e-12,
            rtol=0.0,
        )
    ):
        raise RuntimeError("the ordinary DDF slack aggregate did not reconcile")

    figure = result.plot(kind="improvement", dmu_id=focus)
    _use_reader_facing_text(
        figure,
        (
            (
                "DEA-certified benchmark account for a declared programme",
                "Benchmark account for a declared improvement programme",
            ),
        ),
        context="ordinary DDF improvement",
    )
    _use_reader_facing_text_block(
        figure,
        marker="Each card keeps the variable's original unit",
        text=(
            "Each row keeps its original physical unit. β measures attainable "
            "units of the declared resource-saving and service-expansion "
            "programme; later variable-specific completion is reported "
            "separately. The completed VRS plan is feasible for organization E "
            "within the declared peer population, but need not be unique or "
            "least-cost and is neither causal nor prescriptive."
        ),
        context="ordinary DDF improvement",
    )
    _save(
        figure,
        "ddf-improvement-result.svg",
        "DEA benchmark account for organization E's declared and completed targets",
    )


def ddf_programme_contracts_figure() -> None:
    """Compare three certified first-stage DDF operating contracts for E."""

    frame = load_dataset("slacks_2x2")
    data = DEAData.from_frame(
        frame,
        dmu="dmu",
        inputs=("labor", "capital"),
        outputs=("service", "quality"),
    )
    focus = "E"
    variable_keys = (
        ("input", "labor"),
        ("input", "capital"),
        ("output", "service"),
        ("output", "quality"),
    )
    expected_observed = np.asarray((2.0, 2.8, 1.3, 0.62), dtype=np.float64)
    contracts = (
        {
            "key": "resource",
            "heading": "RESOURCE-SAVING CONTRACT",
            "question": "\n".join(
                (
                    "Protect recorded services;",
                    "test a common observed-input",
                    "contraction.",
                )
            ),
            "direction_note": "g = (observed inputs, zero outputs)",
            "input_direction": "observed",
            "output_direction": "zeros",
            "expected_beta": 0.24725274725274718,
            "expected_direction": (2.0, 2.8, 0.0, 0.0),
            "expected_directional_change": (
                0.49450549450549436,
                0.6923076923076921,
                0.0,
                0.0,
            ),
            "expected_slack_completion": (
                0.0,
                0.0,
                0.3527472527472532,
                0.21054945054945043,
            ),
            "expected_target": (
                1.505494505494506,
                2.1076923076923073,
                1.652747252747253,
                0.8305494505494505,
            ),
        },
        {
            "key": "service",
            "heading": "SERVICE-EXPANSION CONTRACT",
            "question": "\n".join(
                (
                    "Protect recorded resources;",
                    "test a common observed-output",
                    "expansion.",
                )
            ),
            "direction_note": "g = (zero inputs, observed outputs)",
            "input_direction": "zeros",
            "output_direction": "observed",
            "expected_beta": 0.4193548387096773,
            "expected_direction": (0.0, 0.0, 1.3, 0.62),
            "expected_directional_change": (
                0.0,
                0.0,
                0.5451612903225805,
                0.25999999999999995,
            ),
            "expected_slack_completion": (
                0.0,
                1.1249999999999998,
                0.05483870967741931,
                0.0,
            ),
            "expected_target": (
                2.0000000000000004,
                1.6749999999999998,
                1.9000000000000004,
                0.8800000000000001,
            ),
        },
        {
            "key": "joint",
            "heading": "JOINT CONTRACT",
            "question": (
                "Test resource saving and service\n"
                "expansion as one observed-quantity\n"
                "package."
            ),
            "direction_note": "g = (observed inputs, observed outputs)",
            "input_direction": "observed",
            "output_direction": "observed",
            "expected_beta": 0.2472527472527472,
            "expected_direction": (2.0, 2.8, 1.3, 0.62),
            "expected_directional_change": (
                0.4945054945054944,
                0.6923076923076922,
                0.3214285714285714,
                0.15329670329670328,
            ),
            "expected_slack_completion": (
                0.0,
                0.0,
                0.031318681318681346,
                0.05725274725274716,
            ),
            "expected_target": (
                1.5054945054945055,
                2.1076923076923078,
                1.6527472527472529,
                0.8305494505494505,
            ),
        },
    )
    certificate_fields = (
        "lp_postsolve_certified",
        "postsolve_certified",
        "raw_economic_postsolve_certified",
        "published_output_account_certified",
        "economic_postsolve_certified",
    )
    prepared_contracts: list[tuple[dict[str, object], object]] = []

    # Nothing is drawn until all three public fits have passed their complete
    # release certificates and the shared solver-free improvement preparer.
    for contract in contracts:
        result = DDF(
            input_direction=str(contract["input_direction"]),
            output_direction=str(contract["output_direction"]),
            returns_to_scale="vrs",
        ).fit(data)
        metadata_before = result.metadata
        postsolve_before = metadata_before.get("postsolve_certificate", {})
        if not (
            metadata_before.get("method_id") == "static.directional_distance"
            and metadata_before.get("returns_to_scale") == "vrs"
            and metadata_before.get("input_direction") == contract["input_direction"]
            and metadata_before.get("output_direction") == contract["output_direction"]
            and metadata_before.get("compute_slacks") is True
            and metadata_before.get("target_completion_id")
            == "evaluation.target_completion.pareto_koopmans"
            and metadata_before.get("phase_one_solver_calls") == 8
            and metadata_before.get("phase_two_solver_calls") == 8
            and metadata_before.get("solver_calls") == 16
            and metadata_before.get("additional_solver_calls") == 0
            and isinstance(postsolve_before, dict)
            and postsolve_before.get("additional_solver_calls") == 0
        ):
            raise RuntimeError("a DDF programme-contract fit changed its release")

        summary = result.summary(copy=True)
        diagnostics = result.diagnostics.copy(deep=True)
        required_summary = {
            "dmu_id",
            "period",
            "solver_status",
            "primary_solver_status",
            "completion_solver_status",
            "score_valid",
            "score_status",
            "completion_valid",
            "completion_status",
            "target_valid",
            "target_status",
        }
        required_diagnostics = {
            "dmu_id",
            "period",
            "phase",
            "solver_status",
            *certificate_fields,
        }
        missing_summary = required_summary.difference(summary.columns)
        missing_diagnostics = required_diagnostics.difference(diagnostics.columns)
        if missing_summary or missing_diagnostics:
            raise RuntimeError("a DDF programme-contract public ledger is incomplete")
        if not (
            len(summary) == 8
            and summary["dmu_id"].nunique() == 8
            and summary["period"].isna().all()
            and summary["solver_status"].eq("optimal").all()
            and summary["primary_solver_status"].eq("optimal").all()
            and summary["completion_solver_status"].eq("optimal").all()
            and summary["score_valid"].eq(True).all()
            and summary["score_status"].eq("defined").all()
            and summary["completion_valid"].eq(True).all()
            and summary["completion_status"].eq("certified").all()
            and summary["target_valid"].eq(True).all()
            and summary["target_status"].eq("certified_slack_completion").all()
            and len(diagnostics) == 16
            and diagnostics.groupby("dmu_id")["phase"].apply(set).eq({1, 2}).all()
            and diagnostics["solver_status"].eq("optimal").all()
            and diagnostics.loc[:, list(certificate_fields)].eq(True).all(axis=None)
        ):
            raise RuntimeError("a DDF programme-contract certificate was withheld")

        solve_account_before = tuple(
            metadata_before.get(field)
            for field in (
                "phase_one_solver_calls",
                "phase_two_solver_calls",
                "solver_calls",
                "additional_solver_calls",
            )
        )
        prepared = prepare_directional_ddf_improvement_data(
            result,
            dmu_id=focus,
        )
        metadata_after = result.metadata
        solve_account_after = tuple(
            metadata_after.get(field)
            for field in (
                "phase_one_solver_calls",
                "phase_two_solver_calls",
                "solver_calls",
                "additional_solver_calls",
            )
        )
        variables = prepared.variables.copy(deep=True)
        keys = tuple(zip(variables["role"], variables["variable"], strict=True))
        expected_beta = float(contract["expected_beta"])
        if not (
            solve_account_before == (8, 8, 16, 0)
            and solve_account_after == solve_account_before
            and prepared.dmu_id == focus
            and prepared.period is None
            and prepared.returns_to_scale == "vrs"
            and prepared.reference_kind == "global"
            and prepared.target_status == "certified_slack_completion"
            and prepared.provenance
            == (
                ("Method", "static.directional_distance"),
                ("RTS", "VRS"),
                ("Reference", "global"),
            )
            and np.isfinite(prepared.max_reconstruction_residual)
            and prepared.max_reconstruction_residual <= 1e-9
            and keys == variable_keys
            and np.isclose(prepared.beta, expected_beta, atol=1e-12, rtol=0.0)
            and np.allclose(
                variables["observed"].to_numpy(dtype=np.float64),
                expected_observed,
                atol=1e-12,
                rtol=0.0,
            )
            and np.allclose(
                variables["direction"].to_numpy(dtype=np.float64),
                np.asarray(contract["expected_direction"], dtype=np.float64),
                atol=1e-12,
                rtol=0.0,
            )
            and np.allclose(
                variables["directional_change"].to_numpy(dtype=np.float64),
                np.asarray(contract["expected_directional_change"], dtype=np.float64),
                atol=1e-12,
                rtol=0.0,
            )
            and np.allclose(
                variables["slack_completion"].to_numpy(dtype=np.float64),
                np.asarray(contract["expected_slack_completion"], dtype=np.float64),
                atol=1e-12,
                rtol=0.0,
            )
            and np.allclose(
                variables["target"].to_numpy(dtype=np.float64),
                np.asarray(contract["expected_target"], dtype=np.float64),
                atol=1e-12,
                rtol=0.0,
            )
        ):
            raise RuntimeError("organization E's DDF programme contract changed")
        prepared_contracts.append((contract, prepared))

    ink = "#24323d"
    gray = "#5c6b73"
    grid = "#d7e1e4"
    teal = "#176b73"
    orange = "#d97732"
    purple = "#76528f"
    accents = (teal, orange, purple)
    fills = ("#edf7f7", "#fff6ed", "#f6f0f8")

    figure = plt.figure(figsize=(7.6, 11.4), facecolor="white")
    canvas = figure.add_axes((0.0, 0.0, 1.0, 1.0))
    canvas.set_xlim(0.0, 1.0)
    canvas.set_ylim(0.0, 1.0)
    canvas.axis("off")
    canvas.text(
        0.04,
        0.975,
        "Three DDF contracts for the same organization E",
        color=ink,
        fontsize=19,
        fontweight="bold",
        va="top",
    )
    canvas.text(
        0.04,
        0.938,
        "VRS benchmark · same observed operation · only the phase-one "
        "improvement programme changes",
        color=gray,
        fontsize=11.5,
        va="top",
    )
    canvas.add_patch(
        FancyBboxPatch(
            (0.04, 0.855),
            0.92,
            0.065,
            boxstyle="round,pad=0.008,rounding_size=0.012",
            facecolor="#f5f7f8",
            edgecolor=grid,
            linewidth=1.2,
        )
    )
    canvas.text(
        0.06,
        0.901,
        "FIXED OBSERVED RECORD",
        color=ink,
        fontsize=10.5,
        fontweight="bold",
        va="center",
    )
    canvas.text(
        0.06,
        0.875,
        "  ·  ".join(
            (
                "Labor 2.000000",
                "Capital 2.800000",
                "Service 1.300000",
                "Quality 0.620000",
            )
        ),
        color=ink,
        fontsize=10.5,
        va="center",
    )

    card_y = (0.630, 0.405, 0.180)
    for y, accent, fill, (contract, prepared) in zip(
        card_y,
        accents,
        fills,
        prepared_contracts,
        strict=True,
    ):
        canvas.add_patch(
            FancyBboxPatch(
                (0.04, y),
                0.92,
                0.210,
                boxstyle="round,pad=0.010,rounding_size=0.016",
                facecolor=fill,
                edgecolor=accent,
                linewidth=1.7,
            )
        )
        canvas.text(
            0.06,
            y + 0.185,
            str(contract["heading"]),
            color=accent,
            fontsize=9.5,
            fontweight="bold",
            va="top",
        )
        canvas.text(
            0.06,
            y + 0.150,
            str(contract["question"]),
            color=ink,
            fontsize=9.5,
            fontweight="bold",
            va="top",
            linespacing=1.2,
        )
        canvas.text(
            0.06,
            y + 0.088,
            str(contract["direction_note"]).replace(", ", ",\n", 1),
            color=gray,
            fontsize=9.5,
            va="top",
        )
        canvas.text(
            0.06,
            y + 0.040,
            f"β = {prepared.beta:.6f}",
            color=accent,
            fontsize=13.0,
            fontweight="bold",
            va="top",
        )
        canvas.plot(
            (0.40, 0.40),
            (y + 0.018, y + 0.192),
            color=grid,
            linewidth=1.1,
        )
        canvas.text(
            0.425,
            y + 0.185,
            "PHASE 1 · βg IN ORIGINAL UNITS",
            color=gray,
            fontsize=10.0,
            fontweight="bold",
            va="top",
        )
        for row_number, row in enumerate(prepared.variables.itertuples(index=False)):
            row_y = y + 0.147 - 0.029 * row_number
            label = str(row.variable_label)
            observed = float(row.observed)
            direction = float(row.direction)
            change = float(row.directional_change)
            first_target = float(row.directional_target)
            if np.isclose(direction, 0.0, atol=1e-12, rtol=0.0):
                if str(row.role) == "input":
                    account = f"budget cap {observed:.6f}; no saving required"
                else:
                    account = f"output floor {observed:.6f}; no gain required"
            elif str(row.role) == "input":
                account = f"save {change:.6f}  →  {first_target:.6f}"
            else:
                account = f"add {change:.6f}  →  {first_target:.6f}"
            canvas.text(
                0.425,
                row_y,
                label,
                color=ink,
                fontsize=10.0,
                fontweight="bold",
                va="top",
            )
            canvas.text(
                0.515,
                row_y,
                account,
                color=ink,
                fontsize=10.0,
                va="top",
            )
        canvas.plot(
            (0.42, 0.94),
            (y + 0.050, y + 0.050),
            color=grid,
            linewidth=1.1,
        )
        completion_parts: list[str] = []
        for row in prepared.variables.itertuples(index=False):
            completion = float(row.slack_completion)
            if np.isclose(completion, 0.0, atol=1e-12, rtol=0.0):
                continue
            action = "save" if str(row.role) == "input" else "add"
            completion_parts.append(f"{row.variable_label} {action} {completion:.6f}")
        canvas.text(
            0.425,
            y + 0.042,
            "PHASE 2 · SELECTED SLACK\nCOMPLETION AFTER βg",
            color=accent,
            fontsize=9.5,
            fontweight="bold",
            va="top",
        )
        canvas.text(
            0.750,
            y + 0.042,
            " ·\n".join(completion_parts),
            color=gray,
            fontsize=9.5,
            va="top",
            linespacing=1.45,
        )

    canvas.add_patch(
        FancyBboxPatch(
            (0.04, 0.045),
            0.92,
            0.115,
            boxstyle="round,pad=0.009,rounding_size=0.012",
            facecolor="#f5f7f8",
            edgecolor=grid,
            linewidth=1.2,
        )
    )
    canvas.text(
        0.06,
        0.145,
        "HOW TO READ THE CONTRACTS",
        color=purple,
        fontsize=10.5,
        fontweight="bold",
        va="top",
    )
    canvas.text(
        0.06,
        0.116,
        "β is contract-specific: the three β values do not share a generic "
        "efficiency scale.",
        color=ink,
        fontsize=10.5,
        fontweight="bold",
        va="top",
    )
    canvas.text(
        0.06,
        0.088,
        "A zero direction requires no phase-1 change: an observed input remains "
        "a cap and an output a floor.",
        color=ink,
        fontsize=10.5,
        va="top",
    )
    canvas.text(
        0.06,
        0.061,
        "Slack completion is selected only after βg; no causal,\n"
        "implementation-order, or priority conclusion follows.",
        color=gray,
        fontsize=10.5,
        va="top",
    )
    canvas.text(
        0.04,
        0.020,
        "Organization E · VRS technology · the observed operation and comparison\n"
        "population stay fixed across all three contracts",
        color=gray,
        fontsize=10.5,
        va="top",
    )

    _save(
        figure,
        "ddf-programme-contracts-result.svg",
        "Three DDF operating contracts for organization E",
    )


def radial_frontier_figure() -> None:
    frame = load_dataset("frontier_1x1").rename(
        columns={
            "input": "staff_capacity",
            "output": "completed_service",
        }
    )
    data = DEAData.from_frame(
        frame,
        dmu="dmu",
        inputs="staff_capacity",
        outputs="completed_service",
    )
    result = RadialDEA(
        orientation="input",
        returns_to_scale="vrs",
    ).fit(data)
    figure = result.plot(kind="frontier")
    _use_reader_facing_text(
        figure,
        (
            (
                "Resource-saving opportunities on the production frontier",
                "Staff-capacity savings while preserving completed service",
            ),
            ("staff_capacity", "Staff capacity"),
            ("completed_service", "Completed service"),
            ("VRS reference frontier", "VRS benchmark service capacity"),
            (
                "Certified efficient operation",
                "Branch with no remaining represented input or output gap",
            ),
            (
                "Operation with a benchmark opportunity",
                "Branch with a represented resource-saving opportunity",
            ),
            ("Reported DEA target", "Selected slack-completed benchmark plan"),
        ),
        context="radial frontier",
    )
    _use_reader_facing_text_block(
        figure,
        marker="Arrows show the reported resource-saving target",
        text=(
            "Each connector links an observed branch to a selected plan that "
            "preserves completed service while using no more staff capacity. "
            "Input-oriented VRS comparison with one declared peer population; "
            "selected plans include variable-specific completion and remain "
            "conditional, not causal or prescriptive."
        ),
        context="radial frontier",
    )
    _save(
        figure,
        "radial-frontier-result.svg",
        "Resource-saving opportunities on the production frontier",
    )


def radial_improvement_figure() -> None:
    """Show why radial efficiency need not close the operating account."""

    frame = pd.DataFrame(
        {
            "branch": ("A", "B", "C"),
            "resource": (1.0, 2.0, 1.0),
            "service": (1.0, 1.0, 0.5),
        }
    )
    if not (
        frame.shape == (3, 3)
        and tuple(frame["branch"]) == ("A", "B", "C")
        and np.allclose(
            frame[["resource", "service"]].to_numpy(dtype=np.float64),
            np.asarray(((1.0, 1.0), (2.0, 1.0), (1.0, 0.5))),
            atol=0.0,
            rtol=0.0,
        )
    ):
        raise RuntimeError("the exact three-branch radial account changed")

    data = DEAData.from_frame(
        frame,
        dmu="branch",
        inputs="resource",
        outputs="service",
    )
    result = BCCInput().fit(data)
    metadata_before = result.metadata
    expanded = metadata_before.get("expanded_spec", {})
    performance = expanded.get("performance", {})
    technology = expanded.get("technology", {})
    reference = expanded.get("reference", {})
    evaluation = expanded.get("evaluation_protocol", {})
    if not (
        metadata_before.get("method_id") == "static.radial"
        and metadata_before.get("preset_id") == "static.radial.vrs.input"
        and metadata_before.get("model_family") == "radial"
        and metadata_before.get("orientation") == "input"
        and metadata_before.get("returns_to_scale") == "vrs"
        and metadata_before.get("reference_kind") == "global"
        and metadata_before.get("native_score") == "theta"
        and metadata_before.get("efficiency_transform") == "identity"
        and metadata_before.get("compute_slacks") is True
        and metadata_before.get("target_completion_id")
        == "evaluation.target_completion.pareto_koopmans"
        and metadata_before.get("target_completion_scale_anchor")
        == "evaluated_observation"
        and metadata_before.get("slack_phase") == "maximize_row_scaled_sum"
        and metadata_before.get("slack_target_unit_invariant") is True
        and metadata_before.get("compiled_reference_sets") == 1
        and metadata_before.get("phase_one_solver_calls") == 3
        and metadata_before.get("phase_two_solver_calls") == 3
        and metadata_before.get("solver_calls") == 6
        and performance.get("family") == "radial"
        and performance.get("orientation") == "input"
        and performance.get("slack_refinement") is True
        and technology.get("family") == "convex_envelopment"
        and technology.get("returns_to_scale") == "vrs"
        and technology.get("disposal") == "ordinary_free"
        and reference.get("kind") == "global"
        and evaluation.get("target_completion_id")
        == "evaluation.target_completion.pareto_koopmans"
        and evaluation.get("target_completion_scale_anchor") == "evaluated_observation"
        and evaluation.get("secondary_objective") == "maximize_row_scaled_slacks"
    ):
        raise RuntimeError("the complete BCC-I radial release contract changed")

    summary = result.summary(copy=True)
    required_summary = {
        "dmu_id",
        "period",
        "score",
        "efficiency",
        "score_valid",
        "score_status",
        "is_radially_efficient",
        "is_efficient",
        "is_within_reference_technology",
        "solver_status",
        "primary_solver_status",
        "completion_solver_status",
        "completion_valid",
        "completion_status",
        "target_valid",
        "target_status",
        "max_slack",
        "max_scaled_slack",
    }
    if required_summary.difference(summary.columns):
        raise RuntimeError("the public radial summary contract is incomplete")
    if len(summary) != 3 or summary["dmu_id"].duplicated().any():
        raise RuntimeError("the public radial summary roster changed")
    focus = summary.set_index("dmu_id").loc["C"]
    if not (
        focus["period"] is None
        and np.isclose(float(focus["score"]), 1.0, atol=1e-12, rtol=0.0)
        and np.isclose(float(focus["efficiency"]), 1.0, atol=1e-12, rtol=0.0)
        and bool(focus["score_valid"])
        and focus["score_status"] == "defined"
        and bool(focus["is_radially_efficient"])
        and not bool(focus["is_efficient"])
        and bool(focus["is_within_reference_technology"])
        and focus["solver_status"] == "optimal"
        and focus["primary_solver_status"] == "optimal"
        and focus["completion_solver_status"] == "optimal"
        and bool(focus["completion_valid"])
        and focus["completion_status"] == "certified"
        and bool(focus["target_valid"])
        and focus["target_status"] == "certified_slack_completion"
        and np.isclose(float(focus["max_slack"]), 0.5, atol=1e-12, rtol=0.0)
        and np.isclose(
            float(focus["max_scaled_slack"]),
            0.5,
            atol=1e-12,
            rtol=0.0,
        )
    ):
        raise RuntimeError("branch C's two-stage radial claim changed")

    diagnostics = result.diagnostics.copy(deep=True)
    certificate_fields = (
        "lp_postsolve_certified",
        "postsolve_certified",
        "raw_economic_postsolve_certified",
        "economic_postsolve_certified",
        "published_output_account_certified",
    )
    required_diagnostics = {
        "dmu_id",
        "period",
        "phase",
        "solver_status",
        *certificate_fields,
    }
    if required_diagnostics.difference(diagnostics.columns):
        raise RuntimeError("the public radial diagnostics contract is incomplete")
    focus_diagnostics = diagnostics.loc[diagnostics["dmu_id"].eq("C")]
    if not (
        len(focus_diagnostics) == 2
        and set(focus_diagnostics["phase"]) == {1, 2}
        and focus_diagnostics["period"].isna().all()
        and focus_diagnostics["solver_status"].eq("optimal").all()
        and all(focus_diagnostics[field].eq(True).all() for field in certificate_fields)
    ):
        raise RuntimeError("branch C's two fitted phases are not fully certified")

    targets = result.targets_for("C").copy(deep=True)
    slacks = result.slacks.loc[result.slacks["dmu_id"].eq("C")].copy(deep=True)
    target_required = {"role", "variable", "observed", "target"}
    slack_required = {"role", "variable", "slack", "scaled_slack"}
    if target_required.difference(targets.columns) or slack_required.difference(
        slacks.columns
    ):
        raise RuntimeError("the public radial variable ledgers are incomplete")
    targets = targets.set_index(["role", "variable"])
    slacks = slacks.set_index(["role", "variable"])
    expected = {
        ("input", "resource"): (1.0, 1.0, 0.0, 0.0),
        ("output", "service"): (0.5, 1.0, 0.5, 0.5),
    }
    if set(targets.index) != set(expected) or set(slacks.index) != set(expected):
        raise RuntimeError("branch C's radial variable roster changed")
    theta = float(focus["score"])
    reconstruction_residuals: list[float] = []
    for key, (observed, final_target, slack, scaled_slack) in expected.items():
        target_row = targets.loc[key]
        slack_row = slacks.loc[key]
        role = key[0]
        radial_target = theta * observed if role == "input" else observed
        reconstructed = (
            radial_target - slack if role == "input" else radial_target + slack
        )
        values = (
            (float(target_row["observed"]), observed),
            (float(target_row["target"]), final_target),
            (float(slack_row["slack"]), slack),
            (float(slack_row["scaled_slack"]), scaled_slack),
            (reconstructed, final_target),
        )
        reconstruction_residuals.extend(
            abs(actual - expected_value) for actual, expected_value in values
        )
    if max(reconstruction_residuals, default=0.0) > 1e-12:
        raise RuntimeError("branch C's radial target account did not reconstruct")

    figure = result.plot(kind="improvement", dmu_id="C")
    if result.metadata != metadata_before:
        raise RuntimeError("radial improvement rendering mutated fit metadata")
    _use_reader_facing_text(
        figure,
        (
            (
                "DEA-certified two-stage radial performance account",
                "Two-stage radial operating account",
            ),
        ),
        context="radial improvement",
    )
    _use_reader_facing_text_block(
        figure,
        marker="Each card retains the variable's original physical unit",
        text=(
            "Each row retains its original physical unit. θ = 1 leaves no "
            "common resource-saving opportunity for branch C, while phase two "
            "records the remaining service opportunity. The completed "
            "input-oriented VRS plan is feasible but need not be unique or "
            "least-cost and is neither causal nor prescriptive."
        ),
        context="radial improvement",
    )
    _save(
        figure,
        "radial-improvement-result.svg",
        "Radial and completed operating accounts for branch C",
    )


def scale_efficiency_figure() -> None:
    frame = load_dataset("frontier_1x1")
    data = DEAData.from_frame(
        frame,
        dmu="dmu",
        inputs="input",
        outputs="output",
    )
    result = scale_efficiency(data, orientation="input")
    figure = result.plot(
        kind="performance",
        metric="scale_efficiency",
        view="points",
    )
    _use_reader_facing_text_block(
        figure,
        marker="Higher is better",
        text=(
            "Higher values indicate a smaller additional CRS\N{EN DASH}VRS "
            "radial gap; "
            "1 means proportional replication creates no additional scale "
            "inefficiency. Input-oriented comparison of matched CRS and VRS "
            "benchmarks for one declared peer population."
        ),
        context="scale efficiency",
    )
    _use_reader_facing_text(
        figure,
        (
            (
                "Scale Efficiency across organizations",
                "Additional resource-use gap associated with operating scale",
            ),
            (
                "Scale Efficiency",
                "Scale efficiency (CRS efficiency / VRS efficiency)",
            ),
            (
                "Efficient",
                "No additional scale-related radial gap (SE = 1)",
            ),
            (
                "Inefficient",
                "Additional scale-related radial gap (SE < 1)",
            ),
        ),
        context="scale efficiency",
    )
    _save(
        figure,
        "scale-efficiency-performance-result.svg",
        "Additional radial gap under proportional replication",
    )


def three_performance_accounts_figure() -> None:
    """Contrast efficiency, physical productivity, and profitability levels."""

    frame = load_dataset("economic_efficiency_4")
    roles = dataset_info("economic_efficiency_4").roles
    expected_roles = {
        "dmu": "plan",
        "inputs": ("resource",),
        "outputs": ("standard_service", "premium_service"),
        "input_prices": ("price_resource",),
        "output_prices": (
            "price_standard_service",
            "price_premium_service",
        ),
    }
    if any(roles.get(role) != value for role, value in expected_roles.items()):
        raise RuntimeError("the three-account dataset roles changed")

    plans = ("A", "B", "C", "D")
    expected_prices = {
        "price_resource": 2.0,
        "price_standard_service": 3.0,
        "price_premium_service": 5.0,
    }
    if frame.shape != (4, 7) or tuple(frame["plan"]) != plans:
        raise RuntimeError("the four-plan three-account roster changed")
    for column, expected in expected_prices.items():
        values = frame[column].to_numpy(dtype=np.float64)
        if not np.allclose(values, expected, atol=0.0, rtol=0.0):
            raise RuntimeError("the common teaching-price contract changed")

    quantities = frame[["resource", "standard_service", "premium_service"]].to_numpy(
        dtype=np.float64
    )
    expected_quantities = np.asarray(
        (
            (4.0, 6.0, 2.0),
            (5.0, 4.0, 5.0),
            (3.0, 5.0, 1.0),
            (6.0, 3.0, 2.0),
        ),
        dtype=np.float64,
    )
    if not (
        np.isfinite(quantities).all()
        and np.all(quantities[:, 0] > 0.0)
        and np.all(quantities[:, 1:] >= 0.0)
        and np.allclose(quantities, expected_quantities, atol=0.0, rtol=0.0)
    ):
        raise RuntimeError("the exact four-plan quantity account changed")

    data = DEAData.from_frame(
        frame,
        dmu=roles["dmu"],
        inputs=roles["inputs"],
        outputs=roles["outputs"],
    )
    prices = PriceData.common(
        input_prices={"resource": 2.0},
        output_prices={
            "standard_service": 3.0,
            "premium_service": 5.0,
        },
    )
    technical = BCC(
        orientation="input",
        compute_slacks=False,
    ).fit(data)
    profitability = ReturnToDollarEfficiency(
        returns_to_scale="vrs",
    ).fit(data, prices)

    # This figure publishes only the certified score-level radial comparison.
    # It deliberately requests no slack-completed target, so no target or
    # completion claim is required for the displayed technical-efficiency card.
    technical_metadata = technical.metadata
    technical_spec = technical_metadata.get("expanded_spec", {})
    technical_estimator = technical_spec.get("estimator", {})
    technical_performance = technical_spec.get("performance", {})
    technical_reference = technical_spec.get("reference", {})
    if not (
        technical_metadata.get("method_id") == "static.radial"
        and technical_metadata.get("model_family") == "radial"
        and technical_metadata.get("orientation") == "input"
        and technical_metadata.get("returns_to_scale") == "vrs"
        and technical_metadata.get("reference_kind") == "global"
        and technical_metadata.get("compute_slacks") is False
        and technical_metadata.get("solver_calls") == 4
        and technical_metadata.get("phase_one_solver_calls") == 4
        and technical_metadata.get("phase_two_solver_calls") == 0
        and technical_estimator.get("estimator_id") == "estimator.full.dea"
        and technical_estimator.get("kind") == "full_frontier"
        and technical_estimator.get("family") == "dea_envelopment"
        and technical_performance.get("family") == "radial"
        and technical_performance.get("orientation") == "input"
        and technical_performance.get("slack_refinement") is False
        and technical_reference.get("kind") == "global"
    ):
        raise RuntimeError("the technical-efficiency release specification changed")

    technical_summary = technical.summary()
    required_technical_summary = {
        "dmu_id",
        "period",
        "score",
        "efficiency",
        "score_valid",
        "score_status",
        "solver_status",
        "primary_solver_status",
        "orientation",
        "returns_to_scale",
    }
    if required_technical_summary.difference(technical_summary.columns):
        raise RuntimeError("the technical-efficiency public summary is incomplete")
    if (
        len(technical_summary) != 4
        or technical_summary["dmu_id"].duplicated().any()
        or set(technical_summary["dmu_id"]) != set(plans)
        or technical_summary["period"].notna().any()
        or not technical_summary["score_valid"].eq(True).all()
        or not technical_summary["score_status"].eq("defined").all()
        or not technical_summary["solver_status"].eq("optimal").all()
        or not technical_summary["primary_solver_status"].eq("optimal").all()
        or not technical_summary["orientation"].eq("input").all()
        or not technical_summary["returns_to_scale"].eq("vrs").all()
    ):
        raise RuntimeError("the technical-efficiency score release was withheld")
    technical_summary = technical_summary.set_index("dmu_id").loc[list(plans)]
    technical_values = technical_summary["efficiency"].to_numpy(dtype=np.float64)
    expected_technical = np.asarray((1.0, 1.0, 1.0, 7.0 / 12.0))
    if not (
        np.allclose(technical_values, expected_technical, atol=1e-10, rtol=0.0)
        and np.allclose(
            technical_summary["score"].to_numpy(dtype=np.float64),
            expected_technical,
            atol=1e-10,
            rtol=0.0,
        )
    ):
        raise RuntimeError("the exact technical-efficiency account changed")

    technical_diagnostics = technical.diagnostics
    required_technical_certificates = {
        "dmu_id",
        "period",
        "phase",
        "solver_status",
        "lp_postsolve_certified",
        "postsolve_certified",
        "raw_economic_postsolve_certified",
        "published_output_account_certified",
    }
    if (
        required_technical_certificates.difference(technical_diagnostics.columns)
        or len(technical_diagnostics) != 4
        or technical_diagnostics["dmu_id"].duplicated().any()
        or set(technical_diagnostics["dmu_id"]) != set(plans)
        or technical_diagnostics["period"].notna().any()
        or not technical_diagnostics["phase"].eq(1).all()
        or not technical_diagnostics["solver_status"].eq("optimal").all()
        or not technical_diagnostics[
            list(
                required_technical_certificates
                - {"dmu_id", "period", "phase", "solver_status"}
            )
        ]
        .eq(True)
        .all(axis=None)
    ):
        raise RuntimeError("the radial score programmes were not fully certified")

    profitability_metadata = profitability.metadata
    profitability_spec = profitability_metadata.get("expanded_spec", {})
    profitability_estimator = profitability_spec.get("estimator", {})
    profitability_reference = profitability_spec.get("reference", {})
    profitability_valuation = profitability_spec.get("valuation", {})
    if not (
        profitability_metadata.get("method_id")
        == "economic.profitability.return_to_dollar"
        and profitability_metadata.get("model_family") == "profitability"
        and profitability_metadata.get("returns_to_scale") == "vrs"
        and profitability_metadata.get("reference_kind") == "global"
        and profitability_metadata.get("algorithm") == "closed_form_extreme_ratio"
        and profitability_metadata.get("solver_calls") == 0
        and profitability_metadata.get("ratio_kernel_calls") == 1
        and profitability_estimator.get("estimator_id") == "estimator.full.dea"
        and profitability_estimator.get("kind") == "full_frontier"
        and profitability_estimator.get("family") == "dea_extreme_ratio"
        and profitability_reference.get("kind") == "global"
        and profitability_valuation.get("kind") == "supplied_input_and_output_prices"
        and profitability_valuation.get("scope") == "common"
    ):
        raise RuntimeError("the return-to-dollar release specification changed")

    profitability_summary = profitability.summary()
    required_profitability_summary = {
        "dmu_id",
        "period",
        "solver_status",
        "score_status",
        "self_in_reference",
        "observed_cost",
        "observed_revenue",
        "return_to_dollar",
        "observed_profitability",
        "maximum_profitability",
        "profitability_efficiency",
        "score",
        "efficiency",
    }
    if required_profitability_summary.difference(profitability_summary.columns):
        raise RuntimeError("the return-to-dollar public summary is incomplete")
    if (
        len(profitability_summary) != 4
        or profitability_summary["dmu_id"].duplicated().any()
        or set(profitability_summary["dmu_id"]) != set(plans)
        or profitability_summary["period"].notna().any()
        or not profitability_summary["solver_status"].eq("optimal").all()
        or not profitability_summary["score_status"].eq("defined_self_appraisal").all()
        or not profitability_summary["self_in_reference"].eq(True).all()
    ):
        raise RuntimeError("the return-to-dollar score release was withheld")
    profitability_summary = profitability_summary.set_index("dmu_id").loc[list(plans)]

    observed_cost = 2.0 * quantities[:, 0]
    observed_revenue = 3.0 * quantities[:, 1] + 5.0 * quantities[:, 2]
    observed_profit = observed_revenue - observed_cost
    return_to_dollar = observed_revenue / observed_cost
    maximum_profitability = 37.0 / 10.0
    profitability_efficiency = return_to_dollar / maximum_profitability
    for field, expected in (
        ("observed_cost", observed_cost),
        ("observed_revenue", observed_revenue),
        ("return_to_dollar", return_to_dollar),
        ("observed_profitability", return_to_dollar),
        (
            "maximum_profitability",
            np.full(len(plans), maximum_profitability),
        ),
        ("profitability_efficiency", profitability_efficiency),
        ("score", profitability_efficiency),
        ("efficiency", profitability_efficiency),
    ):
        if not np.allclose(
            profitability_summary[field].to_numpy(dtype=np.float64),
            expected,
            atol=1e-12,
            rtol=0.0,
        ):
            raise RuntimeError(f"the return-to-dollar {field} account changed")

    profitability_diagnostics = profitability.diagnostics
    required_profitability_diagnostics = {
        "dmu_id",
        "period",
        "phase",
        "solver_status",
        "algorithm",
        "candidate_count",
        "maximizer_count",
        "selected_reference_dmu_id",
        "selected_reference_cost",
        "selected_reference_revenue",
        "selected_reference_profitability",
        "ratio_reconstruction_residual",
    }
    if (
        required_profitability_diagnostics.difference(profitability_diagnostics.columns)
        or len(profitability_diagnostics) != 4
        or profitability_diagnostics["dmu_id"].duplicated().any()
        or set(profitability_diagnostics["dmu_id"]) != set(plans)
        or profitability_diagnostics["period"].notna().any()
        or not profitability_diagnostics["phase"].eq(1).all()
        or not profitability_diagnostics["solver_status"].eq("optimal").all()
        or not profitability_diagnostics["algorithm"]
        .eq("closed_form_extreme_ratio")
        .all()
        or not profitability_diagnostics["candidate_count"].eq(4).all()
        or not profitability_diagnostics["maximizer_count"].eq(1).all()
        or not profitability_diagnostics["selected_reference_dmu_id"].eq("B").all()
        or not np.allclose(
            profitability_diagnostics["selected_reference_cost"],
            10.0,
            atol=0.0,
            rtol=0.0,
        )
        or not np.allclose(
            profitability_diagnostics["selected_reference_revenue"],
            37.0,
            atol=0.0,
            rtol=0.0,
        )
        or not np.allclose(
            profitability_diagnostics["selected_reference_profitability"],
            maximum_profitability,
            atol=1e-12,
            rtol=0.0,
        )
        or not np.allclose(
            profitability_diagnostics["ratio_reconstruction_residual"],
            0.0,
            atol=1e-12,
            rtol=0.0,
        )
    ):
        raise RuntimeError("the exact return-to-dollar reduction did not reconcile")

    # This is a declared descriptive aggregation, not a DEA-derived index. It
    # remains separate from both the frontier score and the price-valued account.
    service_throughput = quantities[:, 1] + quantities[:, 2]
    physical_productivity = service_throughput / quantities[:, 0]
    expected_throughput = np.asarray((8.0, 9.0, 6.0, 5.0))
    expected_productivity = np.asarray((2.0, 1.8, 2.0, 5.0 / 6.0))
    if not (
        np.allclose(service_throughput, expected_throughput, atol=0.0, rtol=0.0)
        and np.allclose(
            physical_productivity,
            expected_productivity,
            atol=1e-12,
            rtol=0.0,
        )
    ):
        raise RuntimeError("the observed physical-productivity account changed")

    ink = "#24323d"
    gray = "#5c6b73"
    grid = "#d7e1e4"
    teal = "#176b73"
    orange = "#d97732"
    purple = "#76528f"
    pale_teal = "#edf7f7"
    pale_orange = "#fff6ed"
    pale_purple = "#f6f0f8"
    plan_colors = {"A": teal, "B": orange, "C": gray, "D": purple}

    figure = plt.figure(figsize=(12.0, 8.8), facecolor="white")
    layout = figure.add_gridspec(
        1,
        3,
        left=0.04,
        right=0.97,
        top=0.80,
        bottom=0.27,
        wspace=0.055,
    )
    axes = [figure.add_subplot(layout[0, column]) for column in range(3)]
    for axis in axes:
        axis.set_xlim(0.0, 1.0)
        axis.set_ylim(0.0, 1.0)
        axis.axis("off")

    figure.suptitle(
        "Efficiency, productivity, and profitability are different accounts",
        x=0.04,
        y=0.955,
        ha="left",
        color=ink,
        fontsize=21,
        fontweight="bold",
    )
    figure.text(
        0.04,
        0.895,
        "Same four service plans · one VRS comparison · common observed prices",
        ha="left",
        color=gray,
        fontsize=13.0,
    )
    figure.text(
        0.04,
        0.852,
        "Each card answers its own management question; "
        "the numbers do not share a measurement scale.",
        ha="left",
        color=orange,
        fontsize=12.0,
        fontweight="bold",
    )

    card_specs = (
        (
            axes[0],
            teal,
            pale_teal,
            "INPUT-ORIENTED VRS EFFICIENCY",
            "Can the same services be delivered\nwith fewer resources?",
            "Radial comparison · higher is better",
        ),
        (
            axes[1],
            orange,
            pale_orange,
            "PHYSICAL PRODUCTIVITY LEVEL",
            "How many equally counted services\nare delivered per resource unit?",
            "Declared equal-count level",
        ),
        (
            axes[2],
            purple,
            pale_purple,
            "RETURN-TO-DOLLAR PROFITABILITY",
            "How much revenue is earned\nper unit of cost?",
            "Observed prices · higher R/C is better",
        ),
    )
    for axis, accent, fill, heading, question, subtitle in card_specs:
        axis.add_patch(
            FancyBboxPatch(
                (0.01, 0.01),
                0.98,
                0.98,
                boxstyle="round,pad=0.012,rounding_size=0.025",
                facecolor=fill,
                edgecolor=accent,
                linewidth=1.6,
            )
        )
        axis.text(
            0.055,
            0.935,
            heading,
            color=accent,
            fontsize=12.5,
            fontweight="bold",
            va="top",
        )
        axis.text(
            0.055,
            0.845,
            question,
            color=ink,
            fontsize=12.5,
            fontweight="bold",
            va="top",
            linespacing=1.25,
        )
        axis.text(
            0.055,
            0.715,
            subtitle,
            color=gray,
            fontsize=10.8,
            va="top",
        )
        axis.plot((0.055, 0.945), (0.655, 0.655), color=grid, linewidth=1.2)

    axes[0].text(0.08, 0.605, "PLAN", color=gray, fontsize=10.5, fontweight="bold")
    axes[0].text(
        0.90,
        0.605,
        "RADIAL SCORE",
        ha="right",
        color=gray,
        fontsize=10.5,
        fontweight="bold",
    )
    for row, (plan, value) in enumerate(zip(plans, technical_values, strict=True)):
        y = 0.53 - 0.09 * row
        axes[0].text(
            0.08,
            y,
            plan,
            color=plan_colors[plan],
            fontsize=14,
            fontweight="bold",
            va="center",
        )
        axes[0].text(
            0.90,
            y,
            f"{value:.3f}",
            ha="right",
            color=plan_colors[plan],
            fontsize=14,
            fontweight="bold" if plan in {"A", "B"} else "normal",
            va="center",
        )
    axes[0].text(
        0.055,
        0.145,
        "A and B: radial score 1.000",
        color=teal,
        fontsize=11.5,
        fontweight="bold",
        va="top",
    )
    axes[0].text(
        0.055,
        0.085,
        "Radial result; no slack completion.",
        color=gray,
        fontsize=10.0,
        va="top",
    )

    axes[1].text(0.08, 0.605, "PLAN", color=gray, fontsize=10.5, fontweight="bold")
    axes[1].text(
        0.90,
        0.605,
        "SERVICES / RESOURCE",
        ha="right",
        color=gray,
        fontsize=10.5,
        fontweight="bold",
    )
    for row, (plan, value) in enumerate(zip(plans, physical_productivity, strict=True)):
        y = 0.53 - 0.09 * row
        axes[1].text(
            0.08,
            y,
            plan,
            color=plan_colors[plan],
            fontsize=14,
            fontweight="bold",
            va="center",
        )
        axes[1].text(
            0.90,
            y,
            f"{value:.2f}",
            ha="right",
            color=plan_colors[plan],
            fontsize=14,
            fontweight="bold" if plan in {"A", "B"} else "normal",
            va="center",
        )
    axes[1].text(
        0.055,
        0.145,
        "A 2.00  >  B 1.80",
        color=orange,
        fontsize=11.5,
        fontweight="bold",
        va="top",
    )
    axes[1].text(
        0.055,
        0.085,
        "A level, not productivity change.",
        color=gray,
        fontsize=10.0,
        va="top",
    )

    axes[2].text(0.065, 0.605, "PLAN", color=gray, fontsize=10.5, fontweight="bold")
    for x, label in ((0.58, "R/C"), (0.94, "PROFIT  R - C")):
        axes[2].text(
            x,
            0.605,
            label,
            ha="right",
            color=gray,
            fontsize=10.5,
            fontweight="bold",
        )
    for row, (plan, ratio, profit) in enumerate(
        zip(
            plans,
            return_to_dollar,
            observed_profit,
            strict=True,
        )
    ):
        y = 0.53 - 0.09 * row
        color = plan_colors[plan]
        axes[2].text(
            0.065,
            y,
            plan,
            color=color,
            fontsize=14,
            fontweight="bold",
            va="center",
        )
        axes[2].text(
            0.58,
            y,
            f"{ratio:.2f}",
            ha="right",
            color=color,
            fontsize=14,
            fontweight="bold" if plan in {"A", "B"} else "normal",
            va="center",
        )
        axes[2].text(
            0.94,
            y,
            f"{profit:.0f}",
            ha="right",
            color=color,
            fontsize=13.0,
            va="center",
        )
    axes[2].text(
        0.055,
        0.145,
        "B 3.70  >  A 3.50",
        color=purple,
        fontsize=11.5,
        fontweight="bold",
        va="top",
    )
    axes[2].text(
        0.055,
        0.085,
        "Profit is reported separately as R - C.",
        color=gray,
        fontsize=10.0,
        va="top",
    )

    figure.add_artist(
        FancyBboxPatch(
            (0.04, 0.075),
            0.93,
            0.125,
            boxstyle="round,pad=0.008,rounding_size=0.012",
            transform=figure.transFigure,
            facecolor="#f5f7f8",
            edgecolor=grid,
            linewidth=1.2,
        )
    )
    figure.text(
        0.06,
        0.172,
        "THE A/B MANAGEMENT REVERSAL",
        color=ink,
        fontsize=11.0,
        fontweight="bold",
    )
    figure.text(
        0.06,
        0.132,
        "Same technical score",
        color=teal,
        fontsize=11.2,
        fontweight="bold",
    )
    figure.text(
        0.315,
        0.132,
        "A: higher physical throughput",
        color=orange,
        fontsize=11.2,
        fontweight="bold",
    )
    figure.text(
        0.675,
        0.132,
        "B: higher R/C and profit",
        color=purple,
        fontsize=11.2,
        fontweight="bold",
    )
    figure.text(
        0.06,
        0.093,
        "Different accounts support different questions—not a causal explanation, "
        "quality judgement, or management prescription.",
        color=gray,
        fontsize=10.3,
    )
    figure.text(
        0.04,
        0.025,
        "Four service plans · the three accounts do not share one ranking scale",
        ha="left",
        color=gray,
        fontsize=9.8,
    )

    _save(
        figure,
        "three-performance-accounts-result.svg",
        "Three distinct performance accounts for four service plans",
    )


def peer_eligibility_sensitivity_figure() -> None:
    """Show how two ex-ante eligibility rules change Lakeside's evidence."""

    frame = pd.DataFrame(
        {
            "hospital": (
                "Lakeside",
                "North",
                "East",
                "West",
                "Riverside",
                "University",
                "South",
            ),
            "clinical_hours": (120.0, 110.0, 130.0, 105.0, 115.0, 240.0, 108.0),
            "staffed_bed_days": (80.0, 75.0, 85.0, 70.0, 82.0, 160.0, 74.0),
            "risk_adjusted_episodes": (
                100.0,
                105.0,
                112.0,
                96.0,
                98.0,
                210.0,
                101.0,
            ),
            "avoidable_harm_events": (6.0, 4.0, 5.0, 3.0, 7.0, 8.0, 5.0),
            "mission": (
                "district",
                "district",
                "district",
                "district",
                "district",
                "tertiary",
                "district",
            ),
            "service_contract": (
                "standard",
                "standard",
                "standard",
                "integrated_urgent_care",
                "minimum_service",
                "tertiary_referral",
                "standard",
            ),
            "operating_environment": (
                "urban",
                "urban",
                "urban",
                "urban",
                "remote",
                "urban",
                "urban",
            ),
            "common_episode_definition": (True, True, True, True, True, True, False),
        }
    )
    candidate_roster = (
        "Lakeside",
        "North",
        "East",
        "West",
        "Riverside",
        "University",
        "South",
    )
    expected_quantities = np.asarray(
        (
            (120.0, 80.0, 100.0, 6.0),
            (110.0, 75.0, 105.0, 4.0),
            (130.0, 85.0, 112.0, 5.0),
            (105.0, 70.0, 96.0, 3.0),
            (115.0, 82.0, 98.0, 7.0),
            (240.0, 160.0, 210.0, 8.0),
            (108.0, 74.0, 101.0, 5.0),
        ),
        dtype=np.float64,
    )
    quantity_columns = (
        "clinical_hours",
        "staffed_bed_days",
        "risk_adjusted_episodes",
        "avoidable_harm_events",
    )
    if not (
        frame.shape == (7, 9)
        and tuple(frame["hospital"]) == candidate_roster
        and np.allclose(
            frame.loc[:, list(quantity_columns)].to_numpy(dtype=np.float64),
            expected_quantities,
            atol=0.0,
            rtol=0.0,
        )
        and tuple(frame["mission"])
        == (
            "district",
            "district",
            "district",
            "district",
            "district",
            "tertiary",
            "district",
        )
        and tuple(frame["service_contract"])
        == (
            "standard",
            "standard",
            "standard",
            "integrated_urgent_care",
            "minimum_service",
            "tertiary_referral",
            "standard",
        )
        and tuple(frame["operating_environment"])
        == ("urban", "urban", "urban", "urban", "remote", "urban", "urban")
        and tuple(frame["common_episode_definition"])
        == (True, True, True, True, True, True, False)
    ):
        raise RuntimeError("the hospital comparison-candidate ledger changed")

    common_boundary = (
        frame["mission"].eq("district")
        & frame["operating_environment"].eq("urban")
        & frame["common_episode_definition"]
    )
    same_contract_mask = common_boundary & frame["service_contract"].eq("standard")
    district_mission_mask = common_boundary
    cohort_contracts = (
        (
            "same_contract",
            same_contract_mask,
            ("Lakeside", "North", "East"),
            (15.0 / 16.0, 1.0, 1.0),
            (("North", 1.0),),
            (110.0, 75.0, 105.0),
        ),
        (
            "district_mission",
            district_mission_mask,
            ("Lakeside", "North", "East", "West"),
            (65.0 / 72.0, 1.0, 1.0, 1.0),
            (("North", 4.0 / 9.0), ("West", 5.0 / 9.0)),
            (965.0 / 9.0, 650.0 / 9.0, 100.0),
        ),
    )
    score_by_rule: dict[str, float] = {}
    for (
        label,
        mask,
        roster,
        expected_scores,
        expected_peers,
        expected_peer_activity,
    ) in cohort_contracts:
        cohort = frame.loc[mask].copy()
        if tuple(cohort["hospital"]) != roster:
            raise RuntimeError(f"the {label} eligible reference population changed")
        data = DEAData.from_frame(
            cohort,
            dmu="hospital",
            inputs=("clinical_hours", "staffed_bed_days"),
            outputs="risk_adjusted_episodes",
        )
        result = BCC(
            orientation="input",
            compute_slacks=False,
        ).fit(data)

        metadata = result.metadata
        expanded_spec = metadata.get("expanded_spec", {})
        data_roles = expanded_spec.get("data_roles", {})
        technology = expanded_spec.get("technology", {})
        estimator = expanded_spec.get("estimator", {})
        reference = expanded_spec.get("reference", {})
        performance = expanded_spec.get("performance", {})
        evaluation = expanded_spec.get("evaluation_protocol", {})
        n_eligible = len(roster)
        if not (
            metadata.get("method_id") == "static.radial"
            and metadata.get("specialization_id") == "static.radial.vrs"
            and metadata.get("model_family") == "radial"
            and metadata.get("orientation") == "input"
            and metadata.get("returns_to_scale") == "vrs"
            and metadata.get("reference_kind") == "global"
            and metadata.get("compute_slacks") is False
            and metadata.get("target_completion_id") is None
            and metadata.get("compiled_reference_sets") == 1
            and metadata.get("phase_one_template_compilations") == 1
            and metadata.get("phase_one_task_bindings") == n_eligible
            and metadata.get("phase_one_solver_calls") == n_eligible
            and metadata.get("phase_two_solver_calls") == 0
            and metadata.get("solver_calls") == n_eligible
            and data_roles.get("variables")
            == {
                "inputs": ("clinical_hours", "staffed_bed_days"),
                "outputs": ("risk_adjusted_episodes",),
                "bad_outputs": (),
                "polluting_inputs": (),
            }
            and data_roles.get("bad_outputs") == "excluded"
            and technology
            == {
                "family": "convex_envelopment",
                "returns_to_scale": "vrs",
                "disposal": "ordinary_free",
            }
            and estimator
            == {
                "estimator_id": "estimator.full.dea",
                "kind": "full_frontier",
                "family": "dea_envelopment",
            }
            and reference == {"kind": "global"}
            and performance
            == {
                "family": "radial",
                "orientation": "input",
                "slack_refinement": False,
            }
            and evaluation.get("kind") == "self_appraisal"
            and evaluation.get("target_completion_id") is None
            and evaluation.get("secondary_objective") == "none"
        ):
            raise RuntimeError(f"the {label} BCC release specification changed")

        summary = result.summary()
        required_summary = {
            "dmu_id",
            "period",
            "score",
            "efficiency",
            "score_valid",
            "score_status",
            "is_efficient",
            "is_radially_efficient",
            "is_within_reference_technology",
            "solver_status",
            "primary_solver_status",
            "completion_status",
            "target_status",
            "peer_valid",
            "peer_status",
            "dual_valid",
            "orientation",
            "returns_to_scale",
            "reference_size",
        }
        if (
            required_summary.difference(summary.columns)
            or len(summary) != n_eligible
            or summary["dmu_id"].duplicated().any()
            or tuple(summary["dmu_id"]) != roster
            or summary["period"].notna().any()
            or not summary["score_valid"].eq(True).all()
            or not summary["score_status"].eq("defined").all()
            or not summary["solver_status"].eq("optimal").all()
            or not summary["primary_solver_status"].eq("optimal").all()
            or not summary["is_within_reference_technology"].eq(True).all()
            or not summary["completion_status"].eq("not_requested").all()
            or not summary["target_status"].eq("not_requested").all()
            or not summary["peer_valid"].eq(True).all()
            or not summary["peer_status"].eq("certified_primary_program").all()
            or not summary["dual_valid"].eq(True).all()
            or not summary["orientation"].eq("input").all()
            or not summary["returns_to_scale"].eq("vrs").all()
            or not summary["reference_size"].eq(n_eligible).all()
            or not np.allclose(
                summary["score"].to_numpy(dtype=np.float64),
                np.asarray(expected_scores, dtype=np.float64),
                atol=1e-12,
                rtol=0.0,
            )
            or not np.allclose(
                summary["efficiency"].to_numpy(dtype=np.float64),
                np.asarray(expected_scores, dtype=np.float64),
                atol=1e-12,
                rtol=0.0,
            )
        ):
            raise RuntimeError(f"the {label} public BCC score account changed")
        lakeside = summary.set_index("dmu_id").loc["Lakeside"]
        if not (
            pd.isna(lakeside["is_efficient"])
            and not bool(lakeside["is_radially_efficient"])
            and bool(lakeside["is_within_reference_technology"])
        ):
            raise RuntimeError(f"the {label} score-only interpretation changed")

        diagnostics = result.diagnostics
        certificate_fields = (
            "lp_postsolve_certified",
            "postsolve_certified",
            "raw_economic_postsolve_certified",
            "published_output_account_certified",
            "economic_postsolve_certified",
            "published_peer_account_certified",
            "published_dual_account_certified",
        )
        required_diagnostics = {
            "dmu_id",
            "period",
            "phase",
            "solver_status",
            *certificate_fields,
        }
        if (
            required_diagnostics.difference(diagnostics.columns)
            or len(diagnostics) != n_eligible
            or diagnostics["dmu_id"].duplicated().any()
            or tuple(diagnostics["dmu_id"]) != roster
            or diagnostics["period"].notna().any()
            or not diagnostics["phase"].eq(1).all()
            or not diagnostics["solver_status"].eq("optimal").all()
            or not diagnostics.loc[:, list(certificate_fields)].eq(True).all(axis=None)
        ):
            raise RuntimeError(f"the {label} BCC programmes were not certified")

        peers = result.peers("Lakeside")
        if not (
            len(peers) == len(expected_peers)
            and peers["dmu_id"].eq("Lakeside").all()
            and peers["period"].isna().all()
            and peers["reference_period"].isna().all()
            and tuple(peers["reference_dmu_id"])
            == tuple(peer for peer, _ in expected_peers)
            and np.allclose(
                peers["lambda"].to_numpy(dtype=np.float64),
                np.asarray([weight for _, weight in expected_peers]),
                atol=1e-12,
                rtol=0.0,
            )
            and np.isclose(
                peers["lambda"].to_numpy(dtype=np.float64).sum(),
                1.0,
                atol=1e-12,
                rtol=0.0,
            )
            and result.targets.empty
            and result.slacks.empty
        ):
            raise RuntimeError(f"the {label} active-peer account changed")
        peer_rows = cohort.set_index("hospital").loc[
            list(peers["reference_dmu_id"]),
            ["clinical_hours", "staffed_bed_days", "risk_adjusted_episodes"],
        ]
        peer_activity = peers["lambda"].to_numpy(dtype=np.float64) @ peer_rows.to_numpy(
            dtype=np.float64
        )
        if not np.allclose(
            peer_activity,
            np.asarray(expected_peer_activity, dtype=np.float64),
            atol=1e-12,
            rtol=0.0,
        ):
            raise RuntimeError(f"the {label} selected peer activity changed")
        score_by_rule[label] = float(lakeside["score"])

    same_contract_score = score_by_rule["same_contract"]
    district_mission_score = score_by_rule["district_mission"]
    same_contract_saving = 1.0 - same_contract_score
    district_mission_saving = 1.0 - district_mission_score
    if not (
        np.isclose(
            same_contract_saving,
            1.0 / 16.0,
            atol=1e-12,
            rtol=0.0,
        )
        and np.isclose(
            district_mission_saving,
            7.0 / 72.0,
            atol=1e-12,
            rtol=0.0,
        )
        and np.isclose(
            district_mission_saving - same_contract_saving,
            5.0 / 144.0,
            atol=1e-12,
            rtol=0.0,
        )
    ):
        raise RuntimeError("the Lakeside reference-population sensitivity changed")

    ink = "#24323d"
    gray = "#5c6b73"
    grid = "#d7e1e4"
    teal = "#176b73"
    orange = "#d97732"
    purple = "#76528f"
    pale_teal = "#edf7f7"
    pale_orange = "#fff6ed"

    figure = plt.figure(figsize=(12.0, 9.1), facecolor="white")
    canvas = figure.add_axes((0.0, 0.0, 1.0, 1.0))
    canvas.set_xlim(0.0, 1.0)
    canvas.set_ylim(0.0, 1.0)
    canvas.axis("off")

    canvas.text(
        0.045,
        0.945,
        "Same hospital record, different eligibility rules",
        color=ink,
        fontsize=21,
        fontweight="bold",
        va="top",
    )
    canvas.text(
        0.045,
        0.895,
        "The analyst declares who is eligible before DEA selects "
        "positive-intensity peers.",
        color=gray,
        fontsize=13.0,
        va="top",
    )

    canvas.add_patch(
        FancyBboxPatch(
            (0.045, 0.787),
            0.91,
            0.067,
            boxstyle="round,pad=0.008,rounding_size=0.012",
            facecolor="#f5f7f8",
            edgecolor=grid,
            linewidth=1.2,
        )
    )
    canvas.text(
        0.07,
        0.821,
        "CANDIDATE ROSTER  →  PRE-DECLARED ELIGIBILITY RULE  →  "
        "ELIGIBLE POPULATION  →  ACTIVE PEERS",
        color=ink,
        fontsize=12.5,
        fontweight="bold",
        va="center",
    )
    canvas.add_patch(
        FancyBboxPatch(
            (0.045, 0.675),
            0.91,
            0.077,
            boxstyle="round,pad=0.009,rounding_size=0.012",
            facecolor="white",
            edgecolor=teal,
            linewidth=1.5,
        )
    )
    canvas.text(
        0.065,
        0.725,
        "LAKESIDE'S RECORDED OPERATION IS UNCHANGED",
        color=teal,
        fontsize=12.5,
        fontweight="bold",
        va="center",
    )
    canvas.text(
        0.065,
        0.695,
        "120 clinical hours  ·  80 staffed bed-days  ·  "
        "100 risk-adjusted completed episodes",
        color=ink,
        fontsize=12.0,
        va="center",
    )
    card_specs = (
        (
            0.045,
            teal,
            pale_teal,
            "SAME SERVICE-CONTRACT RULE",
            "district + urban + common coding + standard contract",
            "Eligible population (3)",
            "Lakeside · North · East",
            same_contract_score,
            same_contract_saving,
            "North (1.000)",
        ),
        (
            0.515,
            orange,
            pale_orange,
            "SHARED DISTRICT-MISSION RULE",
            "West admitted after prior comparability review",
            "Eligible population (4)",
            "Same-contract three + West",
            district_mission_score,
            district_mission_saving,
            "4/9 North + 5/9 West",
        ),
    )
    for (
        x,
        accent,
        fill,
        heading,
        rule,
        population_label,
        population,
        score,
        saving,
        active_peers,
    ) in card_specs:
        canvas.add_patch(
            FancyBboxPatch(
                (x, 0.278),
                0.44,
                0.355,
                boxstyle="round,pad=0.011,rounding_size=0.016",
                facecolor=fill,
                edgecolor=accent,
                linewidth=1.7,
            )
        )
        canvas.text(
            x + 0.022,
            0.592,
            heading,
            color=accent,
            fontsize=13.5,
            fontweight="bold",
            va="top",
        )
        canvas.text(
            x + 0.022,
            0.548,
            rule,
            color=ink,
            fontsize=11.8,
            fontweight="bold",
            va="top",
        )
        canvas.text(
            x + 0.022,
            0.497,
            f"{population_label}: {population}",
            color=gray,
            fontsize=11.0,
            fontweight="bold",
            va="top",
        )
        canvas.plot((x + 0.022, x + 0.418), (0.425, 0.425), color=grid, linewidth=1.2)
        canvas.text(
            x + 0.022,
            0.390,
            "COMMON PROPORTIONAL RESOURCE-SAVING OPPORTUNITY",
            color=gray,
            fontsize=9.8,
            fontweight="bold",
            va="top",
        )
        canvas.text(
            x + 0.022,
            0.347,
            f"{100.0 * saving:.2f}%",
            color=accent,
            fontsize=23,
            fontweight="bold",
            va="top",
        )
        canvas.text(
            x + 0.165,
            0.365,
            f"Radial score: {score:.4f}",
            color=ink,
            fontsize=10.2,
            fontweight="bold",
            va="top",
        )
        canvas.text(
            x + 0.165,
            0.329,
            f"Active peers: {active_peers}",
            color=ink,
            fontsize=9.8,
            fontweight="bold",
            va="top",
        )
        canvas.text(
            x + 0.022,
            0.294,
            "100 episodes protected · before slack completion",
            color=gray,
            fontsize=9.8,
            va="top",
        )

    canvas.add_patch(
        FancyBboxPatch(
            (0.045, 0.086),
            0.91,
            0.147,
            boxstyle="round,pad=0.009,rounding_size=0.012",
            facecolor="#f6f0f8",
            edgecolor=purple,
            linewidth=1.4,
        )
    )
    canvas.text(
        0.065,
        0.205,
        "INTERPRETATION BOUNDARY",
        color=purple,
        fontsize=11.8,
        fontweight="bold",
        va="top",
    )
    canvas.text(
        0.065,
        0.169,
        "Supported: eligibility changes the resource-saving opportunity "
        "by 3.47 points.",
        color=ink,
        fontsize=11.5,
        fontweight="bold",
        va="top",
    )
    canvas.text(
        0.065,
        0.134,
        "Not supported: a causal contract effect, practice transferability, "
        "or inferior management.",
        color=ink,
        fontsize=11.0,
        va="top",
    )
    canvas.text(
        0.065,
        0.101,
        "Teaching samples are tiny; harm is outside this account; no completed target.",
        color=gray,
        fontsize=10.3,
        va="top",
    )
    canvas.text(
        0.045,
        0.035,
        "Same hospital record; only the pre-declared eligible population changes.",
        color=gray,
        fontsize=9.8,
        va="top",
    )

    _save(
        figure,
        "peer-eligibility-sensitivity-result.svg",
        "Same hospital record under two eligibility rules",
    )


def sbm_improvement_figure() -> None:
    dataset_name = "sbm_slack_contrast"
    frame = load_dataset(dataset_name)
    roles = dataset_info(dataset_name).roles
    data = DEAData.from_frame(
        frame,
        dmu=roles["dmu"],
        inputs=roles["inputs"],
        outputs=roles["outputs"],
    )
    result = SBM(returns_to_scale="crs").fit(data)
    figure = result.plot(kind="improvement", dmu_id="Uneven")
    _use_reader_facing_text_block(
        figure,
        marker="One certified solver-selected optimum",
        text=(
            "One selected feasible CRS plan; alternative peers or targets may "
            "support the same score. Variable-specific resource savings and "
            "service gains are benchmark opportunities, not causal or "
            "prescriptive instructions. Quantities retain their original units."
        ),
        context="classic SBM improvement",
    )
    _save(
        figure,
        "sbm-slack-contrast-result.svg",
        "Selected variable-specific SBM operating plan for the uneven service plan",
    )


def reference_frequency_figure() -> None:
    """Render one certified selected-plan peer-frequency audit."""

    frame = load_dataset("slacks_2x2")
    roles = dataset_info("slacks_2x2").roles
    if not (
        frame.shape == (8, 5)
        and tuple(frame["dmu"]) == tuple("ABCDEFGH")
        and roles
        == {
            "dmu": "dmu",
            "inputs": ("labor", "capital"),
            "outputs": ("service", "quality"),
        }
        and np.allclose(
            frame[["labor", "capital", "service", "quality"]].to_numpy(
                dtype=np.float64
            ),
            np.asarray(
                (
                    (1.0, 3.0, 1.2, 0.70),
                    (1.4, 2.2, 1.6, 0.82),
                    (2.2, 1.5, 2.0, 0.90),
                    (3.0, 1.0, 2.2, 0.94),
                    (2.0, 2.8, 1.3, 0.62),
                    (2.8, 2.4, 1.7, 0.72),
                    (3.4, 1.8, 1.8, 0.78),
                    (2.5, 2.0, 1.6, 0.68),
                ),
                dtype=np.float64,
            ),
            atol=0.0,
            rtol=0.0,
        )
    ):
        raise RuntimeError("the reference-frequency teaching data changed")

    data = DEAData.from_frame(
        frame,
        dmu=roles["dmu"],
        inputs=roles["inputs"],
        outputs=roles["outputs"],
    )
    result = BCC(
        orientation="input",
        compute_slacks=False,
    ).fit(data)
    summary = result.summary()
    expected_scores = np.asarray(
        (
            1.0,
            1.0,
            1.0,
            1.0,
            0.7527472527472527,
            0.7061855670103093,
            0.732484076433121,
            0.817910447761194,
        ),
        dtype=np.float64,
    )
    if not (
        result.metadata.get("method_id") == "static.radial"
        and result.metadata.get("specialization_id") == "static.radial.vrs"
        and result.metadata.get("reference_kind") == "global"
        and result.metadata.get("orientation") == "input"
        and result.metadata.get("returns_to_scale") == "vrs"
        and result.metadata.get("compute_slacks") is False
        and result.metadata.get("target_completion_id") is None
        and result.metadata.get("phase_one_solver_calls") == 8
        and result.metadata.get("phase_two_solver_calls") == 0
        and result.metadata.get("solver_calls") == 8
        and tuple(summary["dmu_id"]) == tuple("ABCDEFGH")
        and summary["period"].isna().all()
        and summary["solver_status"].eq("optimal").all()
        and summary["score_valid"].eq(True).all()
        and summary["peer_valid"].eq(True).all()
        and summary["peer_status"].eq("certified_primary_program").all()
        and np.allclose(
            summary["efficiency"].to_numpy(dtype=np.float64),
            expected_scores,
            atol=1e-12,
            rtol=0.0,
        )
        and summary.loc[:3, "is_radially_efficient"].eq(True).all()
        and summary.loc[4:, "is_radially_efficient"].eq(False).all()
        and summary["is_efficient"].isna().all()
        and result.targets.empty
        and result.slacks.empty
    ):
        raise RuntimeError("the selected BCC peer-frequency source account changed")

    diagnostics = result.diagnostics
    certificate_fields = (
        "lp_postsolve_certified",
        "postsolve_certified",
        "raw_economic_postsolve_certified",
        "published_output_account_certified",
        "economic_postsolve_certified",
        "published_peer_account_certified",
    )
    if not (
        len(diagnostics) == 8
        and tuple(diagnostics["dmu_id"]) == tuple("ABCDEFGH")
        and diagnostics["phase"].eq(1).all()
        and diagnostics["solver_status"].eq("optimal").all()
        and diagnostics.loc[:, list(certificate_fields)].eq(True).all(axis=None)
    ):
        raise RuntimeError("the BCC peer plans are not completely certified")

    expected_edges = (
        ("A", "A"),
        ("B", "B"),
        ("C", "C"),
        ("D", "D"),
        ("E", "B"),
        ("E", "C"),
        ("F", "B"),
        ("F", "C"),
        ("G", "C"),
        ("G", "D"),
        ("H", "B"),
        ("H", "C"),
    )
    source_edges = tuple(
        result.intensities[["dmu_id", "reference_dmu_id"]].itertuples(
            index=False,
            name=None,
        )
    )
    source_peer_tolerance = float(result.metadata["peer_tolerance"])
    source_lambdas = result.intensities["lambda"].to_numpy(dtype=np.float64)
    if not (
        source_edges == expected_edges
        and np.isfinite(source_peer_tolerance)
        and source_peer_tolerance >= 0.0
        and np.isfinite(source_lambdas).all()
        and np.all(source_lambdas > source_peer_tolerance)
    ):
        raise RuntimeError("the BCC solver-selected peer edges changed")

    solver_calls_before_diagnostic = int(result.metadata["solver_calls"])
    frequency = result.reference_frequency()
    account = frequency.reference_frame
    edges = frequency.edge_frame
    expected_total = np.asarray((1, 4, 5, 2, 0, 0, 0, 0), dtype=np.int64)
    expected_self = np.asarray((1, 1, 1, 1, 0, 0, 0, 0), dtype=np.int64)
    expected_other = expected_total - expected_self
    if not (
        frequency.metadata.get("method_id")
        == "analysis.reference_frequency.selected_plan"
        and frequency.metadata.get("source_method_id") == "static.radial"
        and frequency.metadata.get("frequency_unit")
        == "reported_active_solver_selected_peer_edge"
        and frequency.metadata.get("source_peer_tolerance") == source_peer_tolerance
        and frequency.metadata.get("reference_rate_denominator")
        == "all_evaluated_organizations"
        and frequency.metadata.get("observation_count") == 8
        and frequency.metadata.get("active_edge_count") == 12
        and frequency.metadata.get("selected_reference_count") == 4
        and frequency.metadata.get("unselected_reference_count") == 4
        and frequency.metadata.get("self_edge_count") == 4
        and frequency.metadata.get("other_edge_count") == 8
        and frequency.metadata.get("alternate_optima_assessed") is False
        and frequency.metadata.get("global_reference_set_claim") is False
        and frequency.metadata.get("outlier_claim") is False
        and frequency.metadata.get("inference") == "none"
        and frequency.metadata.get("additional_solver_calls") == 0
        and result.metadata.get("solver_calls") == solver_calls_before_diagnostic
        and tuple(account["reference_dmu_id"]) == tuple("ABCDEFGH")
        and account["reference_period"].isna().all()
        and np.array_equal(
            account["reference_frequency"].to_numpy(dtype=np.int64),
            expected_total,
        )
        and np.array_equal(
            account["self_reference_frequency"].to_numpy(dtype=np.int64),
            expected_self,
        )
        and np.array_equal(
            account["other_reference_frequency"].to_numpy(dtype=np.int64),
            expected_other,
        )
        and np.allclose(
            account["reference_rate"].to_numpy(dtype=np.float64),
            expected_total / 8.0,
            atol=0.0,
            rtol=0.0,
        )
        and tuple(
            edges[["dmu_id", "reference_dmu_id"]].itertuples(
                index=False,
                name=None,
            )
        )
        == expected_edges
        and np.allclose(
            edges["lambda"].to_numpy(dtype=np.float64),
            source_lambdas,
            atol=0.0,
            rtol=0.0,
        )
    ):
        raise RuntimeError("the public reference-frequency account changed")

    ink = "#24323d"
    gray = "#687780"
    grid = "#dce5e7"
    teal = "#176b73"
    orange = "#d97732"

    figure, axis = plt.subplots(figsize=(11.2, 7.0), facecolor="white")
    figure.subplots_adjust(left=0.12, right=0.96, top=0.77, bottom=0.22)
    positions = np.arange(len(account))
    other = account["other_reference_frequency"].to_numpy(dtype=np.int64)
    self_frequency = account["self_reference_frequency"].to_numpy(dtype=np.int64)
    total = account["reference_frequency"].to_numpy(dtype=np.int64)
    axis.barh(
        positions,
        other,
        height=0.62,
        color=orange,
        label="Selected by other organizations",
    )
    axis.barh(
        positions,
        self_frequency,
        left=other,
        height=0.62,
        color=teal,
        label="Self-reference",
    )
    axis.set_yticks(positions, account["reference_dmu_id"])
    axis.invert_yaxis()
    axis.set_xlim(0.0, 6.0)
    axis.set_xticks(np.arange(0, 6, 1))
    axis.set_xlabel("Number of reported peer accounts (8 evaluations)", color=ink)
    axis.set_ylabel("Organization", color=ink)
    axis.xaxis.grid(True, color=grid, linewidth=1.0)
    axis.set_axisbelow(True)
    axis.spines[["top", "right", "left"]].set_visible(False)
    axis.spines["bottom"].set_color(grid)
    axis.tick_params(colors=ink, labelsize=11)
    for position, (other_count, self_count, total_count) in enumerate(
        zip(other, self_frequency, total, strict=True)
    ):
        label = (
            f"{other_count} other + {self_count} self"
            if total_count
            else "0 reported edges"
        )
        axis.text(
            float(total_count) + 0.10,
            position,
            label,
            va="center",
            color=ink if total_count else gray,
            fontsize=10.5,
            fontweight="bold" if total_count else "normal",
        )
    figure.suptitle(
        "How often each organization enters the selected peer plans",
        x=0.06,
        y=0.94,
        ha="left",
        color=ink,
        fontsize=20,
        fontweight="bold",
    )
    figure.text(
        0.06,
        0.855,
        "One score-only BCC fit · reported-edge counts above the "
        "source threshold, not sums of λ",
        ha="left",
        color=gray,
        fontsize=12.2,
    )
    axis.legend(
        loc="lower right",
        frameon=False,
        labelcolor=ink,
        fontsize=10.5,
    )
    figure.text(
        0.06,
        0.105,
        "Audit lead: repeated selection can flag comparative reach and a case for "
        "closer practice review.",
        ha="left",
        color=teal,
        fontsize=10.8,
        fontweight="bold",
    )
    figure.text(
        0.06,
        0.058,
        "Not exact support below the reporting threshold; not a superiority "
        "rank, outlier diagnosis, causal or transferability finding, or an "
        "all-optima set.",
        ha="left",
        color=gray,
        fontsize=10.3,
    )
    _save(
        figure,
        "reference-frequency-result.svg",
        "Selected-plan reference frequency for eight service organizations",
    )


def slack_family_rulers_figure() -> None:
    """Show three native reports for one independently checked physical plan."""

    frame = load_dataset("slacks_2x2")
    roles = dataset_info("slacks_2x2").roles
    data = DEAData.from_frame(
        frame,
        dmu=roles["dmu"],
        inputs=roles["inputs"],
        outputs=roles["outputs"],
    )
    results = {
        "Additive": AdditiveDEA(returns_to_scale="vrs").fit(data),
        "RAM": RAM().fit(data),
        "SBM": SBM(returns_to_scale="vrs").fit(data),
    }
    focus = "E"

    # Do not let a plausible-looking common plan enter the book merely because
    # every backend returned ``optimal``. Additive/RAM expose claim-specific
    # release fields; classic SBM exposes a score gate and phase-one economic
    # certificate. The physical target and peer accounts are then rebuilt from
    # every public result below.
    for name in ("Additive", "RAM"):
        result = results[name]
        row = result.summary().set_index("dmu_id").loc[focus]
        expected_status = {
            "score": "defined",
            "target": "certified_published_quantity_account",
            "peer": "certified_thresholded_peer_account",
        }
        for claim, required_status in expected_status.items():
            valid_field = f"{claim}_valid"
            status_field = f"{claim}_status"
            if valid_field not in row.index or status_field not in row.index:
                raise RuntimeError(
                    f"{name} did not expose the {claim} release contract"
                )
            if not bool(row[valid_field]):
                raise RuntimeError(
                    f"{name} withheld its {claim} claim: {row[status_field]}"
                )
            if str(row[status_field]) != required_status:
                raise RuntimeError(
                    f"{name} exposed an unexpected {claim} status: {row[status_field]}"
                )
        diagnostics = result.diagnostics.query("dmu_id == @focus and phase == 1")
        required_certificates = (
            "lp_postsolve_certified",
            "raw_account_certified",
            "published_account_certified",
            "published_quantity_account_certified",
            "published_weighted_slack_account_certified",
            "published_peer_account_certified",
        )
        missing = set(required_certificates).difference(diagnostics.columns)
        if diagnostics.empty or missing:
            raise RuntimeError(
                f"{name} diagnostics omitted certificates: {sorted(missing)}"
            )
        if not diagnostics.loc[:, list(required_certificates)].all(axis=None):
            raise RuntimeError(f"{name} did not certify its complete score account")

    sbm = results["SBM"]
    sbm_row = sbm.summary().set_index("dmu_id").loc[focus]
    if not bool(sbm_row.get("score_valid", False)):
        raise RuntimeError(f"SBM withheld its score claim: {sbm_row['score_status']}")
    sbm_diagnostics = sbm.diagnostics.query("dmu_id == @focus and phase == 1")
    if sbm_diagnostics.empty:
        raise RuntimeError("SBM omitted its phase-one certificate")
    for field in ("postsolve_certified", "economic_postsolve_certified"):
        if field not in sbm_diagnostics or not bool(sbm_diagnostics[field].all()):
            raise RuntimeError(f"SBM did not certify {field}")

    role_order = {
        ("input", variable): position
        for position, variable in enumerate(data.input_names)
    }
    role_order.update(
        {
            ("output", variable): len(data.input_names) + position
            for position, variable in enumerate(data.output_names)
        }
    )

    slack_accounts: dict[str, pd.DataFrame] = {}
    target_accounts: dict[str, pd.DataFrame] = {}
    peer_accounts: dict[str, pd.Series] = {}
    for name, result in results.items():
        slacks = result.slacks.query("dmu_id == @focus").copy()
        slacks["display_order"] = [
            role_order[(str(role), str(variable))]
            for role, variable in zip(slacks["role"], slacks["variable"], strict=True)
        ]
        slack_accounts[name] = slacks.sort_values("display_order").reset_index(
            drop=True
        )

        targets = result.targets.query("dmu_id == @focus").copy()
        targets["display_order"] = [
            role_order[(str(role), str(variable))]
            for role, variable in zip(targets["role"], targets["variable"], strict=True)
        ]
        target_accounts[name] = targets.sort_values("display_order").reset_index(
            drop=True
        )

        peers = result.peers(focus).set_index("reference_dmu_id")["lambda"]
        peer_accounts[name] = peers.sort_index()

    baseline_slacks = slack_accounts["Additive"]
    baseline_targets = target_accounts["Additive"]
    baseline_peers = peer_accounts["Additive"]
    for name in ("RAM", "SBM"):
        slacks = slack_accounts[name]
        targets = target_accounts[name]
        peers = peer_accounts[name]
        if not (
            baseline_slacks[["role", "variable"]].equals(slacks[["role", "variable"]])
            and np.allclose(
                baseline_slacks["slack"], slacks["slack"], atol=1e-9, rtol=0.0
            )
            and baseline_targets[["role", "variable"]].equals(
                targets[["role", "variable"]]
            )
            and np.allclose(
                baseline_targets[["observed", "target"]],
                targets[["observed", "target"]],
                atol=1e-9,
                rtol=0.0,
            )
            and baseline_peers.index.equals(peers.index)
            and np.allclose(baseline_peers, peers, atol=1e-9, rtol=0.0)
        ):
            raise RuntimeError(f"{name} did not select the shared physical plan")

    if not (
        baseline_peers.index.tolist() == ["B", "C"]
        and np.allclose(baseline_peers.to_numpy(), (0.25, 0.75), atol=1e-9)
        and np.isclose(float(baseline_peers.sum()), 1.0, atol=1e-9)
    ):
        raise RuntimeError("the shared VRS peer account did not reconstruct")

    observed = baseline_targets["observed"].to_numpy(dtype=float)
    targets = baseline_targets["target"].to_numpy(dtype=float)
    slacks = baseline_slacks["slack"].to_numpy(dtype=float)
    roles_array = baseline_slacks["role"].astype(str).to_numpy()
    reconstructed = np.where(
        roles_array == "input", observed - slacks, observed + slacks
    )
    if not np.allclose(reconstructed, targets, atol=1e-9, rtol=0.0):
        raise RuntimeError("the shared original-unit target account did not close")

    expected_plan = {
        ("input", "labor"): (2.0, 0.0, 2.0),
        ("input", "capital"): (2.8, 1.125, 1.675),
        ("output", "service"): (1.3, 0.6, 1.9),
        ("output", "quality"): (0.62, 0.26, 0.88),
    }
    actual_plan = {
        (str(slack_row.role), str(slack_row.variable)): (
            float(target_row.observed),
            float(slack_row.slack),
            float(target_row.target),
        )
        for slack_row, target_row in zip(
            baseline_slacks.itertuples(),
            baseline_targets.itertuples(),
            strict=True,
        )
    }
    if actual_plan.keys() != expected_plan.keys() or any(
        not np.allclose(actual_plan[key], expected, atol=1e-9, rtol=0.0)
        for key, expected in expected_plan.items()
    ):
        raise RuntimeError("the shared teaching plan changed")

    headline = {
        name: float(result.summary().set_index("dmu_id").loc[focus, "score"])
        for name, result in results.items()
    }
    expected_headline = {
        "Additive": 1.985,
        "RAM": 0.50625,
        "SBM": 0.5547634428448381,
    }
    if any(
        not np.isclose(headline[name], expected, atol=1e-9, rtol=0.0)
        for name, expected in expected_headline.items()
    ):
        raise RuntimeError("the three native reporting accounts did not reconstruct")

    ink = "#24323d"
    grid = "#dce5e7"
    teal = "#176b73"
    orange = "#d97732"
    blue = "#356fa3"
    gray = "#687780"
    pale = "#f5f8f8"

    figure = plt.figure(figsize=(8.2, 10.2), facecolor="white")
    layout = figure.add_gridspec(
        2,
        1,
        height_ratios=(1.08, 1.0),
        left=0.055,
        right=0.955,
        top=0.84,
        bottom=0.16,
        hspace=0.10,
    )
    ledger_axis = figure.add_subplot(layout[0, 0])
    cards_axis = figure.add_subplot(layout[1, 0])
    for axis in (ledger_axis, cards_axis):
        axis.set_xlim(0.0, 1.0)
        axis.set_ylim(0.0, 1.0)
        axis.axis("off")

    figure.suptitle(
        "One operating plan, three reporting rulers",
        x=0.045,
        y=0.955,
        ha="left",
        color=ink,
        fontsize=19,
        fontweight="bold",
    )
    figure.text(
        0.045,
        0.895,
        "Organization E · one feasible VRS plan · the physical evidence stays fixed",
        ha="left",
        color=gray,
        fontsize=10.5,
    )

    ledger_axis.text(
        0.0,
        0.96,
        "THE SHARED OPERATING EVIDENCE",
        color=teal,
        fontsize=10,
        fontweight="bold",
        va="top",
    )
    ledger_axis.text(
        0.0,
        0.89,
        "Selected peers  0.25 × B + 0.75 × C",  # noqa: RUF001
        color=ink,
        fontsize=13,
        fontweight="bold",
        va="top",
    )
    ledger_axis.text(
        0.0,
        0.835,
        "Each row keeps its own original unit; the rows do not share a quantity axis.",
        color=gray,
        fontsize=9.5,
        va="top",
    )

    headers = (
        (0.02, "Variable"),
        (0.42, "Role"),
        (0.53, "Observed"),
        (0.70, "Change"),
        (0.87, "Target"),
    )
    for x, label in headers:
        ledger_axis.text(
            x,
            0.74,
            label,
            color=gray,
            fontsize=9.5,
            fontweight="bold",
            ha="left" if x == 0.02 else "center",
            va="center",
        )

    row_y = (0.64, 0.51, 0.38, 0.25)
    for position, (y, slack_row, target_row) in enumerate(
        zip(
            row_y,
            baseline_slacks.itertuples(),
            baseline_targets.itertuples(),
            strict=True,
        )
    ):
        if position % 2 == 0:
            ledger_axis.add_patch(
                Rectangle(
                    (0.0, y - 0.052), 0.98, 0.104, facecolor=pale, edgecolor="none"
                )
            )
        role = str(slack_row.role)
        role_label = "Resource" if role == "input" else "Service"
        variable = str(slack_row.variable).replace("_", " ").title()
        change = float(slack_row.slack)
        change_text = (
            "0.000"
            if np.isclose(change, 0.0, atol=1e-12)
            else f"−{change:.3f}"  # noqa: RUF001
            if role == "input"
            else f"+{change:.3f}"
        )
        role_color = blue if role == "input" else teal
        ledger_axis.text(
            0.02,
            y,
            variable,
            color=ink,
            fontsize=10.2,
            fontweight="bold",
            ha="left",
            va="center",
        )
        ledger_axis.text(
            0.42,
            y,
            role_label,
            color=role_color,
            fontsize=9.5,
            ha="right",
            va="center",
        )
        for x, value, color in (
            (0.56, float(target_row.observed), ink),
            (0.72, change_text, orange if change != 0.0 else gray),
            (0.89, float(target_row.target), ink),
        ):
            text_value = value if isinstance(value, str) else f"{value:.3f}"
            ledger_axis.text(
                x,
                y,
                text_value,
                color=color,
                fontsize=10.2,
                fontweight="bold" if x == 0.72 else "normal",
                ha="center",
                va="center",
            )

    ledger_axis.text(
        0.0,
        0.095,
        "Same peers · same slacks · same selected targets",
        color=teal,
        fontsize=10.2,
        fontweight="bold",
        va="center",
    )
    ledger_axis.text(
        0.0,
        0.045,
        "The fitted evidence agrees here; only the reporting ruler changes.",
        color=gray,
        fontsize=9.5,
        va="center",
    )

    cards_axis.text(
        0.0,
        0.96,
        "THREE NATIVE HEADLINES",
        color=teal,
        fontsize=10,
        fontweight="bold",
        va="top",
    )
    card_specs = (
        (
            0.65,
            "ADDITIVE · ORIGINAL-UNIT WEIGHTS",
            f"{headline['Additive']:.3f}",
            "best 0 · lower is closer",
            "weighted original-unit slacks · unit-dependent",
            blue,
        ),
        (
            0.37,
            "RAM · SAMPLE-RANGE RULER",
            f"{headline['RAM']:.6f}",
            "best 1 · higher is closer",
            "efficiency / declared sample ranges",
            teal,
        ),
        (
            0.09,
            "SBM · OWN-OPERATION RULER",
            f"{headline['SBM']:.6f}",
            "best 1 · higher is closer",
            "efficiency / E's observed quantities",
            orange,
        ),
    )
    for y, heading, value, benchmark, meaning, accent in card_specs:
        cards_axis.add_patch(
            FancyBboxPatch(
                (0.0, y),
                0.98,
                0.225,
                boxstyle="round,pad=0.012,rounding_size=0.018",
                facecolor="white",
                edgecolor=grid,
                linewidth=1.15,
            )
        )
        cards_axis.add_patch(
            Rectangle((0.0, y), 0.015, 0.225, facecolor=accent, edgecolor="none")
        )
        cards_axis.text(
            0.05,
            y + 0.178,
            heading,
            color=accent,
            fontsize=9.5,
            fontweight="bold",
            va="center",
        )
        cards_axis.text(
            0.05,
            y + 0.108,
            value,
            color=ink,
            fontsize=19,
            fontweight="bold",
            va="center",
        )
        cards_axis.add_patch(
            Rectangle(
                (0.445, y + 0.045),
                0.0015,
                0.115,
                facecolor=grid,
                edgecolor="none",
            )
        )
        cards_axis.text(
            0.49,
            y + 0.125,
            benchmark,
            color=ink,
            fontsize=9.5,
            va="center",
        )
        cards_axis.text(
            0.49,
            y + 0.072,
            meaning,
            color=gray,
            fontsize=9.5,
            va="center",
        )

    figure.text(
        0.045,
        0.055,
        "Do not compare 1.985, 0.506250, and 0.554763 as one ranking scale:\n"
        "same plan does not mean the same estimand.",
        ha="left",
        color=orange,
        fontsize=10.0,
        fontweight="bold",
    )
    figure.text(
        0.045,
        0.02,
        "Organization E · Additive, RAM, and SBM · same VRS technology, peers,\n"
        "slacks, and selected target",
        ha="left",
        color=gray,
        fontsize=9.5,
    )
    _save(
        figure,
        "slack-family-rulers-result.svg",
        "One operating plan under three slack-reporting rulers",
    )


def undesirable_sbm_improvement_figure() -> None:
    frame = pd.DataFrame(
        {
            "plant": ["A", "C"],
            "resource": [1.0, 2.0],
            "service": [2.0, 1.0],
            "residual": [1.0, 2.0],
        }
    )
    data = DEAData.from_frame(
        frame,
        dmu="plant",
        inputs="resource",
        outputs="service",
        bad_outputs="residual",
    )
    result = UndesirableSBM(returns_to_scale="vrs").fit(data)
    figure = result.plot(kind="improvement", dmu_id="C")
    _use_reader_facing_text_block(
        figure,
        marker="One certified solver-selected optimum",
        text=(
            "One selected feasible VRS plan under separability and strong "
            "disposability; alternative peers or targets may support the same score.\n"
            "Residual reduction is a benchmark opportunity, not a damage valuation, "
            "causal conclusion, or prescription.\n"
            "Quantities retain their original units."
        ),
        context="undesirable-output SBM improvement",
    )
    _save(
        figure,
        "undesirable-sbm-improvement-result.svg",
        "Selected environmental operating plan for plant C",
    )


def environmental_ddf_improvement_figure() -> None:
    """Render one certified conditional environmental-management programme."""

    frame = load_dataset("environmental_panel")
    data = DEAData.from_frame(
        frame,
        dmu="dmu",
        period="period",
        inputs=("energy", "labor"),
        outputs="electricity",
        bad_outputs="co2",
    )
    result = CommonFactorWeakDisposalDDF(
        input_direction="zeros",
        output_direction="observed",
        bad_output_direction="observed",
        reference="contemporaneous",
    ).fit(data)
    focus = "Central"
    period = 2020

    # Discovery is the public promise that this fitted result owns an
    # improvement account.  The book then applies a stricter, case-specific
    # release gate before asking the public plot method to render anything.
    if "improvement" not in {plot.kind for plot in result.available_plots()}:
        raise RuntimeError(
            "the certified environmental DDF result did not expose improvement"
        )

    summary = result.summary()
    required_summary = {
        "solver_status",
        "score",
        "distance",
        "score_valid",
        "score_status",
        "completion_solver_status",
        "completion_valid",
        "completion_status",
        "target_valid",
        "target_status",
        "returns_to_scale",
        "bad_output_disposability",
    }
    missing_summary = required_summary.difference(summary.columns)
    selected_summary = summary.loc[
        (summary["dmu_id"] == focus) & (summary["period"] == period)
    ]
    if missing_summary or len(selected_summary) != 1:
        raise RuntimeError(
            "the environmental DDF result omitted its unique public release row"
        )
    row = selected_summary.iloc[0]
    valid_claims = ("score_valid", "completion_valid", "target_valid")
    if any(not (pd.notna(row[field]) and bool(row[field])) for field in valid_claims):
        raise RuntimeError("the environmental DDF result withheld its selected plan")
    expected_statuses = {
        "solver_status": "optimal",
        "score_status": "defined",
        "completion_solver_status": "optimal",
        "completion_status": "certified",
        "target_status": "certified_slack_completion",
        "returns_to_scale": "crs",
        "bad_output_disposability": "weak_common_factor",
    }
    if any(
        str(row[field]) != expected for field, expected in expected_statuses.items()
    ):
        raise RuntimeError(
            "the environmental DDF result changed its certified production account"
        )

    metadata = result.metadata
    if not (
        metadata.get("method_id") == "environmental.ddf.weak_disposal.common_factor"
        and metadata.get("reference_kind") == "contemporaneous"
        and metadata.get("returns_to_scale") == "crs"
        and metadata.get("bad_output_disposability") == "weak_common_factor"
        and metadata.get("compute_slacks") is True
    ):
        raise RuntimeError(
            "the environmental DDF case no longer represents the declared technology"
        )

    diagnostics = result.diagnostics.loc[
        (result.diagnostics["dmu_id"] == focus)
        & (result.diagnostics["period"] == period)
    ].copy()
    required_certificates = (
        "lp_postsolve_certified",
        "postsolve_certified",
        "raw_economic_postsolve_certified",
        "published_output_account_certified",
        "economic_postsolve_certified",
    )
    missing_diagnostics = {
        "phase",
        "solver_status",
        *required_certificates,
    }.difference(diagnostics.columns)
    if (
        missing_diagnostics
        or len(diagnostics) != 2
        or sorted(diagnostics["phase"].tolist()) != [1, 2]
        or not diagnostics["solver_status"].eq("optimal").all()
        or not diagnostics.loc[:, list(required_certificates)].eq(True).all(axis=None)
    ):
        raise RuntimeError(
            "both environmental DDF solves and quantity accounts must be certified"
        )

    beta = float(row["score"])
    if not (
        np.isfinite(beta)
        and np.isclose(beta, float(row["distance"]), atol=1e-12, rtol=0.0)
        and np.isclose(beta, 0.08381502890173406, atol=1e-12, rtol=0.0)
    ):
        raise RuntimeError("the Central 2020 directional programme changed")

    targets = result.targets_for(focus, period=period).copy()
    slacks = result.slacks.loc[
        (result.slacks["dmu_id"] == focus) & (result.slacks["period"] == period)
    ].copy()
    target_fields = {
        "role",
        "variable",
        "observed",
        "target",
        "direction",
        "directional_change",
        "slack_allowed",
    }
    slack_fields = {"role", "variable", "slack", "scaled_slack"}
    if target_fields.difference(targets.columns) or slack_fields.difference(
        slacks.columns
    ):
        raise RuntimeError("the public environmental quantity ledger is incomplete")

    expected_plan = {
        ("input", "energy"): (110.0, 0.0, 0.0, 110.0, True),
        ("input", "labor"): (55.0, 0.0, 0.0, 55.0, True),
        (
            "output",
            "electricity",
        ): (79.376, 79.376, 6.652901734104043, 86.02890173410405, True),
        (
            "bad_output",
            "co2",
        ): (285.12, 285.12, 23.897341040462415, 261.22265895953757, False),
    }
    if targets.duplicated(["role", "variable"]).any() or len(targets) != len(
        expected_plan
    ):
        raise RuntimeError("the public environmental target ledger is not one-to-one")

    slack_lookup: dict[tuple[str, str], float] = {}
    if slacks.duplicated(["role", "variable"]).any():
        raise RuntimeError("the public environmental slack ledger is not one-to-one")
    for slack_row in slacks.itertuples(index=False):
        key = (str(slack_row.role), str(slack_row.variable))
        slack = float(slack_row.slack)
        scaled_slack = float(slack_row.scaled_slack)
        if not (np.isfinite(slack) and np.isfinite(scaled_slack) and slack >= 0.0):
            raise RuntimeError("the public environmental slack ledger is invalid")
        slack_lookup[key] = slack

    actual_keys: set[tuple[str, str]] = set()
    for target_row in targets.itertuples(index=False):
        key = (str(target_row.role), str(target_row.variable))
        actual_keys.add(key)
        if key not in expected_plan:
            raise RuntimeError("the environmental case exposed an undeclared variable")
        observed = float(target_row.observed)
        direction = float(target_row.direction)
        directional_change = float(target_row.directional_change)
        target = float(target_row.target)
        slack_allowed = bool(target_row.slack_allowed)
        values = np.asarray(
            (observed, direction, directional_change, target), dtype=np.float64
        )
        if not np.isfinite(values).all() or not np.isclose(
            directional_change,
            beta * direction,
            atol=1e-9,
            rtol=0.0,
        ):
            raise RuntimeError("beta times direction did not reconstruct")
        if slack_allowed != expected_plan[key][4]:
            raise RuntimeError("the fitted slack policy changed")
        if slack_allowed:
            if key not in slack_lookup:
                raise RuntimeError("an allowed environmental slack was not published")
            extra_slack = slack_lookup[key]
        else:
            if key in slack_lookup:
                raise RuntimeError("weak-disposal residual slack must not be invented")
            extra_slack = 0.0
        sign = -1.0 if key[0] in {"input", "bad_output"} else 1.0
        reconstructed_target = observed + sign * (directional_change + extra_slack)
        if not np.isclose(target, reconstructed_target, atol=1e-9, rtol=0.0):
            raise RuntimeError("the public environmental target account did not close")
        if not np.allclose(
            (observed, direction, directional_change, target, slack_allowed),
            expected_plan[key],
            atol=1e-9,
            rtol=0.0,
        ):
            raise RuntimeError("the Central 2020 public quantities changed")

    allowed_keys = {key for key, values in expected_plan.items() if values[4]}
    if actual_keys != set(expected_plan) or set(slack_lookup) != allowed_keys:
        raise RuntimeError("the environmental target and slack ledgers do not align")
    if any(not np.isclose(value, 0.0, atol=1e-12) for value in slack_lookup.values()):
        raise RuntimeError("this teaching case no longer has zero extra slack")

    figure = result.plot(kind="improvement", dmu_id=focus, period=period)
    _use_reader_facing_text(
        figure,
        (
            (
                "Certified common directional programme",
                "Common directional improvement programme",
            ),
            ("Certified target", "Selected benchmark plan"),
        ),
        context="environmental DDF improvement",
    )
    _use_reader_facing_text_block(
        figure,
        marker="Each card uses the variable's original unit",
        text=(
            "Central's 2020 programme keeps energy and labour fixed while "
            "electricity rises and carbon dioxide falls in the declared proportion.\n"
            "The same-year CRS weak-disposal benchmark supports this feasible plan, "
            "but not a claim of uniqueness, causation, minimum cost, or managerial "
            "prescription."
        ),
        context="environmental DDF improvement",
    )
    _save(
        figure,
        "environmental-ddf-improvement-result.svg",
        "Conditional environmental improvement plan for Central in 2020",
    )


def luenberger_figure() -> None:
    frame = pd.DataFrame(
        {
            "hospital": ["A", "B", "A", "B"],
            "year": [2020, 2020, 2021, 2021],
            "staff_bundles": [1.0, 2.0, 1.0, 2.0],
            "treatment_batches": [1.0, 2.0, 2.0, 4.0],
        }
    )
    data = DEAData.from_frame(
        frame,
        dmu="hospital",
        period="year",
        inputs="staff_bundles",
        outputs="treatment_batches",
    )
    result = LuenbergerProductivityIndicator(
        input_direction={"staff_bundles": 0.0},
        output_direction={"treatment_batches": 1.0},
        returns_to_scale="crs",
    ).fit(data)
    figure = result.plot(
        kind="performance",
        metric="productivity_change",
        period=2021,
        view="points",
    )
    _use_reader_facing_text(
        figure,
        (
            (
                "Productivity Change across organizations",
                "Treatment-expansion programme change, 2020\N{EN DASH}2021",
            ),
            (
                "Productivity Change",
                "Additional treatment-batch programme units realized",
            ),
            (
                "Valid reported result",
                "Complete four-appraisal programme-change account",
            ),
        ),
        context="Luenberger productivity",
    )
    _use_reader_facing_text_block(
        figure,
        marker="Positive values indicate improvement",
        text=(
            "Positive means more of the declared treatment programme; 0 means "
            "no change. One unit is one additional treatment batch with staff "
            "fixed. Each hospital is appraised against both adjacent-period CRS "
            "technologies; values are absolute units, not percentages."
        ),
        context="Luenberger productivity",
    )
    _save(
        figure,
        "luenberger-performance-result.svg",
        "Luenberger programme-unit change across hospitals, 2020-2021",
    )


def environmental_ml_performance_figure() -> None:
    """Render one certified adjacent-period environmental productivity screen."""

    frame = load_dataset("environmental_panel")
    data = DEAData.from_frame(
        frame,
        dmu="dmu",
        period="period",
        inputs=("energy", "labor"),
        outputs="electricity",
        bad_outputs="co2",
    )
    result = MalmquistLuenbergerDEA().fit(data)
    comparison_period = 2021

    performance = next(
        (plot for plot in result.available_plots() if plot.kind == "performance"),
        None,
    )
    if performance is None or "productivity_change" not in {
        measure.column for measure in performance.measures
    }:
        raise RuntimeError(
            "the adjacent environmental productivity result withheld performance"
        )

    metadata = result.metadata
    if not (
        metadata.get("method_id")
        == "productivity.malmquist_luenberger.chung_fare_grosskopf_1997"
        and metadata.get("model_family") == "malmquist_luenberger"
        and metadata.get("returns_to_scale") == "crs"
        and metadata.get("bad_output_disposability") == "weak_common_factor"
        and metadata.get("period_pairing") == "adjacent_period_identifier_match"
        and metadata.get("technology") == "contemporaneous_environmental_frontiers"
        and metadata.get("additional_solver_calls") == 0
    ):
        raise RuntimeError(
            "the environmental productivity case changed its reference contract"
        )

    summary = result.summary()
    required_summary = {
        "dmu_id",
        "period",
        "base_period",
        "comparison_period",
        "score_valid",
        "score_status",
        "solver_status",
        "productivity_change",
        "efficiency_change",
        "technical_change",
        "multiplicative_account_certified",
        "economic_postsolve_certified",
        "postsolve_certified",
        "all_four_distance_programs_certified",
        "lp_certified_distance_count",
        "certified_distance_count",
        "uncertified_distance_count",
        "all_four_economic_distance_claims_certified",
        "economic_certified_distance_count",
        "failed_distance_count",
        "failed_distance_roles",
        "max_multiplicative_account_residual",
    }
    missing_summary = required_summary.difference(summary.columns)
    transitions = summary.loc[summary["comparison_period"] == comparison_period].copy()
    if (
        missing_summary
        or len(transitions) != 6
        or not transitions["period"].eq(comparison_period).all()
        or not transitions["base_period"].eq(2020).all()
        or transitions["dmu_id"].duplicated().any()
    ):
        raise RuntimeError(
            "the 2020-2021 environmental transition roster is incomplete"
        )
    transitions = transitions.set_index("dmu_id")

    expected_valid = {
        "South": (1.0389691188594246, 1.0, 1.0389691188594246),
        "East": (1.0442445917035588, 1.0, 1.0442445917035588),
        "Central": (
            1.0450571237979644,
            1.000013973925561,
            1.0450425204515756,
        ),
        "Coastal": (1.0516193681210393, 1.0, 1.0516193681210393),
    }
    expected_unavailable = {
        "North": (1, {"base_on_comparison"}),
        "West": (2, {"comparison_on_base", "base_on_comparison"}),
    }
    if set(transitions.index) != set(expected_valid) | set(expected_unavailable):
        raise RuntimeError("the environmental teaching sample changed")

    for dmu_id, expected_account in expected_valid.items():
        row = transitions.loc[dmu_id]
        required_true = (
            "score_valid",
            "multiplicative_account_certified",
            "economic_postsolve_certified",
            "postsolve_certified",
            "all_four_distance_programs_certified",
            "all_four_economic_distance_claims_certified",
        )
        if any(
            not (pd.notna(row[field]) and bool(row[field])) for field in required_true
        ) or not (
            str(row["score_status"]) == "defined"
            and str(row["solver_status"]) == "optimal"
            and int(row["lp_certified_distance_count"]) == 4
            and int(row["certified_distance_count"]) == 4
            and int(row["economic_certified_distance_count"]) == 4
            and int(row["uncertified_distance_count"]) == 0
            and int(row["failed_distance_count"]) == 0
            and str(row["failed_distance_roles"]) == ""
        ):
            raise RuntimeError(f"{dmu_id} lacks its complete four-task ML account")
        account = np.asarray(
            (
                row["productivity_change"],
                row["efficiency_change"],
                row["technical_change"],
            ),
            dtype=np.float64,
        )
        if not (
            np.isfinite(account).all()
            and np.allclose(account, expected_account, atol=1e-12, rtol=0.0)
            and np.isclose(account[0], account[1] * account[2], atol=1e-12)
            and abs(float(row["max_multiplicative_account_residual"])) <= 1e-12
        ):
            raise RuntimeError(f"{dmu_id} did not reconstruct its ML account")

    for dmu_id, (failed_count, failed_roles) in expected_unavailable.items():
        row = transitions.loc[dmu_id]
        published = np.asarray(
            (
                row["productivity_change"],
                row["efficiency_change"],
                row["technical_change"],
            ),
            dtype=np.float64,
        )
        if not (
            pd.notna(row["score_valid"])
            and not bool(row["score_valid"])
            and str(row["score_status"]) == "solver_failed"
            and str(row["solver_status"]) == "infeasible"
            and np.isnan(published).all()
            and int(row["failed_distance_count"]) == failed_count
            and set(str(row["failed_distance_roles"]).split("|")) == failed_roles
            and not bool(row["postsolve_certified"])
            and not bool(row["multiplicative_account_certified"])
            and not bool(row["all_four_distance_programs_certified"])
        ):
            raise RuntimeError(
                f"{dmu_id} no longer exposes its cross-reference boundary"
            )

    diagnostics = result.diagnostics.loc[
        result.diagnostics["comparison_period"] == comparison_period
    ].copy()
    required_diagnostics = {
        "dmu_id",
        "base_period",
        "comparison_period",
        "distance_role",
        "evaluated_period",
        "technology_period",
        "solver_status",
        "backend_solver_status",
        "raw_solver_status",
        "lp_postsolve_certified",
        "postsolve_certified",
        "raw_economic_postsolve_certified",
        "published_output_account_certified",
        "economic_postsolve_certified",
    }
    if (
        required_diagnostics.difference(diagnostics.columns)
        or len(diagnostics) != 24
        or diagnostics.duplicated(["dmu_id", "distance_role"]).any()
    ):
        raise RuntimeError("the environmental ML task ledger is incomplete")

    certificate_fields = (
        "lp_postsolve_certified",
        "postsolve_certified",
        "raw_economic_postsolve_certified",
        "published_output_account_certified",
        "economic_postsolve_certified",
    )
    for dmu_id in expected_valid:
        tasks = diagnostics.loc[diagnostics["dmu_id"] == dmu_id]
        if not (
            len(tasks) == 4
            and tasks["solver_status"].eq("optimal").all()
            and tasks["backend_solver_status"].eq("optimal").all()
            and tasks["raw_solver_status"].eq("optimal").all()
            and tasks.loc[:, list(certificate_fields)].eq(True).all(axis=None)
        ):
            raise RuntimeError(f"{dmu_id} has an uncertified distance task")

    for dmu_id, (_, failed_roles) in expected_unavailable.items():
        tasks = diagnostics.loc[diagnostics["dmu_id"] == dmu_id]
        failed = tasks.loc[tasks["distance_role"].isin(failed_roles)]
        available = tasks.loc[~tasks["distance_role"].isin(failed_roles)]
        if not (
            len(tasks) == 4
            and set(failed["distance_role"]) == failed_roles
            and failed["solver_status"].eq("infeasible").all()
            and failed["backend_solver_status"].eq("infeasible").all()
            and failed["raw_solver_status"].eq("infeasible").all()
            and not failed.loc[:, list(certificate_fields)].eq(True).any(axis=None)
            and available["solver_status"].eq("optimal").all()
            and available.loc[:, list(certificate_fields)].eq(True).all(axis=None)
        ):
            raise RuntimeError(
                f"{dmu_id} did not preserve its reference-technology boundary"
            )

    figure = result.plot(
        kind="performance",
        metric="productivity_change",
        period=comparison_period,
        view="points",
    )
    _use_reader_facing_text(
        figure,
        (
            (
                "Productivity Change across organizations",
                "Adjacent-period environmental productivity change, "
                "2020\N{EN DASH}2021",
            ),
            (
                "Productivity Change",
                "Malmquist\N{EN DASH}Luenberger environmental productivity index",
            ),
            (
                "Valid reported result",
                "Complete four-appraisal environmental productivity account",
            ),
        ),
        context="Malmquist-Luenberger productivity",
    )
    _use_reader_facing_text_block(
        figure,
        marker="Above 1 indicates improvement",
        text=(
            "Above 1: environmental productivity improvement; 1: no change; "
            "below 1: decline. The CRS common-factor weak-disposal programme "
            "holds inputs fixed while electricity expands and CO₂ contracts. "
            "North and West are unavailable because at least one required "
            "cross-period production comparison is infeasible."
        ),
        context="Malmquist-Luenberger productivity",
    )
    _save(
        figure,
        "environmental-ml-performance-result.svg",
        "Adjacent-period environmental productivity change across plants, 2020-2021",
    )


def malmquist_figure() -> None:
    dataset_name = "multiperiod_trajectory_contrast"
    frame = load_dataset(dataset_name)
    roles = dataset_info(dataset_name).roles
    data = DEAData.from_frame(
        frame,
        dmu=roles["dmu"],
        period=roles["period"],
        inputs=roles["inputs"],
        outputs=roles["outputs"],
    )
    adjacent = FGNZMalmquist().fit(data)
    global_ = GlobalMalmquistDEA(
        orientation="output",
        returns_to_scale="crs",
    ).fit(data)
    adjacent_figure = adjacent.plot(
        kind="performance",
        metric="productivity_change",
        period=2,
        view="points",
    )
    _use_reader_facing_text(
        adjacent_figure,
        (
            (
                "Productivity Change across organizations",
                "Productivity change under adjacent-period benchmarks",
            ),
            ("Productivity Change", "Malmquist productivity index"),
            (
                "Valid reported result",
                "Complete four-appraisal productivity account",
            ),
        ),
        context="adjacent-period Malmquist productivity",
    )
    _use_reader_facing_text_block(
        adjacent_figure,
        marker="Above 1 indicates improvement",
        text=(
            "Above 1: productivity growth; 1: no change; below 1: decline. "
            "Output-oriented CRS comparison: each period-1 and period-2 "
            "operating plan is appraised against both adjacent-period "
            "technologies."
        ),
        context="adjacent-period Malmquist productivity",
    )
    _save(
        adjacent_figure,
        "trajectory-contrast-performance-result.svg",
        "Adjacent-period productivity change across service trajectories",
    )
    global_figure = global_.plot(
        kind="performance",
        metric="productivity_change",
        period=2,
        view="points",
    )
    _use_reader_facing_text(
        global_figure,
        (
            (
                "Productivity Change across organizations",
                "Productivity change under a full-horizon benchmark",
            ),
            ("Productivity Change", "Malmquist productivity index"),
            (
                "Valid reported result",
                "Complete full-horizon productivity account",
            ),
        ),
        context="full-horizon Malmquist productivity",
    )
    _use_reader_facing_text_block(
        global_figure,
        marker="Above 1 indicates improvement",
        text=(
            "Above 1: productivity growth; 1: no change; below 1: decline. "
            "Output-oriented CRS comparison: both operating plans are appraised "
            "against one full-horizon retrospective technology."
        ),
        context="full-horizon Malmquist productivity",
    )
    _save(
        global_figure,
        "full-horizon-trajectory-contrast-result.svg",
        "Full-horizon productivity change across service trajectories",
    )


def hicks_moorsteen_figure() -> None:
    frame = load_dataset("productivity_panel")
    data = DEAData.from_frame(
        frame,
        dmu="dmu",
        period="period",
        inputs=("capital", "labor"),
        outputs="output",
    )
    result = HicksMoorsteenDEA(returns_to_scale="vrs").fit(data)
    figure = result.plot(
        kind="performance",
        metric="productivity_change",
        period=2021,
        view="points",
    )
    _use_reader_facing_text(
        figure,
        (
            (
                "Productivity Change across organizations",
                "Hicks\N{EN DASH}Moorsteen total-factor productivity change, "
                "2020\N{EN DASH}2021",
            ),
            (
                "Productivity Change",
                "Hicks\N{EN DASH}Moorsteen TFP index",
            ),
            (
                "Valid reported result",
                "Complete output-and-input quantity account",
            ),
        ),
        context="Hicks-Moorsteen productivity",
    )
    _use_reader_facing_text_block(
        figure,
        marker="Above 1 indicates improvement",
        text=(
            "Above 1: total-factor productivity growth; 1: no change; below 1: "
            "decline. The index is output-quantity growth divided by "
            "input-quantity growth, using input- and output-oriented "
            "comparisons under the two VRS technologies."
        ),
        context="Hicks-Moorsteen productivity",
    )
    _save(
        figure,
        "hicks-moorsteen-performance-result.svg",
        "Hicks-Moorsteen productivity change across organizations, 2020-2021",
    )


def network_radial_figure() -> None:
    frame = load_dataset("network_2stage")
    data = NetworkData.from_frame(
        frame,
        dmu="dmu",
        spec=TwoStageSeriesSpec(
            inputs=("research_staff", "research_budget"),
            intermediates=("patents", "prototypes"),
            outputs=("sales", "market_share"),
            stage_names=("research", "commercialization"),
            link_id="innovation_handoff",
        ),
    )
    result = FareGrosskopfNetworkRadialDEA(
        orientation="input",
        returns_to_scale="crs",
    ).fit(data)
    figure = result.plot(
        kind="performance",
        metric="system_efficiency",
        view="points",
    )
    _use_reader_facing_text(
        figure,
        (
            (
                "System Efficiency across organizations",
                "Connected-system resource-use performance",
            ),
            ("System Efficiency", "System input efficiency"),
            (
                "Inefficient",
                "Represented system-wide resource-saving opportunity (E < 1)",
            ),
        ),
        context="network radial performance",
    )
    _use_reader_facing_text_block(
        figure,
        marker="Higher is better",
        text=(
            "Higher values mean less proportional external-resource saving "
            "remains; 1 means no represented system-wide saving opportunity. "
            "Input-oriented CRS benchmark with protected final outcomes, "
            "coordinated internal handoffs, process-specific peers, and one "
            "declared population."
        ),
        context="network radial performance",
    )
    _save(
        figure,
        "network-system-performance-result.svg",
        "System radial efficiency across research organizations",
    )


def network_sbm_process_figure() -> None:
    frame = load_dataset("three_process_service_chain")
    spec = NetworkSpec(
        processes=(
            ProcessSpec(
                "stage_1",
                inputs="intake_hours",
                outputs="verified_requests",
            ),
            ProcessSpec(
                "stage_2",
                inputs=("verified_requests", "resolution_hours"),
                outputs=("same_day_resolutions", "scheduled_cases"),
            ),
            ProcessSpec(
                "stage_3",
                inputs=("scheduled_cases", "delivery_hours"),
                outputs="completed_services",
            ),
        ),
        links=(
            LinkSpec(
                "handoff_1_2",
                source="stage_1",
                target="stage_2",
                variables="verified_requests",
            ),
            LinkSpec(
                "handoff_2_3",
                source="stage_2",
                target="stage_3",
                variables="scheduled_cases",
            ),
        ),
    )
    data = NetworkData.from_frame(frame, dmu="unit", spec=spec)
    result = NetworkSBM(
        orientation="input",
        returns_to_scale="vrs",
        link_control="free",
        division_weights={
            "stage_1": 0.4,
            "stage_2": 0.2,
            "stage_3": 0.4,
        },
    ).fit(data)
    figure = result.plot(kind="process", dmu_id="resource_drag")
    _use_reader_facing_text(
        figure,
        (
            (
                "Certified connected-organization account for resource_drag",
                "One connected operating account for a service plan",
            ),
        ),
        context="Network SBM process account",
    )
    _use_reader_facing_text_block(
        figure,
        marker="Process values locate input burden",
        text=(
            "Process values locate input burden within one jointly feasible "
            "Network SBM plan and reconstruct the declared-weight system "
            "account. Free handoffs preserve supplier\N{EN DASH}recipient "
            "continuity; "
            "selected values are coordinated benchmarks, not unique, causal, or "
            "prescriptive recommendations. Input-oriented VRS comparison."
        ),
        context="Network SBM process account",
    )
    _save(
        figure,
        "three-process-service-account-result.svg",
        "One connected operating account for a service plan",
    )


def dynamic_trajectory_figure() -> None:
    dataset_name = "dynamic_carryover_portfolio"
    frame = load_dataset(dataset_name)
    roles = dataset_info(dataset_name).roles
    data = DynamicData.from_frame(
        frame,
        dmu=roles["dmu"],
        period=roles["period"],
        spec=DynamicSBMSpec(
            production=PeriodProductionSpec(
                inputs=roles["inputs"],
                outputs=roles["outputs"],
            ),
            carryovers=(CarryOverSpec(roles["free_carryovers"][0], kind="free"),),
        ),
    )
    result = DynamicSBM(
        orientation="input",
        returns_to_scale="crs",
    ).fit(data)
    figure = result.plot(
        kind="trajectory",
        dmu_id="path_04",
        variable=roles["free_carryovers"][0],
    )
    _use_reader_facing_text(
        figure,
        (
            (
                "Certified carry-over trajectory for path_04",
                "Connected carry-over trajectory for a service path",
            ),
        ),
        context="free-carry-over Dynamic SBM",
    )
    _use_reader_facing_text_block(
        figure,
        marker="Outgoing and inherited targets belong to one certified horizon plan",
        text=(
            "Outgoing and inherited targets form one jointly feasible horizon "
            "plan, not separate annual recommendations. The free carry-over "
            "coordinates feasibility rather than entering the score; period "
            "accounts describe the whole selected trajectory. Input-oriented "
            "Dynamic SBM under CRS."
        ),
        context="free-carry-over Dynamic SBM",
    )
    _save(
        figure,
        "carryover-portfolio-trajectory-result.svg",
        "Connected carry-over trajectory for a service path",
    )


def dynamic_scored_carryover_figure() -> None:
    dataset_name = "dynamic_capacity_backlog"
    frame = load_dataset(dataset_name)
    roles = dataset_info(dataset_name).roles
    data = DynamicData.from_frame(
        frame,
        dmu=roles["dmu"],
        period=roles["period"],
        spec=DynamicSBMSpec(
            production=PeriodProductionSpec(
                inputs=roles["inputs"],
                outputs=roles["outputs"],
            ),
            carryovers=(
                CarryOverSpec(roles["good_carryovers"][0], kind="good"),
                CarryOverSpec(roles["bad_carryovers"][0], kind="bad"),
            ),
        ),
    )
    result = DynamicSBM(
        orientation="non-oriented",
        returns_to_scale="vrs",
    ).fit(data)
    figure = result.plot(
        kind="trajectory",
        dmu_id="Strained",
        variable="backlog",
    )
    _use_reader_facing_text(
        figure,
        (
            (
                "Certified carry-over trajectory for Strained",
                "Connected carry-over trajectory for Strained",
            ),
        ),
        context="scored-backlog Dynamic SBM",
    )
    _use_reader_facing_text_block(
        figure,
        marker="Outgoing and inherited targets belong to one certified horizon plan",
        text=(
            "Outgoing and inherited backlog targets form one jointly feasible "
            "horizon plan. Backlog enters every period's performance account, "
            "and the horizon result is not an average of annual scores. Adjacent "
            "balances close under non-oriented Dynamic SBM with VRS."
        ),
        context="scored-backlog Dynamic SBM",
    )
    _save(
        figure,
        "dynamic-sbm-scored-backlog-result.svg",
        "Scored carry-over account for Strained",
    )


def metafrontier_decomposition_figure() -> None:
    frame = load_dataset("metafrontier_groups")
    data = DEAData.from_frame(
        frame,
        dmu="dmu",
        group="technology_group",
        inputs="resource",
        outputs="service",
    )
    result = MetafrontierDEA(
        orientation="output",
        returns_to_scale="vrs",
        compute_slacks=False,
    ).fit(data)
    _save(
        result.plot(kind="metafrontier"),
        "metafrontier-decomposition-result.svg",
        "Within-group performance and pooled-opportunity comparison",
    )


@lru_cache(maxsize=1)
def _community_hospital_analysis() -> dict[str, Any]:
    """Fit the public models needed by the hospital capstone figures once."""

    frame = load_dataset("community_hospital_capstone")
    roles = dataset_info("community_hospital_capstone").roles
    production = (*roles["inputs"], *roles["outputs"])
    usable = (
        frame["reporting_complete"]
        & ~frame["structural_break"]
        & np.isfinite(frame.loc[:, production]).all(axis=1)
        & frame.loc[:, production].gt(0.0).all(axis=1)
    )
    district = usable & frame["service_mandate"].eq("district_general")
    main_rule = district & frame["tertiary_referral_share"].le(0.15)
    broad_rule = district & frame["tertiary_referral_share"].le(0.25)
    counts = (len(frame), int(usable.sum()), int(district.sum()), int(main_rule.sum()))
    if counts != (64, 60, 52, 48) or int(broad_rule.sum()) != 52:
        raise RuntimeError("the community-hospital screening population changed")

    def _data(mask: pd.Series) -> DEAData:
        return DEAData.from_frame(
            frame.loc[mask].reset_index(drop=True),
            dmu=roles["dmu"],
            inputs=roles["inputs"],
            outputs=roles["outputs"],
        )

    main_data = _data(main_rule)
    broad_data = _data(broad_rule)
    primary_result = BCCInput().fit(main_data)
    sbm_result = SBM(returns_to_scale="vrs").fit(main_data)
    broad_result = BCCInput().fit(broad_data)
    scale_result = scale_efficiency(main_data, orientation="input")
    primary = primary_result.summary().set_index("dmu_id")
    sbm = sbm_result.summary().set_index("dmu_id")
    broad = broad_result.summary().set_index("dmu_id").reindex(primary.index)
    scale = scale_result.summary().set_index("dmu_id")
    focus_peers = primary_result.peers("H048")
    focus_targets = primary_result.targets_for("H048")

    if not (
        len(primary) == 48
        and primary["score_valid"].all()
        and sbm["score_valid"].all()
        and broad["score_valid"].all()
        and scale["score_valid"].all()
        and np.isclose(primary.loc["H048", "efficiency"], 1.0 / 1.12)
        and focus_peers["reference_dmu_id"].tolist() == ["H008"]
        and np.allclose(focus_peers["lambda"], (1.0,))
    ):
        raise RuntimeError("the community-hospital public results changed")

    return {
        "primary": primary,
        "sbm": sbm,
        "broad": broad,
        "scale": scale,
        "focus_targets": focus_targets,
    }


def community_hospital_screening_figure() -> None:
    """Show how the hospital population is chosen before DEA is fitted."""

    _community_hospital_analysis()
    ink = "#24323d"
    teal = "#176b73"
    blue = "#3f6f8f"
    pale = "#edf4f3"
    gray = "#687780"

    with plt.rc_context({"font.size": 13.0}):
        figure, axis = plt.subplots(figsize=(12.0, 5.8), facecolor="white")
        axis.set_xlim(0.0, 12.0)
        axis.set_ylim(0.0, 5.8)
        axis.axis("off")
        figure.subplots_adjust(left=0.03, right=0.97, top=0.84, bottom=0.08)
        figure.suptitle(
            "Who belongs in the community-hospital comparison?",
            x=0.04,
            y=0.96,
            ha="left",
            fontsize=19,
            fontweight="bold",
            color=ink,
        )
        figure.text(
            0.04,
            0.875,
            "Population rules are settled before any efficiency value is viewed",
            ha="left",
            fontsize=13,
            color=gray,
        )

        positions = (1.4, 4.4, 7.4, 10.4)
        cards = (
            ("64", "Raw records", "One financial year"),
            ("60", "Usable records", "Complete and\nstable data"),
            ("52", "District-general\nhospitals", "Comparable\nservice mission"),
            ("48", "Main comparison\ngroup", "Referral share\nno more than 15%"),
        )
        for index, (x, card) in enumerate(zip(positions, cards, strict=True)):
            color = teal if index == 3 else blue
            patch = FancyBboxPatch(
                (x - 1.15, 2.25),
                2.3,
                1.9,
                boxstyle="round,pad=0.04,rounding_size=0.08",
                facecolor=pale if index != 3 else "#e3f0ed",
                edgecolor=color,
                linewidth=2.0,
            )
            axis.add_patch(patch)
            axis.text(
                x,
                3.55,
                card[0],
                ha="center",
                va="center",
                fontsize=23,
                fontweight="bold",
                color=color,
            )
            axis.text(
                x,
                3.02,
                card[1],
                ha="center",
                va="center",
                fontsize=13,
                fontweight="bold",
                color=ink,
                linespacing=1.05,
            )
            axis.text(
                x,
                2.57,
                card[2],
                ha="center",
                va="center",
                fontsize=13,
                color=gray,
                linespacing=1.05,
            )
        for left, right in pairwise(positions):
            axis.plot((left + 1.17, right - 1.17), (3.2, 3.2), color=gray, lw=2.0)
            axis.scatter(right - 1.17, 3.2, marker=">", s=90, color=gray, zorder=3)

        axis.text(
            7.4,
            1.2,
            "Broad sensitivity group: all 52 district-general hospitals\n"
            "including four with referral shares between 15% and 25%",
            ha="center",
            va="center",
            fontsize=13,
            color=ink,
            bbox={
                "boxstyle": "round,pad=0.45",
                "facecolor": "#fff4e8",
                "edgecolor": "#d97732",
                "linewidth": 1.6,
            },
        )
        axis.plot((7.4, 7.4), (2.23, 1.73), color="#d97732", lw=1.8)
        _save(
            figure,
            "community-hospital-screening.svg",
            "Community-hospital study population screening",
        )


def community_hospital_performance_figure() -> None:
    """Show the primary score distribution and hospital-level variation."""

    case = _community_hospital_analysis()
    primary = case["primary"]
    scores = primary["efficiency"].astype(float)
    ordered = scores.sort_values()
    ink = "#24323d"
    gray = "#687780"
    teal = "#176b73"
    orange = "#d97732"
    grid = "#dce5e7"

    with plt.rc_context({"font.size": 13.0}):
        figure, (distribution, differences) = plt.subplots(
            1,
            2,
            figsize=(12.0, 6.8),
            gridspec_kw={"width_ratios": (0.9, 1.35)},
            facecolor="white",
        )
        figure.subplots_adjust(
            left=0.08,
            right=0.96,
            top=0.78,
            bottom=0.25,
            wspace=0.28,
        )
        figure.suptitle(
            "Resource stewardship across 48 community hospitals",
            x=0.06,
            y=0.96,
            ha="left",
            fontsize=19,
            fontweight="bold",
            color=ink,
        )
        figure.text(
            0.06,
            0.88,
            "Input-oriented BCC · current services protected · "
            "variable returns to scale",
            ha="left",
            fontsize=13,
            color=gray,
        )

        bins = np.linspace(0.76, 1.01, 11)
        distribution.hist(scores, bins=bins, color="#9ec6c3", edgecolor="white")
        distribution.axvline(scores.median(), color=orange, lw=2.2, linestyle="--")
        distribution.text(
            scores.median() - 0.004,
            10.5,
            f"Median {scores.median():.3f}",
            ha="right",
            va="top",
            fontsize=13,
            color=orange,
            fontweight="bold",
        )
        distribution.set_title(
            "Distribution",
            loc="left",
            fontsize=14,
            fontweight="bold",
        )
        distribution.set_xlabel("BCC-I efficiency")
        distribution.set_ylabel("Number of hospitals")
        distribution.set_xlim(0.76, 1.015)
        distribution.grid(axis="y", color=grid, linewidth=0.8)

        positions = np.arange(1, len(ordered) + 1)
        colors = np.where(np.isclose(ordered, 1.0), teal, "#7f9daa")
        differences.scatter(
            ordered,
            positions,
            c=colors,
            s=42,
            edgecolor="white",
            lw=0.6,
        )
        differences.axvline(1.0, color=teal, lw=1.2)
        differences.set_title(
            "Hospital-level differences",
            loc="left",
            fontsize=14,
            fontweight="bold",
        )
        differences.set_xlabel("BCC-I efficiency")
        differences.set_ylabel("Hospitals ordered by value")
        differences.set_xlim(0.76, 1.015)
        differences.set_ylim(0, 49)
        differences.set_yticks((1, 12, 24, 36, 48))
        differences.grid(axis="x", color=grid, linewidth=0.8)
        annotations = (("H006", (8, 0)), ("H048", (8, 0)), ("H008", (-8, -1)))
        for hospital, offset in annotations:
            y = int(np.where(ordered.index.to_numpy() == hospital)[0][0]) + 1
            differences.annotate(
                f"{hospital}  {ordered.loc[hospital]:.3f}",
                (ordered.loc[hospital], y),
                xytext=offset,
                textcoords="offset points",
                ha="left" if offset[0] > 0 else "right",
                va="center",
                fontsize=13,
                color=orange if hospital == "H048" else ink,
                fontweight="bold" if hospital == "H048" else "normal",
            )
        figure.text(
            0.06,
            0.055,
            f"{int(np.isclose(scores, 1.0).sum())} hospitals score 1.000: "
            "the study finds no supported input saving for them;\n"
            "this does not establish that every resource is used perfectly.",
            ha="left",
            va="bottom",
            fontsize=13,
            color=gray,
        )
        _save(
            figure,
            "community-hospital-performance.svg",
            "Primary efficiency distribution for 48 community hospitals",
        )


def community_hospital_h048_improvement_figure() -> None:
    """Translate H048's BCC result into peer and input quantities."""

    case = _community_hospital_analysis()
    primary = case["primary"]
    focus_targets = case["focus_targets"]
    targets = focus_targets.query("role == 'input'").copy()
    outputs = focus_targets.query("role == 'output'").set_index("variable")["target"]
    targets["retained_percent"] = 100.0 * targets["target"] / targets["observed"]
    labels = ("Clinical staff", "Support staff", "Non-pay spend")
    ink = "#24323d"
    gray = "#687780"
    teal = "#176b73"
    orange = "#d97732"
    grid = "#dce5e7"

    with plt.rc_context({"font.size": 13.0}):
        figure, (peer_axis, input_axis) = plt.subplots(
            1,
            2,
            figsize=(12.0, 6.5),
            gridspec_kw={"width_ratios": (0.92, 1.45)},
            facecolor="white",
        )
        figure.subplots_adjust(
            left=0.06,
            right=0.96,
            top=0.78,
            bottom=0.16,
            wspace=0.24,
        )
        figure.suptitle(
            "H048: from an efficiency value to a management inquiry",
            x=0.055,
            y=0.96,
            ha="left",
            fontsize=19,
            fontweight="bold",
            color=ink,
        )
        figure.text(
            0.055,
            0.88,
            "The selected comparison preserves "
            f"{outputs.loc['quality_adjusted_discharges']:,.0f} "
            "adjusted discharges and "
            f"{outputs.loc['outpatient_encounters']:,.0f} outpatient encounters",
            ha="left",
            fontsize=13,
            color=gray,
        )

        peer_axis.axis("off")
        peer_axis.text(
            0.5,
            0.82,
            "H048",
            transform=peer_axis.transAxes,
            ha="center",
            va="center",
            fontsize=22,
            fontweight="bold",
            color=orange,
        )
        peer_axis.text(
            0.5,
            0.66,
            f"BCC-I efficiency  {primary.loc['H048', 'efficiency']:.3f}",
            transform=peer_axis.transAxes,
            ha="center",
            fontsize=13.5,
            fontweight="bold",
            color=ink,
        )
        peer_axis.plot(
            (0.5, 0.5),
            (0.56, 0.39),
            transform=peer_axis.transAxes,
            color=gray,
            lw=2.0,
        )
        peer_axis.scatter(
            0.5,
            0.39,
            transform=peer_axis.transAxes,
            marker="v",
            s=90,
            color=gray,
        )
        peer_axis.text(
            0.5,
            0.24,
            "Selected peer\nH008  ·  weight 1.000\nSame two service quantities",
            transform=peer_axis.transAxes,
            ha="center",
            va="center",
            fontsize=13,
            color=teal,
            fontweight="bold",
            linespacing=1.45,
            bbox={
                "boxstyle": "round,pad=0.55",
                "facecolor": "#e3f0ed",
                "edgecolor": teal,
                "linewidth": 1.8,
            },
        )

        positions = np.arange(len(targets))
        input_axis.barh(
            positions,
            100.0,
            color="#dfe6e8",
            height=0.62,
            label="Current input",
        )
        input_axis.barh(
            positions,
            targets["retained_percent"],
            color=teal,
            height=0.62,
            label="Supported target",
        )
        for y, retained in zip(positions, targets["retained_percent"], strict=True):
            input_axis.text(
                retained - 1.2,
                y,
                f"{retained:.1f}% retained",
                ha="right",
                va="center",
                color="white",
                fontsize=13,
                fontweight="bold",
            )
            input_axis.text(
                101.5,
                y,
                f"{100.0 - retained:.1f}% lower",
                ha="left",
                va="center",
                color=orange,
                fontsize=13,
                fontweight="bold",
            )
        input_axis.set_yticks(positions, labels)
        input_axis.invert_yaxis()
        input_axis.set_xlim(0, 116)
        input_axis.set_xlabel("Share of H048's current input")
        input_axis.set_title(
            "Input quantities supported by the comparison",
            loc="left",
            fontsize=14,
            fontweight="bold",
        )
        input_axis.grid(axis="x", color=grid, linewidth=0.8)
        figure.text(
            0.055,
            0.055,
            "These quantities guide investigation of staffing and "
            "procurement practice; "
            "they are not automatic budget or workforce decisions.",
            ha="left",
            fontsize=13,
            color=gray,
        )
        _save(
            figure,
            "community-hospital-h048-improvement.svg",
            "H048 peer and supported input reductions",
        )


def community_hospital_roster_sensitivity_figure() -> None:
    """Compare the same 48 hospitals under main and broad peer rosters."""

    case = _community_hospital_analysis()
    main = case["primary"]["efficiency"].astype(float)
    broad = case["broad"]["efficiency"].astype(float)
    change = broad - main
    changed = int((~np.isclose(main, broad)).sum())
    ink = "#24323d"
    gray = "#687780"
    teal = "#176b73"
    orange = "#d97732"
    grid = "#dce5e7"

    with plt.rc_context({"font.size": 13.0}):
        figure, axis = plt.subplots(figsize=(9.8, 7.1), facecolor="white")
        figure.subplots_adjust(left=0.12, right=0.72, top=0.78, bottom=0.25)
        figure.suptitle(
            "How much depends on the hospital comparison group?",
            x=0.07,
            y=0.96,
            ha="left",
            fontsize=19,
            fontweight="bold",
            color=ink,
        )
        figure.text(
            0.07,
            0.88,
            "The same 48 hospitals under the main roster and a "
            "52-hospital sensitivity roster",
            ha="left",
            fontsize=13,
            color=gray,
        )
        axis.plot((0.72, 1.01), (0.72, 1.01), color=gray, lw=1.4, linestyle="--")
        axis.scatter(main, broad, color="#7f9daa", edgecolor="white", s=52, lw=0.6)
        axis.scatter(
            main.loc["H048"],
            broad.loc["H048"],
            color=orange,
            edgecolor="white",
            s=105,
            lw=0.8,
            zorder=4,
        )
        axis.annotate(
            f"H048\n{main.loc['H048']:.3f} → {broad.loc['H048']:.3f}",
            (main.loc["H048"], broad.loc["H048"]),
            xytext=(12, -2),
            textcoords="offset points",
            ha="left",
            va="center",
            fontsize=13,
            color=orange,
            fontweight="bold",
        )
        axis.set_xlim(0.76, 1.012)
        axis.set_ylim(0.72, 1.012)
        axis.set_xlabel("Main group BCC-I efficiency (48 hospitals)")
        axis.set_ylabel("Broad group BCC-I efficiency (52 hospitals)")
        axis.grid(color=grid, linewidth=0.8)
        figure.text(
            0.76,
            0.64,
            f"{changed} of 48\nvalues fall",
            ha="left",
            va="center",
            fontsize=16,
            fontweight="bold",
            color=teal,
        )
        figure.text(
            0.76,
            0.46,
            f"Mean change\n{100.0 * change.mean():.1f} points",
            ha="left",
            va="center",
            fontsize=13,
            color=ink,
        )
        figure.text(
            0.76,
            0.31,
            f"Largest fall\n{100.0 * change.min():.1f} points",
            ha="left",
            va="center",
            fontsize=13,
            color=ink,
        )
        figure.text(
            0.07,
            0.055,
            "A lower value reflects a more demanding set of observed practices.\n"
            "Credibility still depends on whether the wider referral role "
            "is adequately measured.",
            ha="left",
            va="bottom",
            fontsize=13,
            color=gray,
        )
        _save(
            figure,
            "community-hospital-roster-sensitivity.svg",
            "Community-hospital comparison-group sensitivity",
        )


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    radial_frontier_figure()
    radial_improvement_figure()
    scale_efficiency_figure()
    three_performance_accounts_figure()
    peer_eligibility_sensitivity_figure()
    sbm_improvement_figure()
    reference_frequency_figure()
    slack_family_rulers_figure()
    undesirable_sbm_improvement_figure()
    environmental_ddf_improvement_figure()
    directional_distance_figure()
    ddf_programme_contracts_figure()
    luenberger_figure()
    environmental_ml_performance_figure()
    malmquist_figure()
    hicks_moorsteen_figure()
    network_radial_figure()
    network_sbm_process_figure()
    dynamic_trajectory_figure()
    dynamic_scored_carryover_figure()
    metafrontier_decomposition_figure()
    community_hospital_screening_figure()
    community_hospital_performance_figure()
    community_hospital_h048_improvement_figure()
    community_hospital_roster_sensitivity_figure()


if __name__ == "__main__":
    main()
