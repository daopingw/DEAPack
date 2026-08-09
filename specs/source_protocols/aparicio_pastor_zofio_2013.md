# APZ bounded-bad technology and Malmquist--Luenberger consistency (2013/2017)

## Readiness record

| Field | State |
|---|---|
| Canonical preset identifier | `productivity.malmquist_luenberger.aparicio_pastor_zofio_2013` |
| Discovery alias | `productivity.malmquist_luenberger.apz` — lookup label only, never a machine identity |
| 2013 theoretical source | `primary_author_working_paper_page_frozen` |
| 2013 final EJOR version | `bibliographic_record_only_not_line_checked` |
| 2017 operational source | `final_journal_article_page_frozen` |
| Equation audit | `closed_for_2013_theory_and_2017_equations_5_6` |
| Source gate | **PASS** |
| Executable specification gate | **PASS for the exact 2017 CRS domain below** |
| Published empirical results | `located_but_raw_panel_and_pipeline_not_frozen` |
| Independent exact oracle | **PASS — `analytically_derived`** |
| Source-only oracle tests | **PASS — `5_passed`** |
| Implementation status | **PASS — `implemented_public`** |
| Overall release disposition | `current_2.0_development_scope_certified` |
| Public API | **PASS — `APZMalmquistLuenbergerProductivityIndex` plus exact alias** |
| Registry status | **PASS — public `preset_id` in shadow release `.49`** |
| Last access audit | 2026-07-31 |

The 2017 operational article changes the conclusion of the earlier source
audit.  The APZ proposal is no longer missing a finite-dimensional DEA
formulation: equations (5)--(6) specify a CRS environmental technology and a
general LP for multiple inputs, desirable outputs, and undesirable outputs.
The source identity and the machine-level mathematical identity are therefore
closed for that stated domain.

The independent exact oracle is closed in
`specs/oracles/aparicio_pastor_zofio_2013.md`.  It analytically derives the
ordinary and APZ distances and accounts for the 2013 Table 1 data, while a
production-free source compiler verifies the certificate in five tests.  The
public production implementation is independently checked against that
compiler and exact certificate; it is no longer blocked, deferred, or merely
an implementation candidate.

The 2017 article's WIOD empirical tables still cannot be reproduced from the
materials in the repository.  That published-application reproduction remains
deferred as a separate evidence layer and does not reopen the exact-oracle or
production-implementation gates.

The evidence also clarifies the software architecture.  APZ is not a
post-processing correction to an already-computed Chung--Färe--Grosskopf
index.  It is the ordinary four-distance Malmquist--Luenberger composition
evaluated on a distinct bounded-bad production technology.  The natural
implementation unit is therefore an APZ technology/source leaf composed with
the ML operator.  The public implementation, registry record, API, tests,
benchmark, book, and package documentation preserve that composition.  Its
canonical machine identity is
`productivity.malmquist_luenberger.aparicio_pastor_zofio_2013`; the shorter
`productivity.malmquist_luenberger.apz` spelling is a discovery alias only and
must not appear as the registry key, serialized method identity, or result
provenance identifier.

## 1. Defining sources and audited artifacts

### 1.1 The 2013 theoretical article

The final bibliographic record is:

