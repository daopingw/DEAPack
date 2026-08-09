"""Biennial Malmquist indexes using a pooled frontier for each period pair."""

from __future__ import annotations

import numpy as np

from ..data import DEAData
from ..models._common import compile_reference
from ..results import DEAResult
from ._pooled_malmquist import (
    _PooledMalmquistProductivityIndex,
    _PooledReferencePlan,
)
from .productivity import _PanelTransition


class BiennialMalmquistProductivityIndex(_PooledMalmquistProductivityIndex):
    """Estimate the Pastor--Asmild--Lovell Biennial Malmquist index.

    Each adjacent transition uses a technology pooled from exactly its two
    periods. This avoids cross-period radial infeasibility and permits technical
    regress without making an existing pair depend on observations from later
    periods. Unlike the Global Malmquist index, the sequence is not generally
    circular.
    """

    model_family = "biennial_malmquist"
    variant = "pastor_asmild_lovell_biennial"
    pooled_kind = "biennial"
    technology_label = "pair_pooled_biennial_and_contemporaneous_frontiers"
    circularity = "not_guaranteed_pair_specific_references"
    sample_extension = "existing_pairs_unchanged_when_new_periods_are_added"
    _registry_method_id = "productivity.biennial_malmquist"

    def _build_pooled_plan(
        self,
        data: DEAData,
        transitions: tuple[_PanelTransition, ...],
    ) -> _PooledReferencePlan:
        if data.periods is None:
            raise RuntimeError("validated panel lost its period values")
        pairs = {
            (transition.base_period, transition.comparison_period)
            for transition in transitions
        }
        references = {}
        periods_by_key = {}
        metadata_rows: list[dict[str, object]] = []
        for pair in pairs:
            base_period, comparison_period = pair
            rows = np.flatnonzero(
                (data.periods == base_period) | (data.periods == comparison_period)
            ).astype(np.int64, copy=False)
            rows.setflags(write=False)
            references[pair] = compile_reference(data, rows)
            periods_by_key[pair] = pair
            metadata_rows.append(
                {
                    "base_period": base_period,
                    "comparison_period": comparison_period,
                    "reference_observations": int(rows.size),
                }
            )
        order = {period: position for position, period in enumerate(data.period_order)}
        metadata_rows.sort(key=lambda row: order[row["base_period"]])
        return _PooledReferencePlan(
            references=references,
            key_by_period_pair={pair: pair for pair in pairs},
            periods_by_key=periods_by_key,
            metadata={"biennial_reference_sets": tuple(metadata_rows)},
        )

    def fit(self, data: DEAData) -> DEAResult:
        """Estimate adjacent Biennial Malmquist transitions for a panel."""
        return super().fit(data)


BiennialMalmquistDEA = BiennialMalmquistProductivityIndex
"""Discoverability alias for :class:`BiennialMalmquistProductivityIndex`."""
