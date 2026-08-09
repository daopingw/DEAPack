# DEAPack 2.0 architecture

## 0. Greenfield rule

DEAPack 2.0 is a greenfield redesign, not an incremental extension of the
0.1.x class hierarchy. The existing DEAPack and ProdPack repositories are
inputs to the redesign: they preserve useful ideas, examples, public names,
and historical behavior that may deserve migration support. They do not
constrain the new domain model, solver kernel, result schema, package layout,
or method coverage.

In particular:

- the existing `DDF -> DEA -> CCR/BBC` inheritance chain is not retained as
  the organizing architecture;
- productivity is not a thin subclass around three lists of distances;
- undesirable-output support is not represented by one universal equality;
- reference-set selection is not duplicated inside each model class;
- pandas row loops and PuLP expression construction are not carried into the
  numerical kernel;
- backwards compatibility lives at an adapter boundary and can be removed
  independently of the new implementation.

Any reused code must pass the same theoretical, numerical, API, and
performance review as newly written code.

The source-level migration findings and the exact boundary between retained
ideas and rejected behavior are recorded in `specs/LEGACY_AUDIT.md`.

## 1. Design principles

1. **Composition over model-name classes.** Decision context, production
   graph, data roles, technology, frontier estimator, reference policy,
   performance criterion, valuation, evaluation protocol, analysis, and
   uncertainty are independent specifications.
2. **A stable zero-configuration default.** A user installing the base package
   can solve ordinary models without locating an external solver executable.
3. **Matrix APIs in the numerical core.** pandas is accepted at the boundary,
   but per-DMU constraint construction never loops through DataFrame cells.
4. **Results are first-class.** Solver status, native values, slacks, targets,
   peers, intensities, duals, residuals, and metadata survive the solve.
5. **Assumptions are data.** RTS, disposability, direction, normalization,
   reference periods, and tolerances are stored in immutable result metadata.
6. **Correctness before convenience.** No silent shifts, fallback models,
   dropped DMUs, or score transformations.
7. **Optional complexity.** Interactive plots, maps, commercial solvers, and
   advanced uncertainty methods are extras, not base-install requirements.

## 2. Layered system

```text
User data / formula-like selection
                |
                v
        Data validation layer
                |
                v
  Production graph + data-role compiler
                |
                v
 Technology + estimator + reference compiler
                |
                v
 Envelopment/multiplier task compiler
      + valuation/protocol compiler
                |
                v
       Solver-neutral LP task batch
                |
                v
     Solver backend (HiGHS default)
                |
                v
         Unified DEAResult object
          /          |          \
   analysis      visualization   reporting
```

The book and documentation operate at the public data, model, result,
analysis, visualization, and reporting layers. They do not depend on solver
internals.

## 3. Solver policy

The initial default backend will use `scipy.optimize.linprog(method="highs")`:

- HiGHS is a modern LP solver;
- SciPy wheels avoid a separately configured executable;
- the API accepts dense or sparse matrix constraints;
- statuses, residuals, and dual marginals can be retained;
- behavior is consistent across supported desktop platforms.

The backend interface remains solver-neutral. Later optional backends may use
`highspy` directly for repeated-model/basis features or connect to commercial
solvers. Package correctness must never depend on an optional backend.

`LPSolution` therefore carries backend-neutral row marginals and, when the
variable domain requires them, lower- and upper-bound marginals. A model that
publishes a certificate-gated optimum passes the returned candidate through
the shared LP postsolve certificate: primal rows, bounds, the reported
objective, dual signs, KKT stationarity, complementarity, and strong duality
are recomputed independently of the backend status label. Model-specific
account reconstruction is a second gate where a transformed score, network
flow, or dynamic trajectory must be recovered. Public `solver_status` is a
semantic status: an `optimal` backend claim rejected by either certificate is
reported as `numerical_error`. `backend_solver_status` and
`raw_solver_status` preserve the backend claim for audit. An unavailable
certificate instead sets `score_valid=False` and withholds the affected score
and semantic result tables. An optional backend that cannot supply the marginals needed by a
particular variable domain can still implement the protocol, but it cannot
publish that certificate-gated result as valid.

Multi-phase estimators certify and release each economic claim at its own
boundary. In the shared environmental DDF kernel, phase one identifies the
native directional distance and phase two only selects a row-scaled slack
completion. A certified phase-one score remains valid if the optional completion
fails, but no peers, targets, or slack accounts from that failed completion are
released. Cleaned projection accounts are reconstructed before targets are
published. Peer reporting is then certified separately after applying the
display-only `peer_tolerance`; `peer_valid=False` may therefore withhold a peer
table without invalidating a certified score or projection. Separate
`score_valid`, `completion_valid`, `target_valid`, `link_valid`,
`carryover_valid`, `peer_valid`, and `dual_valid` fields are used whenever a
model exposes those accounts. They keep system performance, operating plans,
internal continuity, sparse peer displays, and dual reports from laundering
one another. Every postsolve certificate reports zero additional optimization
calls unless a separately named refinement phase was actually requested.

