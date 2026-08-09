# Andersen--Petersen (1993) radial super-efficiency: deferred release protocol

## Readiness record

| Field | State |
|---|---|
| Candidate identifier | `evaluation.super.ap_radial` |
| Source status | `defining_article_identified_full_text_not_obtained` |
| Implementation status | `prototype_internal_only` |
| Equation-freeze status | `later_source_reconstruction_only` |
| Numerical-oracle status | `candidate_later_source_and_derived_checks` |
| Release disposition | `deferred_to_next_version` |
| Public API | none |
| Registry status | retained non-public prototype |
| Last access audit | 2026-07-31 |

This protocol controls the evidence boundary for DEAPack's proposed
Andersen--Petersen radial super-efficiency method. Prototype code and internal
tests may remain so that the numerical construction can be audited. They are
not current-release evidence for a public catalog method, public symbol, or
executable book recipe.

## 1. Defining source and access boundary

Per Andersen and Niels Christian Petersen (1993), “A Procedure for Ranking
Efficient Units in Data Envelopment Analysis,” *Management Science*, 39(10),
1261--1264. [DOI](https://doi.org/10.1287/mnsc.39.10.1261). The article also
has [JSTOR stable record 2632964](https://www.jstor.org/stable/2632964).

The publisher abstract verifies the paper's purpose and central comparison:
efficient organizations are appraised relative to a reference technology
spanned by the other observations so that frontier units can be ranked. A
complete, legally accessible copy of the four-page article was not obtained
in the audited environment. INFORMS and JSTOR full-text routes required
access that was unavailable, Unpaywall reported no open repository copy, and
no local copy was found.

A longer predecessor is catalogued as Andersen and Petersen (1989),
*A procedure for ranking efficient units in data envelopment analysis*,
Department of Management publication 11/1989, Odense University. The audited
catalog record describes 25 pages plus four unnumbered pages, but no digital
full text was obtained.

Consequently, DEAPack has not page-frozen the defining source's exact primal
or multiplier programme, orientation, returns-to-scale assumption,
non-Archimedean or lexicographic slack treatment, data domain, numerical
illustration, target convention, or failure policy. Those details cannot be
filled from familiarity with later super-efficiency literature.

## 2. What is verified, and what is not

The defining publisher record supports only the following current claims:

- the intended problem is discrimination among DEA-efficient units;
- the evaluated observation is compared with a technology generated without
  using that observation itself; and
- the procedure supplies a framework for ranking efficient units and for
  comparison with parametric rankings.

The following proposed source profile is **not yet verified** from the
defining full text:

1. input orientation rather than output orientation;
2. CRS rather than VRS, NIRS, or NDRS;
3. the exact score normalization and whether slacks enter the objective;
4. whether the programme is evaluated only for efficient units or for the
   complete observation set;
5. strict positivity versus a nonnegative domain with zero components;
6. the treatment of weakly efficient and non-extreme efficient units;
7. the meaning of a solver-selected target or peer intensity; and
8. the treatment of infeasible or unbounded programmes.

Until these items are frozen, input/output orientation, all four RTS options,
panel and custom reference policies, output reciprocal reporting, target
selection, and fail-closed solver handling are prototype conventions or later
extensions. They must not inherit the Andersen--Petersen (1993) source
identity merely because they reuse a radial leave-one-out compiler.

## 3. Later primary evidence

Xue and Harker (2002), “Ranking DMUs with Infeasible Super-Efficiency DEA
Models,” *Management Science*, 48(5), 705--710
([DOI](https://doi.org/10.1287/mnsc.48.5.705.7805)), is available in full and
provides useful but separate evidence. It formulates an input-oriented VRS
super-efficiency programme under strictly positive input and output data,
retains non-Archimedean slack terms, and reports a six-unit numerical example.
It also states that non-CRS infeasibility was recognized in later literature,
not supplied as a complete rule by the 1993 paper.

The current prototype reproduces its Table 2 values for units A--F:
1.500, 1.095238, 1.133333, infeasible, 0.714286, and 0.666667. This validates a
later input-VRS programme and its solver state. It does not turn VRS into a
verified Andersen--Petersen (1993) preset. Xue and Harker propose an economic
ranking interpretation for certain infeasible units; DEAPack's current choice
to return a missing score and preserve the solver status is a conservative
prototype policy, not a source-native 1993 rule.

Lu and Lo (2009), “An interactive benchmark model ranking performers—
Application to financial holding companies,” *Mathematical and Computer
Modelling*, 49, 172--179
([DOI](https://doi.org/10.1016/j.mcm.2008.06.008)), reprints a five-unit,
two-input, one-output table and attributes it to Andersen and Petersen. The
prototype reproduces the displayed scores 1.000, 1.315789, 1.200, 1.250, and
0.750 and its displayed peer mixtures. That is valuable secondary
cross-check evidence, but a later reprint cannot replace the defining article
for a `reproduced` source-oracle claim.

## 4. Why the current tests do not close the gate

The internal tests show that the prototype compiler behaves coherently:

- a one-input, one-output CRS ratio calculation has exact expected values;
- the later Xue--Harker VRS table and infeasible row can be reconstructed;
- input and output reporting, four RTS constraints, unit changes, reference
  exclusion, target thresholding, and fail-closed solver states are tested;
  and
- the indirectly reprinted five-unit table can be reproduced.

These checks do not establish a current public Andersen--Petersen method
because:

1. the defining equations and assumptions have not been transcribed from the
   complete 1993 article;
2. the existing production compiler is not an independent compiler derived
   from page-frozen defining equations;
3. the five-unit table is available only through a later reprint; and
4. the Xue--Harker table belongs to a later, explicitly VRS and
   infeasibility-focused source profile.

An exact synthetic certificate can close numerical correctness for a named
generic radial leave-one-out programme. It cannot establish the historical
source identity that remains unverified.

## 5. Gate for the next version

The candidate may be reconsidered only after all of the following are
available:

1. a complete authorized copy of Andersen and Petersen (1993), or the full
   1989 predecessor with a documented reconciliation to the journal article;
2. page-level transcription and independent review of the defining primal and
   multiplier programmes, objective hierarchy, assumptions, and economic
   interpretation;
3. an explicit source profile for orientation, RTS, data positivity and zero
   handling, reference membership, applicability, and score direction;
4. a source-native rule—or an explicit statement of source silence—for
   infeasibility, unboundedness, weak efficiency, and nonunique targets;
5. a defining-source numerical reproduction, or an exact independently
   compiled certificate whose narrower claim is clearly distinguished from a
   published reproduction;
6. separate identities for later VRS, output-oriented, NIRS/NDRS,
   panel/custom-reference, and infeasibility-diagnostic extensions unless the
   defining source expressly includes them; and
7. synchronized code, registry, book, documentation, and tests that expose
   only the source-frozen profile as Andersen--Petersen.

Until that gate passes, `deferred_to_next_version` is the release disposition.
