# System-radial network output orientation: source-closure protocol

## Readiness record

| Field | State |
|---|---|
| Public method | `network.radial.fare_grosskopf_2000` |
| Capability | `orientation="output"` inside the existing system-radial family |
| CRS source status | `primary_full_text_page_and_equation_checked` |
| VRS source status | `composed_extension`: standard output distance over the separately sourced two-process VRS technology |
| Implementation status | `implemented_public` |
| Equation-freeze status | `frozen` |
| Numerical-oracle status | `analytically_derived_and_independently_compiled` |
| Release disposition | `included_current_version` |
| Public API | `FareGrosskopfNetworkRadialDEA(orientation="output")` |
| Book placement | existing Network DEA core-family chapter; no additional route |
| Last source audit | 2026-08-02 |

This protocol records why output orientation is a measure choice inside the
same connected-system family rather than a new paper-named model. It also
separates the source-native CRS claim from DEAPack's explicit VRS composition.

## 1. Primary sources and exact locators

Färe and Grosskopf's open 1995 working paper, “Productivity and Intermediate
Products: A Frontier Approach,” is the accessible precursor to the 1996
*Economics Letters* article
([DOI](https://doi.org/10.1016/0165-1765(95)00729-6)). The complete eight-page
working paper is deposited by
[EconWPA](https://econwpa.ub.uni-muenchen.de/econ-wp/comp/papers/9506/9506001.pdf).

The source audit freezes the following pages and equations:

- page 4, equations (4)--(5): separate activity intensities for two connected
  nodes, nonnegative CRS activity, external-resource feasibility, final-output
  feasibility, and the production/use accounts for intermediate products;
- page 5, equation (6): the Shephard output distance
  $D_o(x,y)=\inf\{\Theta:(x,y/\Theta)\in S\}$ and the statement that CRS input
  and output distances are reciprocal; and
- page 6, equation (12): the executable inverse-distance programme
  $D_o(x,y)^{-1}=\max\Theta$, with the assessed final-output vector expanded
  by $\Theta$ inside the two-node network technology.

Färe and Grosskopf (2000), “Network DEA,”
([DOI](https://doi.org/10.1016/S0038-0121(99)00012-9)) supplies the later
network-DEA lineage. Podinovski and Bouzdine-Chameeva (2021)
([DOI](https://doi.org/10.1007/s11123-021-00610-3)) supplies the separately
convex two-process VRS technology used by the existing public class.

## 2. Reduction to DEAPack's closed two-stage account

The 1995 source allows external inputs at both nodes and final outputs from
both nodes. DEAPack's basic closed series account is the following transparent
restriction:

- all external inputs enter the upstream process;
- all final outputs leave the downstream process;
- every upstream output is an intermediate input to the downstream process;
- upstream and downstream keep separate nonnegative intensity vectors; and
- unused upstream intermediate supply is strongly disposable.

After renaming the source's process intensities as $\lambda$ (upstream) and
$\mu$ (downstream), the CRS output programme reduces to

$$
\begin{aligned}
\max_{\phi,\lambda,\mu}\quad &\phi\\
\text{subject to}\quad
&X\lambda\leq x_o,\\
&Z\mu\leq Z\lambda,\\
&Y\mu\geq\phi y_o,\\
&\phi,\lambda,\mu\geq0.
\end{aligned}
$$

Thus $\phi=D_o(x_o,y_o)^{-1}$. DEAPack reports the source-native radial factor
as `score` and `system_score`, and the harmonized higher-is-better efficiency
$1/\phi=D_o(x_o,y_o)$ as `efficiency` and `system_efficiency`. Under a valid
self-inclusive reference population, $\phi\geq1$ and efficiency is at most
one. An external custom reference can reverse that familiar range, so
membership and classification remain explicit.

The link equation does not condition on the assessed organization's observed
$z_o$. That value remains a reported comparison only. The output programme
defines one system score and no process efficiencies.

## 3. VRS composition boundary

For VRS, DEAPack adds

$$
\mathbf1^\top\lambda=1,
\qquad
\mathbf1^\top\mu=1.
$$

This is not attributed to the 1995/1996 CRS paper or to Färe and Grosskopf
(2000). It is the standard output distance of equation (6) evaluated on the
separately convex two-process technology already sourced to Podinovski and
Bouzdine-Chameeva (2021). CRS input and output efficiencies coincide by
homogeneity; VRS input and output orientations generally answer different
management questions and need not return the same plan or efficiency.

## 4. Independent numerical evidence

No published Färe--Grosskopf output-efficiency table is claimed. Validation is
instead tied directly to the frozen equations:

1. a production-independent dense compiler constructs the output LP without
   importing DEAPack's sparse network compiler;
2. the two-organization disposal case has an exact CRS output factor of 10 for
   organization U, efficiency 0.1, and a positive surplus of one unit in the
   second intermediate product;
3. a three-organization VRS case gives organization C output factor $3/2$ and
   efficiency $2/3$, while its input efficiency is $1/2$; this detects the
   invalid shortcut of reciprocating the input optimum; and
4. matrix-structure, target, unit/order invariance, reference, compile-reuse,
   and fail-closed tests protect the complete result contract.

The independent derivation and expected accounts are recorded in
`specs/oracles/fare-grosskopf-network-output.md`.

## 5. Handbook and identity boundary

The handbook teaches two management commitments inside one system-radial
account: preserve final services while reducing external resources, or
preserve external resources while expanding final services. Neither
orientation creates stage scores. Solver certificates, native-factor fields,
target residuals, and provenance details remain in package Documentation.

No new method ID, catalog entry, chapter, or appendix is created. The existing
CRS equality between the input-radial system efficiency and the Kao--Hwang
primary system score is not automatically expanded to output targets, VRS,
process attribution, or complete result identity.
