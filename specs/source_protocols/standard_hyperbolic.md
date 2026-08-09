# Standard reciprocal hyperbolic DEA: deferred release protocol

## Readiness record

| Field | State |
|---|---|
| Candidate identifier | `static.hyperbolic.standard_reciprocal` |
| Source status | `primary_definition_partially_frozen` |
| Implementation status | `deferred_source_convention_gate` |
| Equation-freeze status | `modern_reciprocal_path_confirmed_source_native_1985_score_unresolved` |
| Numerical-oracle status | `located_cross_implemented_and_analytical` |
| Release disposition | `deferred_to_next_version` |
| Public API | none |
| Registry status | do not register |
| Last access audit | 2026-07-31 |

The standard reciprocal hyperbolic model is not a public method in the
current version. A modern formulation, an independently executed published
fixture, and the exact algebraic relationship to the implemented
Chavas--Cox generalized-distance path have now been located. Release is still
blocked because the complete 1985 defining chapter has not been page-audited,
the source-native score name and transformation remain ambiguous, primary
sources do not yet give one frozen zero-coordinate domain, and the package
target policy has not been reconciled with the distinction between a path
projection and a strongly efficient target.

## Evidence acquired and its limit

| Evidence | What was checked | What it does not establish |
|---|---|---|
| Färe, Grosskopf, and Lovell (1985), *The Measurement of Efficiency of Production*, Chapter 5, pp. 107--130, especially the cited pp. 110 and 125--126 | Authoritative metadata establish the hyperbolic-graph chapter and the separate generalized Farrell-graph section. | The full pages were not legally obtainable in this audit, so their native graph index, reciprocal convention, data domain, and target language are not frozen. |
| Chavas and Cox (1999), Staff Paper 422 / *Southern Economic Journal* 66, pp. 294--318, staff-paper pp. 4--11 | Definition 2 gives $D(x,y,T,\alpha)$ on $x,y\geq0$; Definition 3 calls $D$ technical efficiency; the polar radial cases, CRS invariance, and comparisons with the 1985 graph measures are explicit. Audited artifact SHA-256: `9ae5a15e99aafdad26c8ab75ff65c5865f72420d20fa9b7fe96620069c78b473`. | Its printed relation between $D(x,y,T,0.5)$ and the 1985 Farrell graph measure cannot substitute for inspecting the 1985 definition; see the convention conflict below. |
| Färe, Margaritis, Rouse, and Roshdi (2016), *EJOR* 254, pp. 312--319, DOI `10.1016/j.ejor.2016.03.045` | The publisher record confirms the modern HDF, its exact VRS DDF-based algorithm, the CRS square-root relationship to radial efficiency, and a seven-DMU one-input/one-output example. | Only the publisher preview was obtainable. It is not a complete page audit of all score, data-domain, and target statements in the article. |
| Halická, Trnovská, and Černý (2024), *EJOR* 312, pp. 298--314, accepted manuscript pp. 8--13, DOI `10.1016/j.ejor.2023.06.039` | Equation (6) gives the standard VRS HDF; equation (10) gives the distinct direction-vector HDF-g; the paper distinguishes HDF from its additive DDF linearisation and proves that a path projection need not be strongly efficient. Audited artifact SHA-256: `34d3f335d4808d7ff5a6fdbd53690f429ae8ff78aeb3ed0f3e040a7363af2526`. | It is a later unifying treatment, not a replacement for the source-native 1985 score convention. |
| CRAN `DJL` 3.9, `dm.hdf` documentation and source | Its documented example explicitly reproduces Table 2 of Färe et al. (2016). The VRS result was independently executed and then checked by exact frontier-intersection equations below. Audited tarball SHA-256: `8f759cb56d7bfd9cefd866c2244ad3065acf8a5d469c695f7f91024bcb580261`. | This validates a numerical HDF convention; it cannot decide what public name or transformation DEAPack should attribute to the unavailable 1985 pages. |

## Modern reciprocal path and conditional exact transformation

The later authoritative formulation minimizes the direct reciprocal
adjustment factor

$$
h_o^*
=
\min\left\{
  h>0:
  (h x_o,h^{-1}y_o)\in\mathcal T
\right\}.
$$

Under a self-inclusive VRS envelopment this has the nonlinear programme

