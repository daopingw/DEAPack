# Oriented Tone SBM: independent analytical oracle

**Method IDs:** `static.sbm.input.tone2001`,
`static.sbm.output.tone2001`  
**Validation kind:** `analytically_derived`  
**Published reproduction:** no

This certificate validates the CRS/VRS input- and output-oriented
slacks-based measures defined by Tone (2001). It combines an exact VRS
fixture with direct LPs compiled independently of DEAPack's production SBM
compiler. The fixture is synthetic: it is not a transcription of a published
oriented-SBM result table, and no published numerical reproduction is
claimed.

## The two management accounts

Let organization $o$ use the strictly positive input vector $x_o$ to
deliver the strictly positive desirable-output vector $y_o$. With reference
intensities $\lambda$, input excesses $s^-$, and output shortfalls $s^+$,
the balance accounts are

$$
X\lambda+s^-=x_o,\qquad
Y\lambda-s^+=y_o,\qquad
\lambda,s^-,s^+\geq0.
$$

Under CRS there is no intensity-sum restriction. Under VRS,
$\boldsymbol{1}^{\mathsf T}\lambda=1$.

The input-oriented measure asks how much of the organization's observed
resource use can be removed, on average across input dimensions, while its
delivered outputs are maintained:

$$
\rho_o^I
=
\min\left\{
1-\frac{1}{m}\sum_{i=1}^m\frac{s_i^-}{x_{io}}
\right\}.
$$

Equivalently, the programme maximizes the average normalized input excess.
Output slacks make the benchmark activity feasible but do not enter this
account.

The output-oriented programme directly maximizes the average normalized
service-expansion account

$$
\tau_o^O
=
\max\left\{
1+\frac{1}{s}\sum_{r=1}^s\frac{s_r^+}{y_{ro}}
\right\}.
$$

DEAPack retains this directly optimized value as
`output_expansion_factor`, and reports the higher-is-better efficiency

$$
\rho_o^O=\frac{1}{\tau_o^O}.
$$

Input slacks preserve feasibility but do not enter the output-expansion
account. Keeping $\tau_o^O$ and $\rho_o^O$ distinct prevents the
directly optimized expansion opportunity from being mistaken for the
package's reciprocal efficiency convention.

## Exact VRS fixture

The analytical fixture has two inputs and two desirable outputs:

| Organization | $x_1$ | $x_2$ | $y_1$ | $y_2$ |
|---|---:|---:|---:|---:|
| A | 2 | 4 | 1 | 2 |
| B | 4 | 2 | 2 | 1 |
| O | 4 | 4 | 1 | 1 |

Write the VRS intensities on A, B, and O as $a,b,c$, so
$a+b+c=1$. Their aggregate input and output vectors are

$$
X\lambda=(4-2a,\;4-2b),\qquad
Y\lambda=(1+b,\;1+a).
$$

### Input-oriented result

When O is evaluated, every convex combination is feasible because
$X\lambda\leq(4,4)$ and $Y\lambda\geq(1,1)$. Its input slacks are
$(2a,2b)$, so the average normalized input excess is

$$
\frac12\left(\frac{2a}{4}+\frac{2b}{4}\right)
=\frac{a+b}{4}\leq\frac14.
$$

Every plan with $a+b=1$ attains the bound. Therefore

$$
\rho_O^I=1-\frac14=\frac34.
$$

For A, the first input balance requires
$4-2a\leq2$, hence $a=1$, and its input account is one. Symmetrically,
B's second input balance requires $b=1$, and its input account is also one.
Thus the exact input-oriented score vector for (A, B, O) is

$$
(1,\;1,\;3/4).
$$

### Output-oriented result

For O, the output slacks are $(b,a)$. Its directly optimized expansion
factor therefore satisfies

$$
\tau_O^O
=1+\frac12(a+b)
\leq\frac32.
$$

Again, every plan with $a+b=1$ attains the bound. Consequently

$$
\tau_O^O=\frac32,\qquad
\rho_O^O=\frac{1}{\tau_O^O}=\frac23.
$$