Juan Aparicio, Jesús T. Pastor, and José L. Zofío (2013), “On the
inconsistency of the Malmquist--Luenberger index,” *European Journal of
Operational Research*, 229(3), 738--742.
[DOI](https://doi.org/10.1016/j.ejor.2013.03.031);
[publisher record](https://www.sciencedirect.com/science/article/pii/S0377221713002592).

The equation freeze for the 2013 analysis uses the authors' complete
prepublication text:

- *Economic Analysis Working Paper Series*, ISSN 1885-6888, Working Paper
  1/2013, Universidad Autónoma de Madrid;
- cover title: “On the inconsistency of the Malmquist-Luenberger index”;
- cover authors: Juan Aparicio, Jesús T. Pastor, and José L. Zofío;
- 19 PDF pages, comprising one cover and internally numbered pages 1--18;
- public institutional-repository locator:
  [UAM author working paper](https://repositorio.uam.es/bitstream/handle/10486/662658/Malmquist-Luenberg%20Index_Aparicio_EAWPS_2013.pdf?sequence=1);
- audited private review copy (not distributed with DEAPack);
- byte size: `116378`;
- SHA-256:
  `6d339b20b00356577f51dd9ef3a772aa3080bbedfafb31128a51d9a00400bf11`.

The source was obtained through the ordinary public UAM repository route.  No
authentication circumvention, paywall bypass, alternate-host reconstruction,
or restricted-endpoint workaround is part of this evidence.  The local copy
is a temporary audit artifact, not a redistribution commitment.  The final
typeset 2013 EJOR article has not separately been compared line by line.  This
remaining bibliographic check does not reopen the operational LP, because the
2017 final article explicitly restates the relevant APZ postulate and supplies
the implementation that the 2013 article did not contain.

### 1.2 The 2017 operational article

The operational source is:

Juan Aparicio, Javier Barbero, Magdalena Kapelko, Jesús T. Pastor, and José L.
Zofío (2017), “Testing the consistency and feasibility of the standard
Malmquist-Luenberger index: Environmental productivity in world air
emissions,” *Journal of Environmental Management*, 196, 148--160.
[DOI](https://doi.org/10.1016/j.jenvman.2017.03.007).

The audited artifact is the final journal PDF:

- audited private review copy (not distributed with DEAPack);
- journal pagination: 148--160;
- PDF page count: `13`;
- byte size: `594212`;
- SHA-256:
  `e1fdb6f414e67dc2de5da27acf21e1830d1613c300f21841e8050fc14b636dba`;
- PDF title: “Testing the consistency and feasibility of the standard
  Malmquist-Luenberger index: Environmental productivity in world air
  emissions”;
- PDF author metadata: `Juan Aparicio`.

All 13 pages were rendered and visually inspected, and the searchable text was
checked against the displayed equations and numerical tables.  Equations
(5)--(6) on journal pages 152--153 are legible and complete.  The artifact was
supplied locally for audit; this protocol does not infer a public acquisition
route or a right to redistribute the publisher PDF.

## 2. Common economic object and distance convention

For each period, the 2017 article observes $K$ producers.  Producer $k$ uses
$N$ nonnegative inputs $x_k\in\mathbb R_+^N$ to produce $M$ nonnegative
desirable outputs $y_k\in\mathbb R_+^M$ and $I$ nonnegative undesirable
outputs $b_k\in\mathbb R_+^I$.  The output correspondence is
$P(x)\subseteq\mathbb R_+^{M+I}$.

Economically, undesirable outputs remain joint products of production.  They
are not silently recoded as inputs.  The compactness requirement says that a
finite input bundle cannot support unbounded amounts of either desirable or
undesirable output.

Equation (1) of the 2017 article defines the output directional distance:

$$
\vec D_o(x,y,b;g)
=\sup\{\beta:(y,b)+\beta g\in P(x)\}.
$$

The standard environmental direction is observation-specific,
$g=(y,-b)$.  A positive $\beta$ has the economic meaning of a common
proportional expansion of desirable outputs and contraction of undesirable
outputs, holding inputs fixed and respecting the reference technology.  The
direction in a cross-period task still belongs to the **target** observation;
it must not be replaced by the reference period's output vector or by a pooled
average.

For concise notation, define

$$
d_s^h
=\vec D_o^s(x_0^h,y_0^h,b_0^h;y_0^h,-b_0^h),
\qquad s,h\in\{t,t+1\},
$$

where $s$ identifies the reference technology and $h$ identifies the target
observation.  Equations (2)--(4) retain the conventional four-distance
Malmquist--Luenberger composition:

$$
ML^s=\frac{1+d_s^t}{1+d_s^{t+1}},
\qquad s\in\{t,t+1\},
$$

$$
MLEFFCH
=\frac{1+d_t^t}{1+d_{t+1}^{t+1}},
$$

$$
MLTECH^t
=\frac{1+d_{t+1}^{t+1}}{1+d_t^{t+1}},
\qquad
MLTECH^{t+1}
=\frac{1+d_{t+1}^{t}}{1+d_t^{t}},
$$

and

$$
ML_t^{t+1}
=\left(ML^tML^{t+1}\right)^{1/2}
=MLEFFCH\,
 \left(MLTECH^tMLTECH^{t+1}\right)^{1/2}.
$$

Values above one denote productivity improvement, catch-up, or technical
progress for the corresponding index component; values below one denote
regress.  These values are economic comparisons of feasible performance, not
post-hoc sign labels.

## 3. What the 2013 article established

The 2013 paper showed that the conventional weak-disposability DEA technology
can yield technical-change signs that conflict with the observed managerial
pattern of increasing desirable output while reducing pollution.  It added
the following bounded bad-output expansion condition, labelled A7 there:

$$
(y,b)\in P(x),\quad b\le b'\le\bar b(x)
\quad\Longrightarrow\quad
(y,b')\in P(x).
$$

Economically, if a production plan is feasible, recording a larger quantity
of each undesirable joint product remains feasible only up to a declared
physical or empirical bound.  This is neither unrestricted bad-output free
disposal nor the treatment of bad outputs as ordinary inputs.

The 2013 one-bad-output illustration combined that postulate with nested
period technologies and a common adjacent-period cap.  It was a sufficient
construction for the consistency proof in that example.  The 2013 article did
not display a general LP implementing A7, and the earlier version of this
protocol consequently left the executable identity open.

For comparison, equation (6) of the 2013 working paper used the conventional
CRS DEA approximation

$$
P_{CFG}^s(x)=\left\{(y,b):
\sum_{k=1}^Kz_k y_k^s\ge y,\quad
\sum_{k=1}^Kz_k b_k^s=b,\quad
\sum_{k=1}^Kz_k x_k^s\le x,\quad
z_k\ge0\right\}.
$$

The bad-output equality is the decisive contrast with the 2017 APZ
technology.  Neither source adds a VRS equation.  In the 2013 illustrative
construction, the additional assumptions were

$$
P^t(x)\subseteq P^{t+1}(x)
$$

and, for its single undesirable output,

$$
\bar b^t(x)=\bar b^{t+1}(x)
=\max_{\substack{k=1,\ldots,K\\s\in\{t,t+1\}}}\{b_k^s\}.
$$

Those formulas freeze what the historical example did; they do not supersede
the period-specific multi-pollutant cap in 2017 equation (6).

### 3.1 The 2013 sign-and-failure example

Table 1 of the 2013 working paper gives a complete one-input, one-good,
one-bad dataset:

| Observation | $x$ | $y$ | $b$ |
|---|---:|---:|---:|
| $A^t$ | 1 | 7 | 2 |
| $B^t$ | 1 | 5 | 5 |
| $A^{t+1}$ | 1 | 8 | 1 |
| $B^{t+1}$ | 1 | 5.5 | 3 |

For producer $B$, the paper establishes that both own-period distances are
zero and hence $MLEFFCH=1$; the conventional technology produces a
technical-change value below one despite the observed increase in the good
output and decrease in pollution; and the reverse cross-period problem is
infeasible.  It also notes possible Pareto--Koopmans slacks.  Under the A7
bounded/nested illustrative technology, the technical-change terms have the
intended greater-than-one sign.

The source publishes zeros, inequalities, and infeasibility, but not all four
cross-period distances, primal solutions, or a complete numerical component
vector.  Table 1 is therefore a strong historical sign-and-failure oracle, not
an exact numerical oracle for the general 2017 APZ LP.

The 2017 article explicitly fills that gap.  It relabels the relevant
conditions as compactness A1 and bounded bad-output expansion A2, then gives
equations (5)--(6).  Its operational technology uses a separate cap for each
pollutant and each reference period.  It does **not** impose nested,
sequential, global, biennial, or pooled reference technologies.  The 2013
nested illustration must therefore remain historical motivation rather than
be promoted into a mandatory 2017 implementation rule.

## 4. Operational APZ production technology: equation (5)

For a period-$s$ reference sample and an input bundle $x$, equation (5), with
period labels generalized from the displayed period $t$, is

$$
\begin{aligned}
P^s(x)=\{(y,b)\in\mathbb R_+^M\times\mathbb R_+^I:\;&
\sum_{k=1}^{K}z_k y_{km}^s\ge y_m,
&&m=1,\ldots,M,\\
&\sum_{k=1}^{K}z_k b_{ki}^s\le b_i,
&&i=1,\ldots,I,\\
&\sum_{k=1}^{K}z_k x_{kn}^s\le x_n,
&&n=1,\ldots,N,\\
&b_i\le\bar b_i^s(x),
&&i=1,\ldots,I,\\
&z_k\ge0,
&&k=1,\ldots,K\}.
\end{aligned}
$$

Proposition 1 specifies the cap componentwise as

$$
\bar b_i^s(x)=\max_{1\le k\le K}\{b_{ki}^s\},
\qquad i=1,\ldots,I.
$$

Although the source retains $x$ in the notation for the conditional bound,
the displayed operational formula is the maximum observed amount of pollutant
$i$ in the **reference period**.  It is not estimated from a global maximum,
from the target period, from both adjacent periods, or from producers selected
by input similarity.  The cap vector must be recomputed whenever the reference
period changes.

The technology has the following source-frozen properties:

- multiple undesirable outputs are supported componentwise;
- desirable outputs use the usual output-dominance inequalities;
- the activity-combination amount of each undesirable output is no greater
  than the candidate undesirable-output coordinate;
- the candidate undesirable-output coordinate is itself capped by the
  reference-period maximum;
- inputs are freely disposable through the usual input-dominance
  inequalities;
- intensities are nonnegative; and
- no equation $\sum_k z_k=1$ appears, so the technology is CRS/conical.

Adding VRS, changing the bad-output inequality to equality, using a common
two-period cap, or replacing the componentwise caps by a scalar cap would
define a different model and would not inherit this source certificate.

## 5. Operational directional-distance LP: equation (6)

Equation (6) evaluates target producer $0$ from period
$h\in\{t,t+1\}$ against the period-$s$ reference technology,
$s\in\{t,t+1\}$:

$$
\begin{aligned}
d_s^h=\max_{\beta,z}\quad &\beta \\
\text{s.t.}\quad
&\sum_{k=1}^{K}z_k y_{km}^s
 \ge y_{0m}^h+\beta y_{0m}^h,
&&m=1,\ldots,M,\\
&\sum_{k=1}^{K}z_k b_{ki}^s
 \le b_{0i}^h-\beta b_{0i}^h,
&&i=1,\ldots,I,\\
&\sum_{k=1}^{K}z_k x_{kn}^s
 \le x_{0n}^h,
&&n=1,\ldots,N,\\
&b_{0i}^h-\beta b_{0i}^h
 \le\bar b_i^s(x_0^h),
&&i=1,\ldots,I,\\
&z_k\ge0,
&&k=1,\ldots,K.
\end{aligned}
$$

The typeset final PDF renders the subscript in the last nonnegativity line of
equations (5) and (6.6) as $z_n$ while simultaneously indexing that line by
$k=1,\ldots,K$.  All preceding sums use $z_k$, and the proof of Proposition 1
immediately begins with “given $z_k\ge0$.”  This is a source typography error,
not a second intensity family; the executable transcription above correctly
uses $z_k$.

The source displays no nonnegativity constraint on $\beta$; the DDF definition
also takes a supremum over feasible movements without imposing
$\beta\ge0$.  An implementation must therefore treat $\beta$ as a free
continuous variable unless a separately sourced variant says otherwise.
Silently accepting a solver's nonnegative-variable default would change
cross-period feasibility and distance values.

The target observation supplies $x_0^h$, $y_0^h$, $b_0^h$, and hence the
direction $(y_0^h,-b_0^h)$.  The reference period supplies the peer data and
the cap.  The cap constraint applies to the projected undesirable-output
coordinate $b_0^h-\beta b_0^h$ for every pollutant.  There is no scalar
shortcut for the general $I$-pollutant case.

## 6. Period/reference policy and task compiler

The APZ index uses two distinct contemporaneous technologies and the ordinary
four own-/cross-period tasks:

| Distance | Reference observations and cap | Target bundle and direction |
|---|---|---|
| $d_t^t$ | period $t$ | period $t$ |
| $d_t^{t+1}$ | period $t$ | period $t+1$ |
| $d_{t+1}^{t}$ | period $t+1$ | period $t$ |
| $d_{t+1}^{t+1}$ | period $t+1$ | period $t+1$ |

For every row, the compiler must:

1. select only the observations from reference period $s$;
2. calculate each $\bar b_i^s$ from those same reference observations;
3. retain the target bundle from period $h$;
4. build the target-specific direction $(y_0^h,-b_0^h)$; and
5. solve equation (6) without pooling either data or caps across periods.

The policy is therefore `contemporaneous_four_task`, not `sequential`,
`global`, `biennial`, or `adjacent_pair_pool`.  A sequential technology can be
studied as a distinct extension, but it is not equation (6) of the audited
2017 operational source.

## 7. Certified domain, returns to scale, and failure semantics

The general variable domains in the article are nonnegative.  Proposition 1's
compactness result is stated under the stronger reference-data conditions

$$
x_k^s\in\mathbb R_{++}^N,
\qquad
b_k^s\in\mathbb R_{++}^I,
\qquad k=1,\ldots,K,
$$

with desirable outputs in $\mathbb R_+^M$.  The first implementation and its
oracle must stay within this strictly positive input-and-bad-output domain.
Zero-input, zero-bad, signed-data, translated-data, VRS, and unbalanced-panel
extensions require separate proofs and source protocols.

The certified operational domain is thus:

- $N\ge1$ inputs, $M\ge1$ desirable outputs, and $I\ge1$ undesirable
  outputs;
- positive reference inputs and undesirable outputs;
- nonnegative desirable outputs;
- CRS/conical intensity scaling;
- proportional target direction $(y_0^h,-b_0^h)$; and
- a separate componentwise observed-maximum cap for every reference period.

The 2017 article reports that the APZ postulate substantially reduces but does
not eliminate cross-period infeasibility.  Consequently:

- `infeasible` is a legitimate task outcome and must not be converted to zero;
- all four distances are required for the geometric ML index and its complete
  decomposition;
- if a required cross-period task is infeasible, dependent components and the
  aggregate index are unavailable with an explicit reason;
- a different reference technology must not be substituted automatically;
- no sign correction or residual adjustment may be applied after solving; and
- Pareto--Koopmans slacks, if reported, are diagnostics and do not silently
  redefine the radial directional distance.

Every successful result must reconstruct the source equations numerically:

$$
ML_t^{t+1}
=\left(ML^tML^{t+1}\right)^{1/2}
=MLEFFCH\left(MLTECH^tMLTECH^{t+1}\right)^{1/2}
$$

within the declared tolerance.

## 8. Published empirical evidence and reproduction status

The 2017 application uses a balanced panel of 39 countries over 1995--2007.
The study has one desirable output (gross value added), two inputs (labour and
capital), and seven possible air emissions: $CO_2$, $CH_4$, $N_2O$, $NO_x$,
$SO_x$, $NH_3$, and NMVOC.  Monetary variables are reported in purchasing
power parity US dollars at constant 1995 prices, and Taiwan is excluded.  The
principal country comparison in Table 3 uses $CO_2$ and $NO_x$.

The article reports that the models were solved with the MATLAB DEA Toolbox,
using dual simplex, an optimality tolerance of $10^{-10}$, and a constraint
tolerance of $10^{-7}$.  An infeasible task was reported as “No feasible point
was found”; dashes in the conventional CFG results denote unavailable values.

Across all 127 nonempty pollutant subsets, 12 adjacent transitions, and 39
countries, Table 4 implies $59{,}436$ LP tasks.  Table 5 reports the following
aggregate counts:

| Number of bad outputs | LP tasks | CFG infeasible | APZ infeasible | Infeasible under either | CFG inconsistent $ML$ | CFG inconsistent $MLEFFCH$ | CFG inconsistent $MLTECH$ |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 3,276 | 193 | 61 | 240 | 53 | 177 | 106 |
| 2 | 9,828 | 2,062 | 177 | 2,205 | 603 | 1,001 | 887 |
| 3 | 16,380 | 6,626 | 284 | 6,856 | 1,445 | 2,366 | 1,850 |
| 4 | 16,380 | 9,856 | 278 | 10,084 | 1,180 | 2,300 | 1,597 |
| 5 | 9,828 | 7,367 | 162 | 7,507 | 437 | 1,145 | 708 |
| 6 | 3,276 | 2,783 | 52 | 2,831 | 84 | 318 | 139 |
| 7 | 468 | 425 | 7 | 432 | 7 | 34 | 13 |
| **Total** | **59,436** | **29,312** | **1,021** | **30,155** | **3,809** | **7,341** | **5,300** |

These tables are valuable published comparison targets, but they are not
independently reproduced empirical oracles:

- Table 2 contains selected descriptive statistics, not the complete
  country-year input/output panel;
- Table 3 contains selected, rounded country results rather than all four
  task-level distances and primal solutions;
- Tables 5--7 contain aggregate counts or distributional summaries, so many
  distinct implementations could match an aggregate while differing on
  individual tasks;
- the exact frozen WIOD vintage, extracted country panel, transformations,
  missing-data decisions, pollutant-combination pipeline, and toolbox version
  are not present in the repository; and
- rounded publication tables cannot establish exact LP equivalence or expose
  a swapped target/reference role.

The empirical evidence is therefore classified as
`published_aggregate_comparison_not_reproduced`.  Once the exact data and
preprocessing pipeline are lawfully obtained and frozen, Table 3 can become a
rounded country-level regression target and Tables 4--7 can become aggregate
acceptance checks.  They would complement, not replace, the analytically
derived exact oracle that is already frozen for the source Table 1 branch.

## 9. Closed independent exact oracle

The exact certificate is frozen in
`specs/oracles/aparicio_pastor_zofio_2013.md` with evidence status
`analytically_derived`.  It uses the 2013 Table 1 data, transcribes the 2013
ordinary technology and the 2017 equations (5)--(6) independently of the
production implementation, and treats $\beta$ as free.

For the conventional CRS technology, the exact task account is:

| Task | Exact distance | Exact peer intensities | Status |
|---|---:|---:|---|
| $d_t^t$ | $0$ | $(0,1)$ | optimal |
| $d_t^{t+1}$ | $5/21$ | $(19/21,2/21)$ | optimal |
| $d_{t+1}^{t}$ | -- | -- | infeasible |
| $d_{t+1}^{t+1}$ | $0$ | $(0,1)$ | optimal |

The finite conventional component is $MLTECH^t=21/26<1$, while the reverse
cross-period task remains infeasible and prevents a complete conventional
geometric account.

For the 2017 APZ technology, with independently compiled reference-period caps
$\bar b^t=5$ and $\bar b^{t+1}=3$, all four tasks are feasible:

| Task | Exact distance | Exact peer intensities |
|---|---:|---:|
| $\bar d_t^t$ | $2/5$ | $(1,0)$ |
| $\bar d_t^{t+1}$ | $3/11$ | $(1,0)$ |
| $\bar d_{t+1}^{t}$ | $3/5$ | $(1,0)$ |
| $\bar d_{t+1}^{t+1}$ | $5/11$ | $(1,0)$ |

The resulting exact account is

$$
\overline{ML}^t=\overline{ML}^{t+1}=\frac{11}{10},\qquad
\overline{MLEFFCH}=\frac{77}{80},\qquad
\overline{MLTECH}^t=\overline{MLTECH}^{t+1}=\frac87,
$$

and hence

$$
\overline{ML}_t^{t+1}
=\frac{77}{80}\times\frac87
=\frac{11}{10}.
$$

The source-only test module
`tests/test_aparicio_pastor_zofio_2013_source.py` imports no DEAPack module and
shares no production LP builder.  Its five tests verify the published sign and
failure claims, the exact ordinary and APZ optima, the cap policy, complete
account reconstruction, non-equivalence to post-processing, and the oracle's
claim scope.  This closes the independent exact-oracle gate as **PASS**.

The certificate is intentionally narrow: one input, one desirable output, one
undesirable output, two adjacent periods, CRS, and the source Table 1
observations.  The 2017 source itself specifies the general multi-bad domain;
multi-bad runtime coverage and public result-contract validation belong to the
  public production tests.  They do not make the independent exact-oracle
  gate open again.

## 10. Gate verdict and non-equivalence boundary

The evidence supports the following precise decision:

| Gate | Verdict | Reason |
|---|---|---|
| Defining literature acquired | **PASS** | Complete 2013 author text and final 2017 operational article audited |
| Mathematical identity | **PASS** | Equation (5) technology, equation (6) LP, caps, direction, CRS, and four task roles are explicit |
| Machine-executable specification | **PASS** | No remaining source choice is needed inside the certified 2017 domain |
| Independent exact oracle | **PASS** | Analytically derived Table 1 certificate and production-free source compiler are frozen; five tests pass |
| Published empirical reproduction | **DEFER** | Exact panel and preprocessing/toolchain are not frozen |
| Production implementation | **PASS** | Public sparse implementation matches the independent exact oracle, general $N/M/I$ tests, cap diagnostics, and failure contract |
| Package release certification | **PASS for the current 2.0 development scope** | Public API, `.48` registry record, targeted and full tests, strict English book/docs builds, and benchmark are present; this is not an archival PyPI release claim |

The source, executable-specification, independent exact-oracle, production,
and current-development release gates have therefore passed.  Only
reproduction of the published WIOD application remains deferred; that
separate empirical gate does not weaken the exact analytical claim.

This public preset remains non-equivalent to:

- the conventional Chung--Färe--Grosskopf environmental technology with bad
  equalities;
- Oh's global Malmquist--Luenberger index;
- a generic sequential or adjacent-pair pooled reference policy;
- a VRS version created by adding $\sum_k z_k=1$;
- by-production, activity-specific, weak-G disposability, material-balance,
  or unrestricted bad-output disposal technologies;
- an APZ-like scalar cap applied to several pollutants; and
- a post-processing switch that changes `technical_change` after conventional
  distances have been solved.

The implementation preserves APZ as a technology/assumption composed with the
existing Malmquist--Luenberger task graph.  Its public result records expose
provenance, cap vectors, reference/target roles, solver status, and
reconstruction residuals.  Production tests reproduce the closed exact
certificate without sharing its independent compiler.
