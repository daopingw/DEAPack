# Quickstart

This short example follows the main DEAPack workflow: prepare a table, fit one
DEA model, and inspect both the overall results and one organization's
benchmark. Run the three code blocks in order.

## 1. Prepare the data

```python
from deapack import BCCInput, DEAData, load_dataset

frame = load_dataset("slacks_2x2")
print(frame.to_string(index=False))

data = DEAData.from_frame(
    frame,
    dmu="dmu",
    inputs=("labor", "capital"),
    outputs=("service", "quality"),
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
model = BCCInput()
result = model.fit(data)
```

`BCCInput` asks how much each DMU could proportionally reduce its inputs while
protecting its outputs, using a variable-returns-to-scale benchmark. See the
{doc}`radial DEA guide <../models/radial>` for input versus output orientation
and CRS versus VRS. If your research question requires another model family,
use the {doc}`method catalog <../user-guide/method-catalog>`.

## 3. Check and interpret the result

```python
summary = result.summary()
summary_columns = [
    "dmu_id", "efficiency", "is_efficient",
    "max_slack", "score_valid", "solver_status",
]
print(summary[summary_columns].round(3))

focus = "E"
status = summary.set_index("dmu_id").loc[focus]
assert status[["score_valid", "target_valid", "peer_valid"]].all()

target_columns = ["role", "variable", "observed", "target"]
peer_columns = ["reference_dmu_id", "lambda"]
print("\nTarget for E:")
print(result.targets_for(focus)[target_columns].round(3))
print("\nReference organizations for E:")
print(result.peers(focus)[peer_columns].round(3))
```

Check `score_valid` and `solver_status` before interpreting a score. Here E's
efficiency is about `0.753`, indicating a proportional input-reduction
opportunity of about 24.7% under this model. Its positive `max_slack` shows
that the radial score is not the whole improvement path. The target records
the fitted input levels and remaining output improvements, while the peer
weights reconstruct that benchmark from B and C. These are conditional
benchmarking results, not causal findings or automatic management
instructions.

The {doc}`result guide <../user-guide/results>` explains scores, validity,
targets, slacks, and diagnostics in depth; the
{doc}`reference-set guide <../user-guide/reference-sets>` explains peer
weights and alternate benchmarks. From the same `result`, continue to
{doc}`visualization <../user-guide/visualization>` or
{doc}`reporting and export <../user-guide/reporting>` when needed.
