# Path-based and multiplicative model design

This specification governs the standard hyperbolic, generalized-path,
Chavas--Cox generalized-distance, and multiplicative DEA families. It records
where numerical machinery may be shared without turning distinct economic
measures into aliases.

`static.generalized_distance.chavas_cox` and `static.multiplicative` are
executable public methods. The standalone standard-hyperbolic and other
generalized-path families remain planned and must not enter `list_methods()`
until their own validation gates are satisfied. At its balanced parameter,
GDF documents only a conditional reciprocal-path algebraic transformation;
it does not expose a result field named as standard hyperbolic efficiency or
promote `static.hyperbolic` as a separate public leaf.

## 1. The economic questions are different

| Family | Operating question | Canonical treatment |
|---|---|---|
| Farrell input | how much of every current input commitment could be saved while current outputs are maintained? | radial preset |
| Farrell output | how much could every current output be expanded with current inputs? | radial preset |
| standard hyperbolic | how far can inputs contract and outputs expand together under reciprocal proportional change? | independent measure family |
| generalized hyperbolic path | what joint input/output change is feasible along a source-qualified non-linear path? | path variant with its formula in provenance |
| Chavas--Cox generalized distance | how should a proportional performance gap be expressed through resource saving and service growth, and how does that account connect to profitability? | implemented independent parameterized family |
| multiplicative DEA | which piecewise Cobb--Douglas/log-linear production account envelops strictly positive observations? | independent technology and measure family |

A shared scalar search routine does not establish economic equivalence. Two
paths are aliases only when their target bundles, feasible set, native score,
and reported transformation agree for every admissible observation.

## 2. Standard hyperbolic efficiency

The following reciprocal convention is a **candidate comparison convention**,
not a source-frozen public method. If the complete defining source ultimately
uses bounded score $h$ for a nonnegative input--output observation
$(x_o,y_o)$ and declared technology $\mathcal T$, its programme would be

$$
h_o^*
=
\inf\left\{
  h>0:
  (h x_o,h^{-1}y_o)\in\mathcal T
\right\}.
$$

On that candidate convention, an observation already in the maintained
technology would ordinarily have $0<h_o^*\leq 1$, with one indicating that no
reciprocal proportional input contraction/output expansion is feasible. A
future released result would also have to report the target
$(h_o^*x_o,h_o^{*-1}y_o)$ and residual slacks.

This is neither an input-oriented Farrell score nor an output-oriented
Farrell score. It is also not a directional distance with an observation-
scaled straight line: the target follows a multiplicative reciprocal path.
The candidate model is a convex nonlinear programme in its scalar path
parameter under the standard convex technology; it cannot be advertised as
an LP merely because each fixed-parameter feasibility check is linear. The
complete defining-source, convention, and oracle freeze remains governed by
`source_protocols/standard_hyperbolic.md`.

## 3. Chavas--Cox generalized distance

The frozen public convention uses bearing parameter
$\alpha\in[0,1]$ and native bounded score

$$
D_G(x_o,y_o;\alpha)
=
\min_{\delta>0}
\left\{
\delta:
\left(\delta^{1-\alpha}x_o,\delta^{-\alpha}y_o\right)
\in\mathcal T
\right\}.
$$

The parameter states how the proportional improvement account is expressed
between resource saving and service growth:

- $\alpha=0$ protects observed services and gives the input-radial score
  $\delta=\theta^I$;
- $\alpha=1$ protects the observed resource budget and gives the bounded
  reciprocal output score $\delta=1/\phi^O$; and
- $\alpha=1/2$ gives a balanced reciprocal proportional path. If a
  source-native standard-hyperbolic leaf later proves the same complete
  composition and uses bounded score $h$, then $h=\sqrt{\delta}$ and
  $\delta=h^2$.

`score`, `efficiency`, and `generalized_distance` report $\delta$.
`resource_commitment` and `service_commitment` report
$\delta^{1-\alpha}$ and $\delta^{-\alpha}$, respectively.

Under the ordinary CRS cone,

$$
D_G(x_o,y_o;\alpha)=\theta_o^{CRS}
\quad\text{for every }\alpha\in[0,1].
$$

The score is invariant to that allocation across operating margins, but the target
contract and peer intensities change. Under VRS, the convexity restriction
prevents free rescaling, so $\alpha$ can change the score and comparator
mix.

