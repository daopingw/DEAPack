# DEAPack method-review programme

These reviews are the evidence layer between the DEA literature and DEAPack's
software, book, and documentation. They are not lists of acronyms and they do
not imply that every reviewed formulation is implemented.

The cross-domain
[`METHOD_COVERAGE_AUDIT.md`](../METHOD_COVERAGE_AUDIT.md) is the maintained
coverage ledger over these streams. It states the canonical grammar,
reader-facing delivery classes, evidence boundary, and the remaining
source-leaf backlog without duplicating the evidence cards below.

## Review streams

| Review | Central question |
|---|---|
| [`STATIC_ECONOMIC.md`](STATIC_ECONOMIC.md) | How should current technical, scale, capacity, cost, revenue, profit, and allocative performance be measured? |
| [`ENVIRONMENTAL.md`](ENVIRONMENTAL.md) | What production account makes an unwanted outcome jointly attainable, reducible, or treatable? |
| [`PRODUCTIVITY.md`](PRODUCTIVITY.md) | What quantity changes over time, relative to which technologies, and under which accounting identity? |
| [`NETWORK_DYNAMIC.md`](NETWORK_DYNAMIC.md) | How do internal processes, intermediate products, shared resources, and intertemporal commitments change attainable performance? |
| [`NETWORK_ADDITIVE.md`](NETWORK_ADDITIVE.md) | How do additive network models attribute measured shortfalls across processes, value intermediate services, and preserve feasible linked targets? |
| [`NETWORK_SBM.md`](NETWORK_SBM.md) | How does the source network SBM attribute divisional performance under fixed or jointly redesigned internal handoffs? |
| [`WEIGHTS_SPECIAL_DATA_HETEROGENEITY.md`](WEIGHTS_SPECIAL_DATA_HETEROGENEITY.md) | How should value judgements, limited managerial control, unusual data roles, and different comparison groups enter the study? |
| [`STATISTICS_UNCERTAINTY.md`](STATISTICS_UNCERTAINTY.md) | Which frontier is estimated, what is random or uncertain, and which population or robustness claim is justified? |
| [`DECISION_SUPPORT.md`](DECISION_SUPPORT.md) | Who may change resources, targets, organizational boundaries, or other units' opportunities, and under which conservation, fairness, or bargaining rule? |

## Current evidence-card inventory

The maintained snapshot below contains 148 evidence cards as of 2026-07-31.
Here, a card means a level-three section containing the common
`economic question` field, which is the same definition used by
`tests/test_literature_reviews.py`.

| Review | Evidence cards |
|---|---:|
| [`STATIC_ECONOMIC.md`](STATIC_ECONOMIC.md) | 29 |
| [`ENVIRONMENTAL.md`](ENVIRONMENTAL.md) | 13 |
| [`PRODUCTIVITY.md`](PRODUCTIVITY.md) | 13 |
| [`NETWORK_DYNAMIC.md`](NETWORK_DYNAMIC.md) | 24 |
| [`NETWORK_ADDITIVE.md`](NETWORK_ADDITIVE.md) | 5 |
| [`NETWORK_SBM.md`](NETWORK_SBM.md) | 10 |
| [`WEIGHTS_SPECIAL_DATA_HETEROGENEITY.md`](WEIGHTS_SPECIAL_DATA_HETEROGENEITY.md) | 25 |
| [`STATISTICS_UNCERTAINTY.md`](STATISTICS_UNCERTAINTY.md) | 21 |
| [`DECISION_SUPPORT.md`](DECISION_SUPPORT.md) | 8 |
| **Total** | **148** |

This is an evidence inventory, not an implementation count. Update the
relevant row and total whenever a card is added, split, merged, or removed;
the literature-review test remains the authoritative structural audit.

## Common evidence record

Each canonical family or important source-qualified variant is audited against
the same record:

```text
economic question
technology and estimator
measure or loss function
returns to scale
data and time structure
native score and improvement direction
exact aliases and their domain
distinct variants that must not be merged
data domain and invariance requirements
failure modes and diagnostic obligations
solver form and optional backend needs
defining source and review source
evidence status
numerical validation oracle and verification status
package recipe or planned canonical ID
reader-facing placement category and exact location
```

An empty field means “not yet established,” not “unrestricted.” Evidence status
distinguishes `primary-checked`, `review-supported`, and
`registry-provisional` claims; it does not certify software. Oracle status is
one of `not located`, `candidate`, `analytically derived`, `reproduced`, or
`cross-implemented`. The last three support independent numerical
verification, but they preserve different evidence claims: an analytically
derived oracle needs an exact, independently compiled certificate and does not
imply that a published dataset or result table has been reproduced.

The **Book location** field is a publication decision, not a future-writing
wish list. It must use exactly one of these three statuses:

- **Active core placement** -- name an exact source path that currently appears
  in [`book/index.md`](../../book/index.md). A source-specific card may point to
  that path only when its reusable family idea is actually taught there.
- **Documentation/source review only** -- retain the formulation, provenance,
  and reproducibility record outside the handbook. Implementation does not
  change this status automatically.
- **Evidence-deferred candidate** -- reserve a potentially field-level family
  whose admission gate is not yet closed. State the missing gate, but do not
  reserve a chapter number or appendix.

[`book/index.md`](../../book/index.md) is the sole authoritative handbook route.
Review ledgers must not invent future chapter numbers, named appendices, or
parallel routes. Handbook appendices pass the same admission gate as chapters;
they are not an overflow destination for specialized methods.

## Merge rule

Historical names share one canonical implementation only when feasible sets,
objectives or exact score transformations, targets, reference membership, and
parameter domains correspond. Shared LP matrices, similar rankings, or a
common directional interpretation are insufficient.

The registry therefore distinguishes:

- aliases and exact score transforms;
- parameter specializations and complete historical presets;
- variants sharing a compiler but changing a measure, technology, graph,
  estimator, reference, valuation, or inferential claim;
- composite analyses that require several fitted tasks.

## Contribution workflow

1. Add or correct the evidence in the relevant review.
2. Reconcile it with an original source and an authoritative review or
   handbook where available.
3. Propose or amend a canonical record in
   [`../METHODS.md`](../METHODS.md).
4. Record compatibility, failure, numerical, and solver consequences.
5. Add a hand-checkable example and a published or independent oracle before
   promoting public implementation.
6. Update the complete package documentation with the code. Update the book
   only if the handbook admission gate is independently passed and the exact
   source path is added to `book/index.md`; otherwise record documentation-only
   or evidence-deferred status here.

This order is deliberate: a class name or solver formulation is never the
first evidence that a model belongs in DEAPack.
