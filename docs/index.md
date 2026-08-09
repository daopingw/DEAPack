# DEAPack Documentation

DEAPack is a composable Python toolkit for DEA-based efficiency, productivity,
and environmental-performance analysis.

This site is the complete package reference. The
[companion Handbook](https://github.com/daopingw/DEAPack/blob/main/book/index.md)
explains theory, model choice, interpretation, and research workflow; this
Documentation focuses on installation, precise behavior, APIs, diagnostics,
and extension. The link opens the maintained English manuscript source while
public Read the Docs deployment is still being verified.

```{warning}
Version 2.0 is under active development and is not yet a drop-in replacement
for DEAPack 0.1.x.
```

## Choose a mainstream starting point

Start from the managerial or economic question, then refine technology,
reference population, data domain, and validity requirements in the linked
page. Historical acronyms that share a mechanism do not need separate engines.

| Question | Mainstream family | First package entry point |
|---|---|---|
| How much could resources fall, or services rise, proportionally? | {doc}`models/radial` | `BCCInput`, `BCCOutput`, `CCRInput`, or `CCROutput` |
| Which individual input excesses and output shortfalls remain? | {doc}`models/sbm` | `SBM`, `InputSBM`, or `OutputSBM` |
| What improvement is feasible along an economically chosen direction? | {doc}`models/directional` | `DirectionalDistanceDEA` |
| How should undesirable outputs change the production account? | {doc}`models/environmental-directional` and {doc}`models/undesirable-sbm` | Choose a named disposal technology and DDF or undesirable-output SBM |
| How does observed price information change the performance question? | {doc}`api/economics` | `CostEfficiency`, `RevenueEfficiency`, `ProfitEfficiency`, or a documented decomposition |
| Which units remain favourable when self-selected valuations must respect a declared policy cone? | {doc}`models/polyhedral-cone-ratio` | `ConeRestrictionProvenance` and `PolyhedralConeRatioDEA` |
| How did performance and best-practice opportunity change over time? | {doc}`analysis/malmquist`, {doc}`analysis/luenberger`, or {doc}`analysis/hicks-moorsteen` | Select the productivity identity before selecting its reference policy |
| Where do performance gaps arise inside a multi-process organization? | {doc}`api/network` | Declare a production graph, then choose a system or process account |
| How do carry-overs connect operating decisions over time? | {doc}`api/dynamic` | `DynamicData`, a carry-over specification, and `DynamicSBM` |
| How should organizations be compared across declared operating environments? | {doc}`analysis/metafrontier` | `RadialMetafrontierDEA` |

The {doc}`user-guide/method-catalog` gives the complete installed inventory
and separates Handbook mother-model routes from source-qualified
Documentation-only leaves.

```{toctree}
:maxdepth: 2
:caption: Getting started

getting-started/installation
getting-started/quickstart
getting-started/migration
```

```{toctree}
:maxdepth: 2
:caption: User guide

user-guide/data
user-guide/method-catalog
user-guide/reference-sets
user-guide/results
user-guide/visualization
user-guide/reporting
user-guide/datasets
user-guide/citing
```

```{toctree}
:maxdepth: 2
:caption: Model and analysis reference

models/radial
models/fdh
models/fch
models/frh
models/cost
models/revenue
models/profit
models/nerlovian
models/profitability
models/generalized-distance
models/multiplicative
models/polyhedral-cone-ratio
models/additive
models/bam
models/sbm
models/ebm
models/directional
models/range-directional
models/environmental-directional
models/zhou-ang-wang-non-chp
models/undesirable-sbm
models/by-production
models/by-production-fgl
models/material-balance
evaluation/cross-efficiency
evaluation/super-efficiency
evaluation/directional-super-efficiency
evaluation/super-sbm
analysis/metafrontier
analysis/reference-frequency
models/fare-grosskopf-network-radial
models/kao-hwang-network
models/chen-additive-network
models/cook-general-additive-network
models/tone-tsutsui-network-sbm
models/kalhor-kazemi-matin-environmental-network
network/sequential
panel/multiperiod-aggregative
models/tone-tsutsui-dynamic-sbm
models/tone-tsutsui-dynamic-network-sbm
analysis/scale-efficiency
analysis/local-returns-to-scale
analysis/scale-elasticity
analysis/relative-directional-scale-elasticity
analysis/mpss
analysis/physical-capacity
analysis/allocative-decomposition
analysis/revenue-allocative-decomposition
analysis/profitability-decomposition
```

## Productivity documentation map

The companion Handbook develops four productivity routes: adjacent-period
Malmquist, Luenberger, Malmquist--Luenberger with undesirable outputs, and
Hicks--Moorsteen. The package Documentation also records reference-policy
companions and specialized research leaves so an implemented public method is
discoverable without turning every technical variation into another Handbook
route.

The FGNZ constructor is the source-qualified preset inside the retained
Malmquist route; it is not a fifth route. Enhanced FGNZ and Ray--Desli are
specialized sections of the [Malmquist package reference](analysis/malmquist.md).
Their availability in Python likewise does not promote them into the Handbook
progression. The exact machine-readable placement of every productivity entry
appears in the [method catalog](user-guide/method-catalog.md).

```{toctree}
:maxdepth: 2
:caption: Productivity — four Handbook routes

analysis/malmquist
analysis/luenberger
analysis/malmquist-luenberger
analysis/hicks-moorsteen
```

```{toctree}
:maxdepth: 2
:caption: Productivity — supporting and sensitivity companions

analysis/global-malmquist
analysis/global-malmquist-luenberger
```

```{toctree}
:maxdepth: 2
:caption: Productivity — specialized Documentation leaves

analysis/biennial-malmquist
analysis/apz-malmquist-luenberger
```

```{toctree}
:maxdepth: 2
:caption: API

api/index
```

```{toctree}
:maxdepth: 2
:caption: Development

developer/architecture
developer/contributing
developer/extending
developer/performance
developer/versioning
developer/hosting
developer/translations
```

```{toctree}
:maxdepth: 1
:caption: Legal and notices

legal/component-licensing
legal/third-party-notices
```

## Project lifecycle

Contributors and research users can review the
[contribution guide](https://github.com/daopingw/DEAPack/blob/main/CONTRIBUTING.md),
[changelog](https://github.com/daopingw/DEAPack/blob/main/CHANGELOG.md), and
{doc}`developer/versioning` policy directly. Citation guidance is in
{doc}`user-guide/citing`; publication operations are reviewed separately from
the public Documentation source.
