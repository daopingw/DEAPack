# Mainstream DEA handbook scope audit

**Editorial status:** evidence review completed 2 August 2026; English source
edition; no model-family chapter expansion authorized by this document. The
applied community-hospital study added on 3 August combines admitted families
and does not change this scope decision.

This audit asks a narrower question than the software method registry: which
DEA ideas are sufficiently established, transferable, and economically
distinct to belong in a book about the field's key models? A method does not
qualify because it has a familiar acronym, a solvable programme, many
citations, or a chapter in a specialist collection. It must add a production
question, performance criterion, organizational account, temporal mechanism,
valuation institution, comparison institution, or inferential claim that
cannot be taught more clearly inside a retained parent family.

The conclusion is conservative. The 18 model and study-design chapters already contain
the principal efficiency, environmental, productivity, network, dynamic, and
heterogeneity families needed for the first English edition. The review found
important omissions to integrate inside existing chapters and mainstream
subjects to keep evidence-deferred. It did not find a reason to add another
standalone model-family chapter now. A later applied capstone may connect these
families without counting as another model route.

This is also a merge audit, not a literature census. Once a core mechanism is
represented, later papers that alter a direction, orientation, weight,
normalization, reference window, decomposition, variable role, or application
constraint remain instances of that mechanism unless they change the economic
question or maintained production account. They may matter greatly for a
particular empirical study without becoming an additional model in this book.
The package Documentation can preserve their exact reproducibility contracts;
the handbook should not reproduce that technical catalogue.

## Evidence base

The scope was triangulated against sources that organize the field rather than
papers that promote one new formulation:

- Subhash Ray's *Data Envelopment Analysis: Theory and Techniques for Economics
  and Operations Research* organizes the core around radial CRS/VRS models,
  nonradial measures, FDH, slacks and congestion, price-based efficiency, and
  productivity change. Its production-economics framing is especially close to
  this book's intended voice: <https://doi.org/10.1017/CBO9780511606731>.
- Cooper, Seiford, and Tone's comprehensive text covers the basic CCR model,
  alternative measures, returns to scale, multiplier restrictions,
  nondiscretionary and categorical variables, super-efficiency, change over
  time, congestion, undesirable outputs, and several specialized applications:
  <https://link.springer.com/book/10.1007/978-0-387-45283-8>.
- The second *Handbook on Data Envelopment Analysis* gives field-level
  treatments of history and basic models, returns to scale, sensitivity,
  weights, Malmquist productivity, qualitative data, congestion, SBM,
  bootstrap and statistical testing, and internal structures:
  <https://link.springer.com/book/10.1007/978-1-4419-6151-8>.
- Cook and Seiford's thirty-year review groups methodological development around
  efficiency measures, multiplier restrictions, variable status, and data
  variation: <https://doi.org/10.1016/j.ejor.2008.01.032>.
- The network-specific handbook demonstrates that network DEA is a mature
  field-level family, while its many combinations of structures, objectives,
  shared resources, dynamics, and undesirable outputs are variants inside that
  family: <https://link.springer.com/book/10.1007/978-1-4899-8068-7>.
- Wang, Du, and Zhang's article on undesirable-output efficiency and
  productivity was reviewed in full. It joins radial and nonradial
  environmental DDFs to Malmquist--Luenberger and Luenberger change accounts,
  and treats contemporaneous, window, sequential, biennial, and global
  technologies as reference-information choices rather than separate economic
  questions: <https://doi.org/10.1177/1536867X221083886>.

These works do not define a mechanical table of contents. A specialist handbook
may properly devote a chapter to a technique that this reader-oriented book can
teach as one decision inside a broader family.

## Retain the current independent routes

| Independent question | Current treatment | Scope decision |
|---|---|---|
| What attainable resource saving or service expansion is represented under CRS, VRS, or an observed-practice technology? | classical radial DEA, with FDH inside the technology comparison | retain |
| How much of a gap is associated with scale, and how does represented output respond locally to changing operating size? | scale performance and management | retain |
| Which individual resources and outcomes have non-proportional shortfalls? | additive, Russell/RAM, and SBM consolidated in the slack-based chapter | retain |
| Is a declared joint operating programme attainable? | directional distance functions | retain |
| Did the organization minimize cost or maximize revenue or profit at observed prices? | one economic-efficiency chapter covering technical, allocative, cost, revenue, profit, and Nerlovian accounts | retain |
| How should jointly produced undesirable outcomes change the production account and the improvement claim? | environmental DDF, weak/strong disposal, by-production relation, and undesirable-output SBM | retain |
| Why did represented productivity change, and which information set defines best practice? | Malmquist, Luenberger, environmental ML/GML, and Hicks--Moorsteen | retain four distinct change accounts; do not split by reference window or paper-specific decomposition |
| Where inside a connected organization do intermediate products and performance gaps arise? | network DEA and network SBM | retain two family chapters |
| How do current decisions create states, assets, or obligations that constrain later opportunities? | Dynamic SBM as the current executable trajectory account; non-SBM dynamic DEA remains a conceptual boundary | retain one family chapter |
| How does within-group operating performance differ from a gap between represented opportunity sets? | group frontiers and metafrontier | retain one family chapter |

