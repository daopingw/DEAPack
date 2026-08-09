# Ray--Desli (1997) VRS Malmquist decomposition oracle

**Method ID:** `productivity.malmquist.decomposition.ray_desli`  
**Source:** Ray and Desli (1997), *American Economic Review* 87(5),
1033--1039, equations (4)--(16)  
**Source domain:** output orientation, positive matched panel, one or more
inputs, exactly one desirable output  
**Published reproduction:** no  
**Production implementation reused:** no  
**Disposition:** implemented/public on the certified domain

## Certificate boundary

The executable certificate is
`tests/test_ray_desli_1997_source_reproduction.py`. It compiles the output
distance programmes directly as dense NumPy/SciPy LPs and imports no
`deapack` module. The source article was visually checked in full, with the
formula and failure account taken from pp. 1034--1037.

This certificate covers Ray--Desli's alternative VRS allocation of one CRS
Malmquist productivity index into native `TECHCH(v)`, `PEFFCH`, and `SCH(v)`
components. A separate public-API test compares the production result with
this compiler task by task. The certificate does not reproduce the Penn World
Tables 5.6 application, certify arbitrary multiple-output data, or extend to
Balk's decomposition.

## Source task graph

For one DMU transition, rows index the reference technology and columns index
the target bundle:

$$
\mathcal D_R=
\begin{bmatrix}
D_R^t(z_t)&D_R^t(z_{t+1})\\
D_R^{t+1}(z_t)&D_R^{t+1}(z_{t+1})
\end{bmatrix},\qquad R\in\{C,V\}.
$$

The role order used in every table below is:

1. `base_on_base`: $D_R^t(z_t)$;
2. `comparison_on_base`: $D_R^t(z_{t+1})$;
3. `base_on_comparison`: $D_R^{t+1}(z_t)$; and
4. `comparison_on_comparison`: $D_R^{t+1}(z_{t+1})$.

The CRS matrix defines the Malmquist index. The VRS matrix defines pure
efficiency and the Ray--Desli allocation of technical and scale change.
`SCH(v)` additionally uses all four ratios
$SE^r(z_q)=D_C^r(z_q)/D_V^r(z_q)$. Thus the complete decomposition has eight,
not four, primitive distance tasks.

## Strictly positive discriminating panel

The fixture has one input and one desirable output. Every own- and
cross-period task is feasible.

| DMU | $x_t$ | $y_t$ | $x_{t+1}$ | $y_{t+1}$ |
|---|---:|---:|---:|---:|
| A | 1.0 | 1.0 | 1.0 | 1.2 |
| B | 2.0 | 3.0 | 1.5 | 2.4 |
| C | 3.0 | 4.0 | 2.5 | 4.2 |
| D | 4.0 | 4.5 | 4.0 | 5.0 |

The source-only compiler returns the following task values. Columns follow
the four-role order above.

| DMU | RTS | base/base | comparison/base | base/comparison | comparison/comparison |
|---|---|---:|---:|---:|---:|
| A | CRS | 0.666666667 | 0.800000000 | 0.595238095 | 0.714285714 |
| A | VRS | 1.000000000 | 1.200000000 | 0.833333333 | 1.000000000 |
| B | CRS | 1.000000000 | 1.066666667 | 0.892857143 | 0.952380952 |
| B | VRS | 1.000000000 | 1.200000000 | 0.909090909 | 1.000000000 |
| C | CRS | 0.888888889 | 1.120000000 | 0.793650794 | 1.000000000 |
| C | VRS | 1.000000000 | 1.200000000 | 0.895522388 | 1.000000000 |
| D | CRS | 0.750000000 | 0.833333333 | 0.669642857 | 0.744047619 |
| D | VRS | 1.000000000 | 1.111111111 | 0.900000000 | 1.000000000 |

