# Biennial Malmquist productivity index

```{eval-rst}
.. currentmodule:: deapack
```

`BiennialMalmquistProductivityIndex` implements the Pastor--Asmild--Lovell
index. `BiennialMalmquistDEA` is its discoverability alias. For each adjacent
transition, one frontier pools all observations from exactly the two periods.

## Definition and decomposition

Let $d^{B(t,t+1)}(z)$ be the Farrell efficiency-form distance under the
two-period pooled technology. Then

$$
BM^{t,t+1}=\frac{d^{B(t,t+1)}(z^{t+1})}
{d^{B(t,t+1)}(z^t)}.
$$

For a plan observed in period $\sigma$, define the contemporaneous biennial
gap as
$BG^\sigma=d^{B(t,t+1)}(z^\sigma)/d^\sigma(z^\sigma)$. Then

$$
EC_B=\frac{d^{t+1}(z^{t+1})}{d^t(z^t)},\qquad
BPC_B=\frac{BG^{t+1}}{BG^t},\qquad BM=EC_B\times BPC_B.
$$

`biennial_gap_change` stores $BPC_B$ explicitly. `best_practice_change` and
`technical_change` mirror it for common decomposition workflows.

## Properties

Both evaluated observations belong to the biennial technology, so no
cross-period radial program is required. Adding a later period leaves an
existing pair unchanged because that period is outside its reference pool.

The index is not generally circular. The $t,t+1$ and $t+1,t+2$ transitions
use different pooled technologies, so their product need not equal a direct
$t,t+2$ comparison. Use Global Malmquist when fixed-sample transitivity is the
required property.

## Example

```python
from deapack import BiennialMalmquistDEA, DEAData, load_dataset

frame = load_dataset("productivity_panel")
data = DEAData.from_frame(
    frame,
    dmu="dmu",
    period="period",
    inputs=["capital", "labor"],
    outputs="output",
)
result = BiennialMalmquistDEA().fit(data)
```

For D from 2020 to 2021, $BM$ is approximately 1.13066, efficiency change is
1.06667, and biennial-gap change is 1.06000. The base-period biennial gap is
about 0.94340 and the comparison-period gap is 1.

Every observation available in either period forms the biennial frontier;
only identifiers present in both periods receive transition rows. Diagnostics
and peers retain `technology_periods=(base_period, comparison_period)`.

## Four-task evidence and release contract

A reported transition rests on four distinct operating-performance claims:
the base and comparison observations are each assessed against their own-period
benchmark and against the common two-period benchmark. DEAPack releases the
headline Biennial Malmquist index only when all four claims survive the same
evidence checks.

For each radial programme, the solver-neutral certificate checks the production
constraints, variable bounds, reported objective, dual feasibility,
complementarity, and strong duality. Separate economic checks then reconstruct
the raw and published input--output accounts in the original quantity units.
The displayed peer weights are thresholded for reporting and have their own
account reconstruction; a peer-reporting failure therefore does not rewrite an
otherwise valid productivity result.

The four positive efficiency-form distances must also reproduce the raw and
published values of $BM$, $EC_B$, both biennial gaps, $BPC_B$, and the complete
$BM=EC_B\times BPC_B$ account. A backend `"optimal"` label alone is not enough
to release those economic claims.

```python
result.summary()[[
    "score_valid",
    "score_status",
    "all_four_distance_programs_certified",
    "all_four_economic_distance_claims_certified",
    "multiplicative_account_certified",
    "peer_valid",
    "peer_status",
]]
```

If one programme or the complete multiplicative account fails, DEAPack
withholds the headline, its four published distances, decomposition components,
and peer rows for that organization--period transition. The diagnostic table
still preserves the backend's raw status, the failed role, and the certificate
reason; other transitions remain independent.

`result.metadata["solver_calls"]` reports the number of unique cached distance
programmes sent to the backend. `result.metadata["additional_solver_calls"]`
and the corresponding field inside `postsolve_certificate` are both zero:
the LP, original-unit economic, thresholded-peer, and complete multiplicative
checks reuse the original primal and dual evidence instead of optimizing again.

## Scope

CRS is the default; other returns-to-scale assumptions are explicit
sensitivity variants. This radial class accepts only desirable outputs.
Biennial environmental productivity requires a separately named directional
technology and undesirable-output assumptions.

This operator remains a documentation-only extension rather than a separate
Handbook route. It changes the reference-information policy of the common
radial productivity framework; it does not add a new economic mechanism to the
book's core progression.

## Validation boundary

The test suite includes an independent rational certificate for the
output-oriented CRS account. Exact upper bounds and attaining witnesses cover
the two contemporaneous distances, the two adjacent-pair pooled distances,
efficiency change, both best-practice gaps, best-practice change, and the
headline productivity index. A separate three-period public-API fixture makes
a base-only or comparison-only organization determine the pair frontier while
excluding a much stronger organization from the following period. It therefore
distinguishes the declared raw two-period union from both a comparison-only
frontier and an incorrectly global pool.

The broader test suite also covers later-period extension stability and a
non-circularity counterexample. The shared postsolve suite injects forged
objectives, forged radial factors, missing dual marginals, stale failed
solutions, broken original-unit accounts, and broken complete multiplicative
accounts. Each case must fail closed at one transition without an extra solve.
The productivity benchmark independently counts unique solver tasks and
reference compilations and requires every retained LP, economic, peer, and
multiplicative residual to remain within the declared tolerance.

These checks validate the implemented computational contract, but they are not
a reproduction of the defining article's empirical application. The method
retains `publication_scope="documentation_only"` because it is a specialized
reference-policy leaf rather than a separate Handbook teaching route; that
reader-placement decision does not weaken its analytical verification.

```{autosummary}
BiennialMalmquistProductivityIndex
BiennialMalmquistDEA
```
