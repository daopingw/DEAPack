# System-radial network output orientation: independent analytical oracle

**Method ID:** `network.radial.fare_grosskopf_2000`  
**Capability:** `orientation="output"`  
**Validation kind:** `primary_equation_and_analytically_derived`  
**Published numerical reproduction:** no

This certificate validates output orientation inside DEAPack's existing
closed two-stage system-radial family. Expected values are derived from the
source equations and exact synthetic accounts, not from the production sparse
compiler or a published empirical table.

## Source equation and closed-series reduction

Färe and Grosskopf's open 1995 working paper, later published in 1996, defines
a two-node CRS network on page 4, the output distance on page 5, equation (6),
and its inverse-distance LP on page 6, equation (12). The source writes

$$
D_o(x,y)^{-1}=\max\Theta
$$

while proportionally expanding the assessed final-output vector within the
connected technology.

Restricting external inputs to node 1, final outputs to node 2, and node 1
outputs to the intermediate products consumed by node 2 gives

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

Here $\lambda$ constructs the upstream supply plan and $\mu$ the downstream
use-and-final-output plan. The source-native `score` is $\phi$; the harmonized
higher-is-better `efficiency` is $1/\phi=D_o(x_o,y_o)$. The programme defines
no process efficiency.

For the separately sourced VRS composition, add

$$
\mathbf1^\top\lambda=1,
\qquad
\mathbf1^\top\mu=1.
$$

## Exact disposal account

The first fixture has one external input, two intermediate products, and one
final output:

| Organization | $x$ | $z_1$ | $z_2$ | $y$ |
|---|---:|---:|---:|---:|
| U | $1$ | $1$ | $2$ | $1/10$ |
| D | $10$ | $1$ | $1$ | $1$ |

For U under CRS, choose upstream intensity $\lambda_U=1$ and downstream
intensity $\mu_D=1$. The resulting plan uses external input one, supplies
$(1,2)$ internally, requires $(1,1)$ downstream, and produces final output
one. It therefore attains

$$
\phi_U=10,
\qquad
E_U=\frac1{10}.
$$

The second intermediate has disposable surplus one. No plan can produce more:
the downstream output/intermediate ratios and the upstream input/intermediate
requirements imply that one unit of external input can support at most one
unit of final output in this fixture. The feasible witness and bound certify
the optimum.

Under CRS, D can scale the same connected plan by ten and also has
$\phi_D=10$. Under VRS, the two process intensities must each sum to one;
sample output cannot exceed one, so D has $\phi_D=1$. These values distinguish
conic scaling from separate process convexification.

## Exact orientation-separation account

The second fixture uses one variable in each role:

| Organization | $x$ | $z$ | $y$ |
|---|---:|---:|---:|
| A | $1$ | $1$ | $1$ |
| B | $3$ | $3$ | $3$ |
| C | $4$ | $2$ | $2$ |

For C under VRS, selecting B for both processes gives a feasible plan with
input three, link supply and requirement three, and final output three. Hence
$\phi_C\geq3/2$. Convexity bounds every represented final output by the sample
maximum three, so $\phi_C\leq3/2$. Therefore

$$
\phi_C=\frac32,
\qquad
E_C^{\mathrm{output}}=\frac23.
$$

The input-oriented optimum on the same VRS technology is $1/2$, not $2/3$.
This fixture proves that output orientation must be solved directly; taking
the reciprocal of an input optimum would produce the wrong factor, plan, and
management interpretation.

Under CRS, C has $\phi_C=2$ and harmonized efficiency $1/2$. This agrees with
its CRS input efficiency, as required by the source's homogeneity result, but
the equality is a property of the conic technology rather than an instruction
to reuse input targets.

## Independent executable check

The automated oracle assembles dense input, link, output, and convexity blocks
directly from the equations above and calls SciPy/HiGHS. It does not import the
production `CompiledTwoStageQuantities`, sparse `envelopment_problem`, or
result post-processing. The tests compare every public output factor and
efficiency with that compiler and separately freeze the exact witnesses,
targets, link surplus, CRS/VRS difference, and VRS orientation difference.

The executable locators are:

- `tests/test_fare_grosskopf_network_radial.py::test_output_matches_independent_dense_source_equation_compiler`;
- `tests/test_fare_grosskopf_network_radial.py::test_output_disposal_oracle_uses_native_factor_and_reciprocal`; and
- `tests/test_fare_grosskopf_network_radial.py::test_output_vrs_hand_oracle_is_not_the_reciprocal_input_programme`.

Additional regression checks cover:

- factor-column placement and right-hand-side signs for both orientations;
- self-inclusive and external-reference classification;
- independent positive rescaling and declaration-order invariance;
- observed-handoff non-conditioning;
- targets reconstructed from complete rather than display-thresholded
  intensities;
- one reference compilation and one solve per assessed organization; and
- fail-closed behavior when the solver or primal-dual certificate fails.

## Claim boundary

The certificate covers a nonnegative, closed, two-process series graph with
external inputs only upstream, final desirable outputs only downstream,
separate process intensities, disposable upstream link surplus, and positive
aggregate input/output support. CRS is a direct reduction of the primary
network output-distance equations. VRS is the declared composition with the
separately sourced process-convex technology.

It does not certify process efficiencies, slack-completed Pareto--Koopmans
efficiency, exact handoff, open or cyclic graphs, shared intensities, external
inputs downstream, final outputs upstream, undesirable intermediates,
sampling inference, or a published Färe--Grosskopf numerical table.
