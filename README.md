# DEAPack

DEAPack is a Python toolkit for data envelopment analysis (DEA), efficiency,
productivity, environmental-performance, network, and dynamic analysis.

Version `2.0.0rc1` is the feature-frozen release candidate for the redesigned
2.x line. It is a pre-release, so small compatibility corrections may still be
made before the first stable release.

## What is included

- A composable numerical package built on NumPy, pandas, SciPy, and sparse
  HiGHS optimization.
- English package Documentation covering installation, models, analysis,
  reporting, visualization, and the public API.
- The bilingual English--Chinese Handbook *Data Envelopment Analysis:
  Efficiency, Productivity, and Environmental Performance with Python*.
- A method registry, source protocols, independent numerical oracles, and
  reproducible benchmark definitions.
- Thirty-three licensed teaching datasets with declared roles, provenance,
  teaching uses, and exact content fingerprints.

The full executable-method inventory is in the
[method catalog](docs/user-guide/method-catalog.md). Design boundaries and
mathematical conventions are recorded in [specs](specs/README.md).

## Installation

DEAPack supports Python 3.10 through 3.13.

For the current GitHub release candidate:

```bash
git clone https://github.com/daopingw/DEAPack.git
cd DEAPack
python -m venv .venv
source .venv/bin/activate
python -m pip install -e .
```

Install the visualization and development extras when needed:

```bash
python -m pip install -e '.[viz]'
python -m pip install -e '.[test,docs,viz]'
```

## Quick example

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

Results can also produce a self-contained management brief and a deterministic
audit bundle:

```python
result.report().save("bcc-result-brief.html")
result.export_bundle("bcc-result-audit.zip")
```

With the visualization extra installed:

```python
figure = result.plot(kind="frontier")
figure.savefig("bcc-frontier.svg", bbox_inches="tight")
```

## Main capabilities

DEAPack groups methods by the analytical question they answer rather than by
paper-specific class names.

- **Classical frontier models:** CCR/BCC radial DEA, FDH, FCH, FRH, additive
  DEA, RAM, BAM, SBM, EBM, directional and generalized-distance models.
- **Economic analysis:** cost, revenue, profit, allocative efficiency,
  Nerlovian efficiency, profitability, and decomposition.
- **Environmental analysis:** undesirable-output technologies, weak disposal,
  by-production, material balance, and environmental productivity.
- **Network and dynamic analysis:** relational, additive, radial, sequential,
  SBM, carry-over, and dynamic-network formulations.
- **Productivity and scale:** Malmquist-family indexes, Luenberger,
  Hicks--Moorsteen, metafrontier, local returns to scale, scale elasticity,
  MPSS, and reference-frequency analysis.
- **Evaluation and communication:** super-efficiency, cross-efficiency,
  target completion, peer diagnostics, publication tables, reports, bundles,
  and plots.

The metafrontier API uses
`RadialMetafrontierDEA` (concise exact alias `MetafrontierDEA`).

Some research families remain documented prototypes rather than public
estimators. Use `list_methods()` to inspect what is executable in the
installed version:

```python
from deapack import list_methods, method_info

print([item.method_id for item in list_methods()])
print(method_info("static.radial.fdh").api_symbols)
```

Nine maintained [literature reviews](specs/reviews/INDEX.md), currently
containing 148 evidence cards, connect defining sources, numerical oracles,
package implementations, and Handbook coverage.

## Teaching datasets

```python
from deapack import list_datasets, load_dataset

for info in list_datasets():
    print(info.name, info.teaching_uses)

frame = load_dataset("strategic_peer_service")
```

The current catalog contains 33 datasets:

- project-created neutral theory, synthetic, and replacement cases;
- the independently selected Zhou equation fixture;
- the Ren directional-scale table under upstream CC BY 4.0; and
- two revenue examples retained under their upstream MIT terms.

Published method names and papers remain cited where relevant, but retired or
restricted published numerical tables are not loaded by the current
Documentation or Handbook examples. Exact dataset terms and attribution are
listed in [DATA_LICENSES.md](DATA_LICENSES.md).

## Documentation and Handbook

- [Documentation home](docs/index.md)
- [Installation guide](docs/getting-started/installation.md)
- [Quick start](docs/getting-started/quickstart.md)
- [Model catalog](docs/user-guide/method-catalog.md)
- [API reference](docs/api/index.md)
- [Handbook home](book/index.md)
- [English--Chinese reading guide](book/reading-guide.md)
- [Migration from 0.1.x](docs/getting-started/migration.md)

The Documentation is English for the first public release. The Handbook is
maintained from one reviewed English source and an edited Chinese translation,
with shared formulas, citations, examples, terminology, and figures.

## Development

```bash
python -m pip install -e '.[test,docs,viz]'
python -m pytest
```

The [contribution guide](CONTRIBUTING.md) describes the source, oracle,
compatibility, testing, documentation, and DCO requirements. The
[benchmark contract](benchmarks/README.md) separates computational evidence
from defining literature and independent numerical validation.

Suggestions are welcome through the repository's issue forms, including model
proposals, data and provenance contributions, bug reports, Documentation
improvements, and Chinese translation corrections.

## Citation

Use [CITATION.cff](CITATION.cff) or [CITATION.md](CITATION.md) to cite
DEAPack. Research using a particular DEA method should also cite that method's
defining literature, as recorded in the corresponding Documentation page and
method metadata.

## Licensing

- Project-owned DEAPack 2.x software: `GPL-3.0-only`.
- Project-owned Documentation prose: `CC-BY-NC-SA-4.0`; executable examples
  remain GPL software.
- Bilingual Handbook Preview 1: Copyright © 2026 Daoping Wang. All Rights
  Reserved.
- Project-created datasets: `CC-BY-4.0` with attribution to Daoping Wang /
  DEAPack.
- Third-party datasets and materials: their recorded upstream terms.

See [COMPONENT_LICENSES.md](COMPONENT_LICENSES.md),
[DATA_LICENSES.md](DATA_LICENSES.md), [NOTICE](NOTICE), and
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) for the precise component
boundaries and attribution requirements.

The preserved uppercase `DEAPack/*.py` 0.1.x compatibility source retains its
original 2024 MIT terms and is excluded from the 2.x package archives.

## Release status

`2.0.0rc1` is a pre-release and is not a drop-in replacement for DEAPack
0.1.x. Release history is recorded in [CHANGELOG.md](CHANGELOG.md), and planned
post-RC work is tracked in [ROADMAP.md](ROADMAP.md).