For A, maintaining its second output requires $1+a\geq2$, hence $a=1$.
For B, maintaining its first output requires $1+b\geq2$, hence $b=1$.
Their expansion factors and reciprocal efficiencies are one. The exact
output-oriented vectors for (A, B, O) are therefore

$$
\tau^O=(1,\;1,\;3/2),\qquad
\rho^O=(1,\;1,\;2/3).
$$

## Why the fixture does not certify a unique target

For O, every mixture $a+b=1$ is optimal in both orientations. Moving from A
to B within that optimal set changes the individual input slacks, output
slacks, peers, and target coordinates while leaving the relevant average
account unchanged. The certificate therefore validates the score and the
active-side average normalized slack, but not a unique peer set, individual
slack vector, or target. A score of one certifies only that the slacks entering
the selected oriented account are zero; it does not certify
Pareto--Koopmans efficiency. DEAPack accordingly leaves generic
`is_efficient` missing and reports the narrower `is_sbm_efficient` status.

## Independently compiled checks

`tests/test_oriented_sbm_independent_oracle.py` performs four public checks:

1. it verifies the exact VRS input score $(1,1,3/4)$, the corresponding
   input-inefficiency account, oriented status, and missing generic-efficiency
   status;
2. it verifies the exact VRS output score $(1,1,2/3)$, the direct expansion
   factors $(1,1,3/2)$, the corresponding output-inefficiency account,
   oriented status, and missing generic-efficiency status;
3. on a separate six-organization, two-input, two-output fixture, it
   hand-compiles the input-oriented CRS and VRS programmes directly with
   `scipy.optimize.linprog`; and
4. on that same fixture, it independently compiles the output-oriented CRS
   and VRS programmes, then checks both the direct $\tau_o^O$ account and
   DEAPack's reciprocal $\rho_o^O$ report.

The independent compiler constructs raw dense balance rows from the data
arrays. It does not call the production SBM compiler, production RTS-matrix
helpers, or a production fit routine. It uses the same SciPy/HiGHS optimizer
class as the package configuration under test, so this is independent problem
compilation rather than an independent-solver reproduction.

## Claim boundary

| Claim | Evidence | Parameter and result scope |
|---|---|---|
| exact input-oriented VRS account | analytical upper bound plus attaining reference plans | all three analytical-fixture organizations; $\rho^I$, average normalized input excess, orientation-specific status, and missing generic-efficiency status |
| input-oriented independent compilation | separately hand-compiled dense LPs | CRS and VRS on one six-organization fixture; score, active-side average normalized slack, orientation-specific status, diagnostics, execution accounting, and target/slack accounting identity |
| exact output-oriented VRS account | analytical upper bound plus attaining reference plans | all three analytical-fixture organizations; directly optimized $\tau^O$, reciprocal $\rho^O$, average normalized output expansion, orientation-specific status, and missing generic-efficiency status |
| output-oriented independent compilation | separately hand-compiled dense LPs | CRS and VRS on one six-organization fixture; $\tau^O$, $\rho^O$, active-side average normalized slack, orientation-specific status, diagnostics, execution accounting, and target/slack accounting identity |

All certified runs use strictly positive cross-sectional inputs and desirable
outputs and a self-inclusive full eligible sample requested through `auto`
and resolved to `global`.

Tone (2001) supplies the defining oriented equations and explicitly discusses
CRS and VRS. Russell sources support an equivalence/alias interpretation on
the matched positive-data domain; they do not replace Tone as the defining
source for these two registry leaves.

The certificate does **not** extend to:

- NIRS or NDRS, which are DEAPack convex-envelopment extensions rather than
  Tone-certified RTS cases for these leaves;
- a published oriented numerical reproduction, which has not been located
  and is deferred to a later evidence version;
- a unique peer set, individual slack allocation, or target;
- non-oriented, weighted, super-efficiency, undesirable-output, zero/signed,
  network, or dynamic SBM formulations;
- custom, external, leave-one-out, group, contemporaneous, sequential,
  window, or biennial reference policies; or
- dual values, alternate-optimum enumeration, sampling inference, or
  uncertainty quantification.
