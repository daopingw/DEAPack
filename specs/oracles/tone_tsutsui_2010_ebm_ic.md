# Tone--Tsutsui EBM-I-C published-chain oracle

**Candidate method ID:** `static.ebm.input.tone_tsutsui_2010.crs`  
**Source:** Tone and Tsutsui, DP09-21 / EJOR 207 (2010), equations
(6)--(8), (15)--(19), and (21)--(26)  
**Production implementation reused:** no  
**Certificate disposition:** source equations reproduced; automatic
calibration and the full source identity remain deferred because three
source-level decisions remain unresolved; the declared-calibration evaluator
is admitted separately under `specs/M13_DECLARED_EBM_IC.md`

## Certificate boundary

This record accompanies the source-only implementation in
`tests/test_tone_tsutsui_2010_ebm_ic_source.py`. The test builds the VRS ADD
projection and CRS EBM linear programmes directly with SciPy/HiGHS and
implements the diversity, affinity, and principal-component formulae with
NumPy. It imports no `deapack` module and is not a hidden production backend.

The certificate proves that the printed input-oriented examples can be
replayed to their reported precision. It also proves, numerically, why the
current evidence is insufficient to define a deterministic automatic
calibration method. The admitted evaluator requires the analyst to declare
epsilon, exact name-keyed input weights, and provenance, then evaluates only
equations (6)--(8). This oracle does not import that production evaluator. It
does not certify output orientation, non-orientation, VRS EBM, or any later
EBM extension.

## Example 1: radial endpoint

The source data on pp. 16--17 are

| DMU | $x_1$ | $x_2$ | $y$ | printed EBM-I-C |
|---|---:|---:|---:|---:|
| A | 1 | 1 | 1 | 1.000 |
| B | 2 | 3 | 1 | 0.500 |
| C | 3 | 2 | 1 | 0.500 |
| D | 4 | 3 | 1 | 0.333 |
| E | 5 | 6 | 1 | 0.200 |
| F | 7 | 6 | 1 | 0.167 |

Equation (19) maps all six rows to $(1,1,1)$. Equations (15)--(18) then give

$$
D=\begin{bmatrix}0&0\\0&0\end{bmatrix},\qquad
\mathcal S_x=\begin{bmatrix}1&1\\1&1\end{bmatrix}.
$$

The simple dominant eigenpair is $\rho_x=2$ with normalized
$w^-=(0.5,0.5)$, so equation (25) gives $\varepsilon_x=0$. The independently
assembled EBM LP returns

$$
(1,\;0.5,\;0.5,\;1/3,\;0.2,\;1/6),
$$

which reproduces the CCR/EBM endpoint and every printed score.

## Example 2: machine-checkable eigenvector ambiguity

The source data and ADD projections on pp. 17--19 are

| DMU | observed $(x_1,x_2)$ | projected $(\bar x_1,\bar x_2)$ |
|---|---:|---:|
| A | (2, 6) | (2, 6) |
| B | (6, 3) | (6, 3) |
| C | (10, 3) | (6, 3) |
| D | (2, 10) | (2, 6) |

The diversity off-diagonal is $0.5$, hence
$\mathcal S_x=I_2$, $\rho_x=1$, and $\varepsilon_x=1$. The paper prints
$w^-=(0.5,0.5)$; with that displayed vector, equations (6)--(8) return the
published scores

$$
(1,\;1,\;0.8,\;0.8).
$$

The principal vector is not identified by the source equations. Both

$$
w_a=(0.5,0.5),\qquad w_b=(0,1)
$$

are nonnegative, sum to one, and satisfy $I_2w=1w$. Yet $w_b$ changes the
EBM scores to

$$
(0.5,\;1,\;1,\;0.3).
$$

The executable oracle checks both eigen-residuals and both score vectors, and
its general calibration helper raises on the repeated dominant root. Thus an
arbitrary `eigh(I)` result would not be a harmless numerical convention: it
would change managerial rankings and efficiency classifications. The equal
weights in Example 2 are a source-displayed value for this example, not a
general tie rule.

## Example 3: hospital chain

### Published calibration matrix

The independent oracle transcribes the 12 integer observations in Table 9
and the 12 projected rows printed to two decimals in Table 10. Applying
equations (15)--(26) to the two printed Table 10 input columns gives

| Quantity | Independent value | Printed value |
|---|---:|---:|
| diversity off-diagonal | 0.264699011551 | 0.265 |
| affinity off-diagonal | 0.470601976897 | 0.471 |
| dominant eigenvalue | 1.470601976897 | 1.471 |
| epsilon | 0.529398023103 | 0.529 |
| normalized weights | (0.5, 0.5) | (0.5, 0.5) |

