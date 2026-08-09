# How to Use This Book

Writing down a DEA programme is not especially difficult. The harder task is deciding
what its result means for an organization. If a hospital is called inefficient, is the
claim that it could use fewer beds while meeting the same commitments, treat more
patients with its current resources, alter its service mix, or learn from a different
group of hospitals? Those are different claims, even if their optimization programs
share much of the same machinery. The notation becomes useful only after the
performance question is clear.

## Your First Journey through the Book

If efficiency analysis is new to you, begin with Part I and let the hospital
example do most of the work. The opening chapter separates three questions that
are often blurred together: how an organization performs against a benchmark,
how much physical output it produces from its resources, and whether it earns a
surplus at observed prices. The study-design chapter then asks what belongs
inside the hospital, which services must be protected, and which hospitals
offer credible evidence. The production-frontier chapter shows how those
choices become a set of attainable operating plans.

Small examples are used deliberately. They let you see resource commitments,
service capacity, comparator organizations, and scale before a large dataset
obscures the argument. Whenever an equation appears, translate it into three
questions: What must the organization preserve? What is it being asked to
change? Whose experience supplies the benchmark? If you can answer those in
ordinary language, the notation is already doing useful work.

For a first pass, continue to classical radial DEA and then the slack-based chapter.
Radial DEA introduces proportional resource saving and service expansion. The
slack-based chapter shows what changes when individual resources and services need
not move together. Next, use the community-hospital study to see how the research
question, comparison group, primary result, peers, improvement quantities, and
sensitivity checks fit together. Directional distance is most helpful after those
ideas are familiar, because it lets management define a coordinated programme of
several changes. The intervening scale chapter
is valuable but optional on this first pass: read its opening distinction between
operating and scale-related shortfalls, then return later for local returns to scale
and scale elasticity. The observed-price chapter is the next stop when cost,
revenue, or profit is the substantive objective.

This gives a deliberately short first-pass route:

1. Part I through the construction of the production frontier;
2. classical radial DEA;
3. Additive, RAM, and SBM measures;
4. the community-hospital efficiency study;
5. directional distance; and
6. whichever applied part matches the production problem.

On this route, concentrate on the organizational question, the neutral value of
the measure, and the interpretation of the target. Bootstrap inference,
second-stage contextual analysis, detailed dual arguments, and specialized
reference policies belong to a researcher's second pass rather than being
prerequisites for understanding CCR and BCC.

After Part II, follow the problem you actually care about. Read Part III when
production creates pollution or another undesirable consequence; Part IV when
performance must be compared over time; Parts V and VI when departments or
periods are joined by internal flows; and Part VII when organizations operate
under meaningfully different opportunities. You do not need network or dynamic
DEA in order to understand a conventional hospital, plant, or bank comparison.

## Where a Second Reading Pays Off

Some sections are written for readers who need to design research, defend an
empirical specification, or extend a model. They belong in the book, but they
need not interrupt a first encounter with DEA.

| Chapter or topic | Read first for | Return later for |
|---|---|---|
| Scale performance | the difference between operating shortfall and scale-related shortfall | local returns to scale, scale elasticity, and the conditions behind congestion diagnostics |
| Study design | organizational boundaries, variable roles, and eligible comparators | sampling inference, contextual second-stage designs, and robustness protocols |
| Community-hospital study | how design choices become a complete management analysis | peer-population, SBM, and scale-assumption sensitivity |
| Economic efficiency | why cost, revenue, and profit protect different commitments | allocative decompositions, price heterogeneity, and the directional profit bridge |
| Malmquist productivity | the four dated appraisals and the operating-performance/opportunity-change decomposition | cross-period feasibility, global benchmark vintages, and long-run chaining |
| Environmental productivity | the joint useful-output/pollution programme and its two change components | signed cross-technology distances and infeasible environmental comparisons |
| Network DEA | why departments must share one feasible organizational plan | relational and additive process accounts, internal-link valuation, and non-unique process attributions |
| Dynamic DEA | why today's carry-over restricts tomorrow's possibilities | carry-over governance, period weights, and the distinction between a trajectory result and its period-level diagnoses |

