# Data Envelopment Analysis

*Efficiency, Productivity, and Environmental Performance with Python*

**A Unified Handbook of Theory, Methods, and Practice**

This directory contains the English source manuscript for the theory-and-
practice Handbook that accompanies DEAPack. The book is organized for readers of production
economics, management, public policy, and empirical efficiency analysis. It is
not a long-form copy of the package API documentation.

[`index.md`](index.md) is the authoritative reading and navigation order. The
live source tree contains the 18 admitted model and study-design chapters, one
applied community-hospital study, and the single unified-framework appendix.
The applied study joins existing BCC, SBM, and scale tools; it does not enlarge
the handbook's model-family scope. Numeric prefixes in chapter filenames are stable
source identifiers and should not be interpreted as a second chapter numbering
system. The editorial principles and current part-level map are recorded in
[`specs/BOOK_ARCHITECTURE.md`](../specs/BOOK_ARCHITECTURE.md). Its handbook
admission gate keeps paper-specific directions, weights, normalizations, and
industry presets in package Documentation unless they add a transferable,
field-level mechanism that the existing model families do not teach.

## Current reading route

The published route is intentionally family-level. It currently has seven
parts:

1. designing a credible performance study;
2. classical DEA models;
3. environmental efficiency and undesirable outputs;
4. productivity change and the evolution of best practice;
5. performance inside multi-process organizations;
6. managing performance across time; and
7. comparing organizations across different operating environments.

Each chapter begins from an economic or managerial question. Mathematics then
defines the maintained technology and measure, and package examples make the
result reproducible. Complete parameters, return fields, exceptions, and
version-specific API behavior belong in the separate `docs/` site.

Earlier source-qualified technical treatments are retained locally outside
the live book tree under the private editorial archive
`specs/archive/book-drafts/`. That archive is deliberately excluded from the
public GitHub source boundary and is not a public link target. It separates
documentation-only, evidence-deferred, and superseded drafts; it is editorial
provenance, not a second reading route or a Sphinx input. Maintained executable
details remain available through package Documentation. A method does not
enter the book merely because it has code, tests, or a reproducible paper
example.

## Editorial consolidation checkpoint

The current publication boundary is a conservative family-level route, not a
catalogue of implemented methods. Cost, revenue, profit, allocative, and
Nerlovian analysis now form one treatment of economic efficiency under observed
prices. Relational, additive, and open-network models are introduced through
the common organizational questions they answer. Dynamic network material now
remains in package Documentation instead of becoming a separate route merely
because it combines two model axes.

Adjacent-period and global reference policies now sit inside the same
conventional or environmental productivity family chapters. Ordinary
Luenberger and Hicks--Moorsteen retain separate chapters because they change
the underlying change account, not merely its benchmark window. Ordinary
cross-efficiency and the radial super-efficiency family remain outside the
published route until their defining-source and numerical-oracle gates close;
a verified Super-SBM branch is not used as a substitute for the latter. FDH is
taught within the radial chapter, additive DEA and RAM within the slack-based
chapter, and by-production within the environmental-technology chapter.
Materials-balance, non-separable undesirable-output SBM, BAM, and other
source-exact specializations remain available in package Documentation without
being promoted into the handbook.

Field recognition alone does not create another chapter. A familiar change to
weights, directions, reference windows, ranking rules, variable treatment, or
one constraint is absorbed into the smallest relevant core-family discussion
when it is pedagogically necessary. The book aims to cover the main line of
DEA reasoning, not to inventory every named modification in the literature.

## Building and checking both editions

From the repository root, a strict local build can be run with:

```bash
.venv/bin/sphinx-build -E -a -W --keep-going -b html book /tmp/deapack-book
.venv/bin/python scripts/check_handbook_translations.py --require-complete
.venv/bin/python book/figures/localize_handbook_figures_zh.py --check
make -C book html-zh SPHINXBUILD=../.venv/bin/sphinx-build PYTHON=../.venv/bin/python
```

Reproducible figure generators live in `book/figures/`; generated SVG assets
live in `book/_static/figures/`. `make -C book html` regenerates the complete
theory and package-result figure set before the strict Sphinx build, matching
the GitHub Actions route. English remains the canonical source edition. The
Chinese edition is maintained in `book/locale/zh_CN/` through Sphinx gettext
catalogs and is reviewed against the shared terminology guide; it is not a
separate manuscript whose equations, code, or results may drift.

Text embedded in an SVG is not processed by gettext. Reviewed Chinese labels
therefore live in `book/figures/zh_CN_labels.json`; the deterministic
localizer writes language-specific variants under
`book/_static/figures/zh_CN/`. Every source SVG is bound by SHA-256, every
visible text node must be translated or explicitly preserved, and a changed
English figure fails closed until its Chinese labels are reviewed again.
