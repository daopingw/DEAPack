# Cross-efficiency and strategic peer appraisal

Cross-efficiency changes **who evaluates whom**. A conventional CCR score lets
each organization choose the nonnegative resource and service valuations that
make its own record look as strong as possible. Cross-efficiency carries that
chosen valuation system across the rest of the comparison population. The
result is a peer-appraisal table rather than another production technology.

DEAPack currently exposes the source-frozen
`LiangWuCookZhuGameCrossEfficiency` protocol. The repository also retains an
ordinary CRS appraiser-by-evaluatee implementation for audit and property
testing, but that implementation is a non-public prototype. Its complete
defining and secondary-goal sources have not passed the release evidence gate.

Aggressive, benevolent, and neutral secondary-goal models are not hidden
options of either implementation. They select among alternate primary
multiplier optima and are deferred until their separate source protocols and
independent oracles are frozen.

## Deferred ordinary CRS candidate

For appraiser $a$, the input-normalized multiplier problem is

$$
\begin{aligned}
\max_{u_a,v_a}\quad &u_a^\top y_a\\
\text{s.t.}\quad
&v_a^\top x_a=1,\\
&u_a^\top y_j-v_a^\top x_j\leq0,\qquad j=1,\ldots,n,\\
&u_a,v_a\geq0.
\end{aligned}
$$

The resulting appraisal of organization $j$ in the later Liang et al. account
is

$$
e_{aj}=\frac{u_a^\top y_j}{v_a^\top x_j},
\qquad
\bar e_j=\frac{1}{n}\sum_{a=1}^n e_{aj}.
$$

Rows identify an appraiser and columns identify an evaluatee. The internal
prototype reports the equal column mean including self-appraisal by default.
It can also exclude the diagonal from its summary, but that switch is a
package experiment rather than a verified historical convention. There is no
current public ordinary-cross-efficiency recipe.

### Alternate multiplier optima

A primary CCR optimum need not identify unique multipliers. Consequently, a
raw cross-appraisal row, its column means, and the resulting ordering may
depend on which optimum the solver returns. The internal prototype makes that
limitation visible:

- `weight_selection` is `solver_selected_primary_optimum`;
- `score_uniqueness` and `multiplier_uniqueness` are `not_assessed`;
- no aggressive, benevolent, or neutral interpretation is attached; and
- changing backend or tolerances may change the matrix without changing the
  diagonal CCR scores.

