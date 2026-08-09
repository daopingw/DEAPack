"""Unified public result container shared by models and analyses."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from os import PathLike
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pandas as pd

from ._registry import _FrozenDict
from .reporting._types import ResultReport
from .visualization._types import PlotInfo

if TYPE_CHECKING:
    from .analysis.reference_frequency import ReferenceFrequencyResult

_REQUIRED_SUMMARY_COLUMNS = {
    "dmu_id",
    "period",
    "score",
    "efficiency",
    "distance",
    "is_efficient",
    "solver_status",
    "model_family",
}


class _FrozenList(list[Any]):
    """A JSON-encodable list that preserves type compatibility without mutation."""

    @staticmethod
    def _immutable(*args: Any, **kwargs: Any) -> None:
        del args, kwargs
        raise TypeError("result metadata is immutable")

    __setitem__ = _immutable
    __delitem__ = _immutable
    __iadd__ = _immutable
    __imul__ = _immutable
    append = _immutable
    clear = _immutable
    extend = _immutable
    insert = _immutable
    pop = _immutable
    remove = _immutable
    reverse = _immutable
    sort = _immutable

    def __copy__(self) -> _FrozenList:
        return self

    def __deepcopy__(self, memo: dict[int, Any]) -> _FrozenList:
        del memo
        return self


def _freeze_result_metadata(value: Any) -> Any:
    if isinstance(value, _FrozenDict):
        return value
    if isinstance(value, Mapping):
        return _FrozenDict(
            {key: _freeze_result_metadata(item) for key, item in value.items()}
        )
    if isinstance(value, list):
        return _FrozenList(_freeze_result_metadata(item) for item in value)
    if isinstance(value, tuple):
        return tuple(_freeze_result_metadata(item) for item in value)
    if isinstance(value, (set, frozenset)):
        return frozenset(_freeze_result_metadata(item) for item in value)
    return value


@dataclass(frozen=True, slots=True)
class DEAResult:
    """Tidy numerical results with assumptions and diagnostics attached."""

    summary_frame: pd.DataFrame
    slacks: pd.DataFrame = field(default_factory=pd.DataFrame)
    targets: pd.DataFrame = field(default_factory=pd.DataFrame)
    intensities: pd.DataFrame = field(default_factory=pd.DataFrame)
    duals: pd.DataFrame = field(default_factory=pd.DataFrame)
    components: pd.DataFrame = field(default_factory=pd.DataFrame)
    multipliers: pd.DataFrame = field(default_factory=pd.DataFrame)
    links: pd.DataFrame = field(default_factory=pd.DataFrame)
    diagnostics: pd.DataFrame = field(default_factory=pd.DataFrame)
    metadata: Mapping[str, Any] = field(default_factory=dict)
    appraisals: pd.DataFrame = field(default_factory=pd.DataFrame)
    history: pd.DataFrame = field(default_factory=pd.DataFrame)

    def __post_init__(self) -> None:
        missing = _REQUIRED_SUMMARY_COLUMNS.difference(self.summary_frame.columns)
        if missing:
            raise ValueError(f"result summary is missing columns: {sorted(missing)}")
        object.__setattr__(
            self,
            "metadata",
            _freeze_result_metadata(dict(self.metadata)),
        )

    def summary(self, *, copy: bool = True) -> pd.DataFrame:
        """Return the one-row-per-observation result table."""
        return self.summary_frame.copy() if copy else self.summary_frame

    def peers(self, dmu_id: object, *, period: object | None = None) -> pd.DataFrame:
        """Return positive reference intensities for one evaluated observation."""
        if self.intensities.empty:
            return self.intensities.copy()
        mask = self.intensities["dmu_id"] == dmu_id
        if period is not None:
            mask &= self.intensities["period"] == period
        return self.intensities.loc[mask].copy()

    def reference_frequency(self) -> ReferenceFrequencyResult:
        """Count peer selections in this result's certified selected plan.

        This zero-solve diagnostic is intentionally restricted to one global
        cross-section under static black-box continuous-convex full DEA.  It
        does not assess alternate optima, outliers, or statistical uncertainty.
        """

        from .analysis.reference_frequency import reference_frequency

        return reference_frequency(self)

    def targets_for(
        self, dmu_id: object, *, period: object | None = None
    ) -> pd.DataFrame:
        """Return variable targets for one evaluated observation."""
        if self.targets.empty:
            return self.targets.copy()
        mask = self.targets["dmu_id"] == dmu_id
        if period is not None:
            mask &= self.targets["period"] == period
        return self.targets.loc[mask].copy()

    def components_for(
        self, dmu_id: object, *, period: object | None = None
    ) -> pd.DataFrame:
        """Return system and process-level scores for one observation."""
        if self.components.empty:
            return self.components.copy()
        mask = self.components["dmu_id"] == dmu_id
        if period is not None:
            mask &= self.components["period"] == period
        return self.components.loc[mask].copy()

    def multipliers_for(
        self,
        dmu_id: object,
        *,
        period: object | None = None,
        id_column: str = "dmu_id",
    ) -> pd.DataFrame:
        """Return multiplier rows in which a declared role has one DMU ID.

        Most models use ``dmu_id``. Pair-specific appraisal protocols instead
        expose explicit roles such as ``protected_dmu_id`` and
        ``focal_dmu_id``; callers select those roles with ``id_column``.
        """
        if self.multipliers.empty:
            return self.multipliers.copy()
        if id_column not in self.multipliers:
            choices = ", ".join(map(str, self.multipliers.columns))
            raise KeyError(
                f"multiplier ID column {id_column!r} is unavailable; "
                f"columns are: {choices}"
            )
        mask = self.multipliers[id_column] == dmu_id
        if period is not None and "period" in self.multipliers:
            mask &= self.multipliers["period"] == period
        return self.multipliers.loc[mask].copy()

    def links_for(
        self, dmu_id: object, *, period: object | None = None
    ) -> pd.DataFrame:
        """Return internal-link accounts for one network observation."""
        if self.links.empty:
            return self.links.copy()
        mask = self.links["dmu_id"] == dmu_id
        if period is not None:
            mask &= self.links["period"] == period
        return self.links.loc[mask].copy()

    def appraisal_rows_for(
        self,
        dmu_id: object,
        *,
        id_column: str = "evaluatee_dmu_id",
    ) -> pd.DataFrame:
        """Return appraisal rows in which a declared role has one DMU ID.

        Cross-efficiency protocols use role-specific identifiers rather than
        overloading the ordinary result ``dmu_id``. For example, ordinary
        cross-efficiency uses ``appraiser_dmu_id`` and
        ``evaluatee_dmu_id``; game cross-efficiency uses
        ``protected_dmu_id`` and ``focal_dmu_id``.
        """
        if self.appraisals.empty:
            return self.appraisals.copy()
        if id_column not in self.appraisals:
            choices = ", ".join(map(str, self.appraisals.columns))
            raise KeyError(
                f"appraisal ID column {id_column!r} is unavailable; "
                f"columns are: {choices}"
            )
        return self.appraisals.loc[self.appraisals[id_column] == dmu_id].copy()

    def history_for(self, dmu_id: object) -> pd.DataFrame:
        """Return iterative analysis history for one DMU."""
        if self.history.empty:
            return self.history.copy()
        if "dmu_id" not in self.history:
            raise KeyError("iterative history does not contain a 'dmu_id' column")
        return self.history.loc[self.history["dmu_id"] == dmu_id].copy()

    def available_plots(self) -> tuple[PlotInfo, ...]:
        """Return immutable descriptions of plots applicable to this result.

        Measure plots require a valid finite optimal value. Quantity-based
        plots apply their own target, dimensionality, peer, and certification
        contracts, including the certified classic and strong-separable
        environmental static SBM variable-improvement accounts, the certified
        ordinary DDF and common-factor environmental DDF directional plans,
        the core radial group/metafrontier identity, and the reported peer-use
        frequencies in one certified selected plan. Discovery does not import
        a plotting backend.
        """
        from .visualization import available_plots

        return available_plots(self)

    def plot(
        self,
        kind: str = "performance",
        *,
        metric: str | None = None,
        period: object | None = None,
        dmu_id: object | None = None,
        variable: str | None = None,
        theme: str = "deapack",
        view: str = "auto",
    ) -> Any:
        """Create a result figure without displaying it.

        Omitting ``metric`` selects the safest declared measure for this
        result when ``kind="performance"``. Explicit performance metrics must
        have registered plotting semantics. Quantity-based kinds such as
        ``"frontier"`` reject ``metric`` and use their result-table contract.
        The classic Dynamic-SBM ``"trajectory"`` plot additionally requires
        one ``dmu_id`` and accepts one carry-over ``variable``. Matplotlib is
        imported only when this method renders a supported plot. The classic
        input-oriented Network-SBM ``"process"`` plot requires one ``dmu_id``
        and accepts ``period`` only for a panel result. The three classic static
        SBM orientations and the certified separable, strongly disposable
        environmental SBM expose ``"improvement"`` for one certified
        variable-specific operating plan. The same kind uses independent
        directional ledgers for ordinary static DDF and the core CRS common-
        factor environmental DDF; neither beta-scaled move is reinterpreted
        as an SBM score. The core radial group/meta account exposes
        ``"metafrontier"`` for a certified cross-organization decomposition;
        panel results accept one selected ``period``. Static convex
        cross-sections with complete certified peer accounts expose
        ``"references"``: it separates reported self-use from use by other
        organizations above the source peer-reporting threshold and makes no
        all-optima, global-reference-set, outlier, or inferential claim.
        """
        from .visualization import plot_result

        return plot_result(
            self,
            kind=kind,
            metric=metric,
            period=period,
            dmu_id=dmu_id,
            variable=variable,
            theme=theme,
            view=view,
        )

    def report(
        self,
        kind: str = "brief",
        *,
        metric: str | None = None,
        period: object | None = None,
        dmu_id: object | None = None,
        detail: str = "brief",
        theme: str = "deapack",
    ) -> ResultReport:
        """Create an immutable, self-contained result report.

        The first reporting contract is a safe standalone HTML brief. It uses
        only the public result tables and declared measure semantics, imports
        no plotting backend, and does not write a file until ``save()`` is
        called on the returned report.
        """
        from .reporting import create_result_report

        return create_result_report(
            self,
            kind=kind,
            metric=metric,
            period=period,
            dmu_id=dmu_id,
            detail=detail,
            theme=theme,
        )

    def export_bundle(self, path: str | PathLike[str]) -> Path:
        """Write a deterministic, complete ``.zip`` result audit bundle.

        The archive contains a self-contained HTML brief, metadata, a hashed
        manifest, and every non-empty public result table in canonical JSONL
        and spreadsheet-safe CSV form. String values are preserved exactly in
        JSONL; supported structured values receive a deterministic encoding.
        Export reads the fitted result only: it imports no plotting backend
        and performs no optimization.
        """
        from .reporting import export_result_bundle

        return export_result_bundle(self, path)

    def publish(
        self,
        path: str | PathLike[str],
        *,
        metric: str | None = None,
        period: object | None = None,
        dmu_id: object | None = None,
        variable: str | None = None,
        theme: str = "deapack",
    ) -> Path:
        """Write a deterministic illustrated ``.zip`` publication bundle.

        The archive combines a reader-facing HTML entry page, reusable SVG
        figures selected from :meth:`available_plots`, and the complete
        ordinary audit bundle. Plotting and export read the fitted result only;
        no optimization is repeated. Selectors unlock plots whose faithful
        construction requires an explicit period, organization, or variable.
        """
        from .reporting import publish_result

        return publish_result(
            self,
            path,
            metric=metric,
            period=period,
            dmu_id=dmu_id,
            variable=variable,
            theme=theme,
        )
