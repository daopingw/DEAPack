# Quickstart

This page follows one complete DEA analysis: inspect a table, declare what its
columns mean, fit a model, check that the result is valid, and explain one
organization's benchmark. The code blocks form one continuous Python session,
so run them in order.

We use a small service-production example with two inputs (`labor` and
`capital`) and two outputs (`service` and `quality`). The fitted model asks:

> How much could each organization proportionally reduce both inputs while
> preserving its outputs, after allowing for differences in operating scale?

## 1. Load and inspect the data

```python
from deapack import BCCInput, DEAData, dataset_info, load_dataset

dataset_id = "slacks_2x2"
frame = load_dataset(dataset_id)
print(frame.to_string(index=False))
```

Each row is a decision-making unit (DMU). Larger input values mean that the
organization uses more resources; larger output values mean that it delivers
more service. With your own data, `frame` can be any pandas `DataFrame` with
one row per observation.

See {doc}`../user-guide/datasets` for the bundled teaching data and
{doc}`../user-guide/data` for accepted table layouts, panel data, missing
values, and validation rules.

## 2. Declare the column roles

DEAPack does not guess which columns are identifiers, inputs, or outputs. The
built-in dataset records those roles in its metadata:

```python
info = dataset_info(dataset_id)
roles = info.column_roles

data = DEAData.from_frame(
    frame,
    dmu=roles["dmu"],
    inputs=roles["inputs"],
    outputs=roles["outputs"],
)

print(
    f"Prepared {data.n_dmus} DMUs; "
    f"inputs={data.input_names}; outputs={data.output_names}"
)
```

For your own table, supply its column names directly—for example,
`dmu="hospital"`, `inputs=("staff", "beds")`, and
`outputs=("treated", "quality")`. Keeping these roles explicit makes the
fitted production question auditable.

## 3. Fit a model

```python
model = BCCInput()
result = model.fit(data)
```

`BCCInput` is an input-oriented, variable-returns-to-scale (VRS) radial DEA
model. It first estimates a common proportional input contraction and then
checks for remaining input excesses or output shortfalls. The returned
`result` retains the model assumptions, solver diagnostics, scores, targets,
slacks, and reference intensities together.

See {doc}`../models/radial` for input versus output orientation, CRS versus
VRS, and the related CCR and BCC presets. Use the
{doc}`../user-guide/method-catalog` when the research question requires a
different model family.

## 4. Check the result before interpreting it

Start with a compact summary rather than assuming that every solver call
produced a usable score:

```python
summary = result.summary()
overview = summary.loc[
    :,
    [
        "dmu_id",
        "efficiency",
        "is_efficient",
        "max_slack",
        "score_valid",
        "solver_status",
    ],
]
print(overview.round({"efficiency": 3, "max_slack": 3}).to_string(index=False))
```

For this example, every row has `score_valid=True` and
`solver_status="optimal"`. Organizations A–D are strongly efficient under
the fitted technology. Organization E has efficiency about `0.753`: its
radial stage identifies a common input contraction of about 24.7%. Its
positive `max_slack` also tells us that the proportional score is not the
whole operational story.

An efficiency score is conditional on the selected variables, comparison
set, orientation, and returns-to-scale assumption. It is a benchmarking
result, not a causal claim or an automatic management prescription.

## 5. Explain one organization

Before using semantic tables, inspect their claim-specific validity fields.
Then query E's target, reference organizations, and remaining slacks:

```python
focus = "E"

checks = summary.set_index("dmu_id").loc[
    focus,
    ["score_valid", "completion_valid", "target_valid", "peer_valid"],
]
print("Validity checks:")
print(checks.to_string())

target = result.targets_for(focus)[
    ["role", "variable", "observed", "target"]
]
peers = result.peers(focus)[
    ["reference_dmu_id", "lambda"]
]
slacks = result.slacks.loc[
    result.slacks["dmu_id"].eq(focus),
    ["role", "variable", "slack"],
]

print("\nTarget:")
print(target.round(3).to_string(index=False))
print("\nReference organizations:")
print(peers.round(3).to_string(index=False))
print("\nRemaining slacks:")
print(slacks.round(3).to_string(index=False))
```

E's fitted target reduces `labor` from 2.000 to about 1.505 and `capital`
from 2.800 to about 2.108. After that common contraction, the slack-completion
stage identifies additional shortfalls in `service` and `quality`. The target
is reconstructed from a reference portfolio containing roughly 86.8% of B
and 13.2% of C. These are model-specific benchmarks—not instructions to copy
another organization literally.

## Where to go next

- **Bring your own data:** {doc}`../user-guide/data`
- **Choose assumptions and a model:** {doc}`../user-guide/method-catalog`
  and {doc}`../reference/index`
- **Understand scores, targets, slacks, validity, and diagnostics:**
  {doc}`../user-guide/results`
- **Understand peers and reference technologies:**
  {doc}`../user-guide/reference-sets`
- **Create plots:** {doc}`../user-guide/visualization`
- **Export a reproducible result or report:** {doc}`../user-guide/reporting`
- **Look up classes and result tables:** {doc}`../api/index`