These fields support implementation audit; they do not promote the prototype
to a source-qualified method. Do not cite its ordering as a published result
or describe it as uniquely determined. The unresolved source boundary and
next-version gate are recorded in the
[ordinary cross-efficiency source protocol](https://github.com/daopingw/DEAPack/blob/main/specs/source_protocols/ordinary_crs_cross_efficiency.md).

## Liang--Wu--Cook--Zhu game cross-efficiency

The 2008 game protocol is not a secondary tie-break. At iteration $t$, it
solves one program for every ordered pair $(d,j)$, where $d$ is the
protected organization and $j$ is the focal organization:

$$
\begin{aligned}
g_{dj}(\eta_d^t)=\max_{u,v}\quad &u^\top y_j\\
\text{s.t.}\quad
&v^\top x_j=1,\\
&u^\top y_r-v^\top x_r\leq0,\qquad r=1,\ldots,n,\\
&u^\top y_d-\eta_d^t v^\top x_d\geq0,\\
&u,v\geq0.
\end{aligned}
$$

All $n^2$ programs use the same old score vector. Only after the complete
synchronous round does the protocol update

$$
\eta_j^{t+1}=\frac{1}{n}\sum_{d=1}^n g_{dj}(\eta_d^t).
$$

The equal mean includes self and is fixed by the source protocol. It is not an
aggregation parameter.

```python
from deapack import (
    DEAData,
    GameCrossEfficiency,
    dataset_info,
    load_dataset,
)

frame = load_dataset("strategic_peer_service")
roles = dataset_info("strategic_peer_service").roles
data = DEAData.from_frame(
    frame,
    dmu=roles["dmu"],
    inputs=roles["inputs"],
    outputs=roles["outputs"],
)

game = GameCrossEfficiency(
    initial_scores=[0.80, 0.85, 0.95, 0.50],
    convergence_tolerance=0.001,
    equilibrium_tolerance=0.001,
).fit(data)

game.summary()[
    [
        "dmu_id",
        "ccr_self_efficiency",
        "score",
        "iterations",
        "equilibrium_verified",
    ]
]
```

For this project-designed four-plan teaching example, the stopping rule
completes four synchronous updates and reports approximately
$(0.9794,0.9762,1.0000,0.6667)$. These values are a project regression oracle,
not a reproduced literature table.

The final table has `protected_dmu_id` rows and `focal_dmu_id` columns. A row
does **not** apply one appraiser's fixed weights to everyone: each cell may
use a different pair-specific multiplier system.

## Result tables and role-aware queries

Both protocols return the standard `DEAResult.summary_frame` plus protocol
tables:

| Table | Deferred ordinary prototype | Public game protocol |
|---|---|---|
| `appraisals` | appraiser × evaluatee | protected × focal |
| `multipliers` | one system per appraiser | optional system per protected–focal pair |
| `history` | empty | synchronous score path |
| `diagnostics` | primary LP certificates | initialization, failure, stopping, and fixed-point diagnostics |

Role-specific game rows can be selected without renaming identifiers:

```python
game.appraisal_rows_for("reach_specialist", id_column="protected_dmu_id")

game_with_weights = GameCrossEfficiency(
    store_appraisals=False,
    store_pair_multipliers=True,
).fit(data)
game_with_weights.multipliers_for(
    "reach_specialist",
    id_column="focal_dmu_id",
)
```

`is_efficient` remains missing for the public game protocol; the internal
ordinary prototype follows the same conservative reporting rule. A
cross-efficiency score is a comparative appraisal, not a certificate of
Pareto--Koopmans efficiency.

## Certification and failure policy

Every multiplier solution must pass:

1. independent primal, bound, and reported-objective checks;
2. a dual optimality and duality-gap certificate; and
3. a postprocessed, dimensionless check that every CRS appraisal is finite and
   no greater than one within tolerance.

The third check prevents a tiny virtual-input denominator from magnifying an
apparently small absolute LP residual into an impossible appraisal.

A custom backend must therefore return primal values, inequality and equality
marginals, and an objective value in the `LPSolution` contract. A backend that
only labels a feasible primal “optimal” is rejected with
`missing_optimality_certificate`.

The game protocol publishes a score only if the synchronous sequence meets its
stopping tolerance **and** one additional complete map verifies the fixed
point. A subproblem failure, iteration limit, suspected stable two-cycle, or
failed verification leaves canonical scores missing. The last iterate and
history remain available for diagnosis; a partial final appraisal matrix is
never exposed as an equilibrium result.

## Domain and computational cost

The public game implementation and internal ordinary prototype currently
require:

- one cross section;
- nonnegative desirable-output data and no undesirable-output block;
- strictly positive values for every input component; and
- positive aggregate desirable output for every organization.

These positivity requirements are current implementation boundaries, not a
claim about every historical cross-efficiency formulation. The ordinary
prototype solves $n$ LPs. One game update solves $n^2$ LPs, followed by
another $n^2$ LPs for fixed-point verification. Set
`store_appraisals=False` to stream column summaries without an $n^2$ table.
Pair-specific multipliers require
$O(n^2(m+s))$ storage and are disabled by default.

The defining ordinary and secondary-goal sources are
[Sexton, Silkman, and Hogan (1986)](https://doi.org/10.1002/ev.1441) and
[Doyle and Green (1994)](https://doi.org/10.1057/jors.1994.84). Their complete
texts were not obtained in the audited environment, so the ordinary and
secondary-goal methods remain deferred. The complete
[Liang, Wu, Cook, and Zhu (2008)](https://doi.org/10.1287/opre.1070.0487)
article supports the later ordinary equations above and the separately
source-frozen public game protocol; it does not close the missing defining
source audit for ordinary cross-efficiency.
