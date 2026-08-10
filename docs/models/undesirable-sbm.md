# Undesirable-output SBM

```{eval-rst}
.. currentmodule:: deapack
```

DEAPack exposes two distinct Tone (2003) undesirable-output SBM specifications:

- `UndesirableSBM` (`UndesirableSlacksBasedDEA`) for independently adjustable
  desirable and undesirable outputs;
- `ToneNonSeparableSBM` for a hybrid in which named good- and bad-output blocks
  share one retained process factor while all remaining outputs stay separable.

Both models require strictly positive inputs, desirable outputs, and undesirable
outputs because observed values normalize the fractional performance account.

## Separable strong-disposal SBM

The separable balances are

$$
X\lambda+s^-=x_o,\qquad
Y\lambda-s^+=y_o,\qquad
B\lambda+s^b=b_o,
$$

and

$$
\rho_o^B=
\frac{1-\frac{1}{m}\sum_i s_i^-/x_{io}}
{1+\frac{1}{s+q}\left(
\sum_r s_r^+/y_{ro}+\sum_h s_h^b/b_{ho}\right)}.
$$

The public component fields retain both subaccount means and their combined
dimension-weighted account:

$$
I_o^y=\frac{1}{s}\sum_r s_r^+/y_{ro},\qquad
I_o^b=\frac{1}{q}\sum_h s_h^b/b_{ho},\qquad
I_o^{yb}=\frac{sI_o^y+qI_o^b}{s+q}.
$$

`desirable_output_inefficiency`, `bad_output_inefficiency`, and
`output_inefficiency` store $I_o^y$, $I_o^b$, and $I_o^{yb}$;
`output_account_factor` stores $1+I_o^{yb}$. The two subaccount means must not
be averaged 1:1 when the numbers of good and bad output dimensions differ.

The bad-output balance permits independent contraction while desirable output
is retained. The implemented technology is therefore separable and strongly
disposable. `disposability="weak"` is rejected because changing a label would
not create a weak-disposal technology.

```python
from deapack import DEAData, UndesirableSBM, dataset_info, load_dataset

frame = load_dataset("environmental_disposability_contrast")
roles = dataset_info("environmental_disposability_contrast").roles
data = DEAData.from_frame(
    frame,
    dmu=roles["dmu"],
    inputs=roles["inputs"],
    outputs=roles["outputs"],
    bad_outputs=roles["bad_outputs"],
)

result = UndesirableSBM(returns_to_scale="vrs").fit(data)
result.summary()[["dmu_id", "efficiency", "output_inefficiency"]]
```

This reproduces only the equal-weight 1:1 branch of Tone's Table 2. The public
class does not expose the report's alternative good/bad weighting ratios.

`UndesirableSBM` shares the solver-neutral LP and dehomogenized SBM-account
postsolve gate used by the classic static SBM core. A published row therefore
has `score_valid=True` only after the primal, bounds, objective, dual
conditions, desirable/bad-output targets, returns-to-scale account,
fractional normalization, and native score all reconstruct. A failed
certificate retains raw diagnostics but withholds that observation's score,
slacks, targets, peers, and duals. This assurance does not transfer by name to
the distinct non-separable hybrid below.

The summary distinguishes structural self inclusion from technology
membership. A certified separable SBM balance proves membership even for an
external row, because the same reference activity and nonnegative gaps reproduce
the assessed plan. `self_in_reference`, `is_within_reference_technology`, and
`membership_status` expose that account; metadata records whether the fitted
comparison is self, mixed, or wholly external. An infeasible external programme
is reported outside the reference technology, while an uncertified numerical
failure leaves membership and classification unavailable. No additional
membership solve is required.

`UndesirableSBM` also accepts `PeerEligibility` when the study needs a
documented, observation-specific comparison population. The eligible rows are
intersected with the selected `reference` policy before the separable SBM
balances are solved. This can make an appraisal self, mixed, or fully external;
it does not alter the strong-disposal balance or reclassify the model as a
weak-disposal SBM. The summary exposes the base and effective reference sizes,
self membership, and compact rule provenance. The non-separable hybrid is not
included in this extension. Its shared-factor account is a separate,
source-qualified production mechanism.

`target_valid`, `peer_valid`, and `dual_valid` are separate publication
claims. The certified dehomogenized balance supplies the target. Reported
intensities are cleaned and thresholded, then must reconstruct that balance
again before peers are released; a large `peer_tolerance` can therefore empty
the peer table without hiding a valid score or target. Dual rows are released
only as one complete, finite original-unit account. These checks reuse the
primary solution and add no optimization task.

### Certified improvement view

The separable result can use the same variable-level view as classic SBM:

```python
figure = result.plot(kind="improvement", dmu_id="A")
```

For this model the plot keeps resource saving, desirable-service gain, and
undesirable-residual reduction in separate rows. Its physical-quantity ledger
and normalized gaps reconstruct the input-retention account, the combined
desirable/bad-output expansion account, and the reported fractional score.
The view therefore preserves the separable strong-disposal interpretation: a
lower bad-output target is represented independently of desirable-output
contraction.

