# Dynamic SBM scored carry-overs: independent analytical oracle

**Method ID:** `dynamic.sbm.tone_tsutsui_2010`  
**Dataset ID:** `dynamic_capacity_backlog`  
**Validation kind:** `analytically_derived`  
**Published reproduction:** no

This certificate validates the good- and bad-carry-over accounts of the
existing Tone--Tsutsui dynamic SBM implementation. The four observations are
theory-led synthetic values chosen for hand reconstruction; they are not
published observations and do not define a new dynamic model or variant.

## Management setting

Two otherwise identical organizations use one unit of a current resource to
deliver one unit of service in each of two periods. They differ only in the
states passed between periods:

| Period | Organization | Resource | Service | Capacity (good) | Backlog (bad) |
|---:|---|---:|---:|---:|---:|
| 1 | Prepared | 1 | 1 | 2 | 1 |
| 1 | Strained | 1 | 1 | 1 | 2 |
| 2 | Prepared | 1 | 1 | 2 | 1 |
| 2 | Strained | 1 | 1 | 1 | 2 |

Capacity is a good carry-over: more of it strengthens the operating position
inherited by the next period. Backlog is a bad carry-over: less of it reduces
the burden inherited by the next period. Both states enter the reported base
score. Current resource and service quantities are deliberately identical so
that the resulting performance gap cannot be misread as a current-period
input or output gap.

The certified public specification is non-oriented Dynamic SBM under VRS,
with the base score and equal period weights. The source formulation applies
implicit unit item weights to carry-overs; this fixture does not claim a
separate public carry-over-weight parameter.

## Exact VRS account

Let $p_t\in[0,1]$ denote the period-$t$ VRS reference weight on Prepared when
Strained is appraised. The remaining weight $1-p_t$ is on Strained. Because
the two organizations have identical current operations, the benchmark keeps
resource and service at one and their slacks are zero. Its carry-over targets
are

$$
z^{\mathrm{good}}_t=1+p_t,
\qquad
z^{\mathrm{bad}}_t=2-p_t.
$$

The good-capacity shortfall and bad-backlog excess are therefore both $p_t$.
Relative to Strained's observed states, their normalized slacks are

$$
\frac{p_t}{1}=p_t,
\qquad
\frac{p_t}{2}.
$$

There is one current input and one bad carry-over on the input side of the
period account, and one current output and one good carry-over on the output
side. Hence

$$
A_t
=1-\frac12\left(0+\frac{p_t}{2}\right)
=1-\frac{p_t}{4},
$$

and

$$
B_t
=1+\frac12\left(0+p_t\right)
=1+\frac{p_t}{2}.
$$

With equal effective period weights $w_1=w_2=1/2$, the horizon score is

$$
\rho
=\frac{\sum_t w_t A_t}{\sum_t w_t B_t}.
$$

This ratio decreases as the weighted reference share on Prepared increases.
Its minimum is attained at $p_1=p_2=1$. The adjacent-period continuity
equations are satisfied because both selected carry-over targets are constant
across the two periods. Therefore, in each period,

$$
s^{\mathrm{good}}=1,
\quad
\frac{s^{\mathrm{good}}}{z^{\mathrm{good}}_o}=1,
\quad
s^{\mathrm{bad}}=1,
\quad
\frac{s^{\mathrm{bad}}}{z^{\mathrm{bad}}_o}=\frac12,
$$

and

$$
A_t=\frac34,
\qquad
B_t=\frac32,
\qquad
\rho_t=\frac{A_t}{B_t}=\frac12.
$$

The horizon account reconstructs exactly as

$$
\rho
=\frac{\tfrac12(3/4)+\tfrac12(3/4)}
       {\tfrac12(3/2)+\tfrac12(3/2)}
=\frac12.
$$

The two effective input-account contributions are $3/8$ and the two output
expansion contributions are $3/4$. The selected capacity target is two and
the selected backlog target is one in both periods.

Prepared already has the greatest observed capacity and least observed
backlog while maintaining the same current operation. Its scored slacks are
zero and its exact horizon and period scores are one.

## Continuity and terminal interpretation

For each carry-over, the selected period-1 target equals the inherited
period-2 target, so the reported continuity residual is zero. Period 2 is the
observed terminal boundary. It has no outgoing period-3 continuity equation
and is reported as
`observed_terminal_no_outgoing_continuity`.

The capacity and backlog trajectory views share the same complete period
accounts $(A_t,B_t,\rho_t)$ and the same horizon score. Their quantity panels
remain role-specific: capacity rises from one to a selected target of two,
whereas backlog falls from two to a selected target of one. Thus a trajectory
chart's performance bars are the complete period account formed jointly by
current operations, capacity, and backlog; they are not an attribution to the
single carry-over displayed in the quantity panel.

## Public validation contract

`tests/test_dynamic_sbm_scored_carryover_case.py` verifies through the public
API:

1. exact horizon and period scores, account levels, period weights, and
   weighted contributions for Prepared and Strained;
2. zero current resource/service slacks, the exact good/bad carry-over slacks,
   normalizations, score inclusion flags, and targets;
3. adjacent-period continuity, the observed terminal boundary, and the
   solver-neutral score and reconstruction certificates already required by
   the result contract; and
4. role-specific capacity/backlog quantities alongside identical complete
   period accounts returned by `prepare_trajectory_data`.

## Claim boundary

| Claim | Evidence | Scope |
|---|---|---|
| exact scored good/bad carry-over account | analytical VRS bound plus attaining reference plan | this two-organization, two-period, strictly positive synthetic fixture; non-oriented VRS base score with equal period weights |
| exact horizon reconstruction | direct weighted ratio of period input and output accounts | score, efficiency, distance, $A_t$, $B_t$, period contributions, and horizon account |
| exact continuity and terminal account | direct equality of adjacent selected targets | capacity and backlog; one adjacent transition and the source terminal-boundary policy |
| trajectory result contract | certified public result tables | role-specific quantities and common complete period accounts for Strained |

This certificate does not claim published numerical reproduction, unique
target selection as a general property, causal attribution of the performance
gap, alternative carry-over weights, other boundary equations, other RTS or
orientation choices, dynamic networks, uncertainty inference, or a new
method identity. The public result therefore retains the conservative
selection label `solver_selected_not_uniqueness_certified` even though the
fixture supplies exact target quantities.
