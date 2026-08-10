# Network data, specifications, and models

```{eval-rst}
.. currentmodule:: deapack
```

## Data

```{autoclass} deapack.NetworkData
:members:
```

```{autoclass} deapack.EnvironmentalNetworkData
:members:
```

## Production-graph specifications

```{autoclass} deapack.ProcessSpec
:members:
```

```{autoclass} deapack.LinkSpec
:members:
```

```{autoclass} deapack.NetworkSpec
:members:
```

```{autoclass} deapack.TwoStageSeriesSpec
:members:
```

```{autoclass} deapack.EnvironmentalNetworkSpec
:members:
```

```{autoclass} deapack.EnvironmentalVariableOwnership
:members:
```

`TwoStageSeriesSpec` is the convenience declaration for the public
Färe--Grosskopf, Kao--Hwang, and Chen--Cook--Li--Zhu leaves. It compiles to a
`NetworkSpec` containing two processes and one process-specific-intensity
link. The relational and additive leaves use its shared-multiplier
declaration; the Färe--Grosskopf envelopment leaf uses quantities and
process-specific intensities without fitting a multiplier account. The same
graph declaration can be wrapped in `EnvironmentalNetworkSpec` to assign
external-input, desirable-output, undesirable-output, and ordinary-
intermediate economic accounts.

## Färe--Grosskopf system-radial model

```{autoclass} deapack.FareGrosskopfNetworkRadialDEA
:members:
```

This class reports one input- or output-radial **system** account and
coordinated upstream/downstream plans. `orientation="input"` is the default.
Under input orientation, `score` and `system_score` are the native contraction
factor $\theta$ and the efficiency fields also contain $\theta$. Under output
orientation, the native score fields contain the expansion factor $\phi$ and
the efficiency fields contain $1/\phi$. Neither orientation defines stage
efficiencies.

The evaluated organization's recorded intermediate handoff is available for
comparison in the link table but does not condition the benchmark; upstream
supply and downstream requirement are chosen endogenously. Peer display
thresholds never change fitted targets: the targets use the complete
intensity vectors and the summary discloses any omitted coefficient mass.
See {doc}`../models/fare-grosskopf-network-radial` for the CRS source
equations, orientation-qualified targets and score transformations, the
separately sourced VRS extension, and the conditional score-only relation to
the Kao--Hwang primary programme.

## Relational two-stage model

```{autoclass} deapack.KaoHwangRelationalDEA
:members:
```

`KaoHwangDEA` is an exact alias for `KaoHwangRelationalDEA`.

The system headline, selected process decomposition, source projection/link
account, and thresholded peer display have independent release gates. Consult
{doc}`../models/kao-hwang-network` before consuming
`score_valid`, `decomposition_valid`, `target_valid`, or `peer_valid`; a valid
system result can survive an unavailable secondary attribution or display.
Postsolve certification reuses the returned primary and secondary solutions
and adds no optimization task.

## Weighted-additive two-stage model

```{autoclass} deapack.ChenCookLiZhuAdditiveDEA
:members:
```

`TwoStageAdditiveDecompositionDEA` is an exact alias for
`ChenCookLiZhuAdditiveDEA`. Here *additive* refers to the endogenous
virtual-resource-share-weighted arithmetic reconstruction of stage
efficiencies, not the slack-sum objective of `AdditiveDEA`.

The system, process, split-link/target, and displayed-peer accounts are
released separately through `score_valid`, `process_account_valid`,
`link_account_valid`/`target_valid`, and `peer_valid`. See
{doc}`../models/chen-additive-network` for the raw and published account
certificates, failure isolation, and primary/secondary/projection solve
ledger.

## General CRS additive network model

```{autoclass} deapack.CookZhuBiYangAdditiveDEA
:members:
```

`GeneralAdditiveNetworkDEA` is an exact alias for
`CookZhuBiYangAdditiveDEA`.

`minimum_process_share` accepts a scalar or a mapping from process ID to
floor. See {doc}`../models/cook-general-additive-network` for the exact graph
domain, result tables, source boundaries, process/link release gates, and
one-primary-solve-per-organization execution contract. This open-DAG method is
a source-qualified member of the Network DEA family.

## Tone--Tsutsui network SBM

```{autoclass} deapack.ToneTsutsuiNetworkSBM
:members:
```

`NetworkSBM` is an exact alias for `ToneTsutsuiNetworkSBM`.

See {doc}`../models/tone-tsutsui-network-sbm` for the source formulation,
complete executable example, result fields, and the declared reproduction
tolerances for Tables 3, 4, and 6.

## Lewis--Sexton sequential network appraisal

```{autoclass} deapack.LewisSextonSequentialNetworkDEA
:members:
```

This procedure evaluates process nodes in network order and propagates
solver-selected hypothetical quantities through an acyclic organization. It
is not a simultaneous joint-network projection. See
{doc}`../network/sequential` for the supported forward-quantity domain,
organizational aggregation, and source boundaries.

## Kalhor--Kazemi Matin environmental general-network model

```{autoclass} deapack.KalhorKazemiMatinNetworkDEA
:members:
```

This model fits the corrected activity-specific weak-disposal technology to a
declared environmental production graph and reports one input-radial system
score. `alpha` and `beta` are process-reference intensity components, not
process efficiencies; no secondary slack completion is run. See
{doc}`../models/kalhor-kazemi-matin-environmental-network` for the complete
data-role, equation, result, validation, and source-boundary contract.

## Minimal executable pattern

```python
from deapack import (
    KaoHwangRelationalDEA,
    NetworkData,
    TwoStageSeriesSpec,
    load_dataset,
)

frame = load_dataset("two_stage_public_service")
spec = TwoStageSeriesSpec(
    inputs=("operation_expenses", "insurance_expenses"),
    intermediates=(
        "direct_written_premiums",
        "reinsurance_premiums",
    ),
    outputs=("underwriting_profit", "investment_profit"),
    stage_names=("premium_acquisition", "profit_generation"),
)
data = NetworkData.from_frame(frame, dmu="company", spec=spec)
result = KaoHwangRelationalDEA().fit(data)
```

The same declared series graph can first be assessed as a coordinated
system-radial production opportunity:

```python
from deapack import FareGrosskopfNetworkRadialDEA

radial_system_result = FareGrosskopfNetworkRadialDEA().fit(data)
```

It can also be appraised under the distinct additive
performance-attribution account:

```python
from deapack import ChenCookLiZhuAdditiveDEA

additive_result = ChenCookLiZhuAdditiveDEA(
    returns_to_scale="vrs",
).fit(data)
```

For a process graph whose assets or obligations also persist across periods,
see the separate {doc}`dynamic-network` API and
{doc}`../models/tone-tsutsui-dynamic-network-sbm` model contract.
