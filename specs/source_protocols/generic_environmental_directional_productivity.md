# Generic environmental directional productivity operators

**Candidate IDs**

- `productivity.environmental_directional.adjacent_geometric`
- `productivity.environmental_directional.global_ratio`

**Current status:** `deferred_to_next_version`

## Why these candidates are deferred

The current codebase contains reusable numerical orchestration for an
adjacent four-distance account and a common-full-sample ratio. The
Chung--Färe--Grosskopf (1997) and Oh (2010) articles define the two
source-qualified public methods that use those engines. They do not, by
themselves, establish every combination of direction, undesirable-output
technology, returns to scale, reference construction, and decomposition that
a fully configurable public operator would permit.

Treating those broad configuration spaces as two published methods would
therefore overstate the literature. Repository identities and synthetic
property tests demonstrate algebraic consistency, but they do not supply the
missing defining source or an independent numerical oracle for the generalized
estimands.

The present release consequently:

- keeps `productivity.malmquist_luenberger.chung_fare_grosskopf_1997` and
  `productivity.global_malmquist_luenberger.oh_2010` public and unchanged;
- retains their common numerical routines only as private implementation
  engines;
- exposes neither generic candidate through the top-level API, discovery
  catalog, machine method registry, book recipe, nor package documentation.

## Reopening gate

A later version may reopen either candidate only after all of the following are
frozen:

1. a primary defining source that supports the complete proposed parameter
   domain, rather than only a named predecessor;
2. source-native equations, direction and disposability semantics, returns to
   scale, reference policy, score convention, and decomposition identity;
3. an economic interpretation that distinguishes a technical environmental
   performance account from complete total factor productivity;
4. explicit feasibility, positivity, panel-comparability, invariance, and
   failure contracts;
5. a published reproduction or independently compiled numerical validation
   path covering the exposed configurations;
6. aligned package tests, benchmark, English book case, and API documentation.

Until that gate closes, a different direction, disposability assumption, or
scale technology must not be reported under the CFG or Oh historical names.
