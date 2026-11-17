# Quickstart

This short example follows the main DEAPack workflow: prepare a table, fit one
DEA model, and inspect both the overall results and one organization's
benchmark. Run the code blocks in order in the same notebook or Python session.

## 1. Prepare the data

```python
from deapack import BCCInput, DEAData, load_dataset

frame = load_dataset("slacks_2x2")
print(frame)

data = DEAData.from_frame(
    frame,
    dmu="dmu",
    inputs=["labor", "capital"],
    outputs=["service", "quality"],
)
```

Each row is a decision-making unit (DMU). `DEAData` tells DEAPack which column
identifies the DMU, which resources should be reduced, and which services
should be protected or expanded. For your own study, replace `frame` and the
column names with those from your pandas `DataFrame`. See the
{doc}`data guide <../user-guide/data>` for panel layouts, variable roles, and
validation, or the {doc}`dataset guide <../user-guide/datasets>` for the
bundled examples.

## 2. Fit the model

```python
result = BCCInput().fit(data)
```

`BCCInput` asks how much each DMU could proportionally reduce its inputs while
protecting its outputs, using a variable-returns-to-scale benchmark. See the
{doc}`radial DEA guide <../models/radial>` for input versus output orientation
and CRS versus VRS. If your research question requires another model family,
use the {doc}`method catalog <../user-guide/method-catalog>`.

## 3. Check and interpret the result

```python
result.summary()
```

Check `score_valid` and `solver_status` before interpreting a score. Here E's
efficiency is about `0.753`, indicating a proportional input-reduction
opportunity of about 24.7% under this model. Its positive `max_slack` shows
that the radial score is not the whole improvement path.

To see E's observed values and improvement targets, run:

```python
result.targets_for("E")
```

To see which organizations form E's benchmark, run:

```python
result.peers("E")
```

The target records the fitted input levels and remaining output improvements;
the peer weights reconstruct that benchmark from B and C. Before using targets
or peers, also check their `target_valid` and `peer_valid` flags in the summary.
These are comparisons under the chosen model, not causal findings.

In a notebook, each final expression displays its table. In a Python script,
use `print(result.summary())`, and likewise for the other tables. The summary
includes additional fields for detailed checking; you do not need to format
or select columns to fit the model.

The {doc}`result guide <../user-guide/results>` explains scores, validity,
targets, slacks, and diagnostics in depth; the
{doc}`reference-set guide <../user-guide/reference-sets>` explains peer
weights and alternate benchmarks. From the same `result`, continue to
{doc}`visualization <../user-guide/visualization>` or
{doc}`reporting and export <../user-guide/reporting>` when needed.