PuLP remains relevant only to the legacy compatibility layer during migration.
Its expression-per-constraint construction and external CBC invocation are not
the DEAPack 2.0 performance baseline.

Integer and genuinely discrete DEA leaves use a separate solver-neutral MILP
task and capability check. The zero-configuration first backend should use
`scipy.optimize.milp`, which reaches the bundled HiGHS integer solver through
the same base SciPy dependency. A continuous LP result is never rounded and
relabeled integer-efficient. Optional commercial backends may accelerate
large discrete studies, but they do not define the model semantics.

## 4. Compilation and reuse

A `CompiledTechnology` owns solver-ready matrices for one production graph
and technology specification. An estimator compiler combines it with a
reference set and sampling construction, and the resulting template is reused
across every evaluated DMU sharing that structural fingerprint. A performance
criterion supplies the objective, bounds, and DMU-dependent right-hand side
without rebuilding the reference matrices. Valuation and evaluation protocols
add only their declared restrictions or secondary tasks.

Direction generation is a named policy boundary. A resolved `DirectionSpec`
retains the variable alignment, units or relative-rate semantics,
normalization rule, zero-component policy, and provenance as elicited,
authorized, literature-prescribed, or analyst-defined. Exogenous,
observation-scaled, range/ideal, and value-optimized directions may share
matrix blocks, but an endogenous price-conditioned direction also changes the
valuation/evaluation fingerprint. No compiler silently normalizes a direction
whose scale has economic meaning.

Governance is compiled under the evaluation protocol, not into
`NetworkSpec`. A future
`GovernanceSpec(players, authority, objectives, move_order, information,
solution_concept)` can place centralized, leader--follower,
non-cooperative, or bargaining decisions on the same physical process graph.
This separation prevents an identical link layout from being mistaken for an
identical optimization problem.

Envelopment and multiplier forms are first-class task compilers over the same
study specification. The multiplier compiler is required for assurance
regions, virtual-share restrictions, cross-efficiency, common weights, and
relational network recipes; these methods must not each grow an unrelated
one-off LP builder.

Panel reference builders return stable groups of row positions keyed by
period labels. Cross-period tasks match on `dmu_id`; periods need only be
ordered, not integer or consecutive.

`ReferencePlan` interns distinct immutable row arrays and assigns them compact
integer set IDs. Model caches use `set_id_for(observation)` and
`rows_for(observation)`; they never rebuild a Python tuple containing every
reference-row integer inside the per-observation loop.

The core task representation contains arrays and sparse matrices only. It does
not contain pandas objects, closures, or model-specific Python constraint
objects, which keeps it serializable for parallel execution.

Tone's public input-, output-, and non-oriented SBM presets are one example of
controlled reuse. They share compiled technology/reference blocks, balance
rows, reference-plan caching, and the sparse SBM task builder. Orientation
still changes the normalized objective and result guarantee, so each fit
retains its own canonical method ID rather than being represented as an
output-format switch. The shared compiler fails closed outside the standard
strictly positive input/output domain; zero- and signed-data extensions do not
enter through preprocessing.

Network compilation is layered rather than inherited from the first named
model:

```text
NetworkSpec
    graph declarations and observed variable roles
CompiledNetworkLayout
    stable node/link indices, incidence, topology, and role slices
NetworkTechnologySpec
    process RTS, intensity groups, link control, balance, and disposition
Measure compiler
    relational, additive, network SBM, directional, or economic task
```

The public graph layer now has both a closed two-stage convenience
specification and a measure-neutral `CompiledNetworkLayout`. The latter
canonicalizes open acyclic series, branching, and skip-link declarations
without choosing a measure, RTS rule, or solver formulation.
`CookZhuBiYangAdditiveDEA` is the first public measure compiled over that
general layout. Cycles, shared resource pools, transformed links, and
node-specific scale assumptions remain outside its checked domain.

`EnvironmentalNetworkSpec` is a source-neutral semantic overlay on the same
process graph. It partitions quantities into input, desirable-output,
undesirable-output, and ordinary-intermediate economic product accounts while
retaining producer/recipient incidence for every internal flow.
`EnvironmentalNetworkData` reuses the immutable `NetworkData` quantity store,
so adding environmental meaning does not duplicate an $n\times v$ matrix.
The Kalhor--Kazemi Matin compiler consumes that overlay to build its corrected
activity-specific $\alpha/\beta$ technology. This does not make those
accounts, weak disposal, or its input-radial score defaults of unrelated
network models.

