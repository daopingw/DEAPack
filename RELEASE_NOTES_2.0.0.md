# Release Notes — DEAPack 2.0.0

DEAPack 2.0.0 is the first stable release of the redesigned lowercase
`deapack` package. It is a greenfield 2.x API rather than a drop-in update to
the historical uppercase DEAPack 0.1.x package.

## Installation

```bash
python -m pip install "DEAPack==2.0.0"
```

DEAPack supports CPython 3.10, 3.11, 3.12, and 3.13. NumPy, pandas, and SciPy
are the required runtime dependencies; Matplotlib views are available through
the optional `viz` extra.

## Highlights

- A common data, technology, model, result, reporting, visualization, and
  audit architecture for DEA-based efficiency and productivity analysis.
- Seventy-five public discovery identities covering classical radial and
  non-radial DEA, economic efficiency, undesirable-output and environmental
  models, productivity indexes, network production, dynamic production,
  metafrontiers, diagnostics, cross-efficiency, and super-efficiency.
- Certified named result tables for scores, targets, slacks, peers, duals,
  components, and diagnostics, with fail-closed behavior where an account is
  not defined or cannot be verified.
- Thirty-three deterministic teaching datasets with exact content hashes,
  roles, provenance, attribution, and item-level redistribution terms.
- English package Documentation covering installation, model choice,
  analysis, visualization, reporting, and the public API.
- Independent analytical, reproduced, or cross-implemented numerical evidence
  for every implemented public method record.

The installed method inventory is authoritative:

```python
from deapack import list_methods

for method in list_methods():
    print(method.method_id)
```

See the [method catalog](docs/user-guide/method-catalog.md) for the public
surface and the [migration guide](docs/getting-started/migration.md) for
moving 0.1.x studies to the 2.x API.

## Compatibility and deferred work

The Python import is `deapack`; the stable wheel does not provide an uppercase
`DEAPack` compatibility package. Existing 0.1.x and ProdPack scripts require
explicit migration.

Statistical inference, Färe--Primont productivity, generic congestion,
automatic EBM calibration, interactive plotting backends, and several
source-incomplete model variants remain future work rather than provisional
2.0 APIs.

## Licensing and citation

- Project-owned software is licensed under `GPL-3.0-only`.
- Project-owned Documentation prose is licensed under
  `CC-BY-NC-SA-4.0`; executable examples remain GPL software.
- Project-created datasets use `CC-BY-4.0` with attribution; retained
  third-party datasets keep their recorded upstream terms.

Exact component boundaries and data attribution are recorded in
[COMPONENT_LICENSES.md](COMPONENT_LICENSES.md),
[DATA_LICENSES.md](DATA_LICENSES.md), and [NOTICE](NOTICE).

Use [CITATION.cff](CITATION.cff) or [CITATION.md](CITATION.md) and record the
exact software version used. No software DOI has yet been assigned.
