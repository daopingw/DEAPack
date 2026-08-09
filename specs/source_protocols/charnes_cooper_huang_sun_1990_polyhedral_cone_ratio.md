# Charnes--Cooper--Huang--Sun polyhedral cone-ratio DEA source protocol

## Readiness record

| Field | State |
|---|---|
| Method identifier | `valuation.weight_restriction.cone_ratio.polyhedral_crs.charnes_etal_1990` |
| General cone source | `complete_primary_article_page_frozen` |
| Finite polyhedral source | `complete_primary_article_page_frozen` |
| Representation source | `complete_primary_article_page_frozen` |
| Equation gate | **PASS for the finite sum-form CRS programme below** |
| Published numerical audit | **PASS for 1990 Example 2** |
| Independent cross-form audit | **PASS in source audit and repository automation** |
| Source anomaly | **1990 Example 3/Table 2 conflicts with its printed data and matrix in 2 of 17 rows** |
| Production implementation | `implemented` as the narrow sparse CR-E leaf |
| Public API | `PolyhedralConeRatioDEA`, `ConeRestrictionProvenance`, and specialized result |
| Registry status | implemented/public machine record and identity-cone relation present |
| Release disposition | `implemented_public_documentation_only_leaf` |
| Last source audit | 2026-08-03 |

This protocol freezes one deliberately narrow valuation-restriction leaf. It
does not open a generic `restrictions=` interface and does not turn every
historical weight-restriction name into an alias. The executable object
supported by the sources is a finite-DMU, input-oriented, constant-returns-
to-scale cone-ratio CCR programme whose input and output valuation cones are
provided directly in nonnegative finite-generator, or **sum**, form.

The published Example 2 is independently reproducible from the printed data
and generator matrix. The corresponding evidence account is recorded in
`specs/oracles/charnes_cooper_huang_sun_1990_cone_ratio.md`. An automated
source-only direct multiplier/envelopment oracle is now independent of the
production sparse compiler, and the dedicated public result contract retains
the source-specific account boundaries below.

## 1. Defining sources and audited artifacts

### 1.1 General cone-ratio model