Kao--Hwang relational and Chen--Cook--Li--Zhu additive models still use
separate measure compilers even where their CRS reference inequalities share
coefficients. Their objectives, normalizations, process accounts, and primal
link projections are not a common economic mechanism. The Cook general
additive compiler does share the Chen CRS primary system programme on the
matched closed two-stage graph; this conditional reduction does not transfer
Chen's VRS intercepts, secondary attribution rules, or Lim--Zhu projection to
an open network.

Graph fingerprints are semantic: reordering process declarations, link
declarations, or named variables does not change the digest. Array layout
order remains an internal compiler concern and cannot alter fitted results.

### 4.1 Large-sample execution policy

Large samples do not justify changing the estimand without saying so. The
exact baseline therefore follows a staged performance policy:

1. canonicalize and scale numeric arrays once;
2. compile each distinct technology/reference structure once into sparse CSC
   blocks;
3. update only the assessed observation's objective and right-hand-side
   coefficients;
4. solve one explicitly counted primary task per assessed unit, plus only the
   secondary tasks requested by a named protocol; and
5. benchmark compilation time, solve time, matrix shape, nonzero count,
   residuals, and result-materialization cost separately.

An optional direct-HiGHS backend may later reuse bases or solver models, and a
process-safe task batch may later evaluate independent units in parallel.
Neither optimization is allowed to change tolerances, peer membership, or
alternate-optimum policy relative to the zero-configuration SciPy baseline.
Nested solver threading and outer parallelism must be coordinated rather than
enabled simultaneously by default.

Screening and decomposition require stronger safeguards. Dominance screening,
column generation, or another exact reduction is enabled only for model
families whose RTS, disposability, graph, and objective admit a proved safe
rule. Subsampling, approximate peer search, or learned candidate selection
changes the estimator or introduces an approximation; it must receive a
separate method/protocol record, error diagnostics, and reproducibility
contract rather than a generic `fast=True` switch.

Long-form result tables can themselves dominate memory when the number of
evaluated-reference pairs is large. The architecture therefore reserves a
future result-materialization policy such as `summary`, `standard`, or
`full`. A reduced policy may omit optional peer, dual, or target rows, but it
must record every omission in metadata and may not weaken solver diagnostics
or silently change the fitted programme. Until a model implements that
contract, its documentation and benchmarks must include the cost of producing
the complete public result.

## 5. Public result contract

`DEAResult` is a tidy, immutable-at-the-boundary result with at least:

```text
summary             one row per evaluated DMU and model task
slacks              long table: dmu, variable role, variable, slack
targets             long table: dmu, variable role, variable, observed, target
intensities         long table: evaluated dmu, reference dmu, lambda
duals               long table: dmu, constraint/variable, marginal
components          long table: system/process/component score, bounds, and
                    aggregation-weight origin
multipliers         long table: fitted multiplier account and contribution
links               long table: internal observed quantity, source/target
                    process projections, disposition, and balance residual
diagnostics         status, message, iterations, primal/dual residuals
metadata            technology, measure, reference, tolerance, versions
```

Required `summary` fields include:

```text
dmu_id, period, score, efficiency, distance, is_efficient,
solver_status, model_family
```

`is_efficient` is a Pareto--Koopmans claim only when the fitted leaf and its
declared target-completion protocol certify it. Measure-specific fields such
as `is_radially_efficient` or `is_directionally_efficient` retain the weaker
native statement. If slack completion is skipped, incompatible, or
unsuccessful, `is_efficient` is nullable rather than copied from a best radial
or directional score. Future network and dynamic results apply the same
distinction to the jointly feasible system and to any source-supported
component statuses.

For oriented SBM, `is_sbm_efficient` records only the optimized side. A score
of one from the input leaf does not certify the output side, and a score of
one from the output leaf does not certify the input side; generic
`is_efficient` therefore remains nullable. Every target row records
`solver_selected_primary_optimum`. In particular, a target on the
non-objective side is a feasible solver selection, not a unique recommendation
or a completed Pareto--Koopmans target. The non-oriented Table 2 oracle and
the absence of located published numerical oracles for the two oriented
leaves are validation metadata rather than runtime behavior.

Fields not meaningful for a model are nullable and accompanied by metadata;
they are not populated with invented zeroes. Output order follows input order,
while identifiers provide the authoritative alignment.

Convenience methods may include:

