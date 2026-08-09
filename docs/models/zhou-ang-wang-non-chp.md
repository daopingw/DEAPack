# Zhou--Ang--Wang non-CHP energy--carbon performance

```{eval-rst}
.. currentmodule:: deapack
```

`ZhouAngWangNonCHPEnergyCarbonDEA` implements the three non-CHP electricity-
generation accounts in Zhou, Ang, and Wang (2012).
`NonCHPEnergyCarbonDEA` is its exact short alias. Both names fit the canonical
method
`environmental.directional_nonradial.energy_carbon.zhou_ang_wang_2012_non_chp`.

The method does not estimate one universal environmental-efficiency score. It
answers one of three declared questions:

- `account="energy"`: how much fossil fuel can be saved and electricity
  expanded while the represented carbon quantity remains fixed;
- `account="carbon"`: how much electricity can be expanded and carbon
  reduced without exceeding the observed fossil-fuel commitment; or
- `account="integrated_energy_carbon"`: what joint fuel-saving,
  electricity-expansion, and carbon-reduction opportunity remains.

The public class is a source preset, not a generic non-radial directional
kernel.

```{note}
This is a specialized, paper-specific application preset. It belongs in the
package Documentation and method catalog rather than the companion
handbook's sequence of principal model families.
```

## Supported source surface

| Dimension | Public behavior |
|---|---|
| Production system | electricity generation without combined heat and power (CHP) |
| Data roles | exactly one fossil-energy input, one electricity output, and one CO2 undesirable output |
| Data domain | every quantity finite and strictly positive |
| Technology | source $T_1$ CRS common-factor weak-disposal construction |
| Reference | homogeneous self-inclusive cross-section only |
| Decision accounts | `energy`, `carbon`, `integrated_energy_carbon` |
| Directions | observed-value directions fixed by the selected source account |
| Weights | source block normalizations fixed at one half or one third |
| Target completion | none beyond the source phase-one component plan |

The class does not expose arbitrary directions, user weights, additional
inputs or outputs, alternative returns to scale, custom or panel references,
zero repairs, signed quantities, or another disposal technology. Those
changes require separately identified models.

## Non-CHP technology and component programme

For positive reference observations $(F_j,E_j,C_j)$, the source technology is

$$
T_1=
\left\{(F,E,C):
\sum_jz_jF_j\leq F,\quad
\sum_jz_jE_j\geq E,\quad
\sum_jz_jC_j=C,\quad
z_j\geq0
\right\}.
$$

There is no convexity equation. The carbon equality is part of this particular
CRS common-factor weak-disposal construction; it should not be copied into an
unrelated environmental technology merely because that technology also has a
CO2 column.

For evaluated system $o$, the complete source form is

$$
\begin{aligned}
\max_{z,\beta_F,\beta_E,\beta_C}\quad
&w_F\beta_F+w_E\beta_E+w_C\beta_C\\
\text{subject to}\quad
&\sum_jz_jF_j\leq F_o-\beta_FF_o,\\
&\sum_jz_jE_j\geq E_o+\beta_EE_o,\\
&\sum_jz_jC_j=C_o-\beta_CC_o,\\
&z_j\geq0,\qquad
\beta_F,\beta_E,\beta_C\geq0.
\end{aligned}
$$

An inactive component is fixed at zero. Component steps are not constrained to
be equal, so a fitted system can have no demonstrated fuel saving and still
have a material electricity-expansion or carbon-reduction opportunity.

## Source accounts and score directions

| Account | Active weights | Raw distance | Performance index |
|---|---:|---:|---:|
| `energy` | $(1/2,1/2,0)$ | $D^{NR}=(\beta_F+\beta_E)/2$ | $EPI=(1-\beta_F)/(1+\beta_E)$ |
| `carbon` | $(0,1/2,1/2)$ | $D^{NR}=(\beta_E+\beta_C)/2$ | $CPI=(1-\beta_C)/(1+\beta_E)$ |
| `integrated_energy_carbon` | $(1/3,1/3,1/3)$ | $D^{NR}=(\beta_F+\beta_E+\beta_C)/3$ | $ECPI=[1-(\beta_F+\beta_C)/2]/(1+\beta_E)$ |

The fixed weights normalize the active fuel, electricity, and carbon blocks.
They are not market prices, expenditure shares, carbon taxes, marginal damage
estimates, or stakeholder priorities. Passing different weights would change
the model identity, so the public constructor does not accept them.

Score direction is explicit:

- a larger raw $D^{NR}$ means more unrealized opportunity and therefore worse
  current performance under the selected account;
- a larger source performance index means better current performance, with
  one as the source best-practice value.

Package plots declare the index as their management-facing default. The raw
distance remains available for opportunity-gap diagnostics and is never
relabeled as higher-is-better performance.

## Exact three-system fixture

`zhou_ang_wang_non_chp_3` is an analytical teaching dataset derived from the
printed equations:

| System | `fossil_energy` | `electricity` | `co2` |
|---|---:|---:|---:|
| A | 1 | 1 | 1 |
| D | 1.5 | 1 | 4 |
| O | 2 | 1 | 4 |