Abraham Charnes, William W. Cooper, Q. L. Wei, and Z. M. Huang (1989),
“Cone ratio data envelopment analysis and multi-objective programming,”
*International Journal of Systems Science*, 20(7), 1099--1118.
[DOI](https://doi.org/10.1080/00207728908910197).

The complete primary article was obtained from the publicly accessible
William W. Cooper archive at Carnegie Mellon University:

- [archival PDF](https://iiif.library.cmu.edu/file/Cooper_box00009_fld00009_bdl0001_doc0001/Cooper_box00009_fld00009_bdl0001_doc0001.pdf);
- audited local artifact:
  a private review copy not distributed with DEAPack;
- PDF pages: `20`;
- byte size: `836992`;
- SHA-256:
  `0590d06d981cb016ff3216881ee8fb81cf9acc143e09a4380bdf8f7fc74e1549`.

The article supplies the general closed-cone ratio model, its transformed
multiplier programme, conic dual, CCR reduction, and the distinction between
score equality and source-defined DEA efficiency. Its arbitrary-cone theory
is broader than the linear-programming leaf frozen here.

### 1.2 Finite polyhedral operational model and examples

Abraham Charnes, William W. Cooper, Z. M. Huang, and D. B. Sun (1990),
“Polyhedral Cone-Ratio DEA Models with an Illustrative Application to Large
Commercial Banks,” *Journal of Econometrics*, 46(1--2), 73--91.
[DOI](https://doi.org/10.1016/0304-4076(90)90048-X).

The complete primary article was obtained from the same public archive:

- [archival PDF](https://iiif.library.cmu.edu/file/Cooper_box00010_fld00007_bdl0001_doc0001/Cooper_box00010_fld00007_bdl0001_doc0001.pdf);
- audited local artifact:
  a private review copy not distributed with DEAPack;
- PDF pages: `20`;
- byte size: `734458`;
- SHA-256:
  `03444da0a90665fd6a6600424ae0f74669f8fe7ef74fed09dcd0b48ec3006142`.

Journal pages 75--79 give equations (1)--(6), the finite-generator cones,
the paired multiplier/envelopment programmes, and the transformed-data
identity. Journal pages 81--85 give three small examples. Example 2 and
Table 1 contain the complete data and matrix needed for a numerical source
reproduction. Example 3 and Table 2 contain the source conflict documented
below.

### 1.3 Exact boundary between half-space and generator forms

Abraham Charnes, William W. Cooper, Z. M. Huang, and D. B. Sun (1991),
“Relations between half-space and finitely generated cones in polyhedral
cone-ratio DEA models,” *International Journal of Systems Science*, 22(11),
2057--2077. [DOI](https://doi.org/10.1080/00207729108910773).

The complete primary article was also obtained from the public Cooper
archive:

- [archival PDF](https://iiif.library.cmu.edu/file/Cooper_box00010_fld00013_bdl0001_doc0001/Cooper_box00010_fld00013_bdl0001_doc0001.pdf);
- audited local artifact:
  a private review copy not distributed with DEAPack;
- PDF pages: `22`;
- byte size: `810627`;
- SHA-256:
  `fa498906f5074f04d13d4fcc83f67b925ec5bb119412769aca0f7def4b32f54d`.

Theorems 1--6 distinguish inclusion from equality and state the required
rank, nonnegativity, invertibility, and extreme-ray conditions. This article
prevents the convenient inverse or pseudoinverse expressions in the earlier
discussion from being misused as a universal half-space-to-generator
conversion algorithm.

All three artifacts were rendered and visually inspected. Displayed
matrices, ratios, tables, and inequality directions were checked against
their page images rather than accepted from OCR alone. The temporary audit
copies are evidence locators, not a repository redistribution commitment.

## 2. Economic and managerial question

Ordinary CCR DEA lets each organization choose any nonnegative supporting
valuation that is favourable to it. With few observations, omitted decision
criteria, or substantive information not represented by the measured
quantities, that flexibility can make an operationally unattractive
organization appear efficient.

The source-qualified question is:

> Which organizations retain favourable input--output performance when the
> implicit valuations are required to belong to declared input and output
> cones supported by market information or expert judgement?

The restriction is therefore additional valuation information. It is not a
sample-cleaning rule, an observed market-price system, statistical inference,
or a common valuation imposed jointly on all organizations. The 1990 banking
application generated cones from selected efficient-basic-dual vectors of
expert-endorsed banks. This narrow protocol does **not** automate that
elicitation step: alternate CCR multiplier optima and modern solver basis
selection would otherwise become an unstated generator-selection policy.

The dual envelopment representation changes the dominance cone used for the
comparison. Consequently, its peer composite and residual account must not
be described as an ordinary componentwise free-disposal target. Restricting
valuations and modifying the corresponding dual dominance order are
mathematically paired descriptions, but their economic labels remain
visible.

## 3. Frozen data and cone domain

Let a cross section contain $n$ organizations, $m$ ordinary inputs, and $s$
desirable outputs:

$$
X=[x_1,\ldots,x_n]\in\mathbb R_+^{m\times n},
\qquad
Y=[y_1,\ldots,y_n]\in\mathbb R_+^{s\times n}.
$$

The input valuation cone $V$ and output valuation cone $U$ are supplied in
finite-generator form:

$$
V=\{A^\top\alpha:\alpha\ge0\},
\qquad
U=\{B^\top\gamma:\gamma\ge0\},
$$

where

$$
A\in\mathbb R_+^{\ell\times m},
\qquad
B\in\mathbb R_+^{k\times s}.
$$

Every row of $A$ or $B$ is one declared generator. The source assumes the
observed input and output vectors lie in the interiors of the corresponding
negative polar cones. For the finite sum form, the operational implication
used by equations (5)--(6) is that every transformed observation is strictly
positive:

$$
Ax_j\in\mathbb R_{++}^{\ell},
\qquad
By_j\in\mathbb R_{++}^{k},
\qquad j=1,\ldots,n.
$$

The implementation rejects non-finite matrices, negative generator
coefficients, all-zero generators, dimension mismatches, and any observation
that violates the transformed strict-positivity domain. It must record the
units, elicitation source, stakeholder, comparison population, and validity
period of $A$ and $B$.

The source profile is one finite, self-inclusive cross section. Panel,
window, sequential, group, non-global, leave-one-out, network, dynamic,
undesirable-output, signed-data, or uncertainty extensions are not implied.

## 4. Frozen multiplier and envelopment programmes

For organization $o$, substituting
$v=A^\top\alpha$ and $u=B^\top\gamma$ in the input-normalized CCR
multiplier programme gives the finite version of 1990 equation (5):

$$
\begin{aligned}
\max_{\alpha,\gamma}\quad
  &\gamma^\top By_o\\
\text{s.t.}\quad
  &\gamma^\top By_j-\alpha^\top Ax_j\le0,
    &&j=1,\ldots,n,\\
  &\alpha^\top Ax_o=1,\\
  &\alpha\ge0,\quad\gamma\ge0.
\end{aligned}
\tag{CR-M}
$$

Its paired input-oriented CRS envelopment, 1990 equation (6) in ordinary
quantity notation, is

$$
\begin{aligned}
\min_{\theta,\lambda}\quad &\theta\\
\text{s.t.}\quad
  &AX\lambda\le\theta Ax_o,\\
  &BY\lambda\ge By_o,\\
  &\lambda\ge0.
\end{aligned}
\tag{CR-E}
$$

There is no convexity equation, free VRS intercept, non-Archimedean epsilon,
phase-two slack objective, or common-weight constraint. Under the source
regularity conditions, the multiplier and envelopment objective values
coincide.

Defining transformed observations

$$
X'=AX,
\qquad
Y'=BY,
$$

makes (CR-M)--(CR-E) exactly the ordinary input-oriented CCR pair for
$(X',Y')$. This is a maintained valuation-cone model, not arbitrary data
preprocessing. Setting $A=I_m$ and $B=I_s$ recovers ordinary CCR.

## 5. Score, efficiency status, multipliers, and targets

The native radial objective is $\theta_o\le1$ under self inclusion. A lower
value means that a larger proportional reduction in the evaluated
organization's transformed input account is compatible with the declared
valuation cones and the reference organizations.

The 1989 and 1990 sources distinguish objective equality from their stronger
efficiency definition. Source-defined efficiency requires an optimum with

$$
\theta_o=1,
\qquad
v=A^\top\alpha\in\operatorname{Int}V,
\qquad
u=B^\top\gamma\in\operatorname{Int}U.
$$

Generator cones can be lower dimensional, and an optimal multiplier vector
can lie on a boundary. The result therefore retains the radial score,
weak/measure-efficiency status, and any separately certified interior-based
source status rather than declaring every score-one row strongly efficient.

The original-coordinate multipliers are reconstructed as

$$
v=A^\top\alpha,
\qquad
u=B^\top\gamma.
$$

They are supporting valuations under the declared cone, not market prices or
causal marginal products. An executable certificate must verify generator
nonnegativity, multiplier reconstruction, normalization, every reference
inequality, the focal objective, and primal--dual agreement.

Likewise, ordinary componentwise slacks cannot be inferred from (CR-E):

$$
A(\theta x_o-X\lambda)\ge0,
\qquad
B(Y\lambda-y_o)\ge0
$$

does not generally imply
$\theta x_o-X\lambda\ge0$ or $Y\lambda-y_o\ge0$ coordinate by coordinate.
The 1990 bank example explicitly reports output accounts in which some
desirable outputs fall while another rises. The result retains:

- the radial account $\theta x_o$;
- the original-coordinate peer composites $X\lambda$ and $Y\lambda$;
- transformed cone residuals;
- peer intensities; and
- an explicit `solver_selected` attribution unless uniqueness is certified.

The ordinary radial Pareto--Koopmans completion protocol is not a source
phase of this method and must not be attached silently.

## 6. Unit covariance and restriction provenance

The entries of $A$ and $B$ inherit the reciprocal units of the quantities
they value. Suppose inputs and outputs are recoded as

$$
\widetilde x=Cx,
\qquad
\widetilde y=Dy,
$$

for positive diagonal unit-conversion matrices $C$ and $D$. Preserving the
same valuation cones requires

$$
\widetilde A=AC^{-1},
\qquad
\widetilde B=BD^{-1},
$$

so that $\widetilde A\widetilde x=Ax$ and
$\widetilde B\widetilde y=By$. Rescaling quantities while leaving the
numerical generator matrices unchanged changes the economic restriction and
can change scores. The independent audit confirms this boundary: multiplying
Example 2 input 1 by 100 while holding $A$ fixed changes the DMU3 score from
$0.988372\ldots$ to $0.588235\ldots$; dividing the first column of $A$ by
100 restores the original score exactly.

Unit-aware covariance is therefore part of the implemented specification, not
an optional display correction.

## 7. Half-space restrictions and the assurance-region boundary

The 1990 article shows, for two input valuations, that

$$
c_1\le\frac{v_2}{v_1}\le c_2,
\qquad c_2\ge c_1>0,
$$

can be written as homogeneous half-space inequalities and represented by the
two generator rays $(1,c_1)$ and $(1,c_2)$. It also writes a general family of
pairwise ratio inequalities. These observations establish that some
assurance-region restrictions are special polyhedral cone-ratio cases.

They do **not** make all half-space restrictions, AR-I, AR-II, or
Wong--Beasley virtual shares exact aliases of this leaf. The 1991 article
shows that half-space-to-generator equality depends on explicit rank,
nonnegativity, invertibility, or complete extreme-ray conditions. A
pseudoinverse can establish only an inclusion under some hypotheses.

The public leaf therefore accepts direct sum-form $A$ and $B$ only.
The following remain deferred:

- automatic general half-space-to-generator conversion;
- Thompson AR-I and AR-II source identities;
- cross-side input--output multiplier restrictions;
- absolute multiplier bounds;
- observation-specific virtual-share restrictions; and
- production trade-offs that modify the attainable technology.

The controlling deferred Thompson record remains
`specs/source_protocols/assurance_region.md`.

## 8. Published Example 2 oracle

Table 1 on journal page 84 contains 17 organizations, two inputs, and a
common output of 2. Example 2 declares

$$
B=[1],
\qquad
A=\begin{bmatrix}1&0.01\\0.01&1\end{bmatrix}.
$$

The article reports

$$
\theta_3=0.9884,
\qquad
\theta_{10}=0.9767.
$$

An independent dense direct-multiplier programme and an independently
assembled transformed-data envelopment programme agree over all 17 rows to
within $9.55\times10^{-15}$. They reproduce the published values and yield
the exact certificates

$$
\theta_3=\frac{85}{86},\quad\lambda_{12}=1,
\qquad
\theta_{10}=\frac{42}{43},\quad\lambda_7=1.
$$

The full data, exact proof, audit procedure, and claim boundary are frozen in
the companion oracle record. Repository automation remains a required step
before a public implementation may claim a controlled `reproduced` oracle
status.

## 9. Example 3/Table 2 source anomaly

Example 3 reuses Table 1 and prints

$$
B=\begin{bmatrix}1\\1\end{bmatrix},
\qquad
A=\begin{bmatrix}0.125&0.025\\0.05&0.05\end{bmatrix}.
$$

Solving equations (5)--(6) from those printed quantities reproduces 15 of the
17 Table 2 scores to four decimals. It does **not** reproduce two rows:

| Organization | Printed Table 2 | Recomputed from printed data and $A,B$ |
|---|---:|---:|
| DMU3 | 0.1923 | 0.5882 |
| DMU10 | 0.3333 | 0.8000 |

Direct multiplier and transformed envelopment programmes agree on the
recomputed values. No erratum or source-author clarification was located in
the audit. Table 2 must therefore be recorded as an unresolved primary-source
conflict, not edited, rationalized from a later textbook, or used as a full
score oracle.

This conflict does not invalidate equations (5)--(6) or Example 2, whose
printed scores are independently reproduced. It does block any claim that
DEAPack reproduces the complete Example 3 table.

## 10. Common weights remain a separate deferred protocol

Roll, Cook, and Golany (1991) examine weight bounds and the notion of a common
set of weights, but the complete primary article, shared objective,
normalization, comparison rule, tie policy, and numerical source oracle have
not been frozen in this repository. A common-weight appraisal chooses one
valuation system jointly for several organizations; cone-ratio DEA restricts
each organization's admissible self-appraisal cone. They do not share a
method identity merely because both use multiplier variables.

`evaluation.common_weight.roll_cook_golany_1991` remains
`source_not_frozen`, `blocked_on_primary_source`, and
`deferred_to_next_version`, with no API or registry record.

## 11. Current-version implementation boundary

The implemented public leaf covers all and only:

- a finite self-inclusive cross section;
- ordinary nonnegative inputs and desirable outputs satisfying transformed
  strict positivity;
- input orientation and CRS;
- exogenous nonnegative sum-form generator matrices $A$ and $B$ with units
  and provenance;
- the primary radial score and solver-selected peer account; and
- original multiplier reconstruction plus primal, dual, and unit-covariance
  certificates.

The repository now automates the independent multiplier/envelopment oracle,
fail-closed malformed-incumbent behavior, randomized cross-form checks,
identity-cone reduction, unit covariance, missing-dual layering, and a
dedicated result schema that does not mislabel cone residuals as ordinary
slacks. These gates authorize only the bounded leaf above.

AR-I, AR-II, common weights, virtual shares, VRS, output orientation,
undesirable outputs, panel/reference extensions, automatic generator
elicitation, statistical inference, and ordinary Pareto target completion
remain outside this source identity.
