# Emrouznejad--Anouze--Thanassoulis (2010) semi-oriented radial measure

## Readiness record

| Field | State |
|---|---|
| Candidate identifier | `static.sorm.emrouznejad_anouze_thanassoulis_2010` |
| Defining-model source | `primary_model_and_coauthor_thesis_chapter_frozen` |
| Boundedness source | `complete_text_and_theorem_proof_not_obtained` |
| Equation audit | VRS input- and output-oriented source programmes transcribed |
| Implementation status | `deferred_source_audit` |
| Numerical-oracle status | `published_example_located_not_reproduced` |
| Release disposition | `deferred_to_next_version` |
| Public API | none |
| Registry status | do not register |
| Last access audit | 2026-07-30 |

This is the controlling source-gate record for the proposed semi-oriented
radial measure (SORM) leaf. The signed-variable split and the two original VRS
programmes can be checked from first-hand material. The gate nevertheless
fails for the current version because the complete companion boundedness
article, including its theorem statements, assumptions, edge cases, and
proofs, has not been obtained.

The accessible abstract-level boundedness statements are useful discovery
evidence, but they are not an executable domain contract. DEAPack will
therefore neither implement nor register SORM in the current version. In
particular, it will not turn a remembered condition, a search-result excerpt,
or an inferred radial bound into public validation logic.

## 1. Defining sources and evidence boundary