This registration is exact. In addition to the three classic static SBM
orientations, `kind="improvement"` accepts
`environmental.sbm.separable_strong`; it does not treat
`ToneNonSeparableSBM`, a weak-disposal environmental model, Network SBM, or
Dynamic SBM as if they shared this account. The displayed plan is one
solver-selected optimum. It is not a causal diagnosis, a monetary valuation
of environmental damage, or a certificate that the target is unique.

## Tone's non-separable hybrid — source-qualified technical extension

`ToneNonSeparableSBM` partitions only outputs. Inputs remain ordinary,
variable-specific resource slacks. For declared non-separable output sets,

$$
Y^{NS_g}\lambda\geq\alpha y_o^{NS_g},\qquad
B^{NS_b}\lambda\leq\alpha b_o^{NS_b},\qquad
\alpha_{\min}\leq\alpha\leq1.
$$

Here `alpha` is the retained share of the evaluated unit's joint operating
process. Reducing it lowers the linked desirable service and residual
together. It must not be interpreted as “less good output is better” or as a
generic declaration of weak disposability.

If $d$ is the total number of good and bad output dimensions, the source
equation is

$$
\rho_o^{NS}=
\frac{1-\frac{1}{m}\sum_i s_i^-/x_{io}}
{1+\frac{1}{d}\left[
\sum_{r\in S_g}s_r^{S_g}/y_{ro}
+\sum_{h\in S_b}s_h^{S_b}/b_{ho}
+\left(|NS_g|+|NS_b|\right)(1-\alpha)
\right]}.
$$

```python
from deapack import (
    DEAData,
    ToneNonSeparableSBM,
    dataset_info,
    load_dataset,
)

frame = load_dataset("environmental_disposability_contrast")
roles = dataset_info("environmental_disposability_contrast").roles
data = DEAData.from_frame(
    frame,
    dmu=roles["dmu"],
    inputs=roles["inputs"],
    outputs=roles["outputs"],
    bad_outputs=roles["bad_outputs"],
)

result = ToneNonSeparableSBM(
    nonseparable_outputs=roles["nonseparable_good_outputs"],
    nonseparable_bad_outputs=roles["nonseparable_bad_outputs"],
    alpha_min=0.7,
    returns_to_scale="vrs",
).fit(data)

result.summary()[
    [
        "dmu_id",
        "efficiency",
        "alpha",
        "input_inefficiency",
        "separable_good_output_inefficiency",
        "separable_bad_output_inefficiency",
        "nonseparable_output_inefficiency",
        "output_inefficiency",
    ]
]
```

The aliases `NonSeparableUndesirableSBM` and `SBMNS` resolve to the same
class.

### Targets and unscored residuals

For a non-separable output, `target` is `alpha * observed`. The selected peer
combination need only provide at least that much desirable output and no more
than that much undesirable output. Its `reference_activity` can therefore
differ from the source target.

`source_reference_residual` records the difference. The matching rows in
`result.slacks` have `partition="nonseparable_residual"`, `scored=False`, and
`included_in_objective=False`, following the source equations (38)--(39).
These residuals must not be added to the native score.

Target rows use:

- `partition="separable"` and a variable-specific slack target for independent
  outputs;
- `partition="nonseparable"` and
  `target_kind="alpha_times_source"` for linked outputs.

### Boundary guard

Under CRS or NIRS, `alpha_min=0` with no separable desirable output permits a
zero-intensity, zero-alpha complete-shutdown boundary that does not anchor a
meaningful operating comparison. DEAPack rejects this specification. Set a
positive `alpha_min` or retain at least one separable desirable output.

## Evidence boundary

The official source is Tone's GRIPS Research Report I-2003-0005,
[doi:10.24545/00000955](https://doi.org/10.24545/00000955).

The separable equal-weight scores and targets reproduce Table 2. For the hybrid
model, Table 4 is transcribed exactly; an independent dense LP and the sparse
public implementation agree on equation (30) under the Table 5 VRS,
`alpha_min=0.7` protocol. All reported alpha values and projections agree with
Table 5 to its displayed precision.

The scores printed for A, E, G, and H do not equal equation (30) when evaluated
with those same projections. DEAPack follows the stated equation and does not
alter the implementation to force the four printed values. This is documented
as an equation-based analytical implementation with a published projection
cross-check, not as a full published numerical reproduction or a claimed
source correction.

CRS, NIRS, and NDRS follow the intensity restrictions in the source equation
family and are covered by implementation smoke/property tests. The independent
published-data numerical oracle certifies only the VRS,
`alpha_min=0.7` Table 4 protocol.

## Scope

Neither class is a by-production model, a material-balance model, a
variable-transformation method, or a generic weak-disposal SBM. Use the
production mechanism and the study question—not the historical model name—to
choose among those specifications.

```{autosummary}
UndesirableSlacksBasedDEA
UndesirableSBM
ToneNonSeparableSBM
NonSeparableUndesirableSBM
SBMNS
```
