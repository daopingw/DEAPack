# DEAPack Documentation

DEAPack is a composable Python toolkit for DEA-based efficiency, productivity,
and environmental-performance analysis.

This site is the complete package reference. The
[companion Handbook](https://github.com/daopingw/DEAPack/blob/main/book/index.md)
explains theory, model choice, interpretation, and research workflow; this
Documentation focuses on installation, precise behavior, APIs, diagnostics,
and extension. The Handbook has its own publication and versioning route.

```{note}
DEAPack 2.0.0 is the first stable 2.x release. It is not a drop-in replacement
for DEAPack 0.1.x; start with the installation and migration guides if you are
upgrading an existing project.
```

```{toctree}
:hidden:
:maxdepth: 3

getting-started/index
user-guide/index
reference/index
api/index
developer/index
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

## Project lifecycle

Contributors and research users can review the
[contribution guide](https://github.com/daopingw/DEAPack/blob/main/CONTRIBUTING.md),
[changelog](https://github.com/daopingw/DEAPack/blob/main/CHANGELOG.md), and
{doc}`developer/versioning` policy directly. Citation guidance is in
{doc}`user-guide/citing`; publication operations are reviewed separately from
the public Documentation source.