Ali Emrouznejad, Ahmed L. Anouze, and Emmanuel Thanassoulis (2010), “A
semi-oriented radial measure for measuring the efficiency of decision making
units with negative data, using DEA,” *European Journal of Operational
Research*.
[DOI](https://doi.org/10.1016/j.ejor.2009.01.001).

A chapter in Anouze's Aston University doctoral thesis explicitly identifies
itself as adopted from the published SORM paper and the companion boundedness
paper. That chapter supplies the complete input- and output-oriented
programmes, the signed numerical example, and the reported score table.
[Coauthor thesis](https://publications.aston.ac.uk/id/eprint/16433/1/Evaluating%2Bproductive%2Befficiency%282010%29.pdf).

The separate boundedness analysis is identified by
[DOI 10.1016/j.ejor.2010.01.032](https://doi.org/10.1016/j.ejor.2010.01.032).
Only abstract and introductory material was available during this audit. The
complete article and theorem proof were not obtained. The first two sources
therefore freeze the model structure, but they do not close the operational
gate that a reliable solver-facing implementation requires.

This protocol does not treat the thesis as permission to guess what is absent
from the boundedness note. It also does not treat the existence of equations
as proof that every admissible-data, score-domain, and failure-status question
has been answered.

## 2. Economic question

SORM addresses a data-representation problem: economically meaningful inputs
or desirable outputs may take positive, zero, and negative numerical values,
so an ordinary proportional radial movement around zero can reverse or
obscure the intended improvement.

The method separates the positive and negative parts of a signed account and
then applies paired proportional requirements. For an input, improvement
means contracting its positive part while expanding the magnitude represented
by its negative part. For a desirable output, improvement means expanding its
positive part while contracting the magnitude represented by its negative
part. “Semi-oriented” refers to this sign-dependent pairing; it is not a new
economic designation of negative values as bad outputs.

## 3. Frozen signed-data representation

For every signed observation `z`, define

```math
z^1=\max\{z,0\},
\qquad
z^2=\max\{-z,0\},
\qquad
z=z^1-z^2.
```

Both components are nonnegative and at most one is positive for a raw scalar
observation. The split preserves the original account's economic role:

- a signed input remains an input for which less of the original quantity is
  preferred; and
- a signed desirable output remains an output for which more of the original
  quantity is preferred.

The source also permits accounts that are known to be nonnegative to remain
in their ordinary form. They are distinguished below from accounts requiring
the signed split.

Let:

- `J={1,...,n}` be the reference population and `o` the focal DMU;
- `I_+` and `O_+` index ordinary nonnegative inputs and outputs;
- `I_s` and `O_s` index signed inputs and outputs;
- `lambda_j` be peer intensities; and
- `h_o` be the semi-oriented radial factor.

The frozen programmes impose VRS convexity,

```math
\sum_{j\in J}\lambda_j=1,
\qquad
\lambda_j\ge0.
```

The material audited here does not authorize a CRS variant, a super-efficiency
variant, an undesirable-output technology, or an automatic second-stage slack
programme.

## 4. Frozen VRS source programmes

### 4.1 Input-oriented SORM

The input-oriented source programme minimizes `h_o`:

```math
\begin{aligned}
\min_{h_o,\lambda}\quad & h_o\\
\text{s.t.}\quad
&\sum_{j\in J}\lambda_j x_{ij}\le h_o x_{io},
&&i\in I_+,\\
&\sum_{j\in J}\lambda_j x^1_{\ell j}\le h_o x^1_{\ell o},
&&\ell\in I_s,\\
&\sum_{j\in J}\lambda_j x^2_{\ell j}\ge h_o x^2_{\ell o},
&&\ell\in I_s,\\
&\sum_{j\in J}\lambda_j y_{rj}\ge y_{ro},
&&r\in O_+,\\
&\sum_{j\in J}\lambda_j y^1_{kj}\ge y^1_{ko},
&&k\in O_s,\\
&\sum_{j\in J}\lambda_j y^2_{kj}\le y^2_{ko},
&&k\in O_s,\\
&\sum_{j\in J}\lambda_j=1,\qquad \lambda_j\ge0.
\end{aligned}
```

Thus the focal output commitments are held while the positive and negative
parts of its inputs move in the improvement directions prescribed by the
source.

### 4.2 Output-oriented SORM

The output-oriented source programme maximizes `h_o`:

```math
\begin{aligned}
\max_{h_o,\lambda}\quad & h_o\\
\text{s.t.}\quad
&\sum_{j\in J}\lambda_j x_{ij}\le x_{io},
&&i\in I_+,\\
&\sum_{j\in J}\lambda_j x^1_{\ell j}\le x^1_{\ell o},
&&\ell\in I_s,\\
&\sum_{j\in J}\lambda_j x^2_{\ell j}\ge x^2_{\ell o},
&&\ell\in I_s,\\
&\sum_{j\in J}\lambda_j y_{rj}\ge h_o y_{ro},
&&r\in O_+,\\
&\sum_{j\in J}\lambda_j y^1_{kj}\ge h_o y^1_{ko},
&&k\in O_s,\\
&\sum_{j\in J}\lambda_j y^2_{kj}\le h_o y^2_{ko},
&&k\in O_s,\\
&\sum_{j\in J}\lambda_j=1,\qquad \lambda_j\ge0.
\end{aligned}
```

Here the focal input commitments are held while the positive and negative
parts of its outputs move in their prescribed improvement directions.

The source leaves `h_o` free in both LPs. It calls the input-oriented optimum
`h_o^*` the input-reduction SORM efficiency and reports `1/h_o^*` as the
output-augmentation SORM efficiency. Those source transformations are
frozen. Their valid bounds across all permitted data patterns, and especially
their degenerate cases, remain part of the missing boundedness audit. No
clipping rule or universal `[0,1]` software contract may be inferred from the
transcription.

## 5. Source boundary and Pareto limitation

The component construction changes the represented production possibility
set. The source warns that SORM can remove part of the possibility set that
would be present under the original unsplit representation. This is a
substantive modelling consequence, not a harmless internal recoding.

The radial factor is proportional within the positive and negative parts, but
it does not exhaust every input excess and output shortfall. A stage-one SORM
projection can therefore fail to be Pareto efficient. The current source
freeze does not authorize DEAPack to:

- label every SORM target strongly or Pareto efficient;
- equate a radial score of one with the absence of all slacks;
- silently append a lexicographic or additive slack stage; or
- present solver-selected peer intensities as a unique managerial benchmark.

When no observation in any modelled account is negative, the sign split loses
its special role and the source programme reduces to the corresponding
ordinary radial VRS structure. This limiting relationship does not make SORM
an alias for ordinary radial DEA on signed data.

## 6. Boundedness evidence not yet frozen

Accessible summary material for the companion note reports conditions along
the following lines:

- the input-oriented programme is bounded when the focal DMU has at least one
  strictly positive input;
- the output-oriented programme is bounded when the focal DMU has at least
  one strictly positive output; and
- supporting both orientations therefore calls for a focal unit with at least
  one strictly positive input and at least one strictly positive output.

These statements are recorded only so that the next audit knows what must be
verified. They must not be copied into a validator, public API contract,
method registry, book recipe, or failure-message taxonomy. Without the
complete theorem text and proof, the audit cannot yet establish:

1. the exact quantifiers and whether each condition is necessary, sufficient,
   or both;
2. all assumptions on the reference set, self-inclusion, VRS convexity, and
   the radial factor;
3. how zero-only, negative-only, mixed-sign, and degenerate accounts enter the
   theorem;
4. whether feasibility and finite optimality require separate diagnostics;
5. the valid score domain for every permitted data pattern; and
6. whether the published theorem corrects, narrows, or supplements the
   original model text.

A plausible LP that happens to solve ordinary examples is not an acceptable
substitute for these missing answers.

## 7. Numerical evidence and future oracle

The coauthor thesis contains a ten-DMU signed-data example and a reported
table of input- and output-oriented SORM results. Those data and results have
been located, but they have not yet been independently transcribed,
recomputed, and certified. They are therefore discovery evidence rather than
a passed numerical oracle.

A future executable oracle must include all of the following:

1. a page-checked transcription of the complete published example, including
   every positive and negative component and every reported score;
2. an independent equation-level compiler for both VRS orientations;
3. reproduction of the published optimum for every DMU, not merely its
   ranking;
4. exact or rational synthetic cases with hand-provable optima;
5. adversarial cases covering zero-only, negative-only, mixed-sign, and
   strictly positive focal accounts;
6. explicit checks for infeasibility, unboundedness, finite-but-out-of-domain
   solutions, solver failure, and alternative peer optima;
7. separate reporting of the invariant score, source target, peer activity,
   and residual slacks; and
8. regression tests proving the non-equivalence boundaries in Section 8.

No published-example fixture should be labelled an oracle until an independent
implementation reproduces the complete result vector within a declared
tolerance.

## 8. Non-equivalence boundary

SORM must remain distinct from the following methods:

- **Portela--Thanassoulis--Simpson RDM.** RDM constructs a
  focal-to-coordinatewise-ideal range direction and reports `1-beta` under
  its own VRS bounded-score argument. SORM splits signed values and applies
  paired semi-radial constraints. Their targets, scores, boundedness
  conditions, and data transformations are different.
- **Modified signed-data SBM (`static.msbm.signed`).** An SBM formulation
  aggregates normalized input and output slacks rather than optimizing one
  SORM radial factor. Its normalizers, weights, monotonicity, and
  strong-efficiency claims require a separate defining source and oracle.
  `static.msbm.signed` remains an umbrella, not a fallback implementation of
  SORM.
- **Undesirable-output DEA.** A negative number is a numerical sign, whereas
  an undesirable output is an economic role for which reduction is
  preferred. SORM's signed desirable-output constraints still pursue more of
  the original desirable account. They do not encode bad-output contraction,
  weak disposability, null-jointness, or environmental production trade-offs.
- **Radial DEA after an arbitrary translation.** Translating all observations
  and running an ordinary radial model changes ratios and can change the
  estimator. It does not reproduce the source's paired positive/negative
  component constraints.
- **An automatic Pareto-completion model.** A second-stage slack optimization
  changes the estimator and target-selection rule. It cannot be silently
  included under the SORM name.

Shared use of VRS intensities or a common LP backend is an implementation
composition opportunity, not evidence that any of these methods are aliases.

## 9. Gate for the next version

The candidate may be reopened only after all of these conditions are met:

1. obtain the complete authorized text of the boundedness article;
2. freeze every theorem, assumption, proof-relevant case distinction, and
   implication for preflight validation and solver-status handling;
3. reconcile the final SORM article, the coauthor thesis chapter, and the
   boundedness note equation by equation, documenting any correction or
   notation change;
4. freeze the native input and output score meanings, admissible domains,
   target equations, slack accounts, and failure semantics;
5. reproduce the full published ten-DMU result vector with an independent
   compiler and add hand-provable signed-data fixtures;
6. test bounded and unbounded edge cases directly against the frozen theorem;
   and
7. pass explicit non-equivalence tests against RDM, a named signed-data SBM
   leaf, undesirable-output DEA, and translated ordinary radial DEA.

Only then may the project add a public class, preset, machine method record,
catalog entry, book implementation recipe, or claim of SORM support. Until
that gate passes, this file records a deliberately deferred candidate for the
next version; it is not documentation of an implemented method.
