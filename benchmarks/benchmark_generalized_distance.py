"""Repeatable generalized-distance performance benchmark.

The CRS path is an exact radial-LP reduction. An interior-alpha VRS fit uses
repeated fixed-delta feasibility LPs, so this benchmark reports both elapsed
time and the number of feasibility solves.

Run from an editable development environment, for example:

    python benchmarks/benchmark_generalized_distance.py --n-dmus 100
    python benchmarks/benchmark_generalized_distance.py --n-dmus 1000 --rts crs
"""

from __future__ import annotations

import argparse
import time

import numpy as np
import pandas as pd

from deapack import GDF, DEAData


def make_data(n_dmus: int) -> DEAData:
    """Return deterministic positive two-input, two-output benchmark data."""
    position = np.arange(1, n_dmus + 1, dtype=np.float64)
    scale = 1.0 + position / max(n_dmus / 4.0, 1.0)
    frame = pd.DataFrame(
        {
            "dmu": [f"D{index:06d}" for index in range(n_dmus)],
            "x1": scale * (1.0 + (position % 31) / 20.0),
            "x2": scale * (1.0 + (position % 43) / 25.0),
        }
    )
    operating_quality = 0.72 + 0.28 * ((position % 29) / 28.0)
    frame["y1"] = (
        np.sqrt(frame["x1"] * frame["x2"])
        * operating_quality
        * (1.0 + (position % 17) / 30.0)
    )
    frame["y2"] = (
        np.power(frame["x1"], 0.35)
        * np.power(frame["x2"], 0.65)
        * operating_quality
        * (1.0 + (position % 19) / 35.0)
    )
    return DEAData.from_frame(
        frame,
        dmu="dmu",
        inputs=("x1", "x2"),
        outputs=("y1", "y2"),
    )


def run_case(
    data: DEAData,
    *,
    alpha: float,
    returns_to_scale: str,
    compute_slacks: bool,
    search_tolerance: float,
) -> None:
    model = GDF(
        alpha=alpha,
        returns_to_scale=returns_to_scale,
        compute_slacks=compute_slacks,
        search_tolerance=search_tolerance,
    )
    start = time.perf_counter()
    result = model.fit(data)
    elapsed = time.perf_counter() - start
    summary = result.summary()
    optimal = int((summary["solver_status"] == "optimal").sum())
    converged = int(summary["search_converged"].fillna(False).sum())
    if len(summary) != data.n_dmus or optimal != data.n_dmus:
        raise AssertionError("every generalized-distance score must solve optimally")
    released_score = summary["score_status"].isin(
        {
            "defined",
            "defined_certified_upper_with_wide_interval",
        }
    )
    if not released_score.all():
        raise AssertionError("every generalized-distance score must be released")
    for column in (
        "score",
        "efficiency",
        "generalized_distance",
        "resource_commitment",
        "service_commitment",
        "search_lower_bound",
        "search_upper_bound",
        "search_absolute_gap",
    ):
        if not np.isfinite(summary[column].to_numpy(dtype=np.float64)).all():
            raise AssertionError(
                f"every generalized-distance {column} value must be finite"
            )
    search_gaps = summary["search_absolute_gap"].to_numpy(dtype=np.float64)
    search_upper = summary["search_upper_bound"].to_numpy(dtype=np.float64)
    expected_convergence = search_gaps <= search_tolerance * np.maximum(
        1.0,
        np.abs(search_upper),
    )
    reported_convergence = (
        summary["search_converged"].fillna(False).to_numpy(dtype=np.bool_)
    )
    if not np.array_equal(reported_convergence, expected_convergence):
        raise AssertionError(
            "generalized-distance search convergence must match its public "
            "interval-tolerance contract"
        )
    if not result.diagnostics["solver_status"].eq("optimal").all():
        raise AssertionError("every requested generalized-distance phase must solve")
    if compute_slacks:
        for table, column in (
            (result.targets, "target"),
            (result.slacks, "slack"),
            (result.slacks, "scaled_slack"),
        ):
            if not np.isfinite(table[column].to_numpy(dtype=np.float64)).all():
                raise AssertionError(
                    f"every requested generalized-distance {column} must be finite"
                )
    print(
        f"n={data.n_dmus} rts={returns_to_scale} alpha={alpha:g} "
        f"full={compute_slacks} elapsed={elapsed:.3f}s "
        f"optimal={optimal}/{data.n_dmus} "
        f"search_converged={converged}/{data.n_dmus} "
        f"feasibility_solves={result.metadata['total_feasibility_solves']} "
        f"target_solves={result.metadata['total_target_solves']} "
        f"strategy={result.metadata['solver_strategy']}"
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n-dmus", type=int, default=100)
    parser.add_argument("--alpha", type=float, default=0.5)
    parser.add_argument(
        "--rts",
        choices=("crs", "vrs", "both"),
        default="both",
    )
    parser.add_argument("--full", action="store_true", help="run the slack phase")
    parser.add_argument("--search-tolerance", type=float, default=1e-7)
    args = parser.parse_args()

    data = make_data(args.n_dmus)
    returns_to_scale = ("crs", "vrs") if args.rts == "both" else (args.rts,)
    for rts in returns_to_scale:
        run_case(
            data,
            alpha=args.alpha,
            returns_to_scale=rts,
            compute_slacks=args.full,
            search_tolerance=args.search_tolerance,
        )


if __name__ == "__main__":
    main()