Network--environmental, dynamic--network, metafrontier--SBM, and similar
cross-products do not create new independent routes. They apply an existing
criterion to a production account already taught elsewhere.

## Integrate inside existing chapters

These subjects are mainstream, but their smallest defensible placement is
inside an existing route. Integration still requires source and numerical
evidence proportionate to any equation or package claim.

| Subject | Smallest placement | Reason |
|---|---|---|
| Congestion | scale chapter | It asks whether excess use of an input suppresses attainable output and therefore requires a production/disposability claim beyond ordinary scale efficiency. The book teaches that management distinction without turning the Färe and Cooper estimator lineages into separate models. |
| Weight restrictions and production trade-offs | radial chapter, bridged to economic efficiency | Value judgements can discipline implausible endogenous multipliers. Assurance-region, cone-ratio, and virtual-share recipes are technical implementations of that cross-cutting choice, not separate efficiency families. |
| Nondiscretionary and categorical quantities | study design, with one radial illustration | These determine what management controls and which peers are eligible. They alter the comparison contract rather than create a new performance criterion. |
| Influence, outliers, perturbation, and reference-population sensitivity | study design and every empirical case | Numerical precision is not empirical certainty. Sensitivity reporting is a credibility obligation, while individual algorithms belong in Documentation. |
| Sampling uncertainty, bootstrap logic, and second-stage safeguards | study design at conceptual level | DEA frontiers are sample estimators. Exact optimization does not justify ordinary OLS/Tobit causal stories for fitted scores. Full inferential methods remain deferred until their data-generating assumptions and implementation evidence close. |
| Quasi-fixed inputs and adjustment costs | short contrast in the dynamic chapter | They are a second economic route to intertemporal dependence, but remain part of the same question about how present choices constrain later opportunities. |
| Discrete groups versus continuous operating environments | study design and metafrontier chapter | A metafrontier compares declared group technologies; a conditional frontier asks how opportunities vary with continuous external conditions. The contrast matters even while the latter's complete methods remain deferred. |
| Productivity versus profitability; organization versus industry aggregation | short sections in the productivity part | Quantity improvement need not imply profit improvement, and an average of organization-level indexes is not automatically an industry productivity account. These are interpretation boundaries, not new DEA models. |

## Mainstream but evidence-deferred

These topics are not dismissed as narrow variants. They remain outside the
published route because their defining source, independent oracle, package
contract, or reader treatment is not yet sufficiently closed.

| Topic | Reopening rule | Likely smallest placement |
|---|---|---|
| Ordinary cross-efficiency and mainstream radial super-efficiency | close the defining programmes, infeasibility and alternate-optimum policies, independent numerical evidence, and ranking interpretation | one consolidated appraisal/ranking treatment, not one chapter per variant |
| Most productive scale size, congestion estimators, and short-run physical capacity | close source distinctions and prevent ordinary scale efficiency from being relabelled as any of these concepts | retain conceptual boundaries in the scale chapter; named estimators remain deferred and none is guaranteed a reader-facing placement |
| Statistical inference, partial frontiers, and contextual second stages | freeze a source protocol and sampling target, reproduce an independent numerical oracle, and provide a typed failure-safe result contract | conceptual safeguards in Part I; a later inference chapter only after all three implementation gates close and the pedagogy justifies it |
| Conditional frontier estimation | close the continuous-environment estimand, assumptions, and numerical evidence | study-design/metafrontier integration rather than a named-model catalogue |
| Färe--Primont productivity | complete the primary-source equation audit and independent multilateral oracle | a future productivity-family treatment because it adds transitive multilateral level comparison; no provisional chapter now |

Deferral means that the book states the boundary without presenting a
half-validated recipe. Missing literature or an incomplete numerical account is
a reason to wait for the next version, not to infer a formulation.

For congestion in particular, distinguishable estimator lineages do not imply
separate handbook models. The scale chapter teaches the single management
question and the boundary between ordinary slack and congestion. A future
source-closed estimator may supply one representative calculation only if it
is needed for that lesson. Further named variants remain in Documentation.
The current Färe--Grosskopf--Lovell and Cooper--Deng--Huang--Li audits are both
`deferred_to_next_version`, so the active book contains no named recipe,
equation programme, or executable congestion case.

## Keep in package Documentation or a later specialist volume

The following do not qualify as independent handbook routes merely because
they can be implemented or have appeared under stable names:

- fixed directions, weights, normalizations, target selectors, and individual
  assurance-region recipes;
- window, sequential, biennial, and other reference-sample policies presented
  as separate productivity models;
- named FGNZ and Ray--Desli decompositions, the APZ technology-specific
  environmental sensitivity preset, and other paper-specific allocations or
  technology recipes;
- SBM-Malmquist, quasi-Malmquist, and other non-core productivity-index
  constructions whose economic lesson is already carried by a retained
  parent route or whose defining-source and validation gates remain open;
