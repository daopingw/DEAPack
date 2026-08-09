"""Deterministic 100,000-edge benchmark for selected-plan reference frequency.

The benchmark constructs one complete certified cross-sectional peer account
with no random draws, then times only the post-estimation aggregation. It
checks the exact self/other/total count identity, the normalized rate, stable
row counts, and the zero-additional-solve contract.

Run the release-sized default with:

    python benchmarks/benchmark_reference_frequency.py

Use a smaller smoke case with:

    python benchmarks/benchmark_reference_frequency.py --n-dmus 1000 \
        --peers-per-dmu 10
"""

from __future__ import annotations

import argparse
import time
from dataclasses import replace

import numpy as np
import pandas as pd

from deapack import CCR, DEAData, reference_frequency


def _certified_source(n_dmus: int, peers_per_dmu: int):  # type: ignore[no-untyped-def]
    if n_dmus < 2:
        raise ValueError("n-dmus must be at least two")
    if peers_per_dmu < 1 or peers_per_dmu > n_dmus:
        raise ValueError("peers-per-dmu must be between one and n-dmus")

    base_frame = pd.DataFrame(
        {
            "dmu": ["A", "B", "C", "D"],
            "input": [1.0, 2.0, 1.5, 3.0],
            "output": [1.0, 1.0, 0.6, 1.2],
        }
    )
    base = CCR().fit(
        DEAData.from_frame(
            base_frame,
            dmu="dmu",
            inputs="input",
            outputs="output",
        )
    )

    identifiers = np.arange(n_dmus, dtype=np.int64)
    evaluated = np.repeat(identifiers, peers_per_dmu)
    offsets = np.tile(np.arange(peers_per_dmu, dtype=np.int64), n_dmus)
    references = (evaluated + offsets) % n_dmus
    edge_count = n_dmus * peers_per_dmu

    summary = pd.DataFrame(
        {
            "dmu_id": identifiers,
            "period": pd.Series([None] * n_dmus, dtype=object),
            "score": np.ones(n_dmus),
            "efficiency": np.ones(n_dmus),
            "distance": np.zeros(n_dmus),
            "is_efficient": np.ones(n_dmus, dtype=bool),
            "solver_status": np.repeat("optimal", n_dmus),
            "model_family": np.repeat("radial", n_dmus),
            "peer_valid": np.ones(n_dmus, dtype=bool),
            "peer_status": np.repeat("certified_primary_program", n_dmus),
        }
    )
    intensities = pd.DataFrame(
        {
            "dmu_id": evaluated,
            "period": pd.Series([None] * edge_count, dtype=object),
            "reference_dmu_id": references,
            "reference_period": pd.Series([None] * edge_count, dtype=object),
            "lambda": np.full(edge_count, 1.0 / peers_per_dmu),
        }
    )
    return replace(base, summary_frame=summary, intensities=intensities)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n-dmus", type=int, default=5_000)
    parser.add_argument("--peers-per-dmu", type=int, default=20)
    args = parser.parse_args()

    source = _certified_source(args.n_dmus, args.peers_per_dmu)
    source_solver_calls = int(source.metadata["solver_calls"])
    source_peer_tolerance = float(source.metadata["peer_tolerance"])
    expected_edges = args.n_dmus * args.peers_per_dmu
    if not source.intensities["lambda"].gt(source_peer_tolerance).all():
        raise AssertionError("every benchmark edge must exceed source peer_tolerance")

    started = time.perf_counter()
    result = reference_frequency(source)
    elapsed = time.perf_counter() - started
    frame = result.reference_frame

    if len(result.edge_frame) != expected_edges:
        raise AssertionError("the active-edge table does not preserve every edge")
    if len(frame) != args.n_dmus:
        raise AssertionError("the reference account must retain every organization")
    if not frame["reference_frequency"].eq(args.peers_per_dmu).all():
        raise AssertionError("the circular fixture must have uniform total frequency")
    if not frame["self_reference_frequency"].eq(1).all():
        raise AssertionError("the circular fixture must have one self edge per row")
    if not frame["other_reference_frequency"].eq(args.peers_per_dmu - 1).all():
        raise AssertionError("the circular fixture has an incorrect other-edge count")
    if (
        not frame["reference_frequency"]
        .eq(frame["self_reference_frequency"] + frame["other_reference_frequency"])
        .all()
    ):
        raise AssertionError("self and other counts must reconstruct total frequency")
    np.testing.assert_allclose(
        frame["reference_rate"],
        args.peers_per_dmu / args.n_dmus,
        rtol=0.0,
        atol=np.finfo(np.float64).eps,
    )
    if result.metadata["additional_solver_calls"] != 0:
        raise AssertionError("reference-frequency aggregation must launch no solves")
    if result.metadata["source_peer_tolerance"] != source_peer_tolerance:
        raise AssertionError("source peer_tolerance provenance must be preserved")
    if result.metadata["reference_rate_denominator"] != ("all_evaluated_organizations"):
        raise AssertionError("the complete reference-rate denominator must be explicit")
    if source.metadata["solver_calls"] != source_solver_calls:
        raise AssertionError("the source solver counter must remain unchanged")

    edge_rate = expected_edges / elapsed if elapsed > 0.0 else float("inf")
    print(
        f"n={args.n_dmus} peers_per_dmu={args.peers_per_dmu} "
        f"edges={expected_edges} elapsed={elapsed:.3f}s "
        f"edges_per_second={edge_rate:.0f} additional_solver_calls=0"
    )


if __name__ == "__main__":
    main()