```python
result.summary()
result.peers(dmu_id)
result.targets_for(dmu_id)
result.components_for(dmu_id)
result.links_for(dmu_id)
result.plot(kind="performance", metric="efficiency")
result.plot(kind="frontier")
result.plot(kind="trajectory", dmu_id=dmu_id, variable=carryover)
result.report(kind="brief")
```

Plotting and reporting functions consume only this public contract. The
quantity-based `frontier` view is not inferred from a score: it requires a
one-input/one-output CRS or VRS `static.radial` result with certified
slack-completed targets and active peers confined to the displayed
cross-section. Multidimensional or cross-period results fail that view rather
than being compressed into a picture that no longer represents the fitted
technology. The Dynamic-SBM `trajectory` view likewise consumes certified
targets, slacks, period components, links, diagnostics, fitted period order,
and numerical tolerance. It plots one carry-over in its original unit and
checks outgoing-to-inherited continuity; it never manufactures a path from
repeated static scores or a generic panel.

## 6. Proposed package layout

```text
src/deapack/
    __init__.py
    data.py
    enums.py
    exceptions.py
    technology/
        base.py
        convex.py
        environmental.py
        reference.py
    estimators/
        full.py
        partial.py
        conditional.py
    structure/
        graph.py
        network.py
        dynamic.py
    compilers/
        envelopment.py
        multiplier.py
        mixed_integer.py
        network_blocks.py
        dynamic_blocks.py
    measures/
        radial.py
        directional.py
        additive.py
        russell.py
        sbm.py
        economic.py
    valuation/
        restrictions.py
        preferences.py
    evaluation/
        protocols.py
        ranking.py
    solvers/
        base.py
        scipy_highs.py
    analysis/
        returns_to_scale.py
        targets.py
        productivity.py
        shadow_prices.py
    inference/
        diagnostics.py
        bootstrap.py
        tests.py
    results.py
    visualization/
    reporting/
    datasets/
```

This is a dependency direction, not a requirement to expose every internal
module as public API.

## 7. Public API style

The public API favors a small number of discoverable specifications:

```python
from deapack import DEAData, RadialDEA

data = DEAData.from_frame(
    frame,
    dmu="region",
    period="year",
    inputs=["capital", "labor", "energy"],
    outputs=["gdp"],
    bad_outputs=["co2"],
)

result = RadialDEA(
    orientation="input",
    returns_to_scale="vrs",
).fit(data)
```

Historical names may be optional discovery constructors:

```python
CCR(orientation="input")  # RadialDEA(..., returns_to_scale="crs")
BCC(orientation="input")  # RadialDEA(..., returns_to_scale="vrs")
```

The complete classic recipes are explicit presets:

```python
CCRInput()   # CRS + input orientation + theta + DEAPack slack completion
CCROutput()  # CRS + output orientation + phi + DEAPack slack completion
BCCInput()   # VRS + input orientation + theta + DEAPack slack completion
BCCOutput()  # VRS + output orientation + phi + DEAPack slack completion
```

Aliases and presets use the same numerical engine. The four presets retain
`method_id="static.radial"` and emit a `preset_id`; a generic call with
numerically matching arguments does not infer that the caller selected a
historical preset. Their `compute_slacks=True` row-scaled lexicographic
target selector is a declared DEAPack policy, not a target-selection claim
attributed uniquely to the foundational papers.

Every fitted result stores:

```text
registry_schema_version
method_id
specialization_id  # optional partial parameter specialization
preset_id          # optional complete validated recipe
expanded_spec
```

`method_id` is canonical. `specialization_id` is present when a constructor
such as CCR fixes a partial parameter composition. `preset_id` is reserved
for a complete validated recipe. A direct Python symbol alias cannot reliably
reveal which spelling the caller typed.

## 8. Compatibility

DEAPack 2.0 uses the project/distribution name `DEAPack` and canonical import
name `deapack`. A temporary top-level `DEAPack` package may forward supported
legacy imports and emit deprecation warnings.

Compatibility never preserves a mathematically incorrect result silently. A
legacy behavior with changed semantics receives a migration note and an
explicit compatibility option if reproducibility requires it.

## 9. Documentation relationship

The repository contains two Sphinx projects:

- `book/`: conceptual narrative and selected reproducible workflows;
- `docs/`: installation, how-to guides, complete model/API reference,
  visualization gallery, and developer documentation.

Both projects use MyST Markdown and gettext translations. Shared files in
`specs/`, shared bibliography data, terminology, and tested examples are
included rather than copied.

The book is versioned by edition. Package documentation is versioned by the
software release. A book citation and a software citation remain separate.
