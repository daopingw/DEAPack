# Farrell radial DEA: independent analytical oracle

**Method ID:** `static.radial`  
**Validation kind:** `analytically_derived`  
**Published reproduction:** no

This record validates DEAPack's radial phase-one scores and selected
slack-completed targets with exact fixtures derived independently of the
production compiler. It is not a transcription of a table in Farrell (1957),
Charnes, Cooper, and Rhodes (1978), or Banker, Charnes, and Cooper (1984), and
it makes no empirical-reproduction claim.

## Exact one-input/one-output score fixture

The fixture contains one input and one desirable output:

| Organization | Input | Output |
|---|---:|---:|
| A | $1$ | $1$ |
| B | $2$ | $1$ |
| C | $1$ | $1/2$ |

Every observed activity satisfies $y_j\leq x_j$, and A attains equality.
Consequently, under CRS any feasible conical reference activity also
satisfies

$$
Y\lambda\leq X\lambda.
$$

For input orientation,
$Y\lambda\geq y_o$ and $X\lambda\leq\theta x_o$ therefore imply
$\theta\geq y_o/x_o$. Choosing
$\lambda_A=y_o$ attains the bound. For output orientation,
$Y\lambda\geq\phi y_o$ and $X\lambda\leq x_o$ imply
$\phi\leq x_o/y_o$; choosing $\lambda_A=x_o$ attains it.
These matching feasible plans and upper bounds certify the CRS optima without
calling a DEA implementation.

The scale restrictions sharpen those bounds:

- VRS and NDRS require $\sum_j\lambda_j\geq1$. Because every reference input
  is at least one, input orientation also requires
  $\theta x_o\geq1$.
- VRS and NIRS require $\sum_j\lambda_j\leq1$. Because every reference output
  is at most one, output orientation also requires
  $\phi y_o\leq1$.

The following A-only or self-reference intensities attain every resulting
bound. Thus each entry has both a feasible primal witness and an independently
derived upper or lower bound.

| RTS | Orientation | A | B | C | Attaining reference intensity |
|---|---|---:|---:|---:|---|
| CRS | input $\theta$ | $1$ | $1/2$ | $1/2$ | $\lambda_A=(1,1,1/2)$ |
| CRS | output $\phi$ | $1$ | $2$ | $2$ | $\lambda_A=(1,2,1)$ |
| VRS | input $\theta$ | $1$ | $1/2$ | $1$ | $\lambda_A=(1,1,1)$ |
| VRS | output $\phi$ | $1$ | $1$ | $2$ | A, B, A respectively |
| NIRS | input $\theta$ | $1$ | $1/2$ | $1/2$ | $\lambda_A=(1,1,1/2)$ |
| NIRS | output $\phi$ | $1$ | $1$ | $2$ | A, B, A respectively |
| NDRS | input $\theta$ | $1$ | $1/2$ | $1$ | $\lambda_A=(1,1,1)$ |
| NDRS | output $\phi$ | $1$ | $2$ | $2$ | $\lambda_A=(1,2,1)$ |

For the VRS input model, C has radial score one but can replace its observed
output $1/2$ by A's output $1$ without using more input. Its exact remaining
output slack is therefore $1/2$. To see that this is the phase-two maximum,
fixing $\theta=1$ permits input at most one; convexity and the fact that every
reference input is at least one force the reference input to equal one.
No convex reference can produce more than the sample maximum output one, and
A attains that bound. Input slack is necessarily zero and output slack can be
at most $1-1/2=1/2$. This separately validates the package distinction
between phase-one radial efficiency and strong Pareto--Koopmans efficiency
after slack completion.

For the VRS output model, B has radial score one because convexity prevents
scaling A above one copy. At that score, replacing B by A preserves output
one while reducing input from two to one. The exact remaining input slack is
therefore one. Every convex reference produces at most output one, so the
fixed output commitment forces output slack to zero. Among references that
produce one, input cannot fall below the sample minimum one, and A attains
that bound; input slack is therefore at most $2-1=1$. Together, C and B
certify the input- and output-oriented completion semantics without selecting
a non-unique peer basis.

## Exact CRS completion fixture for the named presets

The classic CRS input/output preset audit uses a second production set with
two inputs and two desirable outputs:

