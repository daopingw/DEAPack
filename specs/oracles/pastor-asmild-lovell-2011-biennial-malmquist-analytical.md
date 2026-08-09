# Pastor--Asmild--Lovell (2011) Biennial Malmquist analytical oracle

**Method ID:** `productivity.biennial_malmquist`  
**Defining source:** Pastor, Asmild, and Lovell (2011),
[doi:10.1016/j.seps.2010.09.001](https://doi.org/10.1016/j.seps.2010.09.001)  
**Published reproduction:** no  
**Production compiler reused:** no  

## Claim and boundary

This certificate validates two exact, deliberately small cases for the
output-oriented CRS Biennial Malmquist account.  The first isolates a shift in
the attainable output frontier while organizations retain their relative
operating performance.  The second isolates operating catch-up while the
frontier remains unchanged.  For both cases it certifies the four
efficiency-form distances, efficiency change, best-practice change, headline
productivity change, the multiplicative identity, and the membership of the
two-period reference set.

The numbers below are analytically derived teaching fixtures.  They are not a
reproduction of a numerical table, dataset, or empirical application in the
defining article.

The machine-readable certificate separates reference scope rather than treating
all four tasks as if they used one technology.  One exact claim covers the two
own-period distances and efficiency change under `reference_scope=contemporaneous`.
A second covers the two adjacent-pair pooled distances and headline index under
`reference_scope=biennial`.  A third, composition-only claim reconstructs the
gaps, best-practice change, and multiplicative identity from those four already
certified roles; it introduces no additional reference technology.

## Source-form CRS programme

Let $S$ be a declared reference sample of strictly positive one-input,
one-output observations.  Under CRS, ordinary free disposal, and continuous
intensities, the output-oriented radial programme for observation $o$ is

$$
\max_{\phi,\lambda}\ \phi
\quad\text{subject to}\quad
\sum_{j\in S}\lambda_jx_j\le x_o,
\qquad
\sum_{j\in S}\lambda_jy_j\ge \phi y_o,
\qquad
\lambda_j\ge0.
$$

Write $k_S=\max_{j\in S}(y_j/x_j)$.  Every feasible plan obeys

$$
\phi y_o
\le \sum_{j\in S}\lambda_jy_j
\le k_S\sum_{j\in S}\lambda_jx_j
\le k_Sx_o,
$$

so $\phi\le k_Sx_o/y_o$.  If $q$ attains $k_S$, choosing
$\lambda_q=x_o/x_q$ attains the upper bound.  Consequently the exact
Farrell efficiency-form distance is

$$
d^S(x_o,y_o)=\frac{1}{\phi^*}=\frac{y_o}{k_Sx_o}.
$$

The construction therefore proves the optimum: it is not merely the value of
one feasible plan.  Its reference activity attains the upper bound.  The
executable oracle evaluates this formula with rational arithmetic and never
imports DEAPack, its pooled-Malmquist kernel, its reference compiler, or an LP
compiler.

For adjacent periods $0$ and $1$, the biennial membership set is the raw union

$$
S^{B(0,1)}=S^0\cup S^1.
$$

It includes every eligible observation in those two periods, including an
observation whose identifier is absent from the other period.  Matching
identifiers determines which productivity rows are reported; it does not
shrink the reference technology.

## Account identities

For each matched organization, the four certified distances are
$d^0(z^0)$, $d^1(z^1)$, $d^B(z^0)$, and $d^B(z^1)$.  The package account is

$$
BM=\frac{d^B(z^1)}{d^B(z^0)},
\qquad
EC_B=\frac{d^1(z^1)}{d^0(z^0)},
$$

$$
BG^0=\frac{d^B(z^0)}{d^0(z^0)},
\qquad
BG^1=\frac{d^B(z^1)}{d^1(z^1)},
\qquad
BPC_B=\frac{BG^1}{BG^0},
$$

and hence $BM=EC_B\times BPC_B$.

## Exact case 1: frontier shift

| Organization | Period | Input $x$ | Output $y$ |
|---|---:|---:|---:|
| A | 0 | 1 | 1 |
| B | 0 | 2 | 2 |
| A | 1 | 1 | 2 |
| B | 1 | 2 | 4 |

Here $k_0=1$, $k_1=2$, and $k_B=2$.  Both organizations have the same exact
account:

| $d^0(z^0)$ | $d^1(z^1)$ | $d^B(z^0)$ | $d^B(z^1)$ | $EC_B$ | $BG^0$ | $BG^1$ | $BPC_B$ | $BM$ |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| $1$ | $1$ | $1/2$ | $1$ | $1$ | $1/2$ | $1$ | $2$ | $2$ |

Thus the twofold productivity improvement is entirely a movement in the
attainable frontier relative to the common two-period benchmark; neither
organization changes its position relative to its own-period frontier.

## Exact case 2: operating catch-up

| Organization | Period | Input $x$ | Output $y$ |
|---|---:|---:|---:|
| A | 0 | 2 | 1 |
| B | 0 | 1 | 1 |
| A | 1 | 1 | 1 |
| B | 1 | 1 | 1 |

Now $k_0=k_1=k_B=1$.  The exact accounts are:

| Organization | $d^0(z^0)$ | $d^1(z^1)$ | $d^B(z^0)$ | $d^B(z^1)$ | $EC_B$ | $BG^0$ | $BG^1$ | $BPC_B$ | $BM$ |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| A | $1/2$ | $1$ | $1/2$ | $1$ | $2$ | $1$ | $1$ | $1$ | $2$ |
| B | $1$ | $1$ | $1$ | $1$ | $1$ | $1$ | $1$ | $1$ | $1$ |

Organization A halves the resource requirement for the same output and catches
up to observed best practice.  The reference frontier does not move, so its
entire productivity improvement is operating-performance change.

## Three-period behavioral membership check

Reference membership is also checked through public economic results, not only
through a helper that selects row numbers.  The public fixture contains three
periods.  A and B are matched throughout; C appears only in period 0, D only in
period 1, and E only in period 2.  Every input equals 1 and A and B always
produce 1.  E produces 100, deliberately making the excluded third-period
practice much stronger than either adjacent-pair frontier.

Two versions exchange which unmatched member sets the period-0/period-1
frontier:

| Version | C output in period 0 | D output in period 1 | Pair frontier $k_B$ | Unique pair peer |
|---|---:|---:|---:|---|
| base-only leader | 4 | 2 | 4 | C, period 0 |
| comparison-only leader | 2 | 4 | 4 | D, period 1 |

For A, the exact public accounts are:

| Version | $d^0(z^0)$ | $d^1(z^1)$ | $d^B(z^0)$ | $d^B(z^1)$ | $EC_B$ | $BG^0$ | $BG^1$ | $BPC_B$ | $BM$ |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| base-only leader | $1/4$ | $1/2$ | $1/4$ | $1/4$ | $2$ | $1$ | $1/2$ | $1/2$ | $1$ |
| comparison-only leader | $1/2$ | $1/4$ | $1/4$ | $1/4$ | $1/2$ | $1/2$ | $1$ | $2$ | $1$ |

The two runs make C and D, respectively, the unique reported peer of both
period-0/period-1 pooled tasks.  This behavior proves that base-only and
comparison-only raw observations are admitted even though neither receives a
productivity row.  The metadata reports six reference observations and the
diagnostics report only technology periods `(0, 1)`.  If period-2 E leaked into
the pair, the pooled distances would be $1/100$ and E would be the unique peer;
the observed $1/4$ distances and C-or-D peers therefore also prove the outer
period is excluded.

The base-only-leader version is also an exact technical-regress check: the
contemporaneous frontier slope falls from 4 in period 0 to 2 in period 1, while
the stronger period-2 slope of 100 remains outside the period-0/period-1 pool.

## Executable mapping

- Independent rational derivation and exact reference-membership check:
  `tests/test_pastor_asmild_lovell_2011_biennial_malmquist_source.py`.
- Public API comparison for both complete four-distance accounts:
  `tests/test_biennial_malmquist_analytical_public_api.py::test_public_api_matches_exact_frontier_shift_and_catch_up_oracles`.
- Three-period public behavior check for unmatched member inclusion and
  outside-period exclusion:
  `tests/test_biennial_malmquist_analytical_public_api.py::test_public_api_pair_pool_includes_unmatched_rows_and_excludes_other_periods`.
- The public comparison also verifies that diagnostics identify only periods
  0 and 1, the metadata reports four raw reference observations, and no
  off-diagonal contemporaneous cross-period radial task is used.

The certificate is limited to output orientation, CRS, ordinary desirable
outputs, strictly positive one-input/one-output observations, self-inclusive
reference sets, and one matched adjacent transition.  It does not certify input
orientation, VRS or other scale assumptions, multiple-input or multiple-output
numerical fixtures, undesirable outputs, statistical inference, chaining
across different biennial technologies, or the defining article's empirical
results.
