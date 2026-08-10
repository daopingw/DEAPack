# Extending DEAPack

DEAPack has several extension boundaries, but they are not all runtime plugin
APIs. A solver backend can satisfy a public structural protocol, and an
external result object can use the public reporting contract. New built-in
methods, catalog records, and plot kinds currently enter through reviewed
source contributions. This distinction prevents a locally registered name
from looking like a source-qualified DEAPack method.

## Choose the extension boundary

| Goal | Current boundary | Runtime registration? |
|---|---|---:|
| Use another LP or MILP engine | `deapack.solvers.LPSolver` or `MIPSolver` and the backend-neutral task/solution records | Structural protocol; no global registry required |
| Compose an empirical study from supported parts | public data, model, reference, solver, analysis, and result objects | Yes, through ordinary constructors |
| Add a new literature-defined method to DEAPack | evidence protocol, implementation, result contract, machine ontology, catalog, tests, and Documentation | No; reviewed repository contribution |
| Build a report for an external result object | `deapack.reporting.create_result_report` | Yes, if the result supplies the documented summary/metadata contract |
| Export a complete audit bundle for an external result object | `deapack.reporting.export_result_bundle` | Yes, if all documented public table accessors are supplied |
| Make an application-specific figure | consume public `DEAResult` tables or backend-independent preparation data | Yes, in application code |
| Add a built-in `result.plot(kind=...)` route | preparation/validity contract, lazy renderer, registry entry, tests, docs, and figure-size/readability checks | No public plot-registration function yet |

## Solver backends

The solver-neutral objects are public from `deapack.solvers`:

```{eval-rst}
.. autoclass:: deapack.solvers.LPSolver

.. autoclass:: deapack.solvers.LinearProgram
   :members:

.. autoclass:: deapack.solvers.LPSolution
   :members:

.. autoclass:: deapack.solvers.MIPSolver

.. autoclass:: deapack.solvers.MixedIntegerProgram
   :members:

.. autoclass:: deapack.solvers.MIPSolution
   :members:
```

The protocols are structural: an object with a non-empty `name` and a
compatible `solve()` method can be passed to model constructors that document
a `solver=` argument. LP backends receive a minimization `LinearProgram` and
return an `LPSolution`; MILP backends use the separate mixed-integer records.

A backend status is not sufficient to publish a DEA result. DEAPack models
reconstruct primal feasibility, economic balances, targets, and other
method-specific certificates from the returned solution. A backend that omits
marginals can be suitable for a score-only task but cannot support a method
whose public dual or certificate contract requires them. Preserve variable
and row order, return finite arrays with the declared shapes, map native
termination states to `SolverStatus`, and never label a rounded integer
solution as an integer optimum.

The default `SciPyHiGHSSolver` and `SciPyHiGHSMILPSolver` remain the reference
zero-configuration backends. An optional backend must reproduce their
backend-neutral task semantics and pass independent certificates; package
correctness cannot depend on its installation.

## Supported model composition

Most research workflows should compose supported pieces instead of creating a
new class. Keep these choices separate:

1. data roles and observation keys;
2. production graph and technology assumptions;
3. reference population;
4. performance criterion or valuation account;
5. appraisal or target-completion protocol;
6. downstream scale, productivity, network, dynamic, or heterogeneity
   analysis; and
7. solver, tolerances, diagnostics, visualization, and reporting.

The {doc}`../user-guide/method-catalog` identifies executable combinations,
while the repository's
[compatibility matrix](https://github.com/daopingw/DEAPack/blob/main/specs/COMPATIBILITY_MATRIX.md)
records combinations that must fail closed. Do not subclass a nearby model
only to bypass a rejected combination: a changed feasible set, objective,
direction, denominator, disposal rule, reference exclusion, or failure policy
can change the estimand.

## Adding a literature-defined method

There is no public `register_model()` or `register_method()` function. The
installed catalog is governed evidence, not a user namespace. A proposed
built-in method follows the repository
[contribution guide](https://github.com/daopingw/DEAPack/blob/main/CONTRIBUTING.md):

1. state the economic or managerial question and obtain the complete defining
   source;
2. freeze source-native equations, data domain, technology, score meaning,
   target policy, and non-equivalence boundaries;
3. locate the method in the eleven-axis framework and decide whether it is a
   new principal mechanism, a specialization, a preset, or a documented
   extension;
4. implement a backend-neutral task or exact kernel and release claims only
   through independent numerical and economic certificates;
5. return the common `DEAResult` tables, method-specific validity fields, and
   canonical registry provenance;
6. add analytical, invariance, failure, independent-oracle, performance, and
   catalog-parity tests; and
7. document the complete package behavior and its relationship to existing
   method families.

If the source or independent oracle cannot be closed, keep the proposal in a
`deferred_to_next_version` source protocol. An internal prototype or ontology
record does not make it a public method.

## External reporting results

`create_result_report()` accepts a source-independent, already-fitted result
object. It requires `summary(copy=True)` to return a DataFrame with unique
columns containing `dmu_id`, `period`, `score`, `efficiency`, `distance`,
`is_efficient`, `solver_status`, and `model_family`, plus a mapping-like
`metadata` attribute. Candidate performance columns still need DEAPack's
declared measure semantics; a numeric column alone is not enough.

`export_result_bundle()` additionally reads all ten named table attributes:
`slacks`, `targets`, `intensities`, `duals`, `components`, `multipliers`,
`links`, `diagnostics`, `appraisals`, and `history`. Empty DataFrames are
valid. Every accessor must expose an already-fitted, side-effect-free snapshot
and must not mutate concurrently during export. The exporter reads and copies
tables; it never invokes an extension's `report()` method or solver.

See {doc}`../api/reporting` for exact call signatures, serialization rules,
and failure behavior.

## Visualization extensions

Application code can plot from copied public result tables or reuse the
backend-independent preparation objects exported by `deapack.visualization`.
Keep data preparation separate from rendering and enforce the source result's
status and validity gates before drawing substantive values.

The built-in `DEAResult.plot()` catalog is closed in the current release:
there is no supported public function that registers a new kind or measure at
runtime. A contribution to the built-in catalog needs:

- a narrow applicability predicate tied to canonical method metadata;
- backend-free preparation that performs no solve and reconstructs every
  required account;
- explicit metric direction, benchmark, and row-level validity semantics;
- lazy import of the optional rendering backend;
- error handling through `PlotNotAvailableError` rather than a misleading
  fallback;
- tests for applicability, certification failures, determinism, scale, and
  readability; and
- aligned API, user-guide, and case documentation.

The {doc}`../api/visualization` page describes the current registered kinds
and public preparation functions.

## Review checklist

Before proposing any extension, answer five questions:

1. Does it change only computation, or does it change the economic estimand?
2. Which public claims—score, target, peer, dual, component, link, trajectory,
   report, or figure—must be certified independently?
3. Which schema or identity version would a consumer need to distinguish?
4. Can a missing optional dependency or failed secondary task leave upstream
   valid claims intact?
5. Does the contribution extend an existing method family or introduce a
   distinct transferable mechanism that needs its own documented identity?

Use {doc}`architecture`, {doc}`performance`, {doc}`versioning`, and
{doc}`hosting` as the common review entry points.