Several VRS cross distances exceed one. This is valid: a cross-period target
need not belong to the other period's technology. All within-period VRS
distances equal one because the four fixture observations lie on their own
period VRS frontiers. Some within-period CRS distances are below one, so the
fixture also prevents accidental replacement of the CRS Malmquist tasks with
VRS tasks.

## Component and reconstruction oracle

For each DMU the independent compiler evaluates equations (13)--(16):

$$
\Pi=\operatorname{TECHCH}(v)\times
\operatorname{PEFFCH}\times\operatorname{SCH}(v).
$$

| DMU | $\Pi$ | `PEFFCH` | `TECHCH(v)` | `SCH(v)` | reconstruction residual |
|---|---:|---:|---:|---:|---:|
| A | 1.200000000 | 1.000000000 | 1.200000000 | 1.000000000 | $<10^{-12}$ |
| B | 1.066666667 | 1.000000000 | 1.148912529 | 0.928414165 | $<10^{-12}$ |
| C | 1.260000000 | 1.000000000 | 1.157583690 | 1.088474216 | $<10^{-12}$ |
| D | 1.111111111 | 1.000000000 | 1.111111111 | 1.000000000 | $<10^{-12}$ |

All four Malmquist indexes exceed one and therefore indicate productivity
growth under the source direction. DMU B is deliberately diagnostic:
Ray--Desli allocate technical progress of 1.148912529 and a negative scale
contribution of 0.928414165 while retaining the product 1.066666667.
Reciprocating either factor would reverse the source meaning and break the
identity.

## Non-equivalence certificate against FGNZ

The paper states that only `PEFFCH` is common to its decomposition and the
extended FGNZ account. For the same eight distance tasks, the source-contrasted
FGNZ factors are:

| DMU | FGNZ technical change | FGNZ own-period scale change | Ray `TECHCH(v)` | Ray `SCH(v)` |
|---|---:|---:|---:|---:|
| A | 1.120000000 | 1.071428571 | 1.200000000 | 1.000000000 |
| B | 1.120000000 | 0.952380952 | 1.148912529 | 0.928414165 |
| C | 1.120000000 | 1.125000000 | 1.157583690 | 1.088474216 |
| D | 1.120000000 | 0.992063492 | 1.111111111 | 1.000000000 |

Both decompositions reconstruct the same CRS Malmquist index and use the same
`PEFFCH`, yet every displayed technical/scale allocation differs. The test
therefore fails if Ray `TECHCH(v)` is routed to the CRS FGNZ formula or Ray
`SCH(v)` is computed as the simple ratio of own-period scale efficiencies.

## Source-backed partial result under VRS infeasibility

Page 1037 states that a cross-period VRS LP may be infeasible, and Table 1
retains Ireland's Malmquist and pure-efficiency values while marking both
technical and scale change “infeasible solution.” The oracle includes a
separate positive two-DMU panel whose first comparison observation has input
0.5, below every input in the base VRS reference set. Its
`comparison_on_base` VRS task is infeasible, while all CRS tasks and both own
VRS tasks remain feasible.

For that row, the machine certificate returns:

| Component | Value/status |
|---|---|
| CRS Malmquist $\Pi$ | 2.2 |
| `PEFFCH` | 1.0 |
| `TECHCH(v)` | undefined: VRS cross task infeasible |
| `SCH(v)` | undefined: VRS cross task infeasible |
| reconstruction | undefined |

No fallback value is inserted. The public implementation preserves this exact
partial-result boundary and reports the failed VRS cross task separately from
the still-valid CRS productivity and own-period pure-efficiency accounts.

## Gate verdict

The equation, task, component, direction, reconstruction, one-output domain,
and VRS-infeasibility semantics are source-frozen and independently
executable. The production comparison in
`tests/test_ray_desli_productivity.py` checks all eight distances, every
component, reconstruction, partial infeasibility, source-domain rejection,
unit invariance, and execution counters. No formula or index direction
remains unresolved inside this narrow leaf.
