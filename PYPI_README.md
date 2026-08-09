# DEAPack

DEAPack is a source-audited Python toolkit for data envelopment analysis,
efficiency measurement, productivity analysis, and environmental performance.
The redesigned 2.x API uses the lowercase `deapack` import and a common data,
technology, result, visualization, and reporting architecture.

`2.0.0rc1` is the draft release-candidate identity. The candidate has not yet
been published. Its 33 dataset fingerprints now have exact item-level license
and attribution mappings; GitHub and PyPI publication actions remain separate
manual steps. After those authenticated steps complete, the release candidate
will be suitable for public testing and exact version-pinned research; it
will still not be the stable 2.0 compatibility promise.

## Installation

After publication, install the exact release candidate with:

```bash
python -m pip install "DEAPack==2.0.0rc1"
```

Python 3.10, 3.11, 3.12, and 3.13 are supported. NumPy, pandas, and SciPy are
the only required runtime dependencies; ordinary linear programmes use the
HiGHS solver bundled through SciPy. Install `DEAPack[viz]` for the optional
Matplotlib result views.

## Quick start

```python
import pandas as pd

from deapack import BCCInput, DEAData

frame = pd.DataFrame(
    {
        "dmu": ["A", "B", "C", "D"],
        "input": [1.0, 2.0, 3.0, 4.0],
        "output": [1.0, 3.0, 4.0, 4.0],
    }
)
data = DEAData.from_frame(
    frame,
    dmu="dmu",
    inputs="input",
    outputs="output",
)

result = BCCInput().fit(data)
print(result.summary())
print(result.peers("D"))
```

Results expose named summary, target, slack, peer, dual, component, and
diagnostic tables only when the corresponding numerical and economic account
has been certified. They can also produce a self-contained HTML brief and a
deterministic audit archive.

## Scope

The candidate covers the major classical radial and non-radial families,
directional and generalized-distance analysis, price-informed economic
efficiency, undesirable-output and environmental technologies, Malmquist and
related productivity accounts, network and dynamic production, panel models,
and radial metafrontiers. The installed discovery catalog is the authoritative
list of public methods:

```python
from deapack import list_methods

for method in list_methods():
    print(method.method_id)
```

Statistical inference, Färe--Primont productivity, generic congestion,
automatic EBM calibration, and several source-incomplete variants remain
explicit next-version work rather than provisional APIs.

## Documentation and migration

- [Package Documentation source](https://github.com/daopingw/DEAPack/tree/main/docs)
- [English Handbook source](https://github.com/daopingw/DEAPack/tree/main/book)
- [Chinese Handbook catalogs](https://github.com/daopingw/DEAPack/tree/main/book/locale/zh_CN/LC_MESSAGES)
- [2.x migration guide](https://github.com/daopingw/DEAPack/blob/main/docs/getting-started/migration.md)
- [Release notes](https://github.com/daopingw/DEAPack/blob/main/RELEASE_NOTES_2.0.0rc1.md)
- [Contribution guide](https://github.com/daopingw/DEAPack/blob/main/CONTRIBUTING.md)
- [Issue tracker](https://github.com/daopingw/DEAPack/issues)

DEAPack 2.x is a greenfield API. Historical `import DEAPack` and ProdPack
scripts require an explicit migration; the 2.x wheel intentionally provides
only `import deapack`.

## Citation and license

Use the repository's
[`CITATION.cff`](https://github.com/daopingw/DEAPack/blob/main/CITATION.cff)
and record the exact pre-release version and commit used. The DEAPack software
component is licensed under `GPL-3.0-only`. Bundled dataset content is released
only when its provenance record identifies confirmed licensing authority, an
approved redistribution status, content license, attribution, and required
notice; it does not inherit GPL merely by being represented in a Python file.
All 33 current dataset fingerprints have exact mappings: 30 project-created
or independently selected fixtures and one external dataset use
`CC-BY-4.0`, while two external datasets retain upstream `MIT` notices.
Package Documentation and Bilingual Handbook Preview 1 are separate
components and are cited and licensed separately.
