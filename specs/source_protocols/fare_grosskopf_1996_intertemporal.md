# Färe--Grosskopf (1996) intertemporal production: deferred release protocol

## Readiness record

| Field | State |
|---|---|
| Candidate identifier | `dynamic.intertemporal.fare_grosskopf` |
| Source status | `defining_monograph_identified_complete_dynamic_chapter_not_obtained` |
| Implementation status | `none` |
| Equation-freeze status | `lineage_and_structure_only` |
| Numerical-oracle status | `not_located` |
| Release disposition | `deferred_to_next_version` |
| Public API | none |
| Book placement | conceptual lineage inside the existing dynamic chapter only |
| Last access audit | 2026-08-02 |

This protocol preserves a classic dynamic-production lineage without guessing
one universal Färe--Grosskopf programme. The source family is important, but
the current evidence cannot support an executable estimator, public API, or
source-attributed book equations.

## 1. Defining source and access boundary

Rolf Färe and Shawna Grosskopf (1996), *Intertemporal Production Frontiers:
With Dynamic DEA*. [DOI](https://doi.org/10.1007/978-94-009-1816-0).

The official Springer record identifies separate treatments of static
production structure, distance functions and productivity, intertemporal
budgeting, and dynamic production models. The defining dynamic chapter is
pages 151--188. The audited environment exposes the table of contents and
preview material but classifies the book as subscription content. Google
Books likewise supplies only a limited preview. The equations, propositions,
applications, and numerical results needed for a page-level source freeze
were not obtained.

The available author overview confirms the architecture of the contribution:
static network models are used as building blocks before the book turns to
intertemporal budgeting and dynamic models. That supports the economic
lineage. It does not identify which one of the book's distinct dynamic
technologies, objectives, and efficiency measures should become a package
method.

## 2. Why later accessible applications do not close the gate

An author-hosted Jaenicke application identifies a soil-capital technology as
an instance of the book's basic dynamic technology and displays one
time-linked production set and DEA application. It is useful evidence that a
current state can enter the next period's production account. Its
application-specific non-increasing-returns restrictions, state treatment,
and common path expansion cannot be promoted to defaults for the complete
1996 framework. The reported empirical summaries also do not supply the full
observation-level data needed to reproduce every result.

Other accessible investment applications specialize the lineage to their own
capital transition, public/private allocation, returns-to-scale, and boundary
conditions. They can eventually support separately named technical leaves,
but they cannot reconstruct the defining monograph. Implementing one under
the umbrella family name would collapse distinctions the source itself makes.

## 3. Economic claim that is currently supported

The field-level lesson is that dynamic production evaluates an attainable
path, not a stack of unrelated annual benchmarks. A current operating choice
can create, consume, store, or transform a quantity that constrains later
production. Initial and terminal states therefore form part of the comparison
contract.

This lesson is distinct from window DEA and ordinary Malmquist analysis, which
change the comparison information but need not impose a state transition. It
is also not an alias for Dynamic SBM. A Färe--Grosskopf route first defines a
source-specific intertemporal production set and distance or economic
objective. Dynamic SBM starts from typed carry-over identities and forms a
weighted non-radial slack account. Shared time-expanded matrix infrastructure
does not make their scores, targets, or assumptions equivalent.

The active dynamic chapter may retain this conceptual distinction. It must
not attribute a generic LP, returns-to-scale default, target rule, or public
class to Färe and Grosskopf until the source gate closes.

## 4. Items not yet source-frozen

Implementation remains blocked until the source settles:

1. which single route is being implemented: basic dynamic production, time
   substitution, intertemporal budgeting, storable inputs, or another
   explicitly defined technology;
2. the exact period technologies, temporal-link identities or inequalities,
   stock losses, storage rules, and variable domains;
3. the treatment of initial state, terminal state, terminal value, and the
   information available when the path is chosen;
4. returns to scale, convexity, free or costly disposal, and whether those
   restrictions are period-specific or horizon-wide;
5. the native efficiency or economic objective, including whether one common
   factor or period-specific factors expand outputs, states, or both;
6. period weights, discounting, valuations, and any intertemporal budget
   constraint;
7. feasibility, degeneracy, nonunique path, and incomplete-panel behavior;
   and
8. a complete source dataset and expected results, or an exact synthetic
   oracle independently compiled from page-frozen equations.

The Jaenicke non-increasing-returns application and later constant-returns
investment applications demonstrate why these cannot be inferred as one
universal setting.

## 5. Gate for a later version

Reopen `dynamic.intertemporal.fare_grosskopf` only after:

1. an authorized complete copy of the 1996 dynamic chapter and every earlier
   definition on which the selected route depends is available;
2. one economically coherent leaf is selected and transcribed page by page,
   rather than exposing a switchboard of partially related formulations;
3. its state roles, timing, boundary conditions, technology, objective, score,
   and failure contract are independently reviewed;
4. a production-free analytical compiler or complete published-data
   reproduction certifies the selected leaf;
5. tests cover initial/terminal boundaries, the no-link reduction, unit and
   period-order behavior, and solver failure; and
6. the existing dynamic chapter, technical Documentation, registry, and API
   are updated together without claiming equivalence to Dynamic SBM.

Until then, `deferred_to_next_version` is the release disposition and no
public estimator is authorized.
