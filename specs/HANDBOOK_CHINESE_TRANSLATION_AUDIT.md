# Handbook Chinese Translation Risk Audit

**Status:** 30 reader-source catalogs, one theme-interface catalog, and
53-figure localization complete; PDF rendering and maintainer editorial review
pending

**Normative terminology:** [CHINESE_TRANSLATION_GUIDE.md](CHINESE_TRANSLATION_GUIDE.md)
and [terminology/dea_zh_terms.tsv](terminology/dea_zh_terms.tsv)

## 1. Scope and inventory drift

The requested audit baseline contained exactly 27 live Handbook Markdown
sources: 19 chapter files and 8 front-matter, navigation, appendix, and
bibliography-entry files. `book/README.md`, `book/CONTRIBUTING.md`, figure-source
documentation, build products, and `book/_archive/` were excluded because they
are not reader-facing sources in the admitted Handbook route.

During this audit, `book/project-contributions.md` was added to `book/index.md`
and a corresponding gettext catalog was created. The release-safety pass then
added `book/legal-notices.md`, which renders the consolidated third-party
notices into both Handbook editions and the PDFs. The selected Preview 1
rights policy subsequently added the reader-facing `book/copyright.md` page.
The current route therefore contains 30 live Markdown sources. The table below
covers all 27 files in the requested snapshot and records the three new pages
as concurrent deltas. This makes the audit agree with the current 30
reader-source catalogs without silently changing the historical count. One
additional four-message `sphinx.po` catalog localizes theme controls; it is not
another reader source.

At the 27-file snapshot, the source comprised approximately 68,990
whitespace-delimited tokens over 10,482 lines, including 176 display equations,
52 Python fences, 52 figure directives, 88 citation clusters, and 33 explicit
`{doc}`, `{numref}`, or comparable cross-references. The added contribution
page brings the prose-token estimate to roughly 69,206; the later consolidated
legal-notice route brings the current whitespace-token estimate to roughly
75,679. Neither delta adds a formula, Python block, or figure.

These counts are risk indicators, not editorial progress measures. Markdown,
formulae, and code contribute to the rough token count.

## 2. Risk scale and batches

- **Very high:** mistranslation can change a score convention, technology,
  decomposition, organisational account, or package result meaning.
- **High:** dense dependencies, code/figure identity, or evidential boundaries
  require subject-matter review.
- **Medium:** mostly prose or navigation, but terminology, voice, links, or
  metadata must remain consistent.
- **Low:** minimal visible prose; technical directives still require checking.

The batch labels are dependency order, not a command to translate every file
at once:

- **B0 — contracts:** notation, glossary, and unified method map.
- **B1 — voice and foundations:** front matter, navigation, study design, and
  foundational economics.
- **B2 — classical core:** radial, scale, slack, directional, and price-based
  accounts.
- **B3 — environmental and productivity:** depends on B2 score, direction,
  disposability, and reference-technology language.
- **B4 — structured production:** network, dynamic, and heterogeneous
  technologies.
- **B5 — integration and release:** executable case, citation status, and
  bibliography entry point.

## 3. Source-by-source audit

The compact notation `E/P/F` means display equations / Python fences / figure
directives. Counts are approximate and intended only for prioritisation.

