# Cooper--Deng--Huang--Li (2002) congestion: deferred release protocol

## Readiness record

| Field | State |
|---|---|
| Candidate identifier | `analysis.congestion.cooper_deng_huang_li_2002` |
| Source status | `metadata_and_abstract_checked`; later same-author corroboration available |
| Implementation status | `none` |
| Equation-freeze status | `not_frozen_from_defining_source` |
| Numerical-oracle status | `not_located` |
| Release disposition | `deferred_to_next_version` |
| Public API | none |
| Book placement | no named-model placement; congestion concept only inside the scale family |
| Last access audit | 2026-08-02 |

This protocol prevents a historically important simplification of a
slack-based congestion analysis from being promoted as an additional core DEA
family. It also prevents later restatements from being mistaken for a
page-frozen audit of the defining article.

## 1. Defining source and access boundary

The defining article is William W. Cooper, Honghui Deng, Zhaohui Huang, and
Sixin X. Li (2002), “A one-model approach to congestion in data envelopment
analysis,” [DOI](https://doi.org/10.1016/S0038-0121(02)00008-3). The
[Adelphi institutional record](https://scholarlyworks.adelphi.edu/esploro/outputs/journalArticle/A-one-model-approach-to-congestion-in/991004347080306266)
supplies authoritative metadata, the abstract, and a link to the version of
record, but not a deposited full text. The publisher record exposes the
abstract while the complete article remains access-restricted in the audited
environment.

An accessible later paper by the same authors restates a deterministic
one-model programme while developing a chance-constrained extension. It is
useful primary corroboration, but it does not substitute for the 2002 pages,
their exact assumptions, or their numerical table. Likewise, the accessible
[Cooper--Seiford--Zhu (2000) article](https://doi.org/10.1016/S0038-0121(99)00010-5)
belongs to the related unified-additive lineage; it cannot be assumed to be an
exact alias for the 2002 recipe.

## 2. What can and cannot presently be claimed

The available sources support the family-level idea that a projection can be
used to distinguish input excess associated with lost output from ordinary
slack. Later same-author material also indicates an output-oriented VRS first
stage followed by a slack-level problem. That is enough to understand the
lineage, but not enough to attribute a complete executable contract to the
2002 article.

In particular, the defining source has not been page-checked for:

- its exact lexicographic or non-Archimedean objective and a numerically stable
  finite implementation;
- the full target-selection and source-allocation convention;
- all data-domain and returns-to-scale assumptions;
- the treatment of alternate optimal projections;
- the original example data and expected results; and
- any scalar normalization beyond physical input-level congestion amounts.

Strong/weak congestion labels, directional measures, negative-data rules, and
later maximum-projection policies are separate source developments. They are
not switches that can be attached to this candidate.

## 3. Why ordinary additive output cannot be relabelled

A positive input slack says that a represented target uses less of an input.
It does not by itself establish that the excessive input suppressed attainable
output. The selected congestion projection and secondary objective are part of
the estimand. When alternative optimal projections yield different input
amounts or diagnoses, accepting the solver's first optimum would turn a
numerical accident into a management conclusion.

For the same reason, the existing additive DEA implementation cannot be reused
by renaming its slacks. Any later implementation must compile the selected
source programme independently, define its projection-identification policy,
and report physical input-level amounts without inventing a universal,
unit-free congestion index.

## 4. Handbook and package disposition

The handbook may explain congestion as a management problem and briefly state
that one established route studies it through non-radial input excess. It must
not create a Cooper (2002) chapter, model-family section, equation tutorial,
or executable case. Later corrections and application variants remain in
technical Documentation or a later specialist treatment.

`analysis.congestion.cooper_deng_huang_li_2002` is an internal audit locator,
not a public preset. It is absent from the executable registry, public imports,
API Documentation, and book examples. The non-executable
`analysis.congestion.cooper_slack` label remains only a literature-organizing
parent and does not imply an implementation promise.

## 5. Gate for a later version

Reopen the candidate only after:

1. the complete authorized 2002 article is page-audited;
2. its programme is translated into an explicit lexicographic solver contract
   rather than an arbitrary finite epsilon;
3. its complete published example is independently reproduced;
4. alternate projections and source-allocation identification are given an
   explicit fail-closed policy;
5. native amounts, status, targets, and non-applicable fields are specified
   without importing later strong/weak or scalar-index semantics; and
6. the resulting idea is integrated into the existing scale/slack discussion,
   not promoted to a paper-named handbook route.

Until then, `deferred_to_next_version` is the release disposition.
