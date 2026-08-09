# Citing DEAPack and the Companion Book

DEAPack software and the companion book are related but distinct scholarly
works. Cite the object that supports the claim you are making:

- cite **DEAPack software** when reporting a computation, implementation,
  numerical workflow, or exact software version;
- cite the **companion book** when relying on its exposition, taxonomy,
  interpretation, or worked case;
- cite both when a study materially uses both.

## Software release

The machine-readable software metadata are in
[`CITATION.cff`](CITATION.cff). GitHub can render those metadata as BibTeX and
APA text through its **Cite this repository** control.

Version `2.0.0` is the first stable 2.x software release. It does not yet have
a DOI, so identify the exact version and commit used and include the repository
URL. Do not cite a future placeholder DOI.

For archival publication, the project will:

1. archive the tagged software release as a Zenodo **Software** record; and
2. add the assigned persistent DOI to the maintained citation guidance.

A version-specific DOI should be preferred when exact computational
reproducibility matters. A concept DOI may later identify the evolving
software family.

## Companion book

*Data Envelopment Analysis: Efficiency, Productivity, and Environmental
Performance with Python* is a bilingual English--Chinese development
manuscript whose English text is the canonical editorial source. Its cover
strapline is *A Unified Handbook of Theory, Methods, and Practice*. Preview 1
is Copyright © 2026 Daoping Wang, All Rights Reserved. It has no assigned DOI,
ISBN, publisher, formal publication date, or final edition. The two language
renderings are one scholarly work, not two objects with invented identifiers.
None of those fields should be inferred from the software metadata.

After editorial freeze, the book will be deposited separately as a Zenodo
**Publication — Book** record with its own DOI and citation page. The
archival files should include a searchable-text PDF and the corresponding
source snapshot. If a publisher later issues a formal edition, that edition's
publisher-supplied DOI and ISBN will replace—not duplicate—the citation for
the same published object.

See the manuscript's [citation page](book/citing.md) for the book-specific
publication checklist.

## Identifiers that remain intentionally unset

The repository does not invent author ORCIDs or affiliations, software or
book DOIs, an ISBN, a publisher, or a final author/editor order. These fields
will be added only after the responsible people or issuing service confirm
them.
