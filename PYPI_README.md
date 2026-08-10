# DEAPack

DEAPack is an open-source Python framework for data envelopment analysis
(DEA), efficiency measurement, productivity analysis, and environmental
performance.

It is designed for researchers, students, and analysts who want broad method
coverage without writing a separate optimization program for every analysis.
A consistent data, model, and result interface connects classical DEA with
economic, environmental, network, dynamic, and productivity methods.

## Why DEAPack?

- Prepare validated data once and use a consistent estimator workflow.
- Inspect named score, target, slack, peer, component, diagnostic, and status
  tables.
- Move between closely related analysis families without changing packages.
- Create plots, reports, and reproducibility bundles from fitted results.
- Start with documented presets and teaching datasets while keeping model
  assumptions visible.

## Installation

DEAPack `2.0.1` supports Python 3.10 through 3.13.

```bash
python -m pip install "DEAPack==2.0.1"
```

NumPy, pandas, and SciPy are the required runtime dependencies. Install
`DEAPack[viz]` for optional Matplotlib result views.

## Quick start

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
print(result.summary())
print(result.peers("E"))
```

This estimates an input-oriented variable-returns-to-scale frontier. The same
result object provides targets, slacks, peer intensities, diagnostics,
reporting, and visualization when those outputs are available for the chosen
method.

## Coverage

DEAPack includes:

- classical radial and non-radial DEA;
- productivity indexes and scale analysis;
- cost, revenue, profit, and allocative-efficiency analysis;
- undesirable-output and environmental technologies;
- network, dynamic, dynamic-network, panel, and metafrontier models; and
- super-efficiency, cross-efficiency, diagnostics, reporting, and
  visualization.

The installed method catalog is the authoritative inventory of executable
methods. Planned or source-incomplete methods are not exposed as provisional
estimators.

## Documentation

- [Package Documentation](https://deapack.readthedocs.io/)
- [Installation guide](https://github.com/daopingw/DEAPack/blob/main/docs/getting-started/installation.md)
- [Quick start](https://github.com/daopingw/DEAPack/blob/main/docs/getting-started/quickstart.md)
- [Method catalog](https://github.com/daopingw/DEAPack/blob/main/docs/user-guide/method-catalog.md)
- [API reference](https://github.com/daopingw/DEAPack/blob/main/docs/api/index.md)
- [Migration from 0.1.x](https://github.com/daopingw/DEAPack/blob/main/docs/getting-started/migration.md)

DEAPack 2.x is not a drop-in replacement for historical `import DEAPack` or
ProdPack scripts; use the migration guide when updating an older project.

## Citation and licensing

Use the repository's
[`CITATION.cff`](https://github.com/daopingw/DEAPack/blob/main/CITATION.cff)
and record the exact version used. Research using a particular DEA method
should also cite its defining literature, linked from the corresponding
Documentation page.

The software is licensed under `GPL-3.0-only`. Documentation and bundled data
have their own recorded terms, and third-party data retain their upstream
licenses. See the repository's
[component-license map](https://github.com/daopingw/DEAPack/blob/main/COMPONENT_LICENSES.md)
and
[dataset-license map](https://github.com/daopingw/DEAPack/blob/main/DATA_LICENSES.md)
for precise boundaries.