| Batch | Source | Approx. words; E/P/F | Risk | Principal translation risk |
|---|---|---:|---|---|
| B0 | `book/notation.md` | 1,691; 8/0/0 | Very high | Symbols, cross-period indices, score neutral values, and 36 formula lines containing visible English `\text{...}` across the corpus. |
| B0 | `book/glossary.md` | 1,266; 0/0/0 | Very high | Historical aliases, conditional equivalence, and non-equivalence boundaries propagate into every chapter. |
| B0 | `book/appendices/unified-framework.md` | 1,829; 0/0/1 | High | Model-family mergers, managerial-question taxonomy, evidence strength, and causal limits. |
| B1 | `book/index.md` | 252; 0/0/0 | Medium | Nine toctrees, Part titles, visible book title, and anchors; directive bodies are not prose to translate. |
| B1 | `book/preface.md` | 819; 0/0/0 | Medium | Establishes the economics/management voice and separates Handbook teaching from package reference documentation. |
| B1 | `book/reading-guide.md` | 1,529; 0/0/0 | High | Natural beginner-facing reading routes and statements about what evidence cannot support. |
| B1 | `book/chapters/01-foundations/01-efficiency-productivity.md` | 4,075; 11/3/2 | Very high | Efficiency, productivity, profitability, and performance; quantity versus value accounts. |
| B1 | `book/chapters/01-foundations/02-study-design.md` | 5,744; 0/3/3 | High | Organisational boundaries, control, comparability, candidate/eligible comparator/active peer distinctions. |
| B1 | `book/chapters/01-foundations/02-production-frontier.md` | 2,324; 7/0/2 | High | Attainable technology, disposability, convexity, returns to scale, and orientation must be explained economically rather than geometrically. |
| B1 delta | `book/project-contributions.md` | 216; 0/0/0 | Medium | Concurrently added page; contribution credit, authorship, DOI, and translation-review claims must not be strengthened or localized inconsistently. |
| B2 | `book/chapters/02-classical/03-classical-radial.md` | 3,731; 4/3/3 | Very high | Opposite native directions of $\theta$ and $\phi$; Farrell, CCR/BCC, FDH, strong/weak efficiency, and slack completion. |
| B2 | `book/chapters/02-classical/scale-performance-management.md` | 2,365; 5/2/2 | Very high | Scale efficiency, local returns to scale, and scale elasticity answer different questions and do not by themselves prescribe resizing. |
| B2 | `book/chapters/02-classical/04-sbm.md` | 4,184; 14/4/4 | Very high | Additive, RAM, and SBM may report related gaps through different rulers; normalization and target semantics. |
| B2 | `book/chapters/02-classical/05-directional-distance.md` | 4,116; 10/4/3 | Very high | Direction is a unit-bearing management improvement programme, not merely an arrow; signed values across technologies. |
| B2 | `book/chapters/02-classical/economic-efficiency-under-prices.md` | 3,579; 21/1/2 | Very high | Cost/revenue/profit accounts, technical/allocative decompositions, observed prices versus DEA multipliers, and the Nerlovian bridge. |
| B3 | `book/chapters/03-environmental/06-undesirable-outputs-ddf.md` | 3,152; 14/3/4 | Very high | Strong/weak disposability, null jointness, activity-specific disposal, by-production, and pollution-management claims. |
| B3 | `book/chapters/03-environmental/07-undesirable-output-sbm.md` | 2,575; 15/1/2 | Very high | Input excess, desirable-output shortfall, and undesirable-output excess must remain distinct; positive-value normalisation. |
| B3 | `book/chapters/04-productivity/malmquist-productivity-reference-information.md` | 3,812; 8/4/4 | Very high | Four dated appraisals, EC/TC, reference vintage, global/adjacent policy, and infeasible cross-period appraisals. |
| B3 | `book/chapters/04-productivity/12-luenberger.md` | 2,817; 11/1/2 | Very high | Additive indicator units, zero neutral value, and signed cross-period distances; do not relabel it as a multiplicative index. |
| B3 | `book/chapters/04-productivity/environmental-productivity-ml-common-reference.md` | 3,117; 8/5/3 | Very high | Joint production/pollution account, four appraisals, adjacent ML versus GML, and missing results that must not become zero or poor performance. |
| B3 | `book/chapters/04-productivity/17-hicks-moorsteen.md` | 2,444; 4/1/2 | High | Output/input quantity indexes, multiplicative completeness, and chaining; distinct from Malmquist and profitability. |
| B4 | `book/chapters/05-network/network-dea-organizations-links-responsibility.md` | 3,032; 8/3/3 | Very high | Supplying/receiving roles of an internal link, joint system feasibility, open/closed accounts, and non-unique responsibility attribution. |
| B4 | `book/chapters/05-network/20-network-sbm.md` | 2,585; 14/1/2 | Very high | Link governance, process weights, and the non-interchangeability of system performance and process attribution. |
| B4 | `book/chapters/06-dynamic/dynamic-dea-carryovers-trajectories.md` | 3,714; 8/4/3 | Very high | Economic roles of carry-overs, adjacent-period constraints, terminal boundaries, trajectory results, and period diagnoses. |
| B4 | `book/chapters/07-heterogeneity/23-metafrontier.md` | 2,434; 8/1/2 | High | Group versus common frontiers, MTR/TGR, known groups versus clustering, and opportunity gaps versus causal environment effects. |
| B5 | `book/chapters/02-classical/community-hospital-capstone.md` | 2,073; 0/8/4 | High | Densest executable case: data filters, API/result fields, and numbers must stay reproducible; synthetic evidence cannot become a real-health-system claim. |
| B5 | `book/citing.md` | 224; 0/1/0 | High (metadata) | Book and software citations differ; commit/date placeholders must not acquire an invented DOI, ISBN, publisher, or publication year. |
| B5 delta | `book/legal-notices.md` | Includes 6,473-word consolidated notice; 0/0/0 | High (licensing) | Preserve upstream license text, URLs, component/version boundaries, and the statement that the notices do not select a DEAPack project license. |
| B5 | `book/references.md` | 4; 0/0/0 | Low | Preserve the `{bibliography}` directive, BibTeX keys, author names, and original titles. |

## 4. Cross-cutting failure modes

### 4.1 Mathematics