```python
from deapack import (
    DEAData,
    NonCHPEnergyCarbonDEA,
    dataset_info,
    load_dataset,
)

frame = load_dataset("zhou_ang_wang_non_chp_3")
roles = dataset_info("zhou_ang_wang_non_chp_3").roles
data = DEAData.from_frame(
    frame,
    dmu=roles["dmu"],
    inputs=roles["inputs"],
    outputs=roles["outputs"],
    bad_outputs=roles["bad_outputs"],
)

energy = NonCHPEnergyCarbonDEA(account="energy").fit(data)
carbon = NonCHPEnergyCarbonDEA(account="carbon").fit(data)
integrated = NonCHPEnergyCarbonDEA(
    account="integrated_energy_carbon",
).fit(data)

integrated.summary()[
    [
        "dmu_id",
        "directional_nonradial_distance",
        "performance_index",
        "performance_index_name",
        "beta_fossil",
        "beta_electricity",
        "beta_carbon",
        "component_plan_unique",
        "solver_status",
    ]
]
```

The exact results for O are:

| Account | Component steps | Raw $D^{NR}$ | Index | Target $(F^*,E^*,C^*)$ |
|---|---|---:|---:|---|
| Energy | $(0,3/5,0)$ | $3/10$ | $5/8$ | $(2,8/5,4)$ |
| Carbon | $(0,1,1/2)$ | $3/4$ | $1/4$ | $(2,2,2)$ |
| Integrated | $(0,1,1/2)$ | $1/2$ | $3/8$ | $(2,2,2)$ |

These values are an exact analytical oracle, not numbers published for the
article's country application.

The management-facing plot defaults to the selected source performance index:

```python
integrated.plot(
    kind="performance",
    metric="performance_index",
    theme="deapack",
)
```

The index plot is higher-is-better. Use
`metric="directional_nonradial_distance"` for the raw opportunity account,
where larger values mean more unrealized improvement and zero is the no-gap
benchmark.

```python
integrated.plot(
    kind="performance",
    metric="directional_nonradial_distance",
    theme="deapack",
)
```

## Result and multiplicity contract

The summary keeps the source account, raw opportunity distance
(`directional_nonradial_distance`), transformed `performance_index`,
`performance_index_name`, the three `beta_*` component steps, solver state,
`score_valid`, `ranking_value_valid`, and identification status separate.
`score` and `efficiency` repeat the higher-is-better performance index for
standard result discovery; `distance` repeats the source raw opportunity
distance. Their declared plotting semantics remain opposite.

Targets retain `observed`, `direction`, `directional_change`, `target`,
`peer_activity`, `target_unique`, and `target_kind`. Intensities report one
solver-selected CRS peer portfolio; residuals and diagnostics retain
source-row feasibility and certificate evidence.

The LP objective can have a unique optimal value while component steps,
targets, and peers remain non-unique. The result therefore provides
`component_plan_unique`, `performance_index_identified`, `target_unique`, and
`peer_plan_unique`, together with `beta_fossil_lower/upper`,
`beta_electricity_lower/upper`, `beta_carbon_lower/upper`, and
`performance_index_lower/upper`. A fitted portfolio is an admissible
explanatory certificate, not a unique technology plan or a recommendation to
copy another country's generation mix.

The default `diagnose_multiplicity=False` performs only the primary source
solve: one LP per organization. It returns the solver-selected components,
index, target, and peers, while uniqueness and identification flags remain
nullable/not assessed and the range columns remain missing. This is the
efficient choice when only the source score and one certified explanatory
plan are required. `score_valid=True` in this mode certifies the computation
and source-account transformation; it does not claim that the component plan
or transformed index is unique.

Set `diagnose_multiplicity=True` to solve the additional optimal-face range
problems:

```python
diagnosed = NonCHPEnergyCarbonDEA(
    account="integrated_energy_carbon",
    diagnose_multiplicity=True,
).fit(data)
```

Only then may `component_plan_unique`, `performance_index_identified`,
`target_unique`, or `peer_plan_unique` become true when their corresponding
ranges support that conclusion. A false or missing flag must never be turned
into a uniqueness claim in reporting.

Independent positive changes to the units of fossil energy, electricity, and
CO2 co-scale the observed-value directions. Component steps, intensities, raw
distance, and the source performance index remain invariant, while physical
targets co-scale.

## CHP and empirical evidence boundaries

Only the source $T_1$ non-CHP branch is implemented. In the article's printed
CHP programme, the heat component appears in both the electricity and heat
constraints, leaving a positively weighted electricity component absent from
all constraints. The programme is unbounded as printed. No publisher or
author correction was located, so DEAPack does not silently substitute an
inferred equation or expose a CHP option.

The study reports results for 126 countries—82 non-CHP and 44 CHP—but does not
publish the complete unit-level observations required to reconstruct the
reference technologies. No audited complete data bundle has been located.
DEAPack therefore makes no reproduction claim for country scores, ranks,
means, frontier memberships, or statistical tests.

The precise source, oracle, and non-equivalence boundary is recorded in the
[Zhou--Ang--Wang source protocol](https://github.com/daopingw/DEAPack/blob/main/specs/source_protocols/zhou_ang_wang_2012_non_chp_energy_carbon.md).
