# Shared specifications

Files in this directory are normative for DEAPack 2.x package code and package
Documentation. They record the mathematical, numerical, and evidence
contracts behind the public implementation.

- [`CONVENTIONS.md`](CONVENTIONS.md): notation, signs, score direction, and
  names used in public results.
- [`METHOD_UNIVERSE.md`](METHOD_UNIVERSE.md): source-backed review of the DEA
  method universe, inclusions, exclusions, and substantive boundaries.
- [`METHOD_COVERAGE_AUDIT.md`](METHOD_COVERAGE_AUDIT.md): cross-domain
  coverage ledger, canonical study grammar, delivery/evidence separation, and
  the dependency-aware gap roadmap.
- [`LITERATURE_BASELINE.md`](LITERATURE_BASELINE.md): defining sources,
  thematic review programme, and editorial evidence requirements.
- [`reviews/`](reviews/): nine maintainable, field-level literature reviews
  using one evidence schema and mapping methods to canonical recipes, tests,
  and technical Documentation.
- [`LEGACY_AUDIT.md`](LEGACY_AUDIT.md): migration map for the historical
  DEAPack and ProdPack ideas, data, and behaviors.
- [`UNIFIED_FRAMEWORK.md`](UNIFIED_FRAMEWORK.md): the compositional model
  grammar and pairwise equivalence policy.
- [`METHODS.md`](METHODS.md): canonical IDs, relationships, priority,
  implementation status, and evidence snapshot.
- [`registry/`](registry/): the versioned, machine-readable shadow ontology
  for eleven-axis method records and typed A--D relationships. During its
  staged migration, `METHODS.md` remains the human source of truth and
  automated two-way parity checks require one machine record for every public
  `method_id` and reject records that overstate public implementation.
- [`COMPATIBILITY_MATRIX.md`](COMPATIBILITY_MATRIX.md): fail-closed
  data-domain, invariance, target, technology, operator, and inference
  compatibility.
- [`ECONOMIC_MODEL_DESIGN.md`](ECONOMIC_MODEL_DESIGN.md): price-data, optimization,
  result, decomposition, API, and validation contracts for economic DEA.
- [`PATH_MODEL_DESIGN.md`](PATH_MODEL_DESIGN.md): canonical and numerical
  boundaries for hyperbolic, generalized-path, Chavas--Cox, and
  multiplicative DEA.
- [`ARCHITECTURE.md`](ARCHITECTURE.md): software layers, solver policy, result
  contract, compatibility, and package layout.
- [`PERFORMANCE.md`](PERFORMANCE.md): large-sample design and benchmark gates.

Changes to a normative convention require all of the following in the same
pull request:

1. an explanation of the theoretical reason;
2. package tests for the changed behavior;
3. corresponding package Documentation updates;
4. a migration note if public output or API semantics change.
