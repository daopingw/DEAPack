# English book architecture

This specification records the publication architecture of the current English
manuscript. [`book/index.md`](../book/index.md) is the authoritative navigation
order. Numeric prefixes in source filenames are stable storage identifiers;
they do not define a second public chapter numbering system.

The book is not the package API manual. It teaches readers how to formulate a
credible efficiency or productivity study, what economic and managerial claim
each principal method family supports, and how computation can test that
claim. Complete signatures, parameter inventories, paper-specific recipes,
exceptions, and compatibility details remain in the separate package
Documentation.

## Editorial contract

The exposition begins with organizations, production commitments, attainable
operating plans, and management questions. Geometry and optimization formalize
those ideas only after their economic meaning is established. A formula is not
introduced merely because it is historically prominent, and a code example is
not allowed to substitute for a production interpretation.

The manuscript follows five rules:

1. Organize methods by the question and maintained production account, not by a
   catalogue of acronyms.
2. Merge exact aliases while keeping economically material differences visible
   inside the relevant family.
3. Use one notation and terminology system across theory, cases, figures, and
   package examples.
4. Treat package output as reproducible evidence, not as a causal explanation or
   an automatic management prescription.
5. Use figures when they make an operating relationship, benchmark assumption,
   responsibility chain, or change account easier to understand.

Chapters need not follow a mechanical template. Their common discipline is
that the reader should be able to identify the decision question, maintained
technology, measure, evidence, interpretation boundary, and reproducible
calculation.

Numerical integrity is a publication condition, not a second narrative running
through every case. The handbook states the substantive condition that makes a
result interpretable: the required production comparisons are available, the
reported operating plan is feasible, the decomposition closes, or an internal
flow continues across the relevant boundary. Field names for solver status,
post-solve certificates, release gates, and rendering policy belong in package
Documentation. A failed or infeasible comparison remains unavailable; it is
never rewritten as zero or silently promoted to a performance conclusion.

### Handbook admission gate

Package coverage and handbook coverage are deliberately different. DEAPack may
implement a narrow, source-exact preset because researchers need to reproduce
it. That fact alone does not earn the preset a place in the book. A topic enters
the reader-facing route only when editorial review can establish all of the
following:

1. **Independent substance.** It changes a production technology, estimand,
   organizational or temporal structure, evaluation institution, valuation
   problem, or inference claim. A new acronym, fixed direction, fixed weight,
   normalization, industry account, or score display is not an independent
   model family when the underlying mechanism is already taught.
2. **Field-level importance.** The method organizes a recognizable body of
   efficiency or productivity research and is treated across authoritative
   monographs, handbooks, reviews, or substantial independent methodological
   work. One paper or one application is insufficient merely because its
   equations are implementable.
3. **Transferability.** The question and interpretation apply beyond one
   industry, dataset, regulatory programme, or bespoke variable assignment.
4. **Pedagogical necessity.** Readers gain a reusable idea that cannot be
   taught more clearly as a case of an existing family.
5. **Evidence readiness.** The defining sources, economic interpretation,
   equations, numerical oracle, implementation behavior, and limitations are
   sufficiently closed to support a reproducible explanation.

A paper-specific preset that changes only directions, weights, or an
application account belongs in package Documentation and the source registry,
not in a chapter, case, figure, or handbook appendix. Appendices are reserved
for advanced but field-level ideas that pass the same substantive gate; they
are not an overflow catalogue. Historical names that share one mechanism are
explained under the canonical family instead of becoming separate topics.

When a proposed addition is borderline, its review must state which new
economic question or maintained mechanism would be lost if it were absorbed by
the parent family. If that question has no clear answer, the proposal remains
outside the manuscript even when the code is public and fully tested.

The unit of inclusion is therefore a **core model family**, not a named paper.
Before any new material is drafted, the editor must try to absorb it into the
nearest retained family. Different author names, acronyms, orientations,
directions, weights, normalizations, reference samples, decompositions, or
application constraints do not defeat that merger by themselves. A separate
reader-facing treatment is justified only when the merger would erase at least
one of these field-level distinctions:

- the economic or managerial question being answered;
- the maintained production account, including a substantively different
  disposability or feasibility claim;
- the organization of production across processes, groups, or time;
- the valuation or comparison institution needed to interpret performance; or
- the estimand and the meaning of the reported result.

Even then, the smallest adequate placement wins. A core family may warrant a
chapter; a canonical alternative needed to understand that family may warrant
a section; a useful empirical adjustment belongs in a case; and a
source-specific implementation belongs only in Documentation. Citation volume
cannot promote a redundant formulation to a higher level. In particular, two
published formulations of the same underlying DEA mechanism are consolidated
under one economic explanation rather than preserved as parallel model entries.

