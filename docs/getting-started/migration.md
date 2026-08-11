# Migrating from DEAPack 0.1.x and ProdPack

DEAPack 2.x is a redesign, not a compatibility release. The earlier DEAPack
and ProdPack prototypes supplied useful research questions and reference-set
ideas, but their mutable objects and generic distance interface are not the
2.x numerical contract. There is no automatic converter and no promise that
an old script can be made correct by renaming imports.

The historical uppercase runtime is available through the repository's Git
history but is not retained in the current 2.x source tree. The 2.x build
configuration packages only `src/deapack`, so a built wheel does not provide
`import DEAPack` or forwarding wrappers. Manual migration to the lowercase
`deapack` API is required.

Migration should preserve the **empirical question** before it preserves the
old call shape. Record the inputs, desirable and undesirable outputs, DMU and
period keys, returns-to-scale assumption, comparison population, orientation
or direction, and the meaning of every reported component. Then select the
2.x model whose maintained technology and performance account express those
choices.

## The shortest classical migration

An old radial workflow passed separate `DMUs`, `x_vars`, and `y_vars` objects
to `CCR` or the misspelled `BBC`, called `solve()`, and then read mutable
attributes. In 2.x, declare roles once, fit a model, and retain the returned
result:

```python
from deapack import (
    BCCInput,
    DEAData,
    ReferenceSpec,
    dataset_info,
    load_dataset,
)

dataset_name = "multiperiod_trajectory_contrast"
frame = load_dataset(dataset_name)
data = DEAData.from_frame(frame, **dataset_info(dataset_name).roles)
model = BCCInput(
    reference=ReferenceSpec(kind="contemporaneous"),
)
result = model.fit(data)

scores = result.summary()
targets = result.targets
peers = result.intensities
diagnostics = result.diagnostics
```

`BCCInput` is the complete input-oriented VRS recipe, including DEAPack's
declared slack-completion policy. Use `CCRInput`, `CCROutput`, or `BCCOutput`
for the other classical recipes. Use `CCR` or `BCC` when orientation or slack
completion must remain configurable. The historical spelling `BBC` has no
2.x alias: replace it with `BCC` and review the intended orientation.

## Concept map

| Prototype concept | 2.x destination | Migration decision |
|---|---|---|
| `DMUs`, `x_vars`, `y_vars`, `b_vars`, `time` | immutable {class}`deapack.DEAData` | Declare column roles, unique DMU/period keys, and `period_order` when natural sorting is not the study order. |
| `return_to_scale="CRS"` or `"VRS"` | a model constructor or {class}`deapack.TechnologySpec` | Choose RTS as a production assumption; do not infer it from a model nickname. |
| `CCR` | `CCRInput`, `CCROutput`, or configurable `CCR` | Make orientation and target-completion policy explicit. |
| `BBC` | `BCCInput`, `BCCOutput`, or configurable `BCC` | Correct the spelling and re-check the VRS interpretation. |
| `radial=True/False` | a radial, directional, additive, SBM, or other named criterion | A Boolean cannot identify which non-radial economic account was intended. |
| `g_x`, `g_y`, `g_b` DataFrames | named or numerical direction arguments on a directional model | 2.x direction magnitudes are nonnegative; the model defines contraction and expansion signs. |
| a generic bad-output equality | a named environmental technology | Select strong disposal, common-factor weak disposal, activity-specific weak disposal, by-production, or another source-qualified family; an equality alone is not universal weak disposability. |
| `ref_type` and `window` | {class}`deapack.ReferenceSpec` | Choose contemporaneous, global, sequential, window, biennial, or custom comparison observations independently of the measure. |
| `solve()` plus mutable `distance`/`efficiency` | `fit()` returning {class}`deapack.DEAResult` | Read named summary, target, peer, dual, component, and diagnostic tables; preserve solver and certification status. |
| `parallel=True` over PuLP objects | the compiled 2.x task path and default SciPy/HiGHS backend | Benchmark the complete study before adding outer parallelism; do not carry an old `n_jobs` value across automatically. |

The full provenance audit behind this map is maintained in the repository's
[legacy audit](https://github.com/daopingw/DEAPack/blob/main/specs/LEGACY_AUDIT.md).

## Reference populations are specifications, not model names

The old `ref_type` strings now become a reusable specification:

```python
from deapack import ReferenceSpec

contemporaneous = ReferenceSpec(kind="contemporaneous")
global_reference = ReferenceSpec(kind="global")
sequential = ReferenceSpec(kind="sequential")
window = ReferenceSpec(kind="window", window_before=1, window_after=1)
biennial = ReferenceSpec(kind="biennial")
```

This mapping does not guarantee that two old and new scores estimate the same
quantity. The 2.x implementation matches panel rows by declared DMU and period
keys, uses an explicit period order, retains infeasible cross-period tasks,
and refuses one-sided substitutes for missing productivity components. Those
differences can correctly change results that depended on row position,
arithmetic such as `year - 1`, or silent fallback rules.

## ProdPack productivity workflows

`ProdNP(index_type=...)` does not have one universal replacement. A string
that selected a formula in the prototype is now a choice among separately
identified operators:

| Research question | Start with |
|---|---|
| Conventional adjacent-period Malmquist change | {class}`deapack.MalmquistProductivityIndex` |
| Additive Luenberger productivity change | {class}`deapack.LuenbergerProductivityIndicator` |
| Malmquist--Luenberger change with undesirable outputs | {class}`deapack.MalmquistLuenbergerProductivityIndex` |
| Hicks--Moorsteen total-factor productivity | {class}`deapack.HicksMoorsteenProductivityIndex` |
| A common global conventional reference | {class}`deapack.GlobalMalmquistProductivityIndex` |
| A common global undesirable-output reference | {class}`deapack.GlobalMalmquistLuenbergerProductivityIndex` |
| A two-period pooled conventional reference | {class}`deapack.BiennialMalmquistProductivityIndex` |

Before choosing, compare the component identity, native direction, reference
vintage, and cross-period feasibility rule in the corresponding analysis
page. Old `prod_ch`, `eff_ch`, and `te_ch` attributes should not be copied by
position into a new table. Join 2.x component rows by their DMU and period
identifiers and retain the component-validity diagnostics.

## Environmental migrations need a technology decision

The most consequential migration is an old DDF with undesirable outputs. New
work should not select `EnvironmentalDirectionalDistanceDEA(disposability=
"weak")`: that spelling is retained only as a deprecated compatibility
selector for the legacy bad-output equality, and it emits `FutureWarning`.
Choose a named environmental family after stating how undesirable outputs can
change and how they are jointly produced. The {doc}`../models/environmental-directional`,
{doc}`../models/undesirable-sbm`, {doc}`../models/by-production`, and
{doc}`../models/material-balance` pages separate those assumptions.

## Validate the migration

Treat a migrated study as a new empirical specification:

1. compare DMU and period keys, missing rows, column roles, units, and period
   order;
2. record `result.metadata["method_id"]`, any `preset_id`, the expanded
   specification, tolerances, and the installed package version;
3. compare only quantities with the same native definition—especially
   output expansion factors versus reciprocal efficiencies and distance
   values versus bounded displays;
4. inspect solver, score, target, peer, and decomposition validity separately;
5. explain any corrected reference population, score transformation,
   infeasibility rule, sign convention, or production assumption rather than
   recreating it with an unlabeled compatibility switch; and
6. archive the code, data provenance, result tables, and diagnostics used for
   the comparison.

If a historical number survives these checks under the same estimand, keep it
as a regression fixture. If it does not, document why the estimand or audit
contract changed; numerical equality is not the objective of migration.
