"""Shared sparse-matrix helpers for convex DEA model families."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

import numpy as np
from scipy.sparse import csc_matrix, vstack

from ..data import DEAData
from ..enums import ReturnsToScale
from ..exceptions import ModelSpecificationError


@dataclass(frozen=True, slots=True)
class CompiledReference:
    """Sparse quantities with lazily compiled immutable scale statistics."""

    rows: np.ndarray
    inputs: csc_matrix
    outputs: csc_matrix
    bad_outputs: csc_matrix | None = None
    _source_data: DEAData | None = field(
        default=None,
        repr=False,
        compare=False,
    )
    _ordinary_row_max: tuple[np.ndarray, np.ndarray] | None = field(
        init=False,
        default=None,
        repr=False,
        compare=False,
    )
    _absolute_row_max: tuple[np.ndarray, np.ndarray] | None = field(
        init=False,
        default=None,
        repr=False,
        compare=False,
    )
    _bad_output_row_max: np.ndarray | None = field(
        init=False,
        default=None,
        repr=False,
        compare=False,
    )
    _last_validated_rows: np.ndarray | None = field(
        init=False,
        default=None,
        repr=False,
        compare=False,
    )

    @property
    def size(self) -> int:
        return int(self.rows.size)

    def _ordinary_statistics(self) -> tuple[np.ndarray, np.ndarray]:
        """Return the ordinary maxima, compiling them once on serial access."""
        cached = self._ordinary_row_max
        if cached is None:
            # Lock-free initialization is deliberately idempotent: concurrent
            # first readers may duplicate work, while the ordinary serial path
            # compiles one immutable pair exactly once.
            cached = _compile_reference_ordinary_row_statistics(
                self.inputs,
                self.outputs,
            )
            object.__setattr__(self, "_ordinary_row_max", cached)
        return cached

    def _absolute_statistics(self) -> tuple[np.ndarray, np.ndarray]:
        """Return the absolute maxima, compiling them once on serial access."""
        cached = self._absolute_row_max
        if cached is None:
            # See _ordinary_statistics for the benign-race contract.
            cached = _compile_reference_absolute_row_statistics(
                self.inputs,
                self.outputs,
            )
            object.__setattr__(self, "_absolute_row_max", cached)
        return cached

    @property
    def input_row_max(self) -> np.ndarray:
        """Largest observed input in each account."""
        return self._ordinary_statistics()[0]

    @property
    def output_row_max(self) -> np.ndarray:
        """Largest observed desirable output in each account."""
        return self._ordinary_statistics()[1]

    @property
    def input_abs_row_max(self) -> np.ndarray:
        """Largest absolute observed input in each account."""
        return self._absolute_statistics()[0]

    @property
    def output_abs_row_max(self) -> np.ndarray:
        """Largest absolute observed desirable output in each account."""
        return self._absolute_statistics()[1]

    @property
    def bad_output_row_max(self) -> np.ndarray:
        """Largest observed undesirable output in each declared account."""
        if self.bad_outputs is None:
            raise RuntimeError("compiled reference has no bad-output accounts")
        cached = self._bad_output_row_max
        if cached is None:
            row_max = np.asarray(self.bad_outputs.max(axis=1).toarray()).reshape(-1)
            cached = _immutable_vector(row_max)
            object.__setattr__(self, "_bad_output_row_max", cached)
        return cached


def _immutable_vector(values: np.ndarray) -> np.ndarray:
    """Return a zero-copy public view backed by immutable private bytes."""
    contiguous = np.asarray(values, dtype=np.float64).reshape(-1)
    return np.frombuffer(contiguous.tobytes(order="C"), dtype=np.float64)


def _immutable_indices(values: np.ndarray) -> np.ndarray:
    """Return an integer vector whose write protection cannot be reopened."""
    contiguous = np.asarray(values, dtype=np.int64).reshape(-1)
    return np.frombuffer(contiguous.tobytes(order="C"), dtype=np.int64)


def _compile_reference_ordinary_row_statistics(
    inputs: csc_matrix,
    outputs: csc_matrix,
) -> tuple[np.ndarray, np.ndarray]:
    """Compile input/output ordinary maxima as one lazy statistic group."""
    input_row_max = np.asarray(inputs.max(axis=1).toarray()).reshape(-1)
    output_row_max = np.asarray(outputs.max(axis=1).toarray()).reshape(-1)
    return _immutable_vector(input_row_max), _immutable_vector(output_row_max)


def _compile_reference_absolute_row_statistics(
    inputs: csc_matrix,
    outputs: csc_matrix,
) -> tuple[np.ndarray, np.ndarray]:
    """Compile input/output absolute maxima as one lazy statistic group."""
    input_abs_row_max = np.asarray(abs(inputs).max(axis=1).toarray()).reshape(-1)
    output_abs_row_max = np.asarray(abs(outputs).max(axis=1).toarray()).reshape(-1)
    return _immutable_vector(input_abs_row_max), _immutable_vector(output_abs_row_max)


def as_sparse_rows(values: np.ndarray) -> csc_matrix:
    """Convert row-oriented observations into a column-oriented DEA matrix."""
    return csc_matrix(values.T)


def compile_reference(data: DEAData, rows: np.ndarray) -> CompiledReference:
    """Compile one reference set for reuse across evaluated observations."""
    source_rows = np.asarray(rows, dtype=np.int64)
    if source_rows.ndim != 1:
        source_rows = source_rows.reshape(-1)
    compiled_rows = _immutable_indices(source_rows)
    reference = CompiledReference(
        rows=compiled_rows,
        inputs=as_sparse_rows(data.inputs[compiled_rows]),
        outputs=as_sparse_rows(data.outputs[compiled_rows]),
        bad_outputs=(
            None
            if data.bad_outputs is None
            else as_sparse_rows(data.bad_outputs[compiled_rows])
        ),
        _source_data=data,
    )
    if not source_rows.flags.writeable:
        object.__setattr__(reference, "_last_validated_rows", source_rows)
    return reference


def get_or_compile_reference(
    data: DEAData,
    rows: np.ndarray,
    set_id: int,
    compiled_references: dict[int, CompiledReference],
    *,
    compiler: Callable[[DEAData, np.ndarray], CompiledReference] = compile_reference,
) -> CompiledReference:
    """Return a provenance-safe cached reference for one reference-plan set.

    Every cache hit checks its originating data object and exact reference
    rows. Repeated hits from one immutable ``ReferencePlan`` use row-object
    identity as a constant-time exactness certificate; a new plan pays for one
    row-array comparison before gaining the same fast path. Technology
    matrices are never hashed or compared.
    """
    reference = compiled_references.get(set_id)
    if reference is None:
        reference = compiler(data, rows)
        compiled_references[set_id] = reference
    else:
        if reference._source_data is not data:
            raise ModelSpecificationError(
                "compiled reference cache provenance mismatch for "
                f"set_id={set_id}: the cached reference was compiled from a "
                "different DEAData instance"
            )
        expected_rows = np.asarray(rows, dtype=np.int64)
        if expected_rows.ndim != 1:
            expected_rows = expected_rows.reshape(-1)
        if reference._last_validated_rows is not expected_rows and not np.array_equal(
            reference.rows, expected_rows
        ):
            raise ModelSpecificationError(
                "compiled reference cache row mismatch for "
                f"set_id={set_id}: cached rows do not match the current "
                "ReferencePlan"
            )
        if not expected_rows.flags.writeable:
            object.__setattr__(reference, "_last_validated_rows", expected_rows)
    return reference


def join_optional_rows(base: csc_matrix, extra: csc_matrix | None) -> csc_matrix:
    """Append sparse constraint rows when an optional block is present."""
    return base if extra is None else vstack([base, extra], format="csc")


def join_optional_values(
    base: np.ndarray,
    extra: np.ndarray | None,
) -> np.ndarray:
    """Append right-hand-side values when an optional block is present."""
    return base if extra is None else np.concatenate([base, extra])


def rts_matrices(
    n_variables: int,
    n_lambda: int,
    returns_to_scale: ReturnsToScale,
) -> tuple[csc_matrix | None, np.ndarray | None, csc_matrix | None, np.ndarray | None]:
    """Return inequality/equality blocks for a returns-to-scale assumption."""
    row = np.zeros(n_variables, dtype=np.float64)
    row[:n_lambda] = 1.0

    if returns_to_scale is ReturnsToScale.VRS:
        return None, None, csc_matrix(row.reshape(1, -1)), np.asarray([1.0])
    if returns_to_scale is ReturnsToScale.NIRS:
        return csc_matrix(row.reshape(1, -1)), np.asarray([1.0]), None, None
    if returns_to_scale is ReturnsToScale.NDRS:
        return csc_matrix((-row).reshape(1, -1)), np.asarray([-1.0]), None, None
    return None, None, None, None


def clean_small(values: np.ndarray, tolerance: float) -> np.ndarray:
    """Replace solver noise within a declared tolerance by exact zeroes."""
    cleaned = np.asarray(values, dtype=np.float64).copy()
    cleaned[np.abs(cleaned) <= tolerance] = 0.0
    return cleaned
