# Oh (2010) global Malmquist--Luenberger source protocol

## Source identity

- Dong-hyun Oh, “A Global Malmquist--Luenberger Productivity Index,”
  *Journal of Productivity Analysis* 34 (2010), 183--197.
- DOI:
  [10.1007/s11123-010-0178-y](https://doi.org/10.1007/s11123-010-0178-y).
- Defining evidence: the final journal article, not a reconstruction from a
  later application.
- Technology predecessor: Chung, Färe, and Grosskopf (1997),
  [10.1006/jema.1997.0146](https://doi.org/10.1006/jema.1997.0146).

The source-qualified package leaf is
`productivity.global_malmquist_luenberger.oh_2010`. This protocol freezes
Oh's retrospective common-benchmark environmental productivity account. It
does not make the historical name available to arbitrary directions,
returns-to-scale assumptions, bad-output technologies, or temporal reference
rules.

## Primary-source claim locators

| Source location | Claim frozen here |
|---|---|
| p. 186, Eq. (3) | Directional distance expands desirable output and contracts undesirable output; Oh uses the observation-scaled direction $g=(y,b)$ |
| pp. 186--187 | A contemporaneous technology uses observations from one period; one global benchmark is formed from all period technologies |
| p. 187 | GML is the ratio of two directional-distance factors evaluated against the same global benchmark |
| p. 187, Eq. (8) | $GML=EC\times BPC$, with contemporaneous efficiency change and best-practice-gap change |
| p. 188 | The empirical production sets use CRS; BPG represents the period-to-global best-practice gap; GML avoids the two cross-period feasibility problems |
| pp. 195--196, Proposition 1 | GML and its components are circular while the global information set is fixed |
| p. 195 | Adding periods changes the information set and requires historical GML values to be recalculated |

These locators support the narrow account below. They do not by themselves
validate a different environmental technology that happens to use a
full-sample reference.

## Economic production account

For an operating plan $z=(x,y,b)$:

- $x$ records productive resources;
- $y$ records desirable products or services; and
- $b$ records jointly produced undesirable residuals.

Oh's p. 186 directional distance is

$$
D(x,y,b;g_y,g_b)
=
\max\{\beta:(y+\beta g_y,\ b-\beta g_b)\in P(x)\}.
$$

The named index uses $g=(g_y,g_b)=(y,b)$. Inputs are held fixed. A positive
$\beta$ therefore describes an attainable management programme that raises
the observed mix of desirable services while reducing the observed mix of
residuals by the same proportional score. It is an opportunity measure, not
a monetary valuation of pollution or a causal effect of management or
regulation.

The maintained production account treats desirable output as strongly
disposable, desirable and undesirable output as jointly weakly disposable,
and retains null jointness. Under the source's CRS empirical construction,
the period-$r$ programme is

$$
\begin{aligned}
\max_{\lambda,\beta}\quad &\beta\\
\text{s.t.}\quad
&X^r\lambda\leq x_o,\\
&Y^r\lambda\geq(1+\beta)y_o,\\
&B^r\lambda=(1-\beta)b_o,\\
&\lambda\geq0.
\end{aligned}
$$

There is no intensity-sum equation. The equality in the residual account is
part of the CRS common-factor weak-disposal construction; adding a VRS
convexity equation would not preserve this named technology.

## Contemporaneous and global benchmarks

The contemporaneous technology $P^r$ represents environmental production
opportunities observed in period $r$. Its managerial question is: how much
of the declared service-growth and residual-reduction programme remains
available relative to the practices represented in that period?

The paper prints the global technology as

$$
P^G=P^1\cup P^2\cup\cdots\cup P^T
$$

and describes it as one benchmark that envelopes all contemporaneous
technologies. A literal set union and a convex or conical envelope are not
identical in general. The paper then states on p. 188 that its distances are
calculated by DEA under CRS, while omitting the full linear programme.

DEAPack operationalizes that empirical instruction as one pooled CRS
conical envelope:

$$
\mathcal T^G
=
\left\{
(x,y,b):
X^G\lambda\leq x,\;
Y^G\lambda\geq y,\;
B^G\lambda=b,\;
\lambda\geq0
\right\},
$$

where the columns of $(X^G,Y^G,B^G)$ are all observations in the declared
sample vintage. This protocol does not claim the set-theoretic identity
“literal union equals conical hull.” It freezes the pooled DEA envelope as
the source-compatible computational meaning of Oh's single global
benchmark. A future literal-union estimator would be a separate method and
would require its own feasibility, decomposition, and validation contract.

## GML and its economic decomposition

Let

$$
F_r^G=1+D^G(z^r;y^r,b^r),
\qquad
F_r^r=1+D^r(z^r;y^r,b^r).
$$

Oh's p. 187 global index is

$$
GML^{t,t+1}
=
\frac{F_t^G}{F_{t+1}^G}
=
\frac{1+D^G(z^t;y^t,b^t)}
     {1+D^G(z^{t+1};y^{t+1},b^{t+1})}.
$$

A value above one means that the later operating plan has less unrealized
environmental production potential relative to the same retrospective
benchmark.

The contemporaneous operating-performance component is

$$
EC^{t,t+1}
=
\frac{F_t^t}{F_{t+1}^{t+1}}.
$$

It records whether the producer catches up with or falls behind the
opportunities represented in its own period. Define the period-specific
best-practice gap by

$$
BPG^r
=
\frac{1/(1+D^G(z^r;y^r,b^r))}
     {1/(1+D^r(z^r;y^r,b^r))}
=
\frac{F_r^r}{F_r^G}.
$$

This is Oh's source-native Eq. (9) orientation. Because the global benchmark
contains the period benchmark, $0<BPG^r\leq1$ for a defined self-inclusive
source task, up to numerical tolerance. A value closer to one means that
period-specific best practice is closer to the strongest environmental
production opportunities represented anywhere in the fixed sample.

Oh's Eq. (8) defines

$$
BPC^{t,t+1}
=
\frac{BPG^{t+1}}{BPG^t},
\qquad
GML^{t,t+1}=EC^{t,t+1}BPC^{t,t+1}.
$$

Thus $BPC>1$ indicates a narrowing of the period-to-global
best-practice gap. It is not the conventional Malmquist--Luenberger
technical-change component: that component uses two off-diagonal
period-to-period evaluations, while BPC compares both periods with one
retrospective benchmark.

## Feasibility and the sign of the source tasks

Oh's GML needs four source roles for each reported transition:

| Role | Evaluated plan | Reference |
|---|---|---|
| `base_on_base` | $z^t$ | $P^t$ |
| `comparison_on_comparison` | $z^{t+1}$ | $P^{t+1}$ |
| `base_on_global` | $z^t$ | $\mathcal T^G$ |
| `comparison_on_global` | $z^{t+1}$ | $\mathcal T^G$ |

It does not need `comparison_on_base` or `base_on_comparison`. Those
off-diagonal tasks are the source of the conventional ML feasibility
problem discussed on pp. 187--188.

Every plan is a member of its own contemporaneous reference and of the
full-sample global reference. Choosing its self intensity equal to one and
$\beta=0$ is therefore feasible. Consequently, all four own/global
distances above have an optimum $\beta\geq0$, subject only to numerical
tolerance. An unrestricted solver variable may be retained by a shared
kernel, but a negative optimal global or own-period distance is not a
source-supported outcome for this self-inclusive GML protocol.

## Circularity and information vintage

For any three periods evaluated with the same global benchmark,

$$
GML^{t,u}GML^{u,v}
=
\frac{F_t^G}{F_u^G}\frac{F_u^G}{F_v^G}
=
GML^{t,v}.
$$

Oh proves the corresponding circularity of GML, EC, and BPC in Proposition
1. This is an accounting consistency within one fixed information set. It
does not make the global benchmark contemporaneously available to managers
in early periods.

The package defaults to matched adjacent transitions through
`comparison_pairs="adjacent"`. Adjacency is not a theoretical restriction of
the GML ratio. `comparison_pairs="all"` opts into every forward period pair in
the declared order, and an explicit ordered sequence such as
`((1990, 2003),)` requests only those unique forward pairs. Endpoint and chained
comparisons are meaningful only when they use the same global sample vintage.

The panel matching policy is applied to each selected pair:
`unbalanced="drop"` omits unmatched recipients for that pair and
`unbalanced="raise"` rejects it. Either way, all valid observations remain in
the fixed global reference. Pair selection governs which change accounts are
reported; it does not shrink the retrospective benchmark.

For $D$ organizations observed in $P$ balanced periods, all-pairs reporting
produces $D P(P-1)/2=O(DP^2)$ transition rows. It does not require a new
directional programme for every ratio. The cache solves each observation once
against its own-period technology and once against the global technology, at
most $2DP=O(DP)$ optimizations, and reuses those certified tasks to assemble
the nonadjacent accounts without an additional optimization. The larger output,
diagnostics, and peer tables still have quadratic pairwise size and are
therefore opt-in.

Adding a period or otherwise changing global reference membership changes
the retrospective information set. Historical global distances must then be
recomputed. Results from different sample vintages must not be spliced into
one circular chain.

## Evidence and deferral boundary

The analytical certificate is
`specs/oracles/oh-2010-global-malmquist-luenberger-analytical.md`. It derives
exact two- and three-period accounts without using a DEAPack production
compiler.

The public comparison-pair contract is checked in
`tests/test_m13_global_comparison_pairs.py`. The three-period source fixture
releases the exact direct endpoint $GML^{t_0,t_2}=32/17$, verifies that it
equals the product of the two adjacent changes, and independently counts the
same $2DP$ solver calls for adjacent and all-forward reporting.

Oh studies 26 countries over 1990--2003 using GDP, carbon dioxide and
sulphur-oxide emissions, labor, capital, and commercial energy. The article
reports data sources, transformations, descriptive statistics, and
aggregated results, but not the complete country-year input/output rows
needed to reconstruct every DEA reference set. DEAPack therefore makes no
claim to reproduce the published application. That empirical replay is
`deferred_to_next_version`.

The following are also outside this narrow source freeze and remain deferred
until independently sourced and validated:

- VRS, NIRS, NDRS, or scale decompositions;
- activity-specific weak disposal, strong disposal, by-production, material
  balance, network, or dynamic technologies;
- directions other than the observation-scaled $(0,y,b)$ programme;
- sequential, biennial, rolling-window, prospective, or literal-union
  reference policies;
- signed, interval, stochastic, or missing quantities;
- statistical inference, shadow-price interpretation, welfare measurement,
  abatement cost, and causal policy claims.
