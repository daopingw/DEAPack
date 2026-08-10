# DEAPack Documentation

DEAPack is a Python framework for data envelopment analysis (DEA), efficiency
measurement, productivity analysis, and environmental performance.

It gives researchers, students, and analysts a consistent way to prepare data,
choose an appropriate model, fit it, and interpret the resulting scores,
targets, slacks, and peers. It is especially useful when a study extends
beyond classical DEA into economic, environmental, network, dynamic, or
productivity analysis.

```{note}
DEAPack 2.0.1 is the current stable release of the redesigned 2.x API. If you are
upgrading from DEAPack 0.1.x or ProdPack, begin with the
{doc}`getting-started/migration` guide.
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

## Start here

1. {doc}`getting-started/installation` — install DEAPack and optional extras.
2. {doc}`getting-started/quickstart` — fit a first model and inspect its result.
3. {doc}`user-guide/results` — understand scores, targets, peers, validity, and
   diagnostics before reporting them.

## Why DEAPack?

A DEA study involves more than selecting a model acronym. The production
technology, orientation, returns to scale, reference population, data roles,
and treatment of undesirable outputs all affect the question being answered.
DEAPack keeps those choices visible while providing a common workflow:

- prepare a validated `DEAData` object;
- fit a model through a consistent estimator interface;
- inspect named result tables instead of unpacking solver arrays; and
- create plots, reports, and reproducibility bundles from the fitted result.

You can therefore begin with a documented preset such as `BCCInput` and move
to more specialized analyses without abandoning the same data and result
conventions.

## A first model

```python
from deapack import BCCInput, DEAData, load_dataset

frame = load_dataset("frontier_1x1")
data = DEAData.from_frame(
    frame,
    dmu="dmu",
    inputs="input",
    outputs="output",
)

result = BCCInput().fit(data)
result.summary()
```

This fits an input-oriented variable-returns-to-scale frontier. Continue with
the {doc}`getting-started/quickstart` to inspect peers and targets, use your own
data, and visualize the result.

## What can I analyze?

| Area | Start with |
|---|---|
| Classical radial and non-radial DEA | {doc}`reference/core-models` |
| Productivity change and scale | {doc}`reference/productivity-analysis` and {doc}`reference/scale-capacity-decomposition` |
| Cost, revenue, profit, and allocative efficiency | {doc}`api/economics` |
| Undesirable outputs and environmental performance | {doc}`reference/environmental-models` |
| Network, dynamic, panel, and metafrontier structures | {doc}`reference/network-dynamic` and {doc}`analysis/metafrontier` |
| Super-efficiency, cross-efficiency, diagnostics, and communication | {doc}`reference/evaluation`, {doc}`user-guide/reporting`, and {doc}`user-guide/visualization` |

The {doc}`user-guide/method-catalog` is the authoritative inventory of methods
available in the installed release. It distinguishes principal families,
presets, and specialized methods without implying that planned work is already
executable.

## Documentation map

| Section | Use it for |
|---|---|
| {doc}`getting-started/index` | Installation, the first analysis, and migration from older releases |
| {doc}`user-guide/index` | Data preparation, model discovery, result interpretation, reporting, and datasets |
| {doc}`reference/index` | Concepts, assumptions, equations, and method-specific behavior |
| {doc}`api/index` | Public classes, functions, parameters, and return contracts |
| {doc}`developer/index` | Architecture, extension points, contribution, and versioning policies |

## Citation and contributions

Use {doc}`user-guide/citing` when reporting a DEAPack computation, and cite the
defining literature for the particular method used. Questions, reproducible
bug reports, model proposals, and Documentation improvements are welcome
through the project
[contribution guide](https://github.com/daopingw/DEAPack/blob/main/CONTRIBUTING.md).
