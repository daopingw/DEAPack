# DEAPack

[![PyPI](https://img.shields.io/pypi/v/DEAPack.svg)](https://pypi.org/project/DEAPack/) [![Python 3.10–3.13](https://img.shields.io/badge/python-3.10--3.13-blue.svg)](pyproject.toml) [![Documentation](https://readthedocs.org/projects/deapack/badge/?version=latest)](https://deapack.readthedocs.io/) [![Tests](https://github.com/daopingw/DEAPack/actions/workflows/tests.yml/badge.svg)](https://github.com/daopingw/DEAPack/actions/workflows/tests.yml) [![License: GPL-3.0](https://img.shields.io/badge/license-GPL--3.0-blue.svg)](LICENSE)

DEAPack is an open-source Python framework for data envelopment analysis
(DEA), efficiency measurement, productivity analysis, and environmental
performance.

It is designed for researchers, students, and analysts who want to compare the
performance of organizations without writing a new optimization model for
every method. A consistent data, model, and result interface connects
classical DEA with closely related economic, environmental, network, dynamic,
and productivity analyses.

[Documentation](https://deapack.readthedocs.io/) ·
[Installation](docs/getting-started/installation.md) ·
[Quick start](docs/getting-started/quickstart.md) ·
[Method catalog](docs/user-guide/method-catalog.md) ·
[API reference](docs/api/index.md)

## Why DEAPack?

DEA applications often combine several decisions: the production technology,
orientation, returns to scale, reference population, treatment of undesirable
outputs, and interpretation of the resulting targets and peers. DEAPack keeps
those choices explicit while giving them a common Python workflow.

- **One familiar interface:** prepare `DEAData`, fit a model, then inspect a
  `DEAResult`.
- **Connected method coverage:** move from classical efficiency measurement to
  productivity, economic, environmental, network, dynamic, and
  heterogeneity analysis without changing packages.
- **Interpretable results:** work with named score, target, slack, peer,
  component, diagnostic, and status tables.
- **Research-ready outputs:** create plots, reports, and reproducibility
  bundles from the same fitted result.
- **Accessible starting points:** use documented presets and bundled teaching
  datasets while keeping the underlying assumptions visible.

## Install

DEAPack `2.0.1` supports Python 3.10 through 3.13.

```bash
python -m pip install "DEAPack==2.0.1"
```

Install optional visualization support with:

```bash
python -m pip install "DEAPack[viz]==2.0.1"
```

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

The example estimates an input-oriented variable-returns-to-scale frontier.
The same result object provides targets, slacks, peer intensities, diagnostics,
reporting, and visualization when those outputs are available for the chosen
method.

## What you can analyze

| Area | Examples |
|---|---|
| Classical DEA | CCR and BCC radial models, FDH, additive models, RAM, BAM, SBM, EBM, and directional-distance models |
| Productivity and scale | Malmquist-family indexes, Luenberger and Hicks--Moorsteen productivity, returns to scale, and scale elasticity |
| Economic performance | Cost, revenue, profit, allocative efficiency, profitability, and decompositions |
| Environmental performance | Undesirable outputs, weak disposal, by-production, material balance, and environmental productivity |
| Organizational structure | Network, dynamic, dynamic-network, panel, and radial metafrontier models |
| Evaluation and communication | Super-efficiency, cross-efficiency, peer diagnostics, plots, reports, and audit bundles |

The installed [method catalog](docs/user-guide/method-catalog.md) is the
authoritative inventory of executable methods. Planned or source-incomplete
methods are not exposed as provisional estimators.

## Find the right documentation

- **New to DEAPack?** Follow the [installation guide](docs/getting-started/installation.md)
  and [quick start](docs/getting-started/quickstart.md).
- **Choosing a method?** Browse the [models and analysis guide](docs/reference/index.md)
  or search the [method catalog](docs/user-guide/method-catalog.md).
- **Working with data or results?** Use the [user guide](docs/user-guide/index.md).
- **Looking up an object?** Go directly to the [API reference](docs/api/index.md).
- **Upgrading old code?** Read the
  [0.1.x migration guide](docs/getting-started/migration.md); 2.x is not a
  drop-in replacement.

## Data and reproducibility

Bundled datasets have documented roles, provenance, redistribution status,
and attribution. See the [dataset guide](docs/user-guide/datasets.md) and
[dataset license map](DATA_LICENSES.md) before reusing them outside the
package.

DEAPack's implementation claims are linked to defining sources, analytical
checks, and independent numerical evidence where available. The maintained
[literature-review index](specs/reviews/INDEX.md) records that evidence; the
[method catalog](docs/user-guide/method-catalog.md) reports the verification
level of each public entry.

## Citation and licensing

Use [CITATION.cff](CITATION.cff) or [CITATION.md](CITATION.md) and record the
exact DEAPack version used. Research using a particular DEA method should also
cite its defining literature, linked from the corresponding Documentation
page.

The software is licensed under `GPL-3.0-only`. Project-owned Documentation
prose and bundled datasets have separate terms; third-party data retain their
recorded upstream terms. See [COMPONENT_LICENSES.md](COMPONENT_LICENSES.md),
[DATA_LICENSES.md](DATA_LICENSES.md), and [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)
for the exact boundaries.

## Contributing

Questions, reproducible bug reports, model proposals, documentation
improvements, and data-provenance contributions are welcome. Start with the
[contribution guide](CONTRIBUTING.md).

For a source checkout:

```bash
python -m pip install -e '.[test,docs,viz]'
make test PYTHON=python
```

Release history is in [CHANGELOG.md](CHANGELOG.md).
