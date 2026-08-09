# Release Notes — DEAPack 2.0.0rc1

> **Historical pre-release:** `2.0.0rc1` was tagged and published on
> 2026-08-10 and was subsequently superseded by stable `2.0.0`. This file
> preserves the candidate scope and release plan as historical evidence.

DEAPack 2.0 is a greenfield redesign of the historical DEAPack 0.1.x and
ProdPack prototypes. It provides a source-audited, composable Python toolkit
for DEA-based efficiency, productivity, environmental performance, internal
production, and intertemporal analysis. The release candidate emphasizes
explicit economic assumptions, independently checked numerical claims, and
results that fail closed when a score, target, peer, dual, or decomposition
cannot be certified.

The detailed candidate boundary is frozen in the
[2.0 rc1 release-scope record](specs/RELEASE_SCOPE_2_0_RC1.md). The
[installed method catalog](docs/user-guide/method-catalog.md) remains the
authority for callable identities.

## Highlights

- **Broad, organized DEA coverage.** The proposed release exposes 75 public
  discovery identities: 62 fitted `method_id` entries, five constructor or
  reporting specializations, and eight complete presets. These identities
  share compilers where their mathematical programmes coincide; they do not
  claim 75 independent mother models.
- **Auditable results.** Named result tables retain the fitted method,
  specification, solver evidence, validity state, targets, peers, components,
  and diagnostics instead of reducing an analysis to one unqualified score.
- **Independent numerical claims.** All 63 implemented/public machine records
  have at least one claim-scoped independent evidence path: 30 are
  `analytically_derived`, 19 are `reproduced`, and 14 are
  `cross_implemented`. No public record remains `not_located`; the four
  source-gated prototypes remain non-public `candidate` records. Analytical
  certificates do not claim published empirical reproduction outside their
  named domains.
- **Reproducible communication.** A fitted result can produce an HTML brief,
  a deterministic audit bundle, an illustrated publication bundle, and seven
  source-aware Matplotlib views when the optional visualization dependency is
  installed.
- **Audited publication toolchain.** The protected CPython 3.12/Linux release
  lane applies an exact direct-tool constraint, pins MathJax 4.0.0, records the
  resolved Python/static/system/font inventory, and binds it to the existing
  authenticated release evidence. One canonical third-party notice is
  included in the English Documentation and both Handbook language routes;
  it does not select a license for DEAPack-owned components.
- **Research and teaching assets.** The installed catalog contains 33
  deterministic datasets. The selected 17-retain/18-retire route replaces 18
  source-qualified IDs with 16 neutral project teaching cases and never
  aliases an old ID to different numerical content. Three retained external
  fingerprints have exact upstream mappings:
  `ren_cas_directional_scale` under upstream CC BY 4.0 and the two revenue
  examples under upstream MIT. The remaining 30 exact project-created or
  independently selected fingerprints are mapped to CC BY 4.0 with
  attribution to Daoping Wang / DEAPack. A changed fingerprint requires a new
  review rather than inheriting an earlier clearance.
- **Coordinated technical and teaching publications.** The English package
  Documentation gives exact API and failure contracts. The separate companion
  Handbook teaches model choice, economic interpretation, and research
  practice through 18 model or study-design chapters and one applied hospital
  capstone, with English and Chinese editions generated from one reviewed
  source and terminology system.
- **Open scholarly development.** Structured model-proposal, numerical-bug,
  editorial/translation, and pull-request routes welcome contributions even
  when a reader has an idea or counterexample rather than finished code.
  Accepted work keeps traceable credit without treating every contribution as
  automatic software or Handbook authorship.

## Included capability matrix

The counts below are public discovery identities, not unique solver engines
or Handbook chapters.

| Area | Discovery identities | Included capability |
|---|---:|---|
| Static DEA and valuation | 24 | CCR/BCC radial DEA; FDH, FCH, and FRH; Additive, RAM, and BAM; input-, output-, and non-oriented SBM; declared-calibration input CRS EBM; DDF, RDM, and GDF; source-qualified multiplicative DEA; finite polyhedral cone-ratio DEA |
| Scale and economic performance | 12 | Scale efficiency, local returns to scale, radial and relative-directional scale elasticity; cost, revenue, profit, Nerlovian, allocative, and return-to-dollar profitability accounts |
| Environmental performance | 10 | Strong- and named weak-disposal DDF routes, CFG DDF, separable and non-separable undesirable-output SBM, by-production DDF and FGL, material-inflow efficiency, and the non-CHP energy-carbon preset |
| Productivity change | 11 | Adjacent Malmquist with FGNZ, enhanced FGNZ, and Ray--Desli accounts; Luenberger; Global and Biennial Malmquist; CFG and APZ Malmquist--Luenberger; Oh Global Malmquist--Luenberger; Bjurek Hicks--Moorsteen |
| Network production | 9 | Färe--Grosskopf system-radial, Kao--Hwang relational, Chen and Cook additive, Network SBM with source-qualified link roles, Lewis--Sexton sequential, and Kalhor--Kazemi Matin environmental-network analysis |
| Panel and dynamic production | 4 | Park--Park multiperiod aggregation, Dynamic SBM, its ex-post free-carry-over reporting specialization, and Dynamic Network SBM |
| Heterogeneity, diagnostics, and peer appraisal | 5 | Radial metafrontier, selected-plan reference-frequency diagnostics, game cross-efficiency, directional super-efficiency, and super-SBM |