The long result preserves three target stages:

- `path_target`: the algebraic performance contract;
- `phase_one_reference_activity`: the feasible peer activity establishing
  the score; and
- `target`: the row-scaled slack-completed peer activity.

The bearing parameter and these target stages are part of the method
identity, not optional interpretations attached to a generic path solver.
See [Chavas and Cox
(1999)](https://doi.org/10.1002/j.2325-8012.1999.tb00248.x) and the
source-qualified profitability treatment in [Zofío and Prieto
(2006)](https://doi.org/10.1007/s10108-006-9004-0).

## 4. Generalized paths

A generalized path is represented by explicit functions
$\psi_x(s;x_o,g_x)$ and $\psi_y(s;y_o,g_y)$, their admissible scalar interval,
and a monotonicity certificate. Its specification records:

- the defining source and canonical `path_id`;
- input and output path formulae;
- native score and any display transformation;
- directions, bearings, or exponents and their units;
- data domain and treatment of zero or signed coordinates;
- the expected ordering of feasible path points;
- target and strong-efficiency semantics; and
- compatibility with technology, productivity, valuation, and inference
  operators.

“Generalized hyperbolic” is not enough to instantiate a model. If two papers
use different path formulae or parameterizations, they remain separate
variants until an exact transformation is proved.

## 5. Multiplicative DEA

Multiplicative DEA combines inputs and outputs multiplicatively and obtains a
piecewise log-linear, equivalently piecewise Cobb--Douglas, empirical
envelopment. The public `static.multiplicative` identity is one family with
one shared sparse log-space compiler, not two nearly duplicate solvers. Its
two source-frozen catalog presets retain the distinct early formulations:

- `static.multiplicative.original.charnes_etal_1982`, exposed by
  `C2S2MultiplicativeDEA`, is the original log-conic model without a
  convexity identity. Every ordinary input and desirable output must be
  strictly greater than one, the common exponent floor is fixed at one, and
  the score can change when a coordinate is expressed in another positive
  unit.
- `static.multiplicative.invariant.charnes_etal_1983`, exposed by
  `InvariantMultiplicativeDEA`, adds `sum(lambda)=1` in log quantities and
  forms a log-convex piecewise Cobb--Douglas envelope. Every input and
  desirable output must be strictly positive. Independent positive
  coordinate rescaling leaves scores and the co-transformed targets
  unchanged. A finite positive exponent floor is an explicit score-power
  convention; it does not change the peer plan or target.

The defining sources are
[Charnes et al. (1982)](https://doi.org/10.1016/0038-0121(82)90029-5) and
[Charnes et al. (1983)](https://doi.org/10.1016/0167-6377(83)90014-7).
Both implemented variants exclude undesirable outputs. Zero or negative
ordinary quantities, interval/fuzzy observations, arbitrary epsilon repairs,
and additive translations are outside the public contract.

The words *log-conic* and *log-convex* describe the maintained empirical
technology after the source transformation. They are not ordinary CRS/VRS
labels: the 1983 convexity identity acts in log quantities, and the 1982 model
is not CCR. Likewise, the family is not ordinary radial DEA run after a
logged-data preprocessing step; logging changes the technology, score,
slacks, targets, and multiplier account together.

Results retain multiplicative efficiency, log inefficiency, log slacks, log
targets, original-unit targets where exponentiation is representable, peer
intensities, and source exponents. An original-unit overflow or underflow does
not erase the certified log result. The source profile is one self-inclusive
global cross-section. Panel data and non-global reference rules are supported
only as explicitly labelled package extensions; they do not inherit either
historical source profile.

Validation uses an independently compiled dense source programme and an exact
two-DMU analytical oracle for both variants, including scores, slacks, peers,
targets, unit behavior, and the exponent-floor power convention. This is not
a published numerical reproduction.

## 6. Numerical policy

### 6.1 Monotone path models

For a path with a proved monotone feasibility order, the default stable
implementation is:

1. compile the sparse reference technology once;
2. bracket the scalar path parameter;
3. update only the right-hand side for each feasibility evaluation;
4. use HiGHS feasibility solves inside safeguarded bisection; and
5. run the declared slack/target phase at the converged parameter.

This retains the zero-configuration SciPy/HiGHS dependency policy. A model
must report the bracket, absolute and relative score tolerances, number of
feasibility solves, final feasibility residual, and whether the scalar
solution is interval-valued at numerical precision.

Bisection is not exposed for a path whose feasibility order has not been
proved. Such a variant remains unsupported until a reliable optional
nonlinear/conic backend and validation oracle are available. An exact
semidefinite reformulation may be added later as an optional backend; it does
not become a base-installation requirement.

The implemented GDF uses faster exact reductions where the structure permits:

- $\alpha=0$ uses one input-radial LP;
- $\alpha=1$ uses one output-radial LP and reports its reciprocal;
- every CRS interior bearing uses one input-radial LP followed by the exact
  intensity rescaling; and
- only $0<\alpha<1$ under VRS uses fixed-$\delta$ LP feasibility checks
  and geometric bisection.

For interior VRS, the returned score is a certified feasible upper endpoint.
The result retains lower and upper bounds, absolute gap, iteration and solve
counts, and convergence status. Reference rows and the slack-completion
variables are scaled by variable-specific magnitudes; reported quantities and
slacks are restored to original units. The secondary objective maximizes
row-scaled slack, so target selection is invariant to independent positive
unit changes.

### 6.2 Multiplicative models

The two catalog presets use the same compiler. Named arrays are validated and
logged once at the data boundary; the selected reference rows, anchors, and
sparse equality template are compiled outside the per-DMU loop, frozen, and
reused. The 1983 branch anchors log coordinates under its convexity identity
for conditioning, while the 1982 branch keeps the source log-conic account.

The solver handles a normalized exponent-floor-one programme. The result
adapter rescales log inefficiency and certified dual exponents for the 1983
score-power convention, so very small or large finite floors do not distort
the peer plan. Primal feasibility, objective accounting, target
reconstruction, and multiplier marginals are independently certified before
publication. Exponentiation occurs only after those checks; overflow or
underflow is labelled while the finite log score and log target remain
available. Reference-set-specific templates are reused for panel/non-global
extensions without presenting those extensions as source reproductions.

## 7. Result and registry contract

Every fitted result in these families must include:

```text
method_id
technology_id
path_id                 # for a path model
path_parameters
native_score_name
native_score
display_efficiency
score_transform
data_domain
target_inputs
target_outputs
path_residuals
solver_strategy
validation_evidence
```

The canonical boundaries remain:

- `static.hyperbolic`;
- `static.hyperbolic.generalized_path`;
- `static.generalized_distance.chavas_cox` (implemented/public);
- `technology.multiplicative` (implemented through one shared compiler);
- `static.multiplicative` (implemented/public family);
- `static.multiplicative.original.charnes_etal_1982` (catalog preset); and
- `static.multiplicative.invariant.charnes_etal_1983` (catalog preset).

They are not collapsed into `static.directional_distance`.

## 8. Validation gates

No additional entry becomes public until it has:

1. a checked defining formulation and native-score convention;
2. a hand-calculated or published numerical oracle;
3. target-feasibility and strong-efficiency tests;
4. endpoint/equivalence tests only where theory proves them;
5. data-domain failure tests, especially zeros and signed values;
6. unit, monotonicity, and score-domain property tests;
7. bisection-versus-independent nonlinear/conic checks for representative
   hyperbolic paths, or an equivalent trusted comparison;
8. sparse performance benchmarks with compiled-matrix reuse; and
9. matching book and API explanations of the operating question.

The public GDF leaf satisfies these gates through endpoint and CRS
equivalence tests, target and row-unit invariance tests, structural-zero and
failure tests, and the fixed five-DMU
[DataEnvelopmentAnalysis.jl oracle](https://github.com/javierbarbero/DataEnvelopmentAnalysis.jl/blob/ca17532cd4de4e47d159cee563c05d9a0db6a61c/test/deaprofitability.jl#L4-L45).
The same example validates the matched profitability decomposition.

The public multiplicative family satisfies its release gate through the
checked 1982/1983 equations, an independent dense compiler, the exact
two-DMU analytical oracle, domain and unit-behavior tests, fail-closed primal
and multiplier certificates, target-transform range tests, and sparse
compiled-reference benchmarks. It has no published numerical reproduction;
that boundary and the package-extension status of panel/non-global references
remain explicit. Standard and generalized hyperbolic path leaves remain
blocked until equally specific evidence is available, even if a plausible
optimization programme can be coded.
