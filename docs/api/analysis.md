# Analyses

```{autoclass} deapack.RadialMetafrontierDEA
:members:
```

`MetafrontierDEA` is the concise exact alias for the canonical
`RadialMetafrontierDEA` class.

## Selected-plan peer diagnostics

```{autofunction} deapack.reference_frequency
```

```{autoclass} deapack.ReferenceFrequencyResult
:members:
```

Reference frequency counts certified reported peer edges strictly above the
source result's `peer_tolerance` in one solver-selected plan; it never sums
intensities across evaluated organizations and does not claim exact
mathematical support at or below that reporting threshold. The current release
is restricted to one global cross-section under a static black-box
continuous-convex full-DEA model. It fails closed if any evaluation lacks a
certified peer account and makes no all-optima, superiority, outlier, causal,
or inferential claim. See
{doc}`../analysis/reference-frequency` for the exact scope and interpretation.

```{autoclass} deapack.AllocativeDecomposition
:members:
```

```{autoclass} deapack.RevenueAllocativeDecomposition
:members:
```

```{autoclass} deapack.GDFProfitabilityDecomposition
:members:
```

`ProfitabilityDecomposition` is an exact alias for
`GDFProfitabilityDecomposition`.

```{autofunction} deapack.scale_efficiency
```

```{autofunction} deapack.local_returns_to_scale
```

```{autofunction} deapack.scale_elasticity
```

`local_returns_to_scale` and `scale_elasticity` first require a certified VRS
radial score, slack-completed projection, and target account. Each finite
Banker--Thrall support endpoint must then pass LP/KKT/dual and original-unit
economic-account checks; an infinite endpoint is released only with an
independently verified recession ray. The interval, RTS classification, and
elasticity transformations are separate atomic claims. Inspect
`support_interval_valid`, `economic_classification_certified`,
`scale_elasticity_valid`, and `analysis_status` before interpretation. See
{doc}`../analysis/local-returns-to-scale` and
{doc}`../analysis/scale-elasticity` for the boundary semantics and the fixed
four-solve-per-organization ledger; certification adds no fifth solve.

```{autofunction} deapack.relative_directional_scale_elasticity
```

## Evidence-gated prototypes

MPSS and Färe--Grosskopf--Kokkelenberg physical capacity are non-public
development prototypes in this evidence version. Both are deferred to the next
version, so this API reference deliberately provides no callable entry point or
usage contract for either method. Their source audits will be recorded in the
[Banker MPSS protocol](https://github.com/daopingw/DEAPack/blob/main/specs/source_protocols/banker_1984_mpss.md)
and the
[FGK physical-capacity protocol](https://github.com/daopingw/DEAPack/blob/main/specs/source_protocols/fare_grosskopf_kokkelenberg_1989_capacity.md).

```{autoclass} deapack.MalmquistProductivityIndex
:members:
```

```{autoclass} deapack.FGNZMalmquistProductivityIndex
:members:
```

`FGNZMalmquist` is the short alias for the source-qualified,
output-oriented CRS preset.

```{autoclass} deapack.FGNZEnhancedMalmquistProductivityIndex
:members:
```

`FGNZEnhancedMalmquist` is the exact short alias for the source-qualified
six-task FGNZ pure-efficiency and scale-efficiency decomposition. It is a
distinct machine method, not a generic VRS preset.

```{autoclass} deapack.RayDesliMalmquistProductivityIndex
:members:
```

`RayDesliMalmquist` is the exact short alias for the source-qualified,
output-oriented Ray--Desli CRS--VRS decomposition. It is a distinct machine
method rather than an alias for a generic VRS Malmquist calculation.

```{autoclass} deapack.MalmquistDEA
:members:
```

The classic adjacent four-distance APIs expose transition-level
`score_valid` and `peer_valid` gates, role-level solver-neutral LP and
raw/published production-account diagnostics, and a complete multiplicative
account certificate. Certification reuses the cached distance solutions and
adds no solver call. See {doc}`../analysis/malmquist` for the release
boundary. These guarantees do not merge the separately registered enhanced
FGNZ or Ray--Desli task graphs into the core API, and they do not establish a
new release claim for an FGNZ preset.

```{autoclass} deapack.LuenbergerProductivityIndicator
:members:
```

```{autoclass} deapack.LuenbergerDEA
:members:
```

```{autoclass} deapack.GlobalMalmquistProductivityIndex
:members:
```

```{autoclass} deapack.GlobalMalmquistDEA
:members:
```

The classic full-horizon Global Malmquist APIs apply the same four-role LP,
economic-account, peer, and complete multiplicative release discipline to two
own-period and two global-reference appraisals. See
{doc}`../analysis/global-malmquist`. This statement does not extend to
biennial or environmental common-reference operators.

```{autoclass} deapack.BiennialMalmquistProductivityIndex
:members:
```

```{autoclass} deapack.BiennialMalmquistDEA
:members:
```

```{autoclass} deapack.MalmquistLuenbergerProductivityIndex
:members:
```

```{autoclass} deapack.MalmquistLuenbergerDEA
:members:
```

```{autoclass} deapack.APZMalmquistLuenbergerProductivityIndex
:members:
```

`APZMalmquistLuenbergerDEA` is the exact alias for the source-qualified APZ
capped-bad-output composition. It is not an alias for the classic CFG index.

```{autoclass} deapack.GlobalMalmquistLuenbergerProductivityIndex
:members:
```

```{autoclass} deapack.GlobalMalmquistLuenbergerDEA
:members:
```

```{autoclass} deapack.HicksMoorsteenProductivityIndex
:members:
```

`MoorsteenBjurekProductivityIndex`, `HicksMoorsteenDEA`, and
`MoorsteenBjurekDEA` are exact discoverability aliases for the same Bjurek
output-quantity/input-quantity construction.