Global Malmquist and Oh GML retain adjacent comparisons as the default and can
also report every forward period pair or an explicitly selected forward
subset from one fixed sample vintage. Expanding the reported pair table does
not multiply the cached distance-solve graph.

## Data, computation, and result workflow

- CPython 3.10, 3.11, 3.12, and 3.13 are the proposed supported runtimes.
- NumPy, pandas, and SciPy are the base dependencies. The default sparse LP
  backend is SciPy/HiGHS and requires no separately configured solver
  executable.
- Matplotlib is optional through the `viz` extra. The registered views are
  `performance`, `frontier`, `improvement`, `process`, `trajectory`,
  `metafrontier`, and `references`.
- `ReferenceSpec` separates the comparison information set from the
  performance measure. Supported policies include contemporaneous, global,
  sequential, window, biennial, and custom reference populations where the
  selected model admits them.
- Source-neutral observation-specific `PeerEligibility` is available only on
  the audited classical and environmental surfaces documented for it. It is
  not a generic categorical-DEA implementation.

After publication, the exact pre-release installation command will be:

```bash
python -m pip install DEAPack==2.0.0rc1
```

The distribution name remains `DEAPack`; the Python import is lowercase:

```python
import deapack
```

## Package, Documentation, and Handbook

The three surfaces deliberately have different scopes.

| Surface | Promise |
|---|---|
| Python package | Callable methods and utilities returned by `deapack.list_methods()` and documented public modules |
| Package Documentation | Exact constructors, parameters, data domains, result fields, diagnostics, errors, source boundaries, and technical research leaves |
| Companion Handbook | A reader-oriented progression through field-level mechanisms, model choice, interpretation, and worked DEAPack laboratories |

An implemented method labeled `documentation_only` remains callable and
tested; the label means that it is too specialized to become a separate
Handbook route. Conversely, a planned method described in the reviews or
shadow registry is not public unless it appears in the installed catalog.

The Handbook's current route comprises:

1. credible study design and production-frontier foundations;
2. classical radial, scale, slack-based, directional, and price-informed
   economic performance;
3. environmental DDF and undesirable-output SBM;
4. four productivity accounts: Malmquist, Luenberger,
   Malmquist--Luenberger, and Hicks--Moorsteen;
5. two internal-production routes: connected-system Network DEA and Network
   SBM;
6. Dynamic SBM for state-connected operating trajectories; and
7. radial metafrontier analysis for declared operating groups.

See the [Handbook contents](book/index.md) and the
[package Documentation](docs/index.md) for the two separate reading paths.

## Migration and compatibility

DEAPack 2.x is not a drop-in replacement for DEAPack 0.1.x or ProdPack. A
built wheel contains only the lowercase `deapack` package; it does not install
an uppercase `DEAPack` forwarding module. Old scripts must be reviewed for
their data roles, returns to scale, orientation or direction, reference
population, undesirable-output technology, productivity identity, and result
interpretation.

The [migration guide](docs/getting-started/migration.md) maps historical
concepts to explicit 2.x specifications. It intentionally does not promise
that renaming a class will reproduce a historical number when the old workflow
used a different estimand or an unaudited fallback.

As a release candidate, `2.0.0rc1` is not a stable compatibility promise.
Research outputs should record the full package version and release commit.

## Known limitations and explicitly deferred work

The following are **not** part of the proposed rc1 public capability claim:

- the internal MPSS, physical-capacity, ordinary CRS cross-efficiency, and
  Andersen--Petersen radial super-efficiency prototypes;
- Färe--Primont productivity, Färe--Grosskopf non-SBM intertemporal
  production, and Nemoto--Goto investment/adjustment-cost efficiency;
- generic congestion, Banker--Morey categorical or nondiscretionary DEA, and
  generic assurance-region or virtual-share interfaces;