Field recognition is therefore necessary but not sufficient for a separate
route through the book. A well-known adjustment to weights, directions,
reference windows, ranking rules, variable treatment, or one constraint is
taught inside its parent family when readers need it; it does not become a new
chapter merely because the literature gave it a durable name. The handbook is
not intended to enumerate every published DEA modification. Its claim to
comprehensiveness is a coherent account of the principal model families and
the decisions that separate them.

## Publication map

The repository deliberately separates three editorial layers.

| Layer | Purpose | Publication rule |
|---|---|---|
| Published handbook | Teach principal, transferable DEA model families in a reader-oriented sequence | The source appears in `book/index.md`, passes the admission gate, and is included in the strict Sphinx build |
| Family-level consolidation | Reorganize already published material around one economic question without losing a material technology, valuation, organizational, or temporal distinction | Consolidation changes navigation and exposition; it does not create a new model merely to preserve a historical paper name |
| Technical Documentation only | Preserve source-exact formulations, application presets, narrow directions, specialized windows, and reproducibility details | The historical draft is archived outside `book/`; its maintained public treatment belongs in `docs/` and the source registry |
| Evidence-deferred family | Reserve a mainstream topic whose defining source, equations, oracle, or interpretation is not yet closed | No provisional chapter or public recipe is published; the source protocol records what evidence would reopen the gate |

The publication boundary also applies to supporting assets. The handbook
bibliography lists only works cited by the admitted route, and the Sphinx site
copies only figures referenced by that route. A technical source may remain in
the repository for documentation or editorial provenance without its chapter,
figure, or bibliography entry appearing in the published handbook.

The live `book/chapters/` tree contains the 18 admitted model and study-design
sources plus `community-hospital-capstone.md`, an applied study that combines
existing BCC, SBM, and scale tools. The capstone adds a complete empirical
workflow, not another model family. Historical drafts are retained under
`specs/archive/book-drafts/`, preserving their former `chapters/` or
`appendices/` relative path. The archive is not a Sphinx source tree and does
not define a parallel reading route.

The first conservative scope pass places the following retained source drafts
in the documentation-only archive. The files are not deleted, but they are not
published as book chapters:

| Excluded source draft | Parent family or technical role |
|---|---|
| `specs/archive/book-drafts/documentation-only/chapters/02-classical/04-multiplicative-efficiency.md` | specialized multiplicative technology |
| `specs/archive/book-drafts/documentation-only/chapters/02-classical/05-range-directional-signed-data.md` | signed-data directional preset |
| `specs/archive/book-drafts/documentation-only/chapters/02-classical/05-generalized-distance.md` | specialized generalized-distance path |
| `specs/archive/book-drafts/documentation-only/chapters/03-environmental/09-by-production-fgl.md` | efficiency account under by-production |
| `specs/archive/book-drafts/documentation-only/chapters/04-productivity/14-biennial-malmquist.md` | source-specific two-period reference window |
| `specs/archive/book-drafts/documentation-only/chapters/05-network/21-sequential-network.md` | sequential network evaluation protocol |
| `specs/archive/book-drafts/documentation-only/chapters/05-network/22-environmental-network.md` | specialized environmental-network composition |
| `specs/archive/book-drafts/documentation-only/chapters/06-dynamic/20-multiperiod-aggregation.md` | source-specific multiperiod rating protocol |
| `specs/archive/book-drafts/documentation-only/chapters/03-environmental/10-material-balance.md` | material-coefficient and conservation specialization |
| `specs/archive/book-drafts/documentation-only/chapters/06-dynamic/22-dynamic-network-sbm.md` | intersection of the network and dynamic families |

The ordinary cross-efficiency draft,
`specs/archive/book-drafts/evidence-deferred/chapters/02-classical/09-peer-appraisal.md`,
belongs to the evidence-deferred layer instead. Cross-efficiency is a
mainstream family, but the current audit has not closed its defining-source and
independent numerical-oracle gates. It therefore remains outside the live book
without being misclassified as a narrow technical preset. Super-efficiency is
handled the same way: the source-qualified Super-SBM implementation cannot
stand in for the mainstream Andersen--Petersen family while that defining-source
gate remains open, so
`specs/archive/book-drafts/evidence-deferred/chapters/02-classical/10-super-efficiency.md`
is also withheld.

Family consolidation also leaves fourteen superseded source files outside the
build. Their core content has moved rather than been reclassified as
documentation-only:

