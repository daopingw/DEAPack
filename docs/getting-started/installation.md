# Installation

## Supported Python versions

DEAPack declares support for CPython 3.10, 3.11, 3.12, and 3.13. Use an
isolated environment and confirm which interpreter created it:

```bash
python --version
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
```

On Windows PowerShell, activate with `.venv\Scripts\Activate.ps1` instead.
The complete test matrix, rather than an unlisted interpreter version, defines
the supported range for a release.

## Current release-candidate checkout

The repository metadata identifies DEAPack as `2.0.0rc1`. This is a
feature-frozen release candidate, not yet a stable or drop-in replacement for
DEAPack 0.1.x. Clone the repository, enter its root directory, and install the
base package in editable form:

```bash
git clone https://github.com/daopingw/DEAPack.git
cd DEAPack
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
```

Contributors should install the development and documentation tools used by
the repository checks:

```bash
python -m pip install -e '.[dev,docs,viz]'
```

The current source checkout and built 2.x wheel contain the lowercase
`deapack` package only. The historical uppercase runtime remains available in
Git history, not in the current source tree. Existing 0.1.x and ProdPack
studies therefore require the manual review in {doc}`migration`; do not rely
on `import DEAPack` forwarding to the new API.

The base numerical installation uses NumPy, pandas, SciPy, and the HiGHS LP
solver bundled through SciPy. It does not require users to locate a separate
CBC or commercial-solver executable.

Verify the active environment and imported source:

```bash
python -c "import deapack; print(deapack.__version__); print(deapack.__file__)"
```

## Stable, pre-release, and exact research installs

No stable 2.0 installation command should be inferred from release-candidate
metadata. After `2.0.0rc1` is published, its exact pre-release installation
command will be:

```bash
python -m pip install "DEAPack==2.0.0rc1"
```

Before the tagged artifact is available, prefer an editable checkout for
contribution or pin an exact reviewed commit for a research environment. Do
not cite a moving branch as if it were an archival release.

An alpha, beta, or release candidate remains a pre-release even when it is
installable. Record its full version and commit, read the migration notes, and
do not use `--pre` as a substitute for selecting and auditing an exact
release. A tagged and archived release remains distinct from a passing local
candidate build.

## Optional features

```bash
python -m pip install -e '.[viz]'   # Matplotlib result figures
python -m pip install -e '.[docs]'  # Sphinx package Documentation and Handbook
python -m pip install -e '.[test]'  # test runner and schema checks
```

Static plotting and documentation are optional so that the numerical
installation stays predictable. The current public visualization backend is
Matplotlib. Interactive graphics and geospatial maps remain next-version
backends; DEAPack does not advertise installation extras that merely install
Plotly or GeoPandas without a public result adapter.

## Troubleshooting the environment

- If `deapack.__file__` points outside the intended environment, deactivate
  it, remove the unintended installation from that environment, and reinstall
  from the repository root.
- If plotting imports fail, install the `viz` extra; the numerical package
  deliberately does not import Matplotlib during fitting.
- If a solver executable is requested for an ordinary LP, check that the
  intended 2.x environment is active. The default backend is SciPy/HiGHS and
  needs no separate executable.
- If legacy imports fail, use the migration guide. Installing from the 2.x
  repository does not expose the historical uppercase package.
