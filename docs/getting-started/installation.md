# Installation

DEAPack works with Python 3.10–3.13. In a terminal, install it with:

```bash
python -m pip install DEAPack
```

In a Jupyter notebook, use `%pip install DEAPack` in a cell instead, then
restart the kernel if you have just upgraded an imported package. This installs
into the notebook's active Python environment.

The numerical dependencies and the HiGHS optimization solver are installed
with DEAPack. You do not need a separate solver executable or a commercial
solver license for the standard LP models. Continue to the {doc}`quickstart`
to run your first analysis.

## Add plotting

To create figures from your results, install the plotting extra:

```bash
python -m pip install "DEAPack[viz]"
```

Plotting is optional; it is not needed to fit a model. See
{doc}`../user-guide/visualization` for a first figure.

## Optional: use a separate environment

If you do not already have a project environment, a virtual environment keeps
its packages separate from other Python projects:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install DEAPack
```

On Windows PowerShell, activate with `.venv\Scripts\Activate.ps1` instead.
If you already use a conda environment, install DEAPack inside that environment;
there is no need to create a second environment for this guide.

## Upgrading from an older project

DEAPack 2.x combines efficiency and productivity analysis in the lowercase
`deapack` package. It is not a drop-in replacement for DEAPack 0.1.x or
ProdPack. Existing studies should follow the {doc}`migration` guide;
`import DEAPack` is not an alias for the new API.

## Recording an analysis for reproduction

For a paper or archived study, record the version used:

```python
import deapack

print(deapack.__version__)
```

Someone reproducing that study should install the recorded version, for example:

```bash
python -m pip install "DEAPack==2.0.1"
```

The unpinned installation at the top of this page is convenient for learning;
it does not freeze future package updates. For source checkouts, also record
the commit. Cite the software and model as described in
{doc}`../user-guide/citing`. Use a specific pre-release only when the study
requires it, and record its full version rather than using `--pre` to select
an unspecified candidate.

## Troubleshooting

If Python cannot import DEAPack, check that your terminal or notebook uses the
environment where you installed it. In that Python session, inspect:

```python
import deapack

print(deapack.__version__)
print(deapack.__file__)
```

- After an upgrade in a notebook, restart the kernel before importing again.
- If a plotting import fails, install `DEAPack[viz]` in that same environment.
- If an ordinary LP asks for a separate solver executable, check that you are
  using the intended 2.x installation.

Installing from GitHub, editable installs, and developer dependencies are
covered in {doc}`../developer/contributing`; they are not required to use the
package.
