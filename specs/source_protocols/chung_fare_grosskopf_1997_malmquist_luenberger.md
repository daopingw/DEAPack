# Chung--Färe--Grosskopf (1997) Malmquist--Luenberger source protocol

## Source identity

- Y. H. Chung, R. Färe, and S. Grosskopf, “Productivity and Undesirable
  Outputs: A Directional Distance Function Approach,” *Journal of
  Environmental Management* 51 (1997), 229--240.
- DOI:
  [10.1006/jema.1997.0146](https://doi.org/10.1006/jema.1997.0146).
- Predecessor used only to resolve the fixed-input source-edition boundary:
  Chung and Färe, 1995 working paper,
  [equation (2.14)](https://econwpa.ub.uni-muenchen.de/econ-wp/mic/papers/9511/9511002.pdf).

The executable leaf is
`productivity.malmquist_luenberger.chung_fare_grosskopf_1997`. It freezes the
period technology, observed output--residual direction, four distance roles,
and equations (3.5)--(3.7). It is not a configurable label for other
environmental technologies or directions.

## Economic production account

For one observation $z=(x,y,b)$:

- $x$ is a vector of productive resources;
- $y$ is a vector of desirable products or services; and
- $b$ is a vector of jointly produced undesirable residuals.

The source output set $P(x)$ treats $x$ as the available resource
commitment. Desirable output is strongly disposable. Desirable and
undesirable outputs are jointly weakly disposable, and null jointness means
that the maintained technology does not produce positive desirable output
with a zero residual vector.

The source chooses the signed direction $g=(y,-b)$. DEAPack stores direction
magnitudes as $(g^x,g^y,g^b)=(0,y,b)$ and supplies the contraction sign in

$$
(x,\;y+\beta y,\;b-\beta b).
$$

Thus a positive directional distance represents a feasible proportional
increase in the observed desirable-output vector together with a proportional
decrease in the observed residual vector, while resources remain fixed.

## Source-edition boundary

The journal definition of $P(x)$, its stated $g=(y,-b)$, and the surrounding
economic explanation all describe an output-direction programme with fixed
inputs. The journal's printed equation (3.14), however, places
$(1-\beta)x$ on the right-hand side of the input constraint. That row would
contract inputs even though $g^x=0$.

The 1995 working-paper equation (2.14) prints $X\lambda\leq x$, consistent
with the definition. DEAPack therefore freezes the fixed-input programme

$$
\begin{aligned}
\max_{\lambda,\beta}\quad &\beta\\
\text{s.t.}\quad
&X^r\lambda\leq x_o,\\
&Y^r\lambda\geq(1+\beta)y_o,\\
&B^r\lambda=(1-\beta)b_o,\\
&\lambda\geq0,
\end{aligned}
$$

for a period-$r$ reference technology. There is no intensity-sum equation:
the named source leaf is CRS. This protocol records an internal
source-edition inconsistency. It does not claim that a formal publisher
erratum exists.

## Four distance roles

For adjacent periods $t$ and $t+1$, the evaluated observation supplies its
own observed direction in every task. Let the left subscript identify the
evaluated plan and the right subscript identify the technology:

$$
\begin{aligned}
F_{t\mid t}&=1+D^t(z^t;y^t,-b^t),\\
F_{t+1\mid t}&=1+D^t(z^{t+1};y^{t+1},-b^{t+1}),\\
F_{t\mid t+1}&=1+D^{t+1}(z^t;y^t,-b^t),\\
F_{t+1\mid t+1}&=1+D^{t+1}(z^{t+1};y^{t+1},-b^{t+1}).
\end{aligned}
$$

The package result names these tasks:

| Factor | Result field suffix | Evaluated plan | Technology |
|---|---|---|---|
| $F_{t\mid t}$ | `base_on_base` | $z^t$ | $t$ |
| $F_{t+1\mid t}$ | `comparison_on_base` | $z^{t+1}$ | $t$ |
| $F_{t\mid t+1}$ | `base_on_comparison` | $z^t$ | $t+1$ |
| $F_{t+1\mid t+1}$ | `comparison_on_comparison` | $z^{t+1}$ | $t+1$ |

Cross-period distances are not clipped at zero. A negative value records that
the reference-period environmental opportunity set cannot reproduce the
evaluated plan without reversing part of the declared improvement programme.
Every factor $1+D$ must remain strictly positive for the multiplicative index
to be defined.

## Productivity and decomposition

The source equations (3.5)--(3.7) become

$$
ML^{t,t+1}
=
\left(
\frac{F_{t\mid t}}{F_{t+1\mid t}}
\frac{F_{t\mid t+1}}{F_{t+1\mid t+1}}
\right)^{1/2},
$$

$$
EC_{ML}^{t,t+1}=\frac{F_{t\mid t}}{F_{t+1\mid t+1}},
$$

and

$$
TC_{ML}^{t,t+1}
=
\left(
\frac{F_{t\mid t+1}}{F_{t\mid t}}
\frac{F_{t+1\mid t+1}}{F_{t+1\mid t}}
\right)^{1/2}.
$$

They satisfy

$$
ML^{t,t+1}=EC_{ML}^{t,t+1}TC_{ML}^{t,t+1}.
$$

Values above one indicate improvement under this specific environmental
production account. $EC_{ML}$ describes change in performance relative to
each period's own opportunity set. $TC_{ML}$ describes change in the
best-practice environmental opportunities relevant to the two evaluated
plans. Neither component alone identifies a causal management intervention,
policy effect, welfare gain, or monetary value.

## Execution and failure protocol

- Match adjacent observations by stable DMU identifier and ordered period.
- Compile one contemporaneous CRS reference block for each period.
- Cache each unique evaluated-row by technology-period distance task.
- Retain a negative cross-period distance when the LP is optimal.
- Withhold $ML$, $EC_{ML}$, and $TC_{ML}$ if any task fails or any
  $1+D$ factor is nonpositive.
- Preserve all four task diagnostics and the decomposition residual.
- Require comparable ratio-scale resources, desirable outputs, and residuals
  over time.

## Evidence boundary

The independent analytical certificate is
`specs/oracles/chung_fare_grosskopf_1997_malmquist_luenberger.md`. It verifies
the four-task operator without calling the production compiler.

The journal reports geometric means for 39 Swedish pulp-and-paper mills over
1986--1990, but it does not publish the mill-level panel needed to replay
those values. DEAPack therefore does not claim a published Table 2
reproduction. That empirical branch is `deferred_to_next_version`.

Changing the direction, returns to scale, disposal technology, null-jointness
rule, period reference construction, or multiplicative operator defines a
different method. Those broader candidates must pass their own source and
oracle gates rather than inherit the CFG identity.