- multiplicative, generalized, range-directional, BAM, EBM, and specialized
  nonseparable or coefficient-intensive measures when their transferable
  lesson is already carried by a core parent;
- dynamic-network, environmental-network, network-metafrontier, meta-SBM,
  multiperiod aggregation without a state technology, and other combinations
  or technical protocols already separated from the core routes;
- application-specific energy, material-balance, treatment, allocation,
  merger, voting, game, common-weight, or industry-account presets; and
- chance-constrained, fuzzy, interval, Bayesian, and hybrid machine-learning
  formulations presented as if one uncertainty switch covered their different
  assumptions.

The technical registry may preserve these methods for reproducibility. That
does not make them part of the book, its appendices, its cases, or its figures.

## Live-route enforcement check

The complete 18-chapter family route, its applied community-hospital study,
single appendix, executable cases, and referenced figures were re-audited after
the model scope was frozen. No additional model route was admitted, and no
retained chapter failed the field-level gate.

The check did identify presentation details that could make technical leaves
look more important than their economic role:

- the environmental DDF case now calls the family-level common-factor weak-
  disposal interface and declares its input, desirable-output, and bad-output
  directions explicitly; the author-named fixed preset remains in package
  Documentation and the registry;
- the classic SBM case is headed by its reusable orientation question rather
  than the provenance of its five teaching observations;
- the classical radial chapter now labels its public target as the selected
  slack-completed plan rather than silently equating it with the phase-one
  proportional point. Its former abstract O--R--S geometry is replaced by one
  certified original-unit branch account in which $\theta=1$ coexists with a
  remaining service opportunity; the existing scalar frontier figure retains
  its separate technology role, and no model or chapter route is added;
- the directional-distance chapter retains the core distinction between
  directional and strong efficiency, replaces its geometry-first direction
  arrows with a same-operation three-programme management account, and replaces
  its scalar beta ranking with an original-unit operating ledger that separates
  $\beta g$ from slack completion. Exact row-scaled target-selection diagnostics
  remain in package Documentation; and
- the observed-price figure gives cost, revenue, and profit equal visual
  status, while the directional/Nerlovian account appears as a smaller bridge
  for interpreting the profit gap rather than a fourth co-equal objective.
- the opening conceptual route now uses one existing four-plan dataset to keep
  technical efficiency, a deliberately declared equal-count physical-
  productivity level, and observed-price profitability in separate accounts.
  The comparison adds no model family, productivity-change claim, or handbook
  route and does not present DEA multipliers as observed prices.
- the study-design route now holds one hospital operation fixed while two
  pre-declared service-contract populations change the evidence admitted to a
  score-only BCC comparison. The package-driven figure distinguishes the
  candidate roster, eligible population, and active peers, and treats the
  score difference as reference-population sensitivity rather than a new
  estimator, a metafrontier treatment, or a causal contract effect.
- the environmental-productivity chapter now uses adjacent-period
  Malmquist--Luenberger as its sole teaching line. The full-horizon Global
  Malmquist--Luenberger operator remains documented and appears beside the
  Central case only as a two-row reference-information sensitivity check; its
  former standalone derivation, figure, and circularity subsection are not in
  the handbook route.
- the Dynamic-SBM cases use the canonical `DynamicSBM` interface without
  exposing its default source-level score selector, and their reader-facing
  figure footers show the family, orientation, and RTS rather than a registry
  leaf or boundary-policy identifier; and
- the introductory CRS/VRS figure no longer labels an observation as MPSS
  while the named MPSS estimator remains evidence-deferred. The figure keeps
  its intended lesson about convexity and scalable versus locally represented
  opportunity sets without making an unverified scale-target claim.

The productivity chapters passed without a scope correction: Global and GML
remain reference-information policies inside the ordinary and environmental
productivity families, and named decomposition branches remain outside the
reader path. The Luenberger runtime certificate and two-hospital result plot
strengthen the already retained programme-unit change account; they add no
direction preset, decomposition branch, model identity, plot kind, or reader
route. The network chapters retain only the field-level system,
relational, additive, and Network-SBM reporting institutions; accountable-
link specializations and cross-family environmental or dynamic networks stay
in technical Documentation. Park--Park multiperiod aggregation likewise
remains a Documentation-only protocol rather than a dynamic-production route. The
two-period capacity/backlog case is an exact illustration of scored good and bad
carry-overs inside the existing Dynamic-SBM family, not a new model, variant, or
chapter. The Färe--Grosskopf intertemporal and Nemoto--Goto investment families
remain next-version source candidates; neither blocks the current Dynamic-SBM
chapter.

## Editorial consequence

No new model-family chapter is authorized by this audit. The applied capstone
does not alter that conclusion because it teaches a research workflow using
already admitted BCC, SBM, and scale methods. The next manuscript work should
strengthen the smallest existing placements listed above, starting only where
sources and package behavior are ready. The 18-chapter family route changes only if a
future review demonstrates a field-level question that would otherwise be
lost, not because a longer list appears more comprehensive.
