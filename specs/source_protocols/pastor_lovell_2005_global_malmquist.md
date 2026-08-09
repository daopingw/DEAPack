# Pastor--Lovell (2005) Global Malmquist source protocol

## Readiness decision

| Field | Frozen decision |
|---|---|
| Canonical method ID | `productivity.global_malmquist` |
| Defining source | Jesús T. Pastor and C. A. Knox Lovell (2005), “A global Malmquist productivity index,” *Economics Letters* 88(2), 266--271, [doi:10.1016/j.econlet.2005.02.013](https://doi.org/10.1016/j.econlet.2005.02.013) |
| Local evidence status | `primary_checked` |
| Source contract | Frozen for the classic CRS desirable-output account described below |
| Independent evidence | Exact analytical certificate plus a production-free dense LP compiler |
| Disposition | Implemented and public; no new method or book route is authorized by this protocol |

The repository already froze the defining source identity, primary equations,
reference construction, and result convention in
`specs/registry/methods/productivity/productivity.global_malmquist.json` and
`specs/CONVENTIONS.md`. This protocol makes that existing evidence gate
explicit. It does not reconstruct an unavailable empirical table or infer an
additional model from the name “global.”

## Source-frozen production account

Let $z^\sigma=(x^\sigma,y^\sigma)$ be an observed plan and let
$\mathcal T^\tau$ denote the contemporaneous CRS technology represented in
period $\tau$. The package constructs the global technology
$\mathcal T^G$ as one CRS conical DEA envelope of all eligible raw
observations in the declared sample vintage. It is not a literal nonconvex
union of separately estimated frontiers.

For the output-oriented source certificate, the radial expansion factor is
the optimum of

$$
\max_{\lambda,\phi}\ \phi
$$

subject to

$$
X^R\lambda\le x^\sigma,\qquad
Y^R\lambda\ge \phi y^\sigma,\qquad
\lambda\ge0,
$$

where $R$ is either the plan's own period or the fixed global sample. The
Farrell efficiency-form distance used by DEAPack is $d^R(z^\sigma)=1/\phi$.

For two plans of the same organization in periods $t$ and $u$, with $t$ earlier
than $u$ in the declared period order, the frozen
headline account is

$$
GM^{t,u}=\frac{d^G(z^u)}{d^G(z^t)}.
$$

The own-period efficiency change and best-practice gaps are

$$
EC_G^{t,u}=\frac{d^u(z^u)}{d^t(z^t)},\qquad
BPG^\sigma=\frac{d^G(z^\sigma)}{d^\sigma(z^\sigma)}.
$$

Because the global CRS technology contains each contemporaneous CRS
technology, $0<BPG^\sigma\le1$ on the certified positive-distance domain.
Best-practice change is

$$
BPC_G^{t,u}=\frac{BPG^u}{BPG^t},\qquad
GM=EC_G\times BPC_G.
$$

Only four self-contained tasks are required for a transition:
`base_on_base`, `comparison_on_comparison`, `base_on_global`, and
`comparison_on_global`. No plan is evaluated against the other period's
technology.

## Time and reference contract

- The global reference contains every eligible observation in the fixed
  declared sample vintage, including observations not retained as matched
  transition recipients.
- Adding or revising observations changes the vintage and requires all global
  distances to be recomputed.
- The source ratio can compare any two dates within one fixed vintage. The
  public package defaults to identifier-matched adjacent transitions through
  `comparison_pairs="adjacent"`. `comparison_pairs="all"` opts into every
  forward pair in the declared period order, while an explicit ordered
  sequence such as `((2020, 2023),)` requests only those unique forward pairs.
  These are evaluation-protocol choices, not different formulas.
- `unbalanced="drop"` or `"raise"` is applied separately to every selected
  pair. An unmatched organization can still contribute to the fixed global
  reference even when it receives no change row for that pair.
- With $D$ organizations and $P$ balanced periods, all-pairs output has
  $D P(P-1)/2=O(DP^2)$ transition rows and four logical role records per row.
  The task cache still needs at most one own-period and one global solve per
  observation, $2DP=O(DP)$ solves. Nonadjacent ratios are assembled from these
  solved tasks without an additional optimization.
- Circularity follows inside one frozen global reference:

  $$
  GM^{t,t+1}GM^{t+1,t+2}=GM^{t,t+2}.
  $$

  Values computed from different global vintages cannot be combined under
  this identity.

## Independent certificate

The certificate in
`specs/oracles/pastor-lovell-2005-global-malmquist-analytical.md` uses a
strictly positive three-period rational panel. Its dense source compiler in
`tests/test_pastor_lovell_2005_global_malmquist_source.py` imports no DEAPack
module and directly assembles every CRS output LP with SciPy. It verifies:

- all six own-period and global efficiency-form distances;
- unique own-period and global peers in the teaching fixture;
- four exact adjacent GM, EC, BPC, and BPG accounts;
- the $GM=EC_G\times BPC_G$ identity;
- fixed-vintage circularity over three periods; and
- invariance to coherent positive changes in input and output units.

`tests/test_global_malmquist.py::test_public_api_matches_exact_pastor_lovell_three_period_oracle`
checks the default adjacent public result against the independently derived
values, task roles, peer provenance, global sample membership, and canonical
method ID. `tests/test_m13_global_comparison_pairs.py` additionally checks the
direct $t_0$-to-$t_2$ rows, fixed-vintage circularity, explicit pair ordering,
per-pair matching, and the unchanged $2DP$ solve graph under all-pairs output.

## Validation boundary

The analytical certificate is claim-scoped to:

- CRS;
- output orientation;
- nonnegative desirable input/output quantities with positive row aggregates;
- one pooled raw-observation global DEA cone and own-period DEA cones;
- self-inclusive references;
- one fixed global sample vintage; and
- matched forward transitions selected by the adjacent default, the opt-in
  all-forward policy, or an explicit unique forward-pair sequence.

The package permits input orientation and explicit non-CRS sensitivity
specifications, but they do not inherit this source certificate. CRS
input/output agreement retains separate property-test support. The certificate
does not cover undesirable outputs, sequential/biennial/window references,
external or leave-one-out references, inference, causal attribution,
profitability, welfare, or the source article's empirical application.
