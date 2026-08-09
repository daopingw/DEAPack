# Analytical certificate for radial FDH

**Method ID:** `static.radial.fdh`  
**Validation kind:** `analytically_derived`  
**Published reproduction:** no

This certificate validates the public input- and output-oriented radial
free-disposal-hull implementation on one exact synthetic production account.
It is not a reproduction of a published numerical table. Its purpose is to
close the core-family numerical gate independently of the production scan in
`deapack.models.fdh`.

## Maintained technology and finite certificate

For an evaluated organization $o$, an observed activity $j$ can support the
input-oriented comparison only when $y_j\ge y_o$. If $x_{io}>0$, the smallest
common input factor supported by that activity is

$$
\theta_{jo}=\max_i\frac{x_{ij}}{x_{io}}.
$$

If $x_{io}=0$, feasibility additionally requires $x_{ij}=0$. The exact FDH
factor is the smallest $\theta_{jo}$ among the eligible observed activities.

For the output-oriented comparison, activity $j$ is eligible when
$x_j\le x_o$. With positive evaluated outputs, its common expansion factor is

$$
\phi_{jo}=\min_r\frac{y_{rj}}{y_{ro}},
$$

and the exact FDH factor is the largest eligible $\phi_{jo}$. These finite
minimum and maximum operations are an exhaustive certificate because the FDH
admits one observed operating template at a time and then applies ordinary
free disposal; it does not average or rescale several templates.

## Exact five-organization account

The fixture uses two resources and two desirable services:

| Organization | $x_1$ | $x_2$ | $y_1$ | $y_2$ |
|---|---:|---:|---:|---:|
| A | 1 | 4 | 4 | 1 |
| B | 4 | 1 | 1 | 4 |
| C | 2 | 2 | 3 | 3 |
| D | 4 | 4 | 2 | 2 |
| E | 3 | 3 | 1 | 1 |

Direct enumeration gives:

| Organization | input-eligible activities | $\theta$ | output-eligible activities | $\phi$ |
|---|---|---:|---|---:|
| A | A | $1$ | A | $1$ |
| B | B | $1$ | B | $1$ |
| C | C | $1$ | C | $1$ |
| D | C, D | $1/2$ via C | A, B, C, D, E | $3/2$ via C |
| E | A, B, C, D, E | $2/3$ via C | C, E | $3$ via C |

The harmonized efficiency is $\theta$ for the input orientation and
$1/\phi$ for the output orientation. Organizations A--C are radially and
strongly efficient. C is the unique best activity for D and E. The associated
targets are therefore $(x,y)=((2,2),(3,3))$ in both orientations.

The residual accounts further distinguish orientation:

- D under input orientation has zero input slack and output slack $(1,1)$;
- D under output orientation has input slack $(2,2)$ and zero output slack;
- E under input orientation has zero input slack and output slack $(2,2)$; and
- E under output orientation has input slack $(1,1)$ and zero output slack.

The automated certificate checks every score, reciprocal efficiency,
candidate count, efficiency status, selected single-activity peer, target, and
residual account through the public API. No production compiler or private
scan helper is used to derive the expected values.

## Claim boundary

This exact account certifies the ordinary nonnegative, self-inclusive,
cross-sectional radial FDH definition and its public single-peer target
semantics. It does not certify sampling inference, undesirable outputs,
external-reference extrapolation, partial frontiers, statistical robustness,
or any FCH/FRH technology. Those are different estimators or production
accounts.