| Organization | $x_1$ | $x_2$ | $y_1$ | $y_2$ |
|---|---:|---:|---:|---:|
| A | $1$ | $1$ | $1$ | $1$ |
| B | $2$ | $3$ | $1$ | $1/2$ |

Write the CRS intensities on A and B as $a,b\geq0$. When B is evaluated in
input orientation, the first output requirement gives $a+b\geq1$, while the
first input restriction gives

$$
a+2b\leq2\theta.
$$

Consequently $2\theta\geq a+2b=(a+b)+b\geq1$, so
$\theta\geq1/2$. The plan $(a,b)=(1,0)$ attains the bound. Once
$\theta=1/2$ is fixed, $a+2b\leq1$ and $a+b\geq1$ jointly force
$b=0$ and $a=1$. The slack-completed reference is therefore unique in this
fixture: its input target is $(1,1)$ and its output target is $(1,1)$.
Relative to the fixed radial balances for B, the input slacks are
$(0,1/2)$ and the output slacks are $(0,1/2)$.

For output orientation, the first input restriction and first output
requirement give

$$
a+2b\leq2,\qquad a+b\geq\phi.
$$

Thus $\phi\leq a+b\leq2-b\leq2$. The plan $(a,b)=(2,0)$ attains
$\phi=2$. At that fixed factor, the same inequalities force $b=0$ and
$a=2$. The input and output targets are both $(2,2)$; the input slacks are
$(0,1)$ and the output slacks are $(0,1)$.

These bounds and attaining plans are independent of the production
implementation. Because the fixed-factor reference is unique in both
orientations, any strictly positive slack weights recover the same target in
this fixture. DEAPack nevertheless declares one particular general
alternate-optimum policy: `compute_slacks=True` followed by row-scaled
lexicographic slack maximization. That policy is fixed by `CCRInput` and
`CCROutput`; it is package policy rather than a claim that the foundational
CCR paper uniquely prescribed these phase-two targets.

## Executable checks

`tests/test_radial_independent_oracle.py` performs four independent checks:

1. it compares all eight exact RTS--orientation score vectors above with the
   public `RadialDEA` API and checks the corresponding CRS/VRS branches through
   `CCRInput`, `CCROutput`, `BCCInput`, and `BCCOutput`;
2. it checks the exact VRS input slack and target for C and the exact VRS
   output slack and target for B; and
3. it checks the exact CRS input/output factors, peers, slacks, and targets
   derived in the two-organization fixture above through the two named CRS
   presets; and
4. on a separate six-organization, two-input/two-output fixture, it compiles both dense
   envelopment phases directly with `scipy.optimize.linprog` for all eight
   orientation--RTS combinations in score-only and slack-completion modes,
   without importing DEAPack's sparse reference compiler, radial LP builder,
   row-scaling helper, or private model methods.

## Claim boundary

These checks have deliberately different evidential reach:

| Claim | Exact or cross-check? | Parameter and result scope |
|---|---|---|
| phase-one optimum | exact feasible witness plus analytical upper/lower bound | native score and reciprocal display for input/output under CRS, VRS, NIRS, and NDRS |
| phase-two semantics | exact analytical cases | CRS input/output for B in the two-input/two-output fixture and VRS input for C/VRS output for B in the one-input/one-output fixture; radial/strong status, peer, slack, and target as applicable |
| classic preset identity | exact branch expectations plus preset-to-core regression | `CCRInput`, `CCROutput`, `BCCInput`, and `BCCOutput`; fixed RTS, orientation, native score, and DEAPack slack-completion policy, with `method_id="static.radial"` and the corresponding `preset_id` |
| dense two-phase compilation | independently formulated numerical cross-check using the same SciPy/HiGHS optimizer class | all four RTS assumptions, both orientations, and score-only/slack-completion execution on a six-activity, two-input, two-output fixture |

Every fixture is cross-sectional, nonnegative, self-inclusive, and evaluated
against the full eligible sample requested through the default `auto`
reference (resolved to `global`). The certificate therefore does not extend
to custom or external reference populations, leave-one-out appraisal, panel
reference policies, signed quantities, undesirable outputs, or a claim of
unique peers under alternate optimal solutions.

Nor does it certify FDH, FCH, FRH, environmental technologies, productivity
operators, sampling inference, or any other method that happens to reuse
radial matrices.