The same principle applies within the mathematics. The statement of a model
and the meaning of its result belong on the first pass. Proof-oriented detail,
duality, and sensitivity to maintained assumptions reward a slower return once
the economic question is settled.

## If You Are Conducting an Empirical Study

Readers who already have data and a research question need not proceed linearly. Use
the study-design chapter to audit the unit boundary, decision horizon,
managerial control, measurement definitions, and peer-eligibility rule.
Identifying inputs, desirable outputs, and undesirable outputs is necessary
but not sufficient: a contextual condition is not automatically a resource,
an internal handoff is not automatically a final output, and a quantity fixed
over one planning horizon may be adjustable over another. Then go to the
relevant model chapter.

After running the code, do not keep only one efficiency column. Comparator
organizations, benchmark operating plans, resource excesses, output
shortfalls, and returns to scale often explain the result better than
rankings do.

Most model chapters use small datasets as magnifying glasses for observing model
behavior. Before substituting your own data, reproduce the book's result with its
theory dataset; that simple step catches many errors involving column roles,
orientation, and score direction. The community-hospital chapter then brings the
main design and reporting choices together in one larger synthetic study. It is a
workflow template, not evidence about a real health system. A publishable application
must use defensible source data, document provenance and units, screen its comparison
population, pre-specify sensitivity analyses, and report the limitations of its final
conclusions.

## If You Compare or Develop Methods

If you want to compare methods or develop a new model, keep {doc}`notation` and
the model map in the appendix close at hand. Start by separating the management
question, the operating system, the organizations and periods supplying
evidence, and the improvement or economic objective. Technology assumptions
and equations then make those choices precise. Historically different names
are combined when they lead to the same attainable plans and performance
criterion; genuine differences in production structure, disposability, scale,
benchmark policy, valuation, or statistical claim remain visible.

## Moving from a management problem to usable evidence

Each form of evidence in the book answers a different practical question. The
economic discussion identifies the responsibility being assessed: saving resources,
protecting services, improving environmental outcomes, or raising productivity.
Figures show whose experience supplies a credible comparison and what operating
change that comparison makes possible. Equations state the assumptions precisely,
while code tests whether the same reasoning survives realistic combinations of
resources, services, organizations, and periods. When reading a diagram, ask first
what management can alter, what it must preserve, and whether the proposed benchmark
could be implemented within the stated horizon. Coordinates and arrows are useful
only insofar as they make those organizational choices easier to see.

Code blocks contain what is needed to understand and reproduce the analysis.
Complete parameters, return fields, exceptions, and version-compatibility
details live in the separate DEAPack Documentation. The text asks why a model
is appropriate and what its result can support. Readers can consult the API
pages alongside an example when implementation detail is needed, while the
main argument remains readable without them.

The handbook concentrates on mature model families that organize the field. A
paper-specific variant enters the main route only when it has become a
principal family and changes the production setting, performance criterion, or
interpretation in a way the existing family cannot express. Specialized
variants and computational options remain in the DEAPack Documentation.

## Numerical integrity without software plumbing

A performance number is informative only when the comparison it summarizes actually
exists. If another period's technology cannot support the required appraisal, or a
decomposition is undefined, it remains missing; it is never
replaced by zero or described as poor performance. The missing result marks a limit of
the evidence. Each model chapter therefore identifies the feasibility and accounting
conditions that must hold before the result can inform a management or policy
discussion.

DEAPack also retains field-level numerical diagnostics for readers who need to
audit a computation. Those diagnostic names, tolerances, and failure statuses
are described in the package Documentation. The handbook keeps the substantive
question in view: what has been established about the organization's production
possibilities, and what remains unsupported?

One final habit is especially useful. Whenever a unit has an efficiency score of one, ask: Efficient under which technology, orientation, period, and peer group? That question runs through almost the entire book.
