# Nerlovian profit inefficiency

```{eval-rst}
.. currentmodule:: deapack
```

`NerlovianProfitInefficiency` explains foregone profit through two
economically different sources:

- an operating shortfall relative to a declared resource-and-service
  improvement programme; and
- a remaining mismatch between the technically improved plan and the
  price-responsive profit maximum.

It implements the Chambers--Chung--Färe (1998) composition identified by
`economic.nerlovian.ccf1998`.

For nonnegative directions $g_o^x,g_o^y$, not both zero, define

$$
\nu_o=w_o^\top g_o^x+p_o^\top g_o^y>0
$$

and

$$
NI_o=
\frac{\Pi_o^*-\Pi_o}{\nu_o}
=
\underbrace{D_{\mathcal T}(x_o,y_o;g_o^x,g_o^y)}_{\text{technical inefficiency}}
+
\underbrace{AI_o^N}_{\text{allocative inefficiency}}.
$$

The direction defines the operating comparison: it states which physical
resource savings and service gains count as one common unit of technical
improvement. Inputs fall by $\beta g_o^x$, while desirable outputs rise by
$\beta g_o^y$. Its economic units therefore determine how the normalized
profit shortfall should be read.

## Example

```python
from deapack import NerlovianProfitInefficiency

model = NerlovianProfitInefficiency(
    input_direction={"staff": 1.0},
    output_direction={"standard": 1.0, "specialist": 1.0},
)
result = model.fit(data, prices)

result.summary()[
    [
        "dmu_id",
        "profit_gap",
        "direction_value",
        "nerlovian_inefficiency",
        "technical_inefficiency",
        "allocative_inefficiency",
    ]
]
```

Using the data and prices from the maximum-profit page gives
$\nu=2+3+5=10$. For unit D, current profit is $7$, the declared operating
programme can restore $16$, and changing the resource/output mix restores a
further $4$:

$$
20
=
10(1.6)+10(0.4).
$$

Thus `nerlovian_inefficiency=2.0`,
`technical_inefficiency=1.6`, and
`allocative_inefficiency=0.4`.

## Result fields

`score`, `distance`, and `nerlovian_inefficiency` contain $NI_o$; zero is
best and lower is better. `efficiency` is missing because
$1/(1+NI_o)$ is not part of the source method. The raw `profit_gap` and
`direction_value` remain visible, and `reconstruction_residual` audits

$$
NI_o=\text{technical_inefficiency}+\text{allocative_inefficiency}.
$$

`score_valid` is true only when that complete decomposition is defined. A
failed profit-score certificate, directional score certificate, membership check, or
nonnegative allocative residual withholds the headline `score` rather than
leaving a finite but invalid value for downstream ranking.

The two source programmes retain separate evidence. `profit_score_valid` and
`profit_score_status` describe the maximum-profit account;
`directional_score_valid` and `directional_score_status` describe the DDF
account. The optional DDF completion, target, peer, and dual claims have their
own `directional_*_valid` fields. Nerlovian decomposition never treats a bare
`solver_status="optimal"` as evidence that either component is usable.

The result keeps three benchmark-conditioned operating plans distinct:

- `profit_maximizing_activity`;
- `directional_programme`, the direct resource/service counterfactual; and
- `directional_slack_completed_activity`, when the optional completion
  succeeds.

Peers, duals, diagnostics, and targets carry a `component` label. Each
component table is populated only from its certified source programme. A failure in
the optional slack completion does not erase a valid maximum-profit value,
DDF phase-one value, or additive identity. It does make the
Pareto--Koopmans status nullable, and
`decomposition_slack_status` records that the residual-slack check failed or
was skipped.

## Direction and comparability

Named directions are `observed`, `mean`, `ones`, and `zeros`; one side may be
zero, but the joint direction may not be. Vectors, per-observation matrices,
and exact variable-name mappings are also accepted.

Direction scale is part of the estimand. Multiplying both directions by
$a>0$ divides the Nerlovian, technical, and allocative quantities by $a$.
By contrast, multiplying all relevant prices by a common positive constant
scales both the raw profit gap and $\nu_o$, leaving the normalized components
unchanged. Cross-unit or cross-period comparisons require common economic
units and a defensible direction policy; metadata therefore records direction
scope and fingerprints.

## Technology and failure behavior

The first public composition is VRS only and uses exactly the same data,
reference, technology, solver policy, and direction in its profit and DDF
components. It inherits the maximum-profit model's explicit exclusion of
shutdown and rejection of undesirable outputs.

The current price layer requires complete strictly positive prices, a narrower
domain than the abstract theory permits. `direction_value` must exceed
`PriceSpec.denominator_tolerance`. An external observation that cannot be
shown feasible in the reference technology receives a missing Nerlovian score
instead of a negative or normal-looking inefficiency.

`NerlovianEfficiency` is a discoverability alias for
`NerlovianProfitInefficiency`; it does not create a second method ID.

```{autosummary}
NerlovianProfitInefficiency
NerlovianEfficiency
ProfitEfficiency
```
