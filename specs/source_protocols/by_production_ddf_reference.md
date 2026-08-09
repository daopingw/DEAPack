# By-production DDF source protocol

## Readiness record

| Field | State |
|---|---|
| Public method identity | `environmental.by_production.ddf` |
| Source-qualified runtime profile | `murty_russell_levkoff_2012_eq_4_6_4_8_5_4` |
| Primary source | first-hand article chapter obtained and equation-checked |
| Published numerical reproduction | not shipped; paper examples remain citations only |
| Independent executable evidence | project-authored case with separately compiled dense CRS programmes |
| Deferred identities | abatement-output, coupled-subtechnology, and strong-efficiency variants |

The defining source is S. Murty, R. R. Russell, and S. B. Levkoff (2012),
“On Modeling Pollution-Generating Technologies,” *Journal of Environmental
Economics and Management*,
[DOI 10.1016/j.jeem.2012.02.005](https://doi.org/10.1016/j.jeem.2012.02.005).
The equation audit also used the first-hand chapter in
[Levkoff's University of California dissertation](https://escholarship.org/uc/item/4td2w553).

The paper examines a conventional directional-distance index on its
by-production technology, then explains why that index may understate
inefficiency and depend strongly on the chosen direction. The separate FGL
measure is the authors' proposed response. `ByProductionDDF` is therefore a
source-defined diagnostic, not the authors' preferred summary.

## Source-qualified programme

Partition nonnegative inputs as $x=(x^n,x^p)$, with $x^p$ responsible for
the modeled residual. Under the source CRS cross-section,

$$
\mathcal T_1=\{(x,y,b):X\lambda\leq x,\ Y\lambda\geq y,\ \lambda\geq0\},
$$

$$
\mathcal T_2=\{(x,y,b):X^p\mu\geq x^p,\ B\mu\leq b,\ \mu\geq0\},
$$

and $\mathcal T_{BP}=\mathcal T_1\cap\mathcal T_2$. The distinct
$\lambda$ and $\mu$ systems are part of the economic model.

For a fixed nonnegative direction $g=(g^y,g^b)$, the component distances are

$$
\beta_o^1=\sup\{\beta:X\lambda\leq x_o,\
Y\lambda\geq y_o+\beta g^y,\ \lambda\geq0\},
$$

$$
\beta_o^2=\sup\{\beta:X^p\mu\geq x_o^p,\
B\mu\leq b_o-\beta g^b,\ \mu\geq0\},
$$

with $\beta_o^{BP}=\min\{\beta_o^1,\beta_o^2\}$. A zero joint step is only a
directional statement; it need not establish Pareto--Koopmans efficiency.

## Evidence and boundary

The public project case and independent compiler are documented in
`specs/oracles/by-production-ddf-project-case.md` and
`tests/test_by_production_source_oracle.py`. The repository does not contain
the paper's illustrative data or printed numerical results.

VRS/NIRS/NDRS, observation-varying directions, temporal or custom references,
coupled intensities, prices, damage weights, inference, causal claims, and
strong-efficiency completion are package extensions or
`deferred_to_next_version`; they do not inherit the source profile.
