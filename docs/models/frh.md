# Free-replicability hull

```{eval-rst}
.. currentmodule:: deapack
```

`FreeReplicabilityHullDEA` (`FRH`) is for settings in which a complete
operating module can be copied, but a fractional module is not credible. A
module might be a branch format, clinic team, vessel, production line, or
standard service unit. Several whole modules may operate together.

This assumption changes the benchmark opportunity set:

- FDH asks what one observed unit demonstrates;
- FRH also admits portfolios containing whole-number copies of observed
  modules; and
- CRS convex DEA additionally treats arbitrary fractional activity levels as
  attainable.

FRH is therefore neither an “additive DEA” slack score nor a rounded CCR
solution. It changes the production technology before the radial performance
criterion is applied.

## Technology and scores

For reference input and output matrices $X$ and $Y$, DEAPack maintains

$$
\widehat{\mathcal T}_{FRH}
=
\left\{(x,y):
Xz\leq x,\quad
Yz\geq y,\quad
z\in\mathbb Z_+^n
\right\}.
$$

The entries of $z$ count replicated reference modules. Inputs and outputs may
themselves be continuous quantities.

Input orientation minimizes the common resource factor:

$$
\min_{\theta,z}\ \theta
\quad\text{s.t.}\quad
Xz\leq\theta x_o,\quad
Yz\geq y_o,\quad
z\in\mathbb Z_+^n.
$$

Both `score` and `efficiency` report $\theta$. Output orientation maximizes
the common service factor:

$$
\max_{\phi,z}\ \phi
\quad\text{s.t.}\quad
Xz\leq x_o,\quad
Yz\geq\phi y_o,\quad
z\in\mathbb Z_+^n.
$$

Here `score` reports the native expansion factor $\phi$, while `efficiency`
reports $1/\phi$ when that denominator is valid. Under matched data and
ordinary free disposal, the familiar nesting is

$$
\theta^{CRS}\leq\theta^{FRH}\leq\theta^{FDH},
\qquad
\phi^{CRS}\geq\phi^{FRH}\geq\phi^{FDH}.
$$

These inequalities compare assumptions; they do not say which assumption is
appropriate for a particular industry.

FRH has no `returns_to_scale` argument. Integer additivity is the maintained
replication technology, whereas CRS, VRS, NIRS, and NDRS name different
technologies. Finite economic limits on module copies would also define a
different bounded-replication model and are not silently inferred.

## Reproducible cross-implementation example

```python
from deapack import DEAData, FDH, FRH, CCR, dataset_info, load_dataset

frame = load_dataset("integer_coordination_hulls")
roles = dataset_info("integer_coordination_hulls").roles
data = DEAData.from_frame(
    frame,
    dmu=roles["dmu"],
    inputs=roles["inputs"],
    outputs=roles["outputs"],
)

frh_input = FRH(orientation="input").fit(data)
frh_output = FRH(
    orientation="output",
    compute_slacks=False,
).fit(data)

frh_input.summary()[
    [
        "dmu_id",
        "score",
        "total_replications",
        "integer_solution_certified",
        "mip_gap",
    ]
]
frh_input.peers("D")
```

The data are the six-unit illustration used by the R `Benchmarking` package
for `RTS="add"`. DEAPack independently reproduces its input factors

```text
A  1.0000000000
B  0.9090909091
C  1.0000000000
D  0.9615384615
E  0.8333333333
F  1.0000000000
```

and output factors

```text
A  1.000
B  1.500
C  1.000
D  1.125
E  1.500
F  1.500
```

For unit D, both orientations select two copies of A plus one copy of C.
`replication_count` carries that whole-module meaning; the compatibility
column `lambda` contains the same integer and must not be interpreted as a
convex weight.

## Slacks, targets, and certification

With the default `compute_slacks=True`, a second mixed-integer program holds
the radial optimum and maximizes row-scaled free-disposal residuals. The
result keeps two plans distinct:

- `radial_target` records the proportional resource or service commitment;
- `integer_reference_activity` records the selected whole-module portfolio.

The difference is reported as a `free_disposal_residual`. Only a successfully
completed second phase can populate generic `is_efficient`; score-only fits
leave that strong classification missing. Peer-portfolio and target
uniqueness are not claimed.

Each summary row and diagnostic record exposes solver status, MIP gap,
integer-solution certification, and completion certification. A time or node
limit, non-integral incumbent, infeasible comparison, or unacceptable
numerical violation fails closed. DEAPack does not round a fractional
solution after optimization and does not fabricate LP dual or shadow-price
information for this non-convex technology.

The SciPy/HiGHS MILP backend is included in DEAPack's ordinary numerical
dependencies. One comparison population is compiled once and reused across
evaluated units. Large reference sets can still make FRH substantially more
expensive than FDH's dominance scan or a continuous CRS LP; solver
diagnostics and runtime should therefore accompany large studies.

FRH currently accepts non-negative desirable-output data and intentionally
rejects declared undesirable outputs. Environmental replication requires an
explicit, source-qualified disposal technology rather than an automatic
combination of model switches.

```{autosummary}
FreeReplicabilityHullDEA
FRH
```

See {doc}`fdh` for the one-observed-unit technology and {doc}`radial` for the
continuously divisible convex technology.
