# Exceptions and failure handling

DEAPack distinguishes invalid data, inconsistent model specifications, solver
execution failures, and requests for result views that cannot be constructed
faithfully. The current public hierarchy has one core branch and two
view-specific branches:

```text
Exception
├── DEAPackError
│   ├── DataValidationError       (also ValueError)
│   ├── ModelSpecificationError   (also ValueError)
│   └── SolverError               (also RuntimeError)
├── PlotNotAvailableError         (ValueError)
└── ReportNotAvailableError       (ValueError)
    ├── PublicationBundleNotAvailableError
    └── ResultBundleNotAvailableError
```

`PlotNotAvailableError` and the reporting exceptions do **not** currently
inherit from `DEAPackError`. Catch them explicitly when a user can request an
optional view. Ordinary `TypeError` and `ValueError` can also arise from
argument type/value checks and enum parsing; the hierarchy does not yet wrap
every invalid Python call.

## Core errors

```{eval-rst}
.. autoclass:: deapack.exceptions.DEAPackError
   :show-inheritance:

.. autoclass:: deapack.exceptions.DataValidationError
   :show-inheritance:

.. autoclass:: deapack.exceptions.ModelSpecificationError
   :show-inheritance:

.. autoclass:: deapack.exceptions.SolverError
   :show-inheritance:
```

`DataValidationError` means that observations do not satisfy the declared
schema or a model's data domain. `ModelSpecificationError` means that the
requested technology, measure, reference rule, graph, or other model choices
are inconsistent. `SolverError` is reserved for a selected backend that
cannot run; a fitted row with an infeasible, unbounded, limit, or numerical
status is usually retained in the result tables instead of converted into one
study-wide exception.

## Visualization errors

```{eval-rst}
.. autoclass:: deapack.visualization.PlotNotAvailableError
   :show-inheritance:
   :no-index:
```

This error protects interpretation. It can indicate an unknown plot kind, a
missing required result account, an unsupported selection, or a validity gate
that prevents a faithful figure. A missing Matplotlib installation instead
raises `ImportError` with the `DEAPack[viz]` installation instruction.

## Reporting and bundle errors

```{eval-rst}
.. autoclass:: deapack.reporting.ReportNotAvailableError
   :show-inheritance:
   :no-index:

.. autoclass:: deapack.reporting.ResultBundleNotAvailableError
   :show-inheritance:
   :no-index:

.. autoclass:: deapack.reporting.PublicationBundleNotAvailableError
   :show-inheritance:
   :no-index:
```

`ReportNotAvailableError` protects the compact reading view when its requested
measure or selection has no declared, valid interpretation.
`ResultBundleNotAvailableError` is more specific: it means the complete audit
archive could not be represented or written under the bundle contract.
`PublicationBundleNotAvailableError` protects the illustrated publication
boundary, including explicit plot selections, atomic archive writing, and the
optional Matplotlib dependency. Unlike a direct `result.plot(...)` call,
`result.publish(...)` wraps a missing backend in this typed error while
retaining the `DEAPack[viz]` installation instruction.

## Catch errors at the right boundary

```python
from deapack.exceptions import DEAPackError
from deapack.reporting import (
    PublicationBundleNotAvailableError,
    ReportNotAvailableError,
    ResultBundleNotAvailableError,
)
from deapack.visualization import PlotNotAvailableError

try:
    result = model.fit(data)
except DEAPackError as error:
    # Correct the data, specification, or backend configuration.
    raise

try:
    figure = result.plot(kind="performance")
except PlotNotAvailableError:
    figure = None

try:
    result.export_bundle("analysis.zip")
except ResultBundleNotAvailableError:
    raise
except ReportNotAvailableError:
    # Relevant only when calling the report API separately; bundle export
    # normally converts an unavailable brief into a diagnostic cover.
    raise

try:
    result.publish("analysis-publication.zip")
except PublicationBundleNotAvailableError:
    # Install DEAPack[viz], correct an explicit selector, or inspect the
    # message for an atomic serialization failure.
    raise
```

Do not catch `Exception` around an entire empirical workflow and replace the
result with a missing score. First distinguish a bad study specification from
row-level optimization status, then preserve diagnostics for every attempted
observation.