Symbols, index roles, constraints, inequality directions, ratios, and score
neutral values remain unchanged. Across the snapshot, 36 display-math lines
contain visible English in `\text{...}`. These phrases may be translated, but
each change needs token-level comparison and rendered inspection. A Chinese
label that reverses “evaluated period” and “technology period”, for example,
would alter the productivity account even if the algebra remained intact.

### 4.2 Python and package results

Imports, API names, parameters, dataset IDs, result fields, string values, and
expected output remain in English. The 53 Python fences require an identity or
executable check. Literal result fields displayed in prose or tables should
remain in code font rather than receiving a Chinese substitute.

### 4.3 Figures

The 53 referenced SVGs contain at least one `<text>`, `<title>`, or `<desc>`
element. Gettext translates a Markdown caption and `:alt:` value but does not
translate text embedded in an SVG. All 53 now have reviewed language-specific
variants under `book/_static/figures/zh_CN/`. The maintained
`book/figures/zh_CN_labels.json` binds every English source by SHA-256
and classifies every visible node as translated or explicitly preserved; the
deterministic localizer fails closed when a source changes. Figure paths,
directive `:name:` values, and `{numref}` targets remain stable.

### 4.4 Citations and cross-references

The 88 citation clusters retain their BibTeX keys. The 33 explicit
cross-references retain their target docnames/labels while visible link text may
be translated. Chinese headings can change automatic slugs; any heading used by
a stable external or cross-edition link should receive an explicit source label.

### 4.5 Evidential strength

The translation must not turn relative, conditional evidence into a causal
diagnosis. In particular, “technology” usually means a production-opportunity
set rather than machines or engineering knowledge; “benchmark” is a supported
comparison plan rather than a proven transferable practice; “target” is not a
management instruction; process and period decompositions do not uniquely
assign managerial responsibility.

## 5. Terminology gates still requiring chapter-level care

The main requested terminology is frozen in the companion TSV. Three
chapter-local issues still require a defining-source check rather than an
invented Chinese label:

1. **By-production.** Chinese usage is not stable enough in the verified source
   set to freeze a single short label. On first translation retain
   `by-production` in Latin script and explain that production of valued output
   and generation/abatement of pollution are represented as linked processes.
2. **Method-specific MTR/TGR direction.** “共同技术比率”和“技术差距比” are
   frozen names, but the prose must verify each method's numerator, denominator,
   neutral value, and “larger is better” convention before interpreting a
   reported result.
3. **Hicks–Moorsteen account labels.** Retain the proper names and verify the
   exact input/output quantity-index convention; do not infer a Chinese
   decomposition name from Malmquist terminology.

These are local evidence gates, not reasons to delay terminology work in the
foundational chapters.

## 6. Translation and review order used

1. **B0 contract review:** notation, glossary, and unified framework.
2. **B1 voice calibration:** preface, reading guide, foundations, and study
   design.
3. **B2 classical core:** radial, scale, SBM, DDF, price accounts, and the
   hospital integration case.
4. **B3 environmental/productivity:** disposal, environmental accounts, and
   all four productivity routes.
5. **B4 structured production:** network flows, dynamic states, and group
   technologies.
6. **B5 integration:** citation, bibliography, executable case, strict
   catalog preservation, and localized figures.

`book/project-contributions.md` was translated with B1 while preserving its
separate contribution-credit, authorship, and DOI boundaries.

## 7. Release acceptance

A Chinese Handbook release requires more than non-empty PO messages:

- strict Sphinx HTML build and Chinese XeLaTeX/PDF build;
- CJK font, line-break, bookmark, running-head, and metadata inspection;
- terminology lint and mixed-pair detection;
- formula and code identity checks plus runnable-example verification;
- citation and cross-reference integrity checks;
- translated captions/alt text and localized SVG text/title/description;
- subject-matter review for economic meaning, score direction, causal restraint,
  and non-prescriptive targets.

All 2,741 non-header messages (2,737 reader-source messages and four theme
labels) are translated, with zero fuzzy, empty, preservation,
header-placeholder, untranslated-prose, or current-English-source-sync
findings under the automated gate. All 53 live figures pass the source-bound
localization gate.
Those results establish structural completeness, not final editorial approval:
the Chinese HTML has passed strict build, search, and representative visual
inspection, while the PDF still requires rendered inspection. The maintainer
must also approve the prose and component license. Package Documentation
remains English-only for the 2.0 release line.

## 8. Archived translation warning

`book/_archive/zh-source-2026-06-22/` and the reverse-direction archived gettext
material cover only 22 files and predate the present route and writing contract.
They may supply candidate phrases after manual review, but they must not be used
as a one-to-one translation base. Geometry-first headings and explanations in
that archive are specifically non-normative for the new Chinese edition.
