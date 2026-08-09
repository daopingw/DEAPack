# Zhou--Ang--Wang (2012) non-CHP energy--carbon source protocol

## Readiness record

| Field | State |
|---|---|
| Candidate identity | `environmental.directional_nonradial.energy_carbon.zhou_ang_wang_2012_non_chp` |
| Frozen source presets | `energy`, `carbon`, and `integrated_energy_carbon` |
| Primary source | complete journal article obtained and equation-checked |
| Source branch admitted by this protocol | $T_1$, countries without combined heat and power (CHP) plants, equations (4) and (6)--(10) |
| Source branch not admitted | $T_2$/CHP, equations (11)--(15), because the printed LP is internally unbounded as written |
| Current numerical certificate | `analytically_derived`; exact fixture plus an independently assembled dense LP |
| Published application reproduction | `not_reproduced`; the complete 126-country observations are not available in the article or an audited source bundle |
| Production implementation | none asserted by this protocol |
| Current disposition | source-frozen for a narrow non-CHP implementation; every generalized switch and the CHP branch are deferred |
| Last source audit | 2026-07-31 |

The defining source is P. Zhou, B. W. Ang, and H. Wang (2012),
“Energy and CO2 Emission Performance in Electricity Generation: A
Non-radial Directional Distance Function Approach,” *European Journal of
Operational Research* 221(3), 625--635,
[DOI 10.1016/j.ejor.2012.04.022](https://doi.org/10.1016/j.ejor.2012.04.022).

This record freezes a historical electricity-generation application, not a
generic `nonradial=True` option. Its economic question is whether a comparable
non-CHP electricity system can save fossil energy, supply more electricity,
or reduce CO2 by different proportions, as demonstrated by the same
cross-sectional reference population.

## 1. Frozen production account

For each organization, let

- $F>0$ be fossil-fuel input;
- $E>0$ be electricity generated, the desirable output; and
- $C>0$ be CO2 emissions, the undesirable output.

For positive reference observations $(F_j,E_j,C_j)$, source equation (4)
constructs the CRS technology

$$
T_1=
\left\{(F,E,C):
\sum_j z_jF_j\leq F,\quad
\sum_j z_jE_j\geq E,\quad
\sum_j z_jC_j=C,\quad
z_j\geq0
\right\}.
$$

There is no intensity-sum equation. Fossil input and electricity are strongly
disposable in the directions stated by the source. The CO2 equality belongs
to the source's common-factor weak-disposal construction; it is not a generic
definition of every weakly disposable technology. With strictly positive
reference emissions, $C=0$ forces all intensities to zero and supplies the
source null-jointness account.

The source separates countries with and without CHP plants before constructing
the two frontiers. This protocol retains that comparability decision. It does
not pool the one-good-output $T_1$ observations with CHP observations that
also produce useful heat.

## 2. Component-specific directional programme

For evaluated organization $o$, source equations (6)--(7) define

$$
\begin{aligned}
\max_{z,\beta_F,\beta_E,\beta_C}\quad
&w_F\beta_F+w_E\beta_E+w_C\beta_C\\
\text{s.t.}\quad
&\sum_jz_jF_j\leq F_o+\beta_Fg_F,\\
&\sum_jz_jE_j\geq E_o+\beta_Eg_E,\\
&\sum_jz_jC_j=C_o+\beta_Cg_C,\\
&z_j\geq0,\qquad \beta_F,\beta_E,\beta_C\geq0.
\end{aligned}
$$

Only components active in a source preset are decision variables. An inactive
component is fixed at zero rather than returned as an economically meaningless
free variable. The demonstrated target is

$$
(F_o^*,E_o^*,C_o^*)=
(F_o+\beta_Fg_F,\ E_o+\beta_Eg_E,\ C_o+\beta_Cg_C).
$$

The component steps need not be equal. That is the defining non-radial
feature: management's demonstrated opportunity to save fuel need not have
the same percentage as its opportunity to expand electricity or reduce CO2.
The optimal weighted sum $D^{NR}=w^\top\beta$ is a source-native
inefficiency distance. A larger value means more unrealized improvement, not
better current performance.

## 3. The three source presets

The candidate may expose an `account` selector only as a choice among these
three immutable source presets:

| `account` | Signed direction $g$ | Weights $w$ | Source performance index |
|---|---|---|---|
| `energy` | $(-F_o,E_o,0)$ | $(1/2,1/2,0)$ | $EPI_1=(1-\beta_F)/(1+\beta_E)$ |
| `carbon` | $(0,E_o,-C_o)$ | $(0,1/2,1/2)$ | $CPI_1=(1-\beta_C)/(1+\beta_E)$ |
| `integrated_energy_carbon` | $(-F_o,E_o,-C_o)$ | $(1/3,1/3,1/3)$ | $ECPI_1=[1-(\beta_F+\beta_C)/2]/(1+\beta_E)$ |

The article states that each performance index lies between zero and one on
its maintained domain, with larger values representing better current
performance and one representing source-directional best practice. These
indexes are source-native transformations of a selected component solution;
they do not replace the raw $w^\top\beta$ result.

The weights normalize the input, desirable-output, and undesirable-output
blocks in the three published accounts. They are not prices, social-damage
weights, or analyst-supplied value judgments. The observed-value directions
also matter: under a coherent positive change of units for $F$, $E$, or $C$,
the corresponding data and direction co-scale, leaving $z$, $\beta$, the raw
distance, and the performance index unchanged while targets co-scale.

## 4. Source preset versus generalized switch

The following are not admitted under the Zhou--Ang--Wang identity:

- arbitrary direction components or user-supplied weights;
- more than one input, desirable output, or undesirable output;
- VRS, NIRS, or NDRS;
- custom, leave-one-out, external, panel, window, sequential, biennial, or
  global references;
- zero, negative, translated, interval, or missing quantities;
- a strong-disposal, activity-specific weak-disposal, by-production,
  material-balance, network, or treatment technology; or
- a radial DDF, weighted additive DEA, directional SBM, or Tone undesirable-
  output SBM score.

Shared matrix assembly with one of those methods would be implementation
reuse, not a model alias. A future generalized component-directional API must
obtain its own defining source, domain contract, and oracle. It must not be
reported as “Zhou--Ang--Wang (2012)” merely because equation (7) can accept
symbols called $g$ and $w$.

## 5. The CHP branch fails closed

The source's general definition (11) for the CHP technology $T_2$ contains
separate electricity and heat components $\beta_{2E}$ and $\beta_{2H}$.
However, the printed electricity row in equation (12) is

$$
\sum_m z_{2m}E_{2m}\geq E+\beta_{2H}g_{2E},
$$

and the printed heat row also uses $\beta_{2H}$. Consequently
$\beta_{2E}$ appears with a positive coefficient in the objective but in no
constraint. Model (B.3) in Appendix B repeats the same electricity-row
substitution. As printed, every CHP preset with positive electricity weight
is therefore unbounded.

Equations (13)--(15), Appendix C, and the diagonal construction in equation
(11) make an intended replacement by $\beta_{2E}$ plausible, but they do not
constitute a formal correction. No publisher erratum or author-issued
correction was located in this audit. DEAPack must not silently repair the
row, reproduce the reported CHP numbers under an inferred equation, or expose
the $T_2$ branch under the source name. It remains
`deferred_to_next_version` until first-hand corrective evidence closes the
equation.

## 6. Multiplicity and result identification

The raw LP objective has a well-defined optimal value when the programme is
feasible and bounded, but peers, component steps, and targets need not be
unique. Appendix B.1 supplies a sufficient multiplicity construction for the
integrated non-CHP programme when

$$
\beta_F+\beta_E+\beta_C=1.
$$

On that particular optimal face $ECPI_1=1/2$, even though the component plan
can change. This special result is not a general proof that every transformed
index is invariant over every optimal face. A future implementation must
distinguish the identified raw objective from solver-selected component plans.
Before it labels a component target or transformed performance index unique,
it should check the relevant range over the optimal face or report the
ambiguity explicitly. It must never advertise a unique peer portfolio,
least-cost plan, engineering prescription, or causal abatement effect.

## 7. Numerical and empirical evidence boundary

The exact analytical certificate is
`specs/oracles/zhou_ang_wang_2012_non_chp_energy_carbon.md`. It uses one
strictly positive three-organization fixture and LP arrays assembled directly
from equations (4) and (7). The exact component solutions, targets, raw
distances, and all three source indexes were also checked with a stand-alone
dense SciPy/HiGHS programme during the source audit.

The correct evidence label is `analytically_derived`:

- the fixture values are exact consequences of the printed source equations,
  not numbers printed in the article;
- the dense programme was independent equation assembly, but there is no
  production implementation against which it could be a cross-implementation
  test; and
- use of an LP solver to corroborate the rational derivation does not turn the
  fixture into a published reproduction.

The empirical study uses 2005 IEA-derived observations for 126 countries,
split into 82 non-CHP and 44 CHP countries. The article publishes summary
statistics and selected country results in Appendix C, while stating that the
remaining values are available from the corresponding author. It does not
supply the complete unit-level reference data needed to rebuild either
frontier. No audited complete source bundle was located. DEAPack therefore
does not claim to reproduce Appendix C, the reported country means, rankings,
frontier memberships, or hypothesis tests. The 126-country replay remains
`deferred_to_next_version`.

## 8. Narrow implementation gate

A later production change may admit only the three non-CHP presets above and
must, at minimum:

1. require one finite strictly positive $F$, $E$, and $C$ column and a
   self-inclusive homogeneous reference population;
2. compile the CRS technology once and solve one sparse LP per organization
   and source preset with inactive components fixed at zero;
3. return component steps, raw $w^\top\beta$, the named source performance
   index, target quantities, peer intensities, residuals, and multiplicity
   diagnostics separately;
4. verify target reconstruction, primal feasibility, the source score range,
   and coherent unit invariance;
5. fail closed on non-optimal or unbounded solves; and
6. preserve `source_preset`, production account, disposal, null-jointness,
   CRS, reference policy, and the `analytically_derived` evidence label in
   result metadata.

This protocol does not itself register a method, implement a solver, or make
the candidate public.