The small extra digits are calculations from the rounded published matrix,
not a claim about unavailable full-precision author data.

### Independent equations-(6)--(8) results

Using $\varepsilon_x=0.529398023103$ and $w^-=(0.5,0.5)$, the source-only LP
returns:

| DMU | score | $\theta$ | doctor excess | nurse excess |
|---|---:|---:|---:|---:|
| A | 1.000000000000 | 1.000000000000 | 0 | 0 |
| B | 1.000000000000 | 1.000000000000 | 0 | 0 |
| C | 0.867634751013 | 0.885036764706 | 1.643566176471 | 0 |
| D | 0.985789216330 | 1.015966386555 | 3.078151260504 | 0 |
| E | 0.760543504097 | 0.766090841400 | 0.461057334326 | 0 |
| F | 0.770916726258 | 0.846459054210 | 15.696424452134 | 0 |
| G | 0.898188519719 | 0.901960784314 | 0 | 3.349019607843 |
| H | 0.788277369120 | 0.804386065106 | 1.886556253569 | 0 |
| I | 0.930877919278 | 0.960392156863 | 0 | 27.206274509804 |
| J | 0.829470003742 | 0.884547848990 | 10.403863037752 | 0 |
| K | 0.911989737896 | 0.963571703191 | 10.328123798539 | 0 |
| L | 0.946460068711 | 0.958204334365 | 0 | 12.600619195046 |

All scores, radial factors, and input excesses agree with Tables 9 and 13 at
the reported precision. Maximum input-balance and output-feasibility
violations in the executable certificate are below $10^{-10}$. The fitted
output surplus is zero for every row in this example.

### Hospital D management account

The independently selected optimum for D has

$$
\lambda_A=0.211764705882=18/85,\qquad
\lambda_B=1.058823529412=18/17,
$$

and all other intensities zero. It gives

$$
\theta^*=1.015966386555=1209/1190,
\quad s^-=(3.078151260504,0),
$$

$$
x_D^*=X\lambda^*=(24.352941176471,170.682352941176),
\quad y_D^*=(180,72).
$$

The score is $0.985789216330$ using the epsilon computed from printed Table
10. Doctor use decreases from 27 to 24.35, while nurse use increases from 168
to 170.68. The test explicitly asserts both inequalities. This is the
source's input-mix substitution interpretation on p. 21; an input-oriented
result schema must not relabel both components as contractions.

## Source conflict in the first calibration stage

Solving equation (19) from the exact integer Table 9 data reproduces every
Table 10 row to its two-decimal display tolerance except hospital G. For G,
the ADD optimum is the unchanged row

$$
(33,235,220,88),
$$

whereas Table 10 prints $(33,235,220,88.04)$. A separate feasibility LP in
the executable oracle proves that the exact printed vector cannot be written
as any nonnegative VRS combination of the exact Table 9 rows. It is therefore
not just a different optimum selected by HiGHS.

Using all equation-(19) projections from the integer Table 9 data gives

$$
S_{12}=0.470579885680,
\quad\rho_x=1.470579885680,
\quad\varepsilon_x=0.529420114320,
$$

instead of the values above from rounded Table 10. The downstream difference
is small, but the data lineage is not closed. It may reflect unavailable
pre-rounding observations, a transcription error, or an undocumented
calculation; the present evidence cannot choose among those explanations.

## Why automatic calibration remains deferred

The numerical chain is strong enough to freeze the equations and semantics,
but not to publish a deterministic estimator. The three calibration blockers
are independently executable or source-explicit:

1. ADD, SBM, and unprojected observations are all permitted calibration
   populations, and optimal ADD/SBM projections may be nonunique without a
   source selector.
2. Example 2 proves that a repeated dominant eigenvalue can materially change
   scores under different source-admissible eigenvectors.
3. The hospital-G Table 9-to-Table 10 transition cannot be reproduced from
   the printed data.

The score LP also has no source secondary objective for unique peers, slacks,
or targets. This is a reporting limitation, not a fourth calibration blocker:
one primary optimum can be returned if it is labelled solver-selected and no
uniqueness claim is made.

No source rule is invented to close the three calibration gaps. The full
identity `static.ebm.input.tone_tsutsui_2010.crs` remains
`deferred_to_next_version`. The narrower
`static.ebm.input.tone_tsutsui_2010.crs.declared` identity conditions on an
immutable analyst declaration and makes no claim that the deferred calibration
chain was run.