| Superseded source files | Published family chapter |
|---|---|
| `superseded/chapters/02-classical/06-cost-and-allocative-efficiency.md`, `superseded/chapters/02-classical/07-revenue-and-output-allocative-efficiency.md`, `superseded/chapters/02-classical/08-profit-and-nerlovian-efficiency.md` | `economic-efficiency-under-prices.md` |
| `superseded/chapters/05-network/17-two-stage-relational.md`, `superseded/chapters/05-network/18-two-stage-additive.md`, `superseded/chapters/05-network/19-general-additive-network.md` | `network-dea-organizations-links-responsibility.md` |
| `superseded/chapters/06-dynamic/21-dynamic-sbm.md` | `dynamic-dea-carryovers-trajectories.md` |
| `superseded/chapters/04-productivity/11-malmquist.md`, `superseded/chapters/04-productivity/13-global-malmquist.md` | `malmquist-productivity-reference-information.md` |
| `superseded/chapters/04-productivity/15-malmquist-luenberger.md`, `superseded/chapters/04-productivity/16-global-malmquist-luenberger.md` | `environmental-productivity-ml-common-reference.md` |
| `superseded/chapters/02-classical/alternative-benchmark-technologies.md` | FDH section in `03-classical-radial.md` |
| `superseded/chapters/02-classical/03-slacks-additive.md` | additive/RAM sections in `04-sbm.md` |
| `superseded/chapters/03-environmental/08-by-production.md` | by-production section in `06-undesirable-outputs-ddf.md` |

The superseded paths in this table are relative to
`specs/archive/book-drafts/`. The canonical replacements use one case and one
economic vocabulary across each family. The superseded drafts remain only as
editorial provenance and do not define parallel reader routes or registry
placements.

## Current seven-part published route

The current route contains 18 model and study-design chapter sources and one
applied-study chapter. The first number defines the family-level boundary; the
capstone demonstrates how those choices work together and is not another
implemented method or historical name.

### Part I — Designing a Credible Performance Study

Part I begins with the performance question rather than a model acronym. It
distinguishes benchmark-conditioned technical efficiency, explicitly
aggregated productivity levels, productivity change through time,
observed-price profitability and relative-price recovery, and environmental
performance under joint production. It then establishes the organization and
decision horizon, the economic roles of recorded quantities, the eligible
comparison population, and the limits of the eventual claim. Only after those
choices are visible does it show how observed organizations become an
empirical production technology:

- `01-efficiency-productivity.md`;
- `02-study-design.md`; and
- `02-production-frontier.md`.

The three chapters therefore follow one reader-facing sequence: define the
performance account; decide who is responsible for what and who may credibly
teach whom; then decide which unobserved operating plans the evidence should
make attainable. Readers encounter variable roles, control, units, reference
populations, observed feasibility, convexity, disposability, FDH, returns to
scale, and orientation before selecting a score.

### Part II — Classical DEA Models

The published route proceeds through:

1. classical input- and output-oriented radial DEA, including FDH as the
   principal observed-practice alternative to convex averaging;
2. scale efficiency, local returns, and scale response;
3. one slack-based family chapter joining classic additive DEA, RAM, and SBM;
4. a community-hospital applied study joining design, BCC, SBM, peer, target,
   scale, and sensitivity evidence without introducing a new model;
5. directional distance functions; and
6. economic efficiency under observed prices, unifying cost, revenue, profit,
   allocative, and Nerlovian accounts.

The order is conceptual rather than chronological. Readers first understand a
proportional management question and the benchmark technology supporting it,
then diagnose variable-level gaps and declared joint improvement programmes.
Observed prices or a changed appraisal institution enter only after the
technical comparison contract is visible.

The second-round editorial closure still treats the five model treatments as
transferable mother families rather than a procession of historical labels.
The capstone is an application of those treatments, not a sixth family. Each chapter begins
with an organizational decision, preserves one project-wide notation system,
and distinguishes the reported score, the operating plan it supports, and the
claim that management may make from it. Detailed constructor, field,
certificate, and compatibility contracts remain in package Documentation, so
the handbook can explain economic meaning without becoming an API manual.
The rendered HTML, site header, tables, and dense result accounts have been
checked at ordinary reading width. Part II is therefore editorially closed for
the current English route; later paper-specific directions, weights,
normalizations, and score displays cannot reopen it unless they pass the
field-level handbook admission gate.

The observed-price chapter now holds one technology and dataset fixed while
the management commitment changes. Source-specific return-to-expenditure and
profitability decompositions remain in package Documentation. BAM likewise
remains a documented additive-family specialization rather than a handbook
topic; classic additive DEA and RAM carry the transferable lesson. Ordinary
cross-efficiency is a mainstream family, but its published chapter is deferred
until the defining sources and independent numerical evidence close.
Super-efficiency is also deferred: a verified Super-SBM branch does not replace
the still-unclosed mainstream radial family.

### Part III — Environmental Efficiency and Undesirable Outputs

Part III rebuilds the production account when valued output is jointly
produced with residuals or other unwanted outcomes. The environmental-DDF
chapter covers joint production, disposal assumptions, and the reusable
by-production insight that intended output and residual generation may need
separate relations. The second chapter develops the standard separable
undesirable-output SBM. Tone's non-separable hybrid and coefficient-intensive
materials-balance formulations remain in package Documentation rather than
becoming parallel core routes.

