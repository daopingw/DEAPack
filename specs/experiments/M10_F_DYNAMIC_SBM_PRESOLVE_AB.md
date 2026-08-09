# M10-F: Dynamic-SBM HiGHS presolve A/B experiment

## Decision boundary

This is a governed solver experiment, not a model variant and not a release
benchmark default. It must not alter `DynamicSBM`, `SolverOptions`, the public
API, or `benchmarks/cases.json`. The existing default remains
`SolverOptions(presolve=True)` unless a separate, reviewed decision changes it.

The experiment may support only a conservative decision to retain the
existing default. A switch to `presolve=False` is out of scope. Any result
divergence, incomplete solve, failed certificate, source-tree change, or
runtime-import mismatch closes the gate and forbids a default-change
recommendation.

## Frozen matrix

The executable record is
`benchmarks/experiments/dynamic_sbm_presolve_ab.py`. Its default matrix is the
Cartesian product of:

- data profiles: `oracle`, `realistic`, and `extreme`;
- orientations: `input`, `output`, and `non-oriented`; and
- returns to scale: `crs` and `vrs`.

This produces 18 cases and 36 independently launched fits. The oracle profile
uses the analytically certified `dynamic_capacity_backlog` fixture. The
realistic profile is a deterministic 12-organization, three-period operating
panel. The realistic and extreme profiles both include good, bad, free, and
fixed carry-overs plus discretionary and non-discretionary period production
variables. The extreme profile applies heterogeneous valid unit multipliers
from `1e-12` through `1e12`; all observations remain finite and strictly
positive.

## Comparison contract

Each case compares `presolve=True` with `presolve=False` for:

- solver and publication statuses;
- horizon and period scores and accounts;
- targets, slacks, carry-over links, and components;
- thresholded peer identities and intensities; and
- all published primal, economic, target, peer, duality, carry-over, balance,
  continuity, fixed-account, and reconstruction certificates and residuals.

Categorical and Boolean fields require exact equality. Numeric fields use
`atol=2e-8` and `rtol=2e-8`. HiGHS message prose and iteration counts are
recorded by neither the economic result contract nor the comparison because
they describe an execution path rather than a fitted result.

Both arms must also independently satisfy a completeness gate: every expected
trajectory must be optimal and every score, target, peer, dual, and carry-over
certificate must be valid. Identical failures do not count as equivalence
success.

## Evidence identity and timing interpretation

The JSON record reuses the release runner's canonical
`deapack-source-tree-sha256-v1` ledger and adds this experiment script and this
specification. It verifies the ledger before execution, verifies that the
runtime import resolves to `src/deapack`, and hashes the same scope again after
the final arm. A start-to-finish change fails the experiment.

Each arm runs once in a fresh process with common numerical thread variables
set to one. Worker elapsed time, parent-observed wall time, and sampled process
RSS are exploratory and order-sensitive. They are not a speed claim, a stable
performance baseline, or evidence for switching the default. A performance
decision would require randomized arm order, warm-up policy, repetitions, and
like-for-like retained reports on controlled hardware.

## Frozen command

From the repository root:

```bash
python benchmarks/experiments/dynamic_sbm_presolve_ab.py --format json
```

The text form is intended for review:

```bash
python benchmarks/experiments/dynamic_sbm_presolve_ab.py --format text
```

## Observed result

The 2026-08-03 small-matrix run closed every per-arm completeness gate: all
expected trajectories were optimal and every score, target, peer, dual, and
carry-over certificate was valid under both settings. Source identity and the
start-to-finish ledger check also passed.

Only the six oracle cases were equivalent across every compared result field.
All six realistic cases and all six extreme-scale cases diverged:

- realistic input-oriented cases selected different non-objective output/free
  carry-over adjustments, targets, and peer plans while preserving the
  headline score;
- realistic output and non-oriented cases exposed alternative optimal peer
  plans; and
- extreme-scale cases additionally produced materially different published
  original-unit residual values, even though both arms passed the package's
  normalized publication certificates.

The experiment therefore failed the equivalence gate. The decision is
`no_default_change_due_to_observed_divergence`: retain the existing
`presolve=True` public/default behavior, do not advertise `presolve=False` as
an equivalent route, and make no speed or memory claim from the single-pass
observations.
