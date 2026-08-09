# Quickstart

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

This fit asks whether each organization could reduce all represented inputs
by one common proportion while protecting its observed outputs. `BCCInput`
uses a convex VRS benchmark, fixes the input orientation, and completes
remaining ordinary input and output slacks after preserving the radial score.
Its result records:

```python
result.metadata["method_id"]  # "static.radial"
result.metadata["preset_id"]  # "static.radial.vrs.input"
```

Use `CCRInput`, `CCROutput`, or `BCCOutput` when the management question and
scale assumption identify one of the other complete classical recipes. See
{doc}`../models/radial` for the four-way map, native $\theta$/$\phi$ scores,
and target-policy boundaries.

`CCR` and `BCC` are partial RTS specializations of `RadialDEA`: they fix CRS
or VRS, default to input orientation, and still allow orientation and slack
completion to be configured. For a large job that deliberately needs radial
scores only:

```python
from deapack import BCC

score_only = BCC(
    orientation="input",
    compute_slacks=False,
).fit(data)
```

In score-only mode, `is_radially_efficient` is available but `is_efficient`
remains missing: strong efficiency cannot be claimed without checking slacks.
Use the complete presets when a stable, slack-completed CCR-I, CCR-O, BCC-I,
or BCC-O identity should travel with the result.
