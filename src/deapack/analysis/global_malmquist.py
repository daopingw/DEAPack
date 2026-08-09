"""Circular Global Malmquist productivity indexes on a pooled technology."""

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


class GlobalMalmquistProductivityIndex(_PooledMalmquistProductivityIndex):
    """Estimate the circular Global Malmquist productivity index.

    The Pastor--Lovell index measures each observation against one pooled
    technology containing all sample periods. Its ratio is circular within a
    fixed sample and avoids the cross-period radial programs used by the
    geometric Malmquist index. The decomposition retains the change in
    contemporaneous operating performance and replaces the geometric
    opportunity-change component with best-practice-gap change.

    Constant returns to scale is the classic default. Other returns-to-scale
    assumptions are supported as explicit sensitivity specifications.
    """

    model_family = "global_malmquist"
    variant = "pastor_lovell_global"
    pooled_kind = "global"
    technology_label = "pooled_global_and_contemporaneous_frontiers"
    circularity = "within_fixed_global_sample"
    sample_extension = "recompute_all_global_distances_when_periods_are_added"
    _registry_method_id = "productivity.global_malmquist"

    def _build_pooled_plan(
        self,
        data: DEAData,
        transitions: tuple[_PanelTransition, ...],
    ) -> _PooledReferencePlan:
        all_rows = np.arange(data.n_dmus, dtype=np.int64)
        all_rows.setflags(write=False)
        key = "all_periods"
        pairs = {
            (transition.base_period, transition.comparison_period): key
            for transition in transitions
        }
        return _PooledReferencePlan(
            references={key: compile_reference(data, all_rows)},
            key_by_period_pair=pairs,
            periods_by_key={key: data.period_order},
            metadata={
                "global_reference_periods": data.period_order,
                "global_reference_observations": data.n_dmus,
            },
        )

    def fit(self, data: DEAData) -> DEAResult:
        """Estimate adjacent Global Malmquist transitions for a panel."""
        return super().fit(data)


GlobalMalmquistDEA = GlobalMalmquistProductivityIndex
"""Discoverability alias for :class:`GlobalMalmquistProductivityIndex`."""
