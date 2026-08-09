# Declared-calibration input-oriented EBM

```{eval-rst}
.. currentmodule:: deapack
```

The epsilon-based measure (EBM) is useful when a manager wants one benchmark
to recognize both a common resource-saving programme and the fact that some
resources can be substituted more readily than others. DEAPack's public EBM
route is deliberately narrow: it evaluates the input-oriented CRS programme
in [Tone and Tsutsui (2010)](https://doi.org/10.1016/j.ejor.2010.07.014) after
the analyst has declared the importance calibration. It is a conditional
evaluator, not an automatic calibration engine.

## The admitted decision problem

For organization $o$, the public score is

$$
\gamma_o=
\theta-\varepsilon\sum_i w_i\frac{s_i^-}{x_{io}},
$$

with the source input-oriented CRS balances

$$
\theta x_o-X\lambda-s^-=0,\qquad Y\lambda\ge y_o,\qquad
\lambda,s^-\ge0.
$$

The first term records a common proportional input factor. The second records
the declared importance-weighted input mix. They are optimized together under
one feasible peer plan; EBM is not an average of a separately fitted CCR score
and an SBM score.

`InputOrientedEpsilonBasedDEA` requires a
`DeclaredEBMCalibration`. Its `epsilon`, exact name-keyed input weights, and
source, decision owner, calibration population, and validity period are
immutable and fingerprinted in the result metadata. There is no default
epsilon, automatic equal weighting, or silent weight normalization.

```python
import pandas as pd

from deapack import (
    DEAData,
    DeclaredEBMCalibration,
    InputOrientedEpsilonBasedDEA,
)

frame = pd.DataFrame(
    {
        "hospital": ["A", "B", "C"],
        "physicians": [4.0, 5.0, 7.0],
        "nurses": [8.0, 6.0, 10.0],
        "treated_cases": [12.0, 12.0, 12.0],
        "quality_adjusted_discharges": [9.0, 9.0, 9.0],
    }
)

calibration = DeclaredEBMCalibration(
    epsilon=0.4,
    input_weights={"physicians": 0.6, "nurses": 0.4},
    source="2026 service-resource review",
    decision_owner="hospital operations committee",
    calibration_population="licensed acute-care hospitals",
    validity_period="2026 planning cycle",
)

data = DEAData.from_frame(
    frame,
    dmu="hospital",
    inputs=["physicians", "nurses"],
    outputs=["treated_cases", "quality_adjusted_discharges"],
)
result = InputOrientedEpsilonBasedDEA(calibration=calibration).fit(data)
result.summary()[
    ["dmu_id", "score", "radial_factor", "weighted_normalized_input_excess"]
]
```

The route accepts one strictly positive, ordinary-input/ordinary-output cross
section. It fixes CRS and one full self-inclusive reference technology. There
is no option for panel data, alternative returns to scale, undesirable outputs,
external reference populations, peer-eligibility rules, or an output/non-
oriented EBM. Those are separate method and evidence tasks.

## Read an input-oriented target as an input mix

Here $\theta$ is free, as in the source programme. Consequently an EBM target
need not reduce every input separately. A hospital may use fewer physicians
and more nurses while delivering the maintained output bundle. That is a
feasible resource-substitution recommendation under the declared peer
technology, not a sign error and not a claim that every input should increase.

`targets`, `slacks`, and `peers` describe one solver-selected primary optimum.
They are not unique prescriptions. The result labels their selection status,
and each claim has its own postsolve certificate: a certified score need not
imply that every target, peer, or dual account can be published.

## Endpoints and boundaries

With $\epsilon=0$, the score equals the input-oriented CCR score under this
same CRS, full-sample profile. Its EBM target remains a solver-selected EBM
optimum, so it is not claimed to reproduce a CCR slack-completion target.

With $\epsilon=1$, the public call is **not** an input-SBM alias. The standard
equal-weight input SBM also fixes $\theta=1$; the EBM source programme leaves
$\theta$ free. At this endpoint the EBM score does not identify theta, so
DEAPack reports the minimum feasible theta for the solver-selected peer plan
without another optimization call. This package-defined completion preserves
the score but does not turn the selected target into a unique source target.

The source paper also develops an affinity/PCA procedure for constructing
epsilon and weights. DEAPack does **not** run it. Its calibration population,
projection selection, repeated-eigenvalue rule, and one published-table data
lineage remain unresolved in the current evidence record. Accordingly,
`static.ebm` and `static.ebm.input.tone_tsutsui_2010.crs` remain deferred;
only `static.ebm.input.tone_tsutsui_2010.crs.declared` is executable.

## Audit the released accounts

`score` (also exposed as `efficiency`) is $\gamma$, with one denoting EBM input
efficiency in the source's limited sense. `distance` is $1-\gamma$ for this
self-inclusive profile. `radial_factor`, `weighted_normalized_input_excess`,
and `weighted_input_mix_ratio` show how the declared compromise is assembled.
The metadata records the exact calibration fingerprint, confirms
`automatic_affinity_pca_run=False`, and reports one compiled reference, one
primary LP per organization, and zero secondary solves.

```{autosummary}
DeclaredEBMCalibration
InputOrientedEpsilonBasedDEA
```