### Part IV — Productivity Change and the Evolution of Best Practice

Part IV contains four family-level chapters. Conventional Malmquist and
environmental Malmquist--Luenberger each teach adjacent-period and global
reference policies inside one chapter, because changing the information
window does not by itself create another production-account family. Ordinary
Luenberger remains distinct as an additive, programme-denominated change
measure, while Hicks--Moorsteen remains distinct as a complete quantity-index
account of total output growth relative to total input growth.

The reference-policy comparisons retain feasibility, circularity, and
historical-revision consequences without turning every admissible reference
window into a separate route through the book.

### Part V — Performance Inside Multi-Process Organizations

Part V opens the organizational black box in two chapters. The first treats
intermediate products, process-specific peers, system-only radial performance,
relational products, additive process attribution, and open graph structure as
reporting institutions over one connected organization. The second retains
network SBM as a distinct non-radial account of variable-specific resource
excesses and service shortfalls under explicit link-continuity and handoff-
governance constraints.

System, process, and link quantities keep their organizational roles, and a
shared intermediate account does not imply common peers or causal stage
effects.

### Part VI — Managing Performance Across Time

Part VI distinguishes repeated annual comparisons from a dynamic technology
in which current decisions affect later opportunities. One family chapter
uses Dynamic SBM for the carry-over and trajectory account. Dynamic network
SBM remains in package Documentation as an intersection of process and
temporal coordination rather than another core route created by combining two
model axes.

### Part VII — Comparing Organizations Across Different Operating Environments

Part VII contains one current-edition route: the radial metafrontier question
of whether declared groups face different represented production opportunities
and how an opportunity gap differs from within-group operating performance.
The groups are known before estimation; this route is neither clustering nor a
conditional-frontier estimator. The decomposition remains descriptive and
does not assign causes to managers or institutions. No statistical-inference
chapter is authorized in the current edition.

## Source-gated placement queue

Several field-level subjects may eventually be necessary for a mature
handbook. They are an editorial and evidence queue, not provisional chapters
or a promise that each subject will receive an independent model treatment:

- weight restrictions and the disciplined use of value judgements;
- ordinary cross-efficiency and the evaluator's peer-appraisal institution;
- the mainstream radial super-efficiency family;
- nondiscretionary and categorical variables;
- congestion and the production assumptions needed to identify it;
- sensitivity analysis, sampling variation, and statistical inference; and
- operating environments, conditional frontiers, and related comparison
  designs.

Each subject must pass the same admission gate, close its sources and numerical
evidence, and find the smallest reader-oriented placement. In many cases that
placement will be a section, interpretation box, or applied-study safeguard
inside an existing family chapter. Listing a subject here does not authorize
an implementation claim, a chapter number, or a placeholder in the published
navigation. In particular, an inferential procedure remains next-version until
its source protocol, independent numerical oracle, and typed result/failure
contract all close.

The evidence and placement decisions behind this queue are recorded in
[`MAINSTREAM_BOOK_SCOPE_AUDIT.md`](MAINSTREAM_BOOK_SCOPE_AUDIT.md). That audit
currently authorizes no additional chapter.

## Appendices and method coverage

The single published appendix holds one unified reader-facing map from a
study's production story and management question to the principal model
families. It explains relationships among those families; it does not mirror
the complete technical registry. The former stand-alone method-map draft is
retained at
`specs/archive/book-drafts/superseded/appendices/method-map.md` because its
useful model-selection role has been consolidated into that appendix. It is not
part of the live appendix tree. Specialized presets remain in package
Documentation, and deferred methods remain outside the book until both their
field-level importance and evidence boundary are established.

## Cases and visual language

Small deterministic theory cases support hand calculation, equivalence checks,
invariance tests, and failure demonstrations. Larger cases add institutional
roles and empirical context only when those details help answer the chapter's
question. Figures use resources, services, operating plans, benchmark
opportunities, organizational processes, and period information sets as their
primary language.

Technical historical terms such as *projection*, *catch-up*, *frontier shift*,
or *arrow* may appear after their economic meaning has been stated. They should
not become the organizing explanation for a reader who needs to understand
what an organization can change, what it must deliver, and what the evidence
can support.

Tables and figures follow the same rule. Their reproducible generators must
verify every quantity they display, but the chapter explains the economic
condition rather than narrating the software's certificate pipeline. Readers
who need field-level statuses, tolerances, or failure schemas are directed to
package Documentation.

## Maintenance rule

When the publication order changes, update `book/index.md`, this specification,
`book/README.md`, and the exact Sphinx exclusion list in the same change. Do not
reintroduce a parallel numbered future table of contents. English remains the
working source edition until the substantive and editorial structure is stable
enough for localization.