$$
\begin{aligned}
\min_{h,\lambda}\quad & h \\
\text{s.t.}\quad
&X\lambda\leq h x_o,\\
&Y\lambda\geq h^{-1}y_o,\\
&\mathbf 1^\top\lambda=1,\qquad \lambda\geq0,\quad h>0.
\end{aligned}
$$

Its phase-one reciprocal path target is

$$
(x_o^{path},y_o^{path})=(h_o^*x_o,h_o^{*-1}y_o).
$$

For exactly the same observation, reference population, technology, returns
to scale, disposability assumptions, and target stage, the implemented
Chavas--Cox model at $\alpha=1/2$ is

$$
\delta_o^*
=
\min\left\{
  \delta>0:
  (\delta^{1/2}x_o,\delta^{-1/2}y_o)\in\mathcal T
\right\}.
$$

Matching path coordinates gives

$$
h_o^*=\sqrt{\delta_o^*},
\qquad
\delta_o^*=(h_o^*)^2.
$$

This is a conditional exact score transform and path-target identity, not a
blanket alias. Under the matched ordinary CRS cone, $\delta$ equals the
bounded radial technical-efficiency score, while $h$ is its square root. Under
VRS, $h$ is not an input- or output-oriented radial score.

### Unresolved 1985 score convention

Chavas and Cox's staff-paper p. 7 prints that the 1985 Farrell graph measure
is $D(x,y,T,0.5)^2$. Read literally, that statement does not match the direct
coordinate substitution above or the later CRS square-root relationship.
The difference may reflect another source-native graph index, a reciprocal or
power convention, or a printing error. DEAPack must not choose among those
possibilities without the complete 1985 pp. 107--130. Consequently:

- $h$ is the confirmed modern path-coordinate score used only for this
  protocol's algebra and oracle;
- `farrell_graph_efficiency`, `hyperbolic_distance`, and any reciprocal or
  squared display field remain unfrozen source names; and
- the future public preset may be named only after its source-native field and
  higher-is-better direction have been checked directly.

## Data-domain gate

The sources currently support two different release profiles:

- Chavas--Cox defines GDF for nonnegative $x$ and $y$, and the 2016 publisher
  description states nonnegative input/output vectors with at least one
  nonzero component in each vector; but
- Halická et al. state that standard HDF is commonly defined for componentwise
  positive data, then use their more general HDF-g construction to handle
  signed data under separately admissible directions.

Reciprocal scaling itself requires $h>0$ but does not algebraically divide by
each coordinate. A structural zero therefore remains zero along the path and
is not automatically invalid. Before release, the defining source profile
must say whether DEAPack accepts structural zeros, which positive-support
conditions guarantee a finite bounded optimum, and whether signed-data HDF-g
is a different leaf rather than an extension of standard HDF. No silent
epsilon replacement or translation is permitted.

## Target and efficiency semantics

The reciprocal path identifies one unique coordinate target, even when peer
intensities are nonunique. Later path-model analysis shows that this boundary
point need not be Pareto--Koopmans strongly efficient, and a score of one need
not certify strong efficiency. A future result must therefore distinguish:

- `path_target`: $(h x_o,h^{-1}y_o)$;
- `phase_one_reference_activity`: the activity generated by the selected
  phase-one intensities; and
- `target`: an optional slack-completed strongly efficient benchmark chosen by
  an explicit DEAPack second-stage policy.

Slack completion must not change the native $h$, and a package-selected strong
target must not be attributed to the historical source unless that target
selection is itself source-fixed.

## Independent numerical oracle now available

The seven-DMU VRS fixture documented as reproducing Table 2 of Färe et al.
(2016) is

| DMU | $x$ | $y$ | $h$ |
|---|---:|---:|---:|
| a | 2 | 3 | 1 |
| b | 4 | 7 | 1 |
| c | 9 | 10 | 1 |
| d | 6.5 | 8.5 | 1 |
| o | 10 | 4 | 0.518670608516... |
| p | 6 | 2 | 0.452035741742... |
| q | 9 | 8 | 0.863606693226... |

The `DJL` 3.9 implementation returned these values independently. They also
follow from the piecewise-linear VRS frontier:

$$
\begin{aligned}
h_o&=\frac{-23+\sqrt{2929}}{60},
&30h_o^2+23h_o-20&=0,\\
h_p&=\frac{1+\sqrt{97}}{24},
&12h_p^2-h_p-2&=0,\\
h_q&=\frac{-23+\sqrt{4849}}{54},
&27h_q^2+23h_q-40&=0.
\end{aligned}
$$

