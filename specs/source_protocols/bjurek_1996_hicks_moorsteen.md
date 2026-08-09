# Bjurek (1996) Hicks--Moorsteen source protocol

## Readiness record

| Field | State |
|---|---|
| Current method identity | `productivity.hicks_moorsteen.bjurek_1996` |
| Defining source | Bjurek (1996), *The Scandinavian Journal of Economics* 98(2), 303--313, [DOI 10.2307/3440861](https://doi.org/10.2307/3440861) |
| Existing evidence record | `specs/reviews/PRODUCTIVITY.md`, section 5.1, marked `primary-checked` |
| Authoritative equation check | Zelenyuk (2023), equations (12)--(22), [DOI 10.1007/s11123-023-00692-1](https://doi.org/10.1007/s11123-023-00692-1) |
| Independent oracle | exact analytical fixture plus dense source-form VRS programmes; no production code reused |
| Published empirical reproduction | no |
| Source-gate disposition | passed for the narrow bilateral identity below |
| Deferred beyond this gate | decompositions, environmental extensions, multilateral references, inference, and Bjurek's empirical tables |

The evidence is sufficient to freeze the formula family without inferring a
paper-specific extension. Bjurek's DOI establishes the defining article, the
existing review records the primary-source check, and the authoritative
productivity review gives the input and output distance definitions, the two
period-specific input and output quantity indexes, and their geometric
reconciliation explicitly. Färe, Grosskopf, and Roos's contemporary CESifo
paper also records that Bjurek's construction is a ratio of Malmquist output
and input quantity indexes and studies its well-definedness conditions.

This protocol does not claim a new page-level audit of a locally archived
Bjurek PDF. It freezes only the formula boundary independently confirmed by
the evidence above.

## Frozen bilateral identity

Let $(x^t,y^t)$ and $(x^{t+1},y^{t+1})$ be the same producer in two periods,
and let $D_O^r$ and $D_I^r$ be Shephard output and input distances relative
to technology $\mathcal T^r$. The two output quantity views are

$$
Q_y^t=\frac{D_O^t(x^t,y^{t+1})}{D_O^t(x^t,y^t)},
\qquad
Q_y^{t+1}=\frac{D_O^{t+1}(x^{t+1},y^{t+1})}
{D_O^{t+1}(x^{t+1},y^t)}.
$$

The matching input quantity views are

$$
Q_x^t=\frac{D_I^t(x^{t+1},y^t)}{D_I^t(x^t,y^t)},
\qquad
Q_x^{t+1}=\frac{D_I^{t+1}(x^{t+1},y^{t+1})}
{D_I^{t+1}(x^t,y^{t+1})}.
$$

The bilateral indexes and total-factor-productivity change are

$$
Q_y^{t,t+1}=\sqrt{Q_y^tQ_y^{t+1}},
\qquad
Q_x^{t,t+1}=\sqrt{Q_x^tQ_x^{t+1}},
\qquad
HM^{t,t+1}=\frac{Q_y^{t,t+1}}{Q_x^{t,t+1}}.
$$

Each of the four quantity views is a ratio of two distances. One transition
therefore has four output-distance and four input-distance tasks. The period
technology, fixed bundle, and evaluated bundle are part of every task; they
cannot be reordered without defining a different quantity index.

## Exact oracle boundary

The independent certificate is
`tests/test_bjurek_1996_hicks_moorsteen_source.py`, documented in
`specs/oracles/bjurek-1996-hicks-moorsteen-analytical.md`. It compiles dense
linear programmes directly with NumPy and SciPy and imports no `deapack`
module.

The certified fixture deliberately has:

- one matched producer of interest observed in both periods;
- a dominated reference activity in each period, so the reference arrays are
  nontrivial but the exact active intensity is provable;
- two strictly positive inputs and two strictly positive desirable outputs;
- two contemporaneous VRS technologies;
- all eight distances positive and finite; and
- nonproportional input and output changes, so the two period views differ.

The fixture checks the eight primitive values, both period-specific output
and input quantity views, $Q_y$, $Q_x$, $HM=Q_y/Q_x$, and reciprocal time
reversal. Expected values are derived algebraically in the oracle note and
are not generated from package output.

VRS is frozen only for this exact executable certificate. The bilateral
quantity-index identity is not promoted into a claim that one returns-to-
scale assumption is universally required by the family.

## Release boundary

This gate supports the existing adjacent bilateral Hicks--Moorsteen identity.
It does not supply an efficiency-change/technical-change, scale, mix, or
causal decomposition. It does not establish circularity for chained periods,
an environmental technology, an industry aggregation rule, a common global
reference, statistical inference, or a published empirical reproduction.
Those questions require their own sources and tests and remain outside the
current model boundary.