- automatic affinity/PCA EBM calibration, alternate EBM orientations or RTS,
  and a generic hyperbolic family;
- bootstrap inference, order-$m$/order-$\alpha$ and conditional frontiers,
  Simar--Wilson second-stage procedures, structure tests, and generic
  stochastic, chance-constrained, robust, interval, fuzzy, or Bayesian DEA;
- general-network VRS, cycles, and shared-resource pools not covered by a
  source-qualified public leaf; and
- interactive or geospatial plotting backends and Chinese package
  Documentation. The Chinese Handbook is part of the publication candidate.

Some narrower source-qualified neighbors are included. For example, game
cross-efficiency, directional super-efficiency, and super-SBM are public even
though ordinary cross-efficiency and Andersen--Petersen radial
super-efficiency remain deferred. The declared-calibration EBM evaluator is
public even though automatic EBM calibration is not.

## Release verification sequence

No local development checkpoint is a substitute for release evidence from a
clean revision. Before tagging, the same clean release commit must pass the
CPython 3.10--3.13 matrix, full pytest and Ruff gates, warning-as-error package
Documentation and bilingual Handbook HTML/PDF builds, reviewed examples,
figure drift checks, all frozen smoke and release benchmarks, strict
sdist/wheel validation, and installed-runtime smoke. Licenses, authorship
metadata, and every dataset redistribution decision must also be approved
before that commit is pushed to the public GitHub repository.

The selected component policy is GPL-3.0-only for software,
CC-BY-NC-SA-4.0 for project-owned Documentation prose with embedded code under
GPL, All Rights Reserved for Bilingual Handbook Preview 1, and CC-BY-4.0 for
project-created data only after origin and authority confirmation. The clean
release build must validate the compound archive expression and exact shipped
license files, pinned direct-tool constraint, resolved toolchain/license
inventory, consolidated third-party notices, and actual embedded-font
inventory. The factual
[software provenance and dependency audit](specs/SOFTWARE_PROVENANCE_AND_DEPENDENCY_AUDIT_2_0_RC1.md)
records the selected policy and the still-pending identity, ownership,
authority, prior-delivery, and service-control facts without treating a policy
selection as an authenticated publication approval.

Only then may the maintainer create the authenticated `v2.0.0rc1` tag. The
tag-triggered Python, Documentation, and benchmark workflows must pass; these
ordinary validation runs deliberately upload no distributable artifacts. The
protected GitHub workflow must then run `action=prepare` from the exact tag to
rebuild the release gates, bilingual PDFs, fixed bundle, private five-asset
draft, and private receipt before any GitHub pre-release is published. The
tag-resident sign-off can only
pre-authorize the public push and named exact tag; it cannot contain its own
commit/tag OID or post-tag execution evidence. The first external HMAC v2
claim records the real `exact_tag=approve/executed` with matching peeled OID,
then authorizes GitHub alone while every later platform remains untouched.
Successors carry a monotonic sequence plus the complete preceding
HMAC-authenticated claim and its canonical SHA-256; the verifier rejects a
direct downstream claim or any rewrite of earlier evidence. Canonical payload
and numeric gate-report objects are embedded and hashed, not represented by
unchecked digest-shaped placeholders.
After private page review, the offline HMAC claim is verified by a separately
approved `action=publish` run, whose final step alone exposes the draft as a
GitHub prerelease. That action triggers no package, hosting, or archival
publication. TestPyPI, production PyPI, the
three hosted projects, and Zenodo are separately approved later stages;
TestPyPI and PyPI each require an explicit manual exact-version dispatch.

Exact filenames, sizes, hashes, counts, logs, and workflow links produced by
the immutable tag belong in the GitHub pre-release evidence, not in a commit
made after the tag. A post-tag failure produces `2.0.0rc2`; the failed tag is
not rewritten. Previously reported dirty-worktree checks and artifact hashes
must not be copied into that evidence. The full protocol is defined in the
[release and archival checklist](docs/developer/releasing.md).

## Citation and publication status

The rc1 candidate currently has **no DOI**. The companion Handbook has **no
DOI, ISBN, publisher, or formal publication date**. Software and book are
separate scholarly objects and will retain separate version and citation
histories. Do not infer book metadata from the software release or include the
book as an asset under a software DOI.

Until archival identifiers are assigned, cite the exact software version and
commit as described in [CITATION.md](CITATION.md). The Handbook should be
described during this stage as **Bilingual Handbook Preview 1 (English and
Chinese), compatible with DEAPack 2.0.0rc1**, not as a final first edition.
Both language renderings identify one scholarly work; they do not receive
separate invented identifiers.