A read-only replay through the current
`GeneralizedDistanceDEA(alpha=0.5, returns_to_scale="vrs")` path returned
$\sqrt{\delta}=(1,1,1,1,0.518670613971,0.452035780266,
0.863606715330)$, agreeing with the independent values at the configured
scalar-search tolerance. This confirms that a future preset can reuse the GDF
compiler; it is not additional source evidence.

This closes the former “no independent oracle” gap. It does not close the
source-convention, domain, or target-policy gates.

## Models that must not be merged under “generalized hyperbolic”

The label names several different lineages rather than one option-rich model:

| Lineage | Defining change | Disposition |
|---|---|---|
| Färe--Grosskopf--Lovell generalized Farrell graph (1985, pp. 125--126) | Aggregates source-specific input/output graph adjustments and chooses over a parameter; Chavas--Cox report a distinct formula. | Defer until the original pages and an oracle are audited. |
| Chavas--Cox GDF (1999) | Uses bearing $\alpha$ in $(\delta^{1-\alpha}x,\delta^{-\alpha}y)$ over the ordinary quantity technology. | Already implemented only as `static.generalized_distance.chavas_cox`; not renamed generalized HDF. |
| Direction-vector HDF-g (Halická et al. 2024) | Uses $x_o+(h-1)g_x$ and $y_o+(h^{-1}-1)g_y$; it may support signed data with admissible directions. | Separate future source-qualified generalized-path leaf. |
| Generalized hyperbolic distance with fixed subsets (Wilson 2025) | Allows selected subsets of inputs and outputs to remain fixed and attaches DEA/FDH estimation and inference. | Full formulation not obtained; defer to a later version. |
| Generalized multiplicative directional distance / log-linear technology | Changes the maintained technology and multiplicative distance account, not just the HDF path. | Keep with the multiplicative/log-linear lineage; no HDF alias. |

A path equation, admissible parameter set, technology, native score,
zero/signed-data domain, target semantics, and oracle must be frozen for each
lineage before any can appear under `static.hyperbolic.generalized_path`.

## Non-equivalence boundaries

- **Directional distance:** DDF with observation-scaled directions is the
  first-order additive linearisation of the reciprocal output adjustment near
  $h=1$; it is not an exact HDF alias away from the frontier.
- **Ordinary radial DEA:** matched CRS scores have a square-root relationship,
  but VRS hyperbolic targets jointly change inputs and outputs and generally
  differ from both radial projections.
- **Multiplicative DEA:** HDF measures a reciprocal path over an ordinary
  quantity technology. Multiplicative DEA estimates a log-conic or log-convex
  piecewise Cobb--Douglas technology. Shared logarithms or scalar searches do
  not make the technologies or scores equivalent.
- **Chavas--Cox GDF:** only the balanced $\alpha=1/2$ path has the conditional
  coordinate transform above; source identity, native display convention,
  and generalized extensions remain distinct.

## Implementation boundary

No second numerical solver may be copied or created for the standard path. If
the next-version evidence gate passes, the implementation must be a thin,
source-retaining preset over `GeneralizedDistanceDEA(alpha=0.5)`. It must
report the frozen native HDF/graph score while preserving the auditable
relationship `generalized_distance = h**2`. Generalized lineages require
their own semantic records even when they can share a fixed-parameter LP
feasibility compiler.

## Next-version release gate

Before publication:

1. legally obtain and page-audit Färe, Grosskopf, and Lovell (1985), Chapter 5,
   especially pp. 110 and 125--126;
2. freeze the native score name, optimization direction, reciprocal/power
   transforms, admissible data, technology, and target language;
3. decide and test the structural-zero policy without epsilon repair;
4. reproduce the seven-DMU oracle above through the future public preset,
   including exact $h$, $\delta=h^2$, path targets, peers, and residuals;
5. test the CRS radial relationship and the VRS non-equivalence, external
   references, row/unit transformations, solver failures, and phase-two
   strong-target policy; and
6. audit every generalized lineage separately rather than adding a generic
   `variant=` switch.

Until all source-native obligations are satisfied, both the standalone
standard leaf and every generalized-hyperbolic leaf remain deferred and
absent from the public registry.
