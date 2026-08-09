# Changelog

All notable changes to released versions of DEAPack will be recorded here.
The project follows Semantic Versioning for the software package; companion
book editions have a separate publication history.

## Unreleased — 2.0.0rc1

DEAPack 2.0 is a greenfield redesign of the historical 0.1.x package. It is
now feature-frozen at the M13 boundary for its first public release candidate.
`2.0.0rc1` remains unreleased until a clean committed revision passes the
remote Python matrix, strict Documentation and Handbook builds, release
benchmarks, distribution reproduction, and installed-package smoke tests.
The frozen capability surface, explicit deferrals, and current verification
boundaries are recorded in [`RELEASE_NOTES_2.0.0rc1.md`](RELEASE_NOTES_2.0.0rc1.md),
while the complete development evidence remains in [`ROADMAP.md`](ROADMAP.md).

### Added

- M14-A first-public-candidate release boundary. The software metadata is
  synchronized to the PEP 440 candidate `2.0.0rc1`, the supported interpreter
  interval is CPython 3.10--3.13, and the M13 scientific surface is frozen.
  Candidate scope, release notes, bilingual maintainer review packets, scoped
  archive rules, fail-closed dataset-rights auditing, and separated
  TestPyPI/PyPI trusted-publishing workflows are prepared locally. No commit,
  tag, upload, hosted project, DOI, or release is claimed.

- M14-B open scholarly contribution routes. `CONTRIBUTING.md`, structured
  model-proposal, numerical-bug, and documentation/translation issue forms,
  a pull-request checklist, developer Documentation, and a Handbook project
  page now invite suggestions, counterexamples, data, figures, cases,
  translations, documentation, and code. Accepted work retains traceable
  credit without treating every contribution as automatic software or book
  authorship.

- M14-C bilingual Handbook production. The English manuscript remains the
  canonical source, while Sphinx/gettext now builds a reader-edited Chinese
  edition governed by an 85-term DEA terminology table and a Chinese editorial
  guide. All 2,731 messages across 28 reader catalogs and one UI catalog are
  translated; formula, code, citation, link, and identifier invariants pass;
  and all 52 Handbook figures have deterministic, fail-closed Chinese SVG
  counterparts. Strict English and Chinese HTML and LaTeX-source routes pass.
  Final bilingual PDFs remain a clean Linux-CI and visual-review gate.

- M14-D final local engineering preflight. The synchronized dirty worktree
  passed 3,239 of 3,240 collected tests with one expected dependency-branch
  skip, Ruff lint and formatting over 397 Python files, whitespace checks, 61
  reviewed executable blocks, all Chinese translation/source-sync/math/figure
  gates, strict
  93-source package Documentation, and strict 28-source English and Chinese
  Handbook HTML.
  A locally built wheel and scoped sdist passed strict validation and
  fresh-wheel smoke; both remain private because they contain blocked package
  datasets. The release-specific distribution audit correctly remains blocked
  because none of the 35 bundled datasets yet has both an approved
  redistribution status and a content-license declaration.

- M14-E factual dataset-rights triage. A fail-closed 35-row evidence record now
  distinguishes 13 project-origin candidates, four explicit upstream open
  bases, one equation-derived fixture requiring confirmation, one restrictive
  paper-level basis, and 16 rows for which no explicit redistribution basis was
  located. The proposed shortest rc1 route is 17 conditional retains and 18
  replacements or exclusions, with a signed maintainer record, component
  license carve-outs, all-source propagation scan, archive inspection, and
  final PEP 639 metadata review required before any public Git push. No dataset
  was declared cleared by this research.

- M14-F fail-closed dataset replacement laboratory. Sixteen independently
  constructed theoretical or synthetic candidate frames now cover all 18
  proposed replacement paths. Shared Cook/Tone three-stage network paths and
  the paired Tone separable/non-separable policy routes each deliberately have
  one atomic candidate owner. The oracles now exercise active weak disposal,
  upstream/downstream network bottlenecks, fixed/free-link target movement,
  game versus self appraisal, non-redundant fixed carry-overs, a directly
  fittable 28-plan directional-super stress surface, same-frame environmental
  adjustment policies, and an independently constructed cost decomposition,
  in addition to the other analytical and structural accounts. A cross-family
  audit locks content fingerprints, proves exact queue coverage and JSON-native
  evidence, and confirms that the installed catalog remains 35 records. An
  independent role-aware screen found no legacy hash collision, label reuse,
  complete role-aligned copy, positive rescaling, or non-degenerate positive-
  affine match; this is not an authorship or rights conclusion. Every candidate
  is still private, `candidate_only`, redistribution-unknown, and unlicensed;
  no public builder, dataset identity, provenance record, book result, or
  release-rights decision changed.

- M14-G signed-decision and propagation preflight. A sole authoritative,
  fully unsigned pre-tag maintainer record now separates evidence, route choice,
  implementation, and release clearance for all 35 current datasets,
  component licenses, scholarly identities, external services, and eight
  staged publication actions. A read-only promotion contract binds all 16
  candidate stories, roles, replacement paths, content and oracle hashes,
  license files, human approvals, and the proposed 35−18+16=33 post-remediation
  catalog without changing the current 35-record API. A second fail-closed
  audit freezes 925 known identifier-bearing or high-risk source/archive
  paths; its release mode remains blocked until maintainer rights decisions,
  identifier-free numerical fingerprinting, and PDF text/visual review are
  complete. The expanded dirty-tree gate passed 3,239 of 3,240 tests with one
  expected dependency-branch skip and formatted 397 Python files. None of
  these technical controls signs a decision or establishes rights.

- M14-H identifier-independent payload and post-tag PDF controls. A
  private-key HMAC catalog now binds 18 blocked dataset paths and three
  reviewed hidden table/result sources as 15 source families and 21 logical
  bindings. Its public manifest contains no key or raw table, value, label,
  row, or token stream; candidate mode currently records 1,742 fingerprints
  and 877 blocked matches, while release mode cannot substitute an empty or
  minimized catalog. A separate candidate gate validates 156 current
  review-surface single-page PDFs and all 156 pages through Poppler text
  extraction and bounded one-page rendering. Final bilingual PDFs and human
  page review are post-tag evidence: an external claim must bind the immutable
  tag, live toolchain and PDF inventory, distinct English/Chinese page
  ledgers, full payload/numeric reports, artifact digest, protected gate-code
  hashes, the tag-resident pre-tag sign-off record, five fixed staged action
  rows beginning with the exact tag, and a tag-pinned protected key without rewriting
  the tag. A separate HMAC-authenticated completion claim closes execution
  evidence and prerequisite order. Both
  release modes remain blocked by existing data payloads and pending
  human/trust evidence; neither gate determines authorship, similarity,
  rights, or publication quality. The synchronized local checkpoint collects
  3,293 tests, of which 3,292 pass and one expected dependency branch skips;
  Ruff lint and formatting cover 401 Python files, and all 43 release
  benchmarks pass. These dirty-tree results are review evidence only.

- M14-I GitHub-first staged publication controls. The production-PyPI workflow
  no longer listens for a published GitHub Release; both TestPyPI and PyPI are
  independent manual workflows accepting an exact canonical version. TestPyPI
  remains separate staging. Production must be dispatched from the exact tag
  ref and downloads one fixed PyPI claim plus its fixed claim-bound bundle from
  the matching non-draft GitHub Release. Its unprotected build job has neither
  the HMAC secret nor OIDC. The protected job creates an owner-only external
  key file and machine-verifies the HMAC, peeled tag OID, tag-pinned key
  fingerprint, sign-off, candidate manifest, protected code, workflow,
  bilingual evidence, bundle digest, and cumulative action ledger before OIDC.
  GitHub must already be approve/executed and PyPI approve/pending or executed;
  a normal Release or environment approval is insufficient. The exact wheel
  and sdist from that authenticated bundle are compared with the prepared
  copies and rehashed immediately before upload. Initial authorization now
  records the executed exact tag and approves only GitHub next; later platform
  fields remain null pending records, each
  reached action gets a new cumulative claim, withhold blocks dependencies,
  and completion permits no pending row. TestPyPI evidence cannot approve
  production PyPI, release immutability remains a preferred final service
  control rather than an rc1 hard gate, and no Git, platform, upload, hosting,
  DOI, or archival action is claimed.

- M14-J non-self-referential tag and claim state machine. The immutable
  sign-off now contains only prospective `public_push` and named-`exact_tag`
  authorizations; it never attempts to store the containing commit/tag OID or
  post-tag execution evidence. The protected external claim schema advances to
  v2 with five ordered actions: `exact_tag`, `github_prerelease`, `pypi`,
  `rtd`, and `zenodo`. Its first snapshot requires the exact tag already
  approve/executed, requires that row's execution OID to equal the top-level
  peeled tag OID, newly approves GitHub alone, and leaves every later action
  null and pending. Progressive successors and completion preserve strict
  prerequisite order. HMAC authentication, exact OID, tag-pinned key,
  signed machine-readable pre-tag clearances, action-specific tagged workflow
  path/hash/run/head/success bindings, sign-off/protected-code hashes (including
  the dynamically imported dataset-release gate), fixed bundle membership and
  bilingual PDF cross-hashes, bilingual page evidence,
  and both release data gates remain mandatory; TestPyPI remains independent
  staging. Claims now carry a monotonic sequence, the full preceding
  HMAC-authenticated claim, and its canonical digest; recursive verification
  forbids direct downstream entry and rewriting prior evidence. Canonical
  payload/numeric report objects are embedded and hashed, eliminating
  unchecked digest-shaped gate placeholders.

- M14-K reachable GitHub-first prerelease state machine. A single manual,
  exact-tag `publish-github-release.yml` now supports two separately approved
  runs. `prepare` runs the signed pre-tag, dataset, propagation, strict
  Documentation/Handbook, bilingual PDF, reviewed-example, test, release-
  benchmark, distribution, and installed-wheel gates before creating or
  safely reusing only a private draft prerelease. It uploads a deterministic
  four-member bundle plus its four readable members, rejects unknown,
  duplicate, or same-name-different-byte assets, and never clobbers. Only
  after that run finishes successfully can the offline helper create the
  initial v2 HMAC claim from explicit human page-review fields, release-cleared
  reports, the fixed bundle, and the GitHub API prepare-run record. `publish`
  requires exactly those five assets plus the externally uploaded claim,
  verifies that the claim refers to the distinct completed prepare run,
  performs the existing `github_prerelease` claim verification, and
  re-downloads every byte before its final and only visibility mutation flips
  the draft to a prerelease. The claim key appears only in one protected
  materialization step as a mode-0600 file outside the checkout; preparation
  and build scripts never receive it. TestPyPI and PyPI remain independent
  manual workflows, while no RTD or Zenodo workflow is created or triggered.
  The new path is prepared locally only; no Git or external publication action
  is claimed.

- M14-L release-execution and alignment hardening. Direct invocation of the
  GitHub prerelease helper now bootstraps the repository import path from any
  working directory. The protected prepare workflow consumes exactly one
  timestamped release-benchmark `report.json`, rejecting zero, multiple,
  symlinked, non-regular, pre-existing, or byte-drifting reports instead of
  using a non-matching top-level glob. Five blocking benchmarks now fail
  closed on their public optimality, score-status, certificate, finite-value,
  and residual contracts rather than merely printing them. The live shadow
  registry summary is synchronized to shadow.58 and the 75-entry discovery
  catalog. Reader-facing dataset prose no longer promises migration of the
  provenance-unknown legacy provincial CSV: rc1 remains blocked while that
  asset or a detected propagation exists. These changes are local candidate
  hardening only; no dataset, license, Git, or external release decision is
  implied.

- M14-M public-source and prerelease-governance hardening. Root gettext output,
  private review artifacts, scratch keys, benchmark logs, and other generated
  surfaces are now explicitly excluded from Git, while the sdist defensively
  prunes the historical uppercase package and every private/generated root.
  Public prose no longer links to excluded editorial archives or local review
  output, the PyPI long description states that rc1 is still an unpublished
  draft, and human rights decisions consistently point to the sole
  authoritative sign-off rather than an evidence worksheet. The three
  source-checked but independent-oracle-unresolved public methods are frozen
  by an exact rc1 allowlist: no fourth exception may enter, and all three must
  gain independent validation or leave the public surface before stable 2.0.
  The root contribution guide now routes bilingual changes through the full
  Handbook translation and figure gates. Final component licenses, inbound
  contribution terms, dataset clearance, and any Git or external publication
  action remain pending maintainer decisions.

- M14-N zero public numerical-oracle debt. The three source-checked public
  records frozen by M14-M now carry independently reviewed, claim-scoped
  analytical certificates. Green--Cook FCH exhausts every nonempty binary
  coalition of a four-organization fixture in both orientations with exact
  rational arithmetic. Biennial Malmquist separates contemporaneous,
  adjacent-pair pooled, cross-reference accounting, and raw-membership claims;
  three-period public cases reject comparison-only, base-only, matched-only,
  and whole-sample pooling errors. Dynamic Network SBM has a joint
  two-period/two-process non-oriented CRS primal--dual certificate in which
  both within-period link and interperiod carry-over continuity change the
  optimum. The registry now contains 28 `analytically_derived`, 21
  `reproduced`, 14 `cross_implemented`, 4 deferred `candidate`, and zero
  `not_located` records. These certificates do not claim published empirical
  reproduction, broaden their named domains, change Handbook scope, add a
  method identity, or resolve any pending license, dataset, Git, or external
  publication decision.

- M14-O release provenance, notice, and reproducibility hardening. One
  canonical third-party notice now travels through the English Documentation
  and both Handbook language routes, preserving the audited Sphinx, PyData
  theme, Bootstrap, Font Awesome, Pygments, MathJax, font, Sphinx-derived
  page-style, and `fncychap` terms without selecting a DEAPack component
  license. The protected CPython 3.12/Linux release lane applies one exact
  direct-tool constraint, pins MathJax 4.0.0, emits a resolved
  dependency/license/static-asset/font inventory, and binds that inventory to
  the existing authenticated receipt and claim rather than creating another
  Release asset. The RDM teaching figure is independently rebuilt from a
  project-designed signed three-unit example and a new geometry-plus-range
  account; it reproduces neither published observations nor a source figure.
  The live publication routes now comprise 94 Documentation sources/97 HTML
  pages, 29 Handbook reader sources/32 HTML pages per language, 30 Chinese
  catalogs with 2,821/2,821 translated messages, and 53 localized figures.
  A separate software provenance and dependency audit records that the
  current private candidate still carries MIT metadata and that final
  component, authorship, contribution, data, and prior-delivery decisions
  remain unsigned. No main license, dataset clearance, Git action, or external
  publication is implied.

- M14-P selected release policy and rights-safe dataset surface. The software
  and its code examples use GPL-3.0-only; original Documentation prose and
  visual expression use CC-BY-NC-SA-4.0 with embedded code remaining GPL;
  Handbook Preview 1 is All Rights Reserved; and project-created teaching
  datasets are eligible for CC-BY-4.0 only after a truthful, item-level
  creator, authority, attribution, and fingerprint approval. DCO 1.1 governs
  software contributions, while substantive Handbook and translation
  contributions remain closed until an appropriate signed rights agreement is
  professionally reviewed and in force. Exact PEP 639 metadata, component and
  data license maps, canonical notices, archive validation, DCO trailers,
  constrained hosted builds, and style-specific PDF-font provenance now make
  those boundaries executable rather than aspirational.

  The installed data catalog is reduced from 35 to 33 entries: 17 historical
  project routes are retained, 18 source-qualified identifiers are retired
  without aliases, and 16 neutral project-designed replacements take their
  place. The historical provincial CSV is removed from the 2.0 source tree.
  Three external datasets have exact content-hash license mappings (one
  CC-BY-4.0 and two MIT); the other 30 remain fail-closed until the maintainer
  signs the required origin and authority facts. Published methods and their
  citations remain, but unlicensed published tables, frozen result vectors,
  and derived illustrations are removed or replaced across the public source
  surface. This checkpoint records the selected policy but does not invent
  authorship, employer consent, prior-delivery facts, service-account control,
  a signature, a Git action, or an external publication.

- M13-A fixed-vintage pair selection for the Pastor--Lovell Global Malmquist and
  Oh Global Malmquist--Luenberger operators. The adjacent default is retained;
  every forward pair or an explicit validated subset can now be reported from
  the same cached period technologies. Three-period source-form oracles close
  non-adjacent decomposition and circularity, while solver work remains
  linear in organizations times periods and only the reported table can grow
  quadratically in the number of periods. Biennial Malmquist remains
  adjacent-only.

- M13-B source-neutral environmental comparison rights. `PeerEligibility` now
  composes with the generic environmental DDF, common-factor weak-disposal
  DDF, Chung--Färe--Grosskopf DDF, and separable undesirable-output SBM. The
  declared candidate population intersects the base reference policy, and
  fitted provenance and appraisal status are reported without changing any
  model's production/disposal account. Specialist environmental, network,
  dynamic, and productivity leaves remain excluded.

- M13-C declared-calibration Tone--Tsutsui EBM-I-C. Public
  `static.ebm.input.tone_tsutsui_2010.crs.declared` exposes
  `InputOrientedEpsilonBasedDEA` and requires an immutable
  `DeclaredEBMCalibration`, compiles one sparse full-sample CRS technology,
  solves one primary LP per organization, and reproduces all three published
  examples. Automatic affinity/PCA calibration and the wider EBM family remain
  deferred. The method is an advanced bridge within the Handbook's SBM
  chapter and has a separate package-Documentation page, registry record,
  benchmark, and fail-closed result contract.

- M13-D refined the companion-book identity to *Data Envelopment Analysis*;
  *Efficiency, Productivity, and Environmental Performance with Python*; and
  *A Unified Handbook of Theory, Methods, and Practice*. The complete
  Python-bearing title remains the scholarly metadata and citation title; the
  shorter main title remains stable for discovery and running heads. The
  synchronized source/web gate passed 3,124 tests with one expected skip,
  Ruff and whitespace checks, strict 92-source package Documentation and
  27-source Handbook builds, 24 reviewed-example sessions covering 62 code
  blocks, and all 43/43 source-bound smoke benchmarks. The 288-file,
  5,305,198-byte executable ledger remained unchanged with aggregate SHA-256
  `b4edccecaf03415555b93c1acb2862214d9467527c54d81b536f6ff3d1b95207`.
  The strict LaTeX-source and 52-figure preparation stages passed, but the
  existing title-correct 233-page PDF still predated the M13 prose at that
  checkpoint; no release-tier M13 claim was made.

- M13-E final English-Handbook artifact. The synchronized 233-page PDF is
  searchable, contains 554,859 normalized extracted characters, is 5,973,333
  bytes, and has SHA-256
  `e4c35c9e32d6519c6a551f642c4b460051dd1178b37ff5e56156e9709db65378`.
  Its metadata carries the complete Python-bearing title and every referenced
  font is embedded. A 15-sheet review of all 233 rendered pages, plus enlarged
  checks of the cover, EBM bridge, environmental comparison rights, Global
  Malmquist/GML forward-pair sections, bibliography, and glossary index found
  no clipping, overlap, missing figure, illegible type, abnormal blank page,
  broken running head, or incomplete continuation. This is a local development
  artifact, not a released edition.

- M12 unified source-neutral comparison rights across the audited classical
  black-box core. `PeerEligibility` now composes with the generic and CRS/VRS
  radial constructors, all four fixed radial recipes, Additive/Weighted
  Additive, RAM, ordinary input/output/non-oriented SBM aliases, and ordinary
  DDF. Each fit uses the exact intersection of the base `ReferenceSpec` and
  the declared candidate population, reports base/effective population sizes
  and self/technology-membership status, preserves compact provenance, and
  derives self, mixed, or external appraisal from the fitted reference plan.
  The existing method and preset identities are retained. RAM freezes one
  full-data range population before eligibility while allowing an
  observation-specific effective VRS comparison population; restricted RAM is
  labelled `deapack_ram_extension` rather than retaining the exact full
  self-inclusive source profile. The new blocking
  `benchmark_core_peer_eligibility.py` asserts $K$ compilations and $N$ solves
  per Additive/RAM/ordinary-SBM/score-only-DDF case, compact metadata, sparse
  matrices, and no peer leakage for $K$ repeated populations among $N$
  evaluations. A focused release-scale run passed all six cases at $N=1000$,
  $K=20$, with 20 compilations, 1,000 solves, 50,000 effective edges, and an
  881-byte compact audit per model (120 compilations and 6,000 solves total);
  this is not yet a full 41-case suite claim. Undesirable-output SBM,
  environmental DDFs, BAM, generalized
  and range-directional measures, and other specialist families remain
  outside this capability; no new categorical or Banker--Morey identity was
  added.

- M12-B integrated verification. The synchronized local gate passed 3,025
  tests with one expected skip, Ruff checks over 364 maintained Python files,
  whitespace checks, strict 27-source Handbook and 91-source package
  Documentation builds, and all selected executable examples. Source-bound
  smoke and release benchmark suites each passed 41/41 cases against the same
  unchanged 285-file, 5,210,695-byte ledger
  (`c24867a65ae444141e3a8536525e72031ae2420d9387e2d075decb8c88d18b5f`),
  with runtime import verified and 239.64 MiB release-tier peak process-tree
  RSS. The fully reviewed 233-page Handbook PDF is 5,964,722 bytes, exposes
  546,903 searchable characters, and has SHA-256
  `3309d32df0d56f16b5b653e3e4438f7111dea9e5e7fe0d85842d31c3f9b79da9`.
  Its metadata retains the full Python-bearing title, while the cover keeps
  *A Unified Theory-to-Practice Handbook* as the separate strapline. Fresh
  isolated distributions passed strict metadata/archive validation, and the
  wheel installed with all declared dependencies outside the source tree,
  passed the installed-runtime smoke, and reported no broken requirements.
  The reports still describe a dirty local worktree; this is neither a public
  release nor clean-commit remote-CI evidence.

- M11 source-neutral observation-specific peer eligibility for the ordinary
  radial route. Public `PeerEligibilityProvenance` and `PeerEligibility`
  declarations are accepted only by `RadialDEA`, `CCR`, and `BCC`. For each
  evaluated observation, declared candidates intersect the rows admitted by
  the base `ReferenceSpec`; they cannot restore an excluded row, and fitted
  positive-intensity peers remain results. Compact provenance records the
  intersection and states `categorical_interpretation: not_claimed`. The
  fixed-orientation convenience classes and other model families do not expose
  this option. No standalone catalog method, categorical role/compiler, or
  Banker--Morey identity was added. The provisional named categorical leaf
  remains deferred to the next version because its defining equations,
  `dea3` schema, variant boundary, and independent oracle are not frozen.

- M11-B integrated verification. Peer-eligibility declarations now use
  factory-only, exact type-aware keyed or explicit positional construction;
  equivalent row memberships canonicalize to stable specifications and
  compiled populations, while ambiguous keys, signed-64-bit overflow, empty
  intersections, and unsupported downstream reuse fail closed. The local gate
  passed 2,931 tests with one expected skip, Ruff and whitespace checks,
  strict 27-source Handbook and 91-source package Documentation builds, and
  all selected executable documentation examples. Source-bound smoke and
  release benchmark suites each passed 40/40 cases against the same unchanged
  284-file, 5,182,265-byte ledger (`2fa663c1681f729d04d0f2c2d1ceb840f3d4fbaecdfc3f2b49770455441b461e`),
  with runtime import verified and 263.7 MiB release-tier peak process-tree RSS.
  The visually reviewed 233-page, 52-figure Handbook PDF is 5,963,714 bytes
  with SHA-256
  `59718e9e6c172c45d28615d6d6bed4ce720414e824b51ac904c0c44ccf12d959`
  and the exact title metadata *Data Envelopment Analysis: Efficiency,
  Productivity, and Environmental Performance with Python*. The benchmark
  reports still record a dirty worktree. Fresh distributions also passed
  strict metadata/archive validation and an installed-wheel smoke with all
  declared dependencies; this remains local evidence, not a public release.

- M10-G source-bound integration gate. The schema-1.1 release suite passed all
  39/39 cases against an unchanged 283-file, 5,135,753-byte executable ledger
  with aggregate SHA-256
  `d2d9a3314a077541a8670ce6d5ded935f3c8dbea83e0dbbabf376fbf52d2e104`;
  runtime import resolved to the hashed source tree and peak sampled
  process-tree RSS was 233.28 MiB. The synchronized local gate completed 2,864
  tests with one expected skip, strict 27-source Handbook and 91-source package
  Documentation builds, reviewed examples, lint/format/whitespace checks,
  strict distribution metadata/archive validation, and an installed-wheel
  smoke with complete dependencies. Rendered HTML identity and the actual PDF
  metadata title now have explicit release verifiers. The benchmark report is
  source-bound but still records a dirty worktree, so this is not clean-commit
  CI or a public release.

- M10-F governed Dynamic-SBM HiGHS-presolve A/B checkpoint. Across 18 cases
  and 36 independently launched arms, all 36/36 arms were optimal and passed
  every score, target, peer, dual, and carry-over certificate; the headline score
  family agreed within $5.218\times10^{-15}$. Only 6/18 oracle cases were
  fully equivalent. The 12/18 realistic/extreme cases selected different
  non-headline accounts, targets, alternate optimal peers, or original-unit
  residuals, so the existing `presolve=True` default is retained. The
  source-bound 285-file, 5,173,553-byte record has aggregate SHA-256
  `bf95c8aac1c4fcdc08e6841121c223d727de5d618195351637c263c46f00e6ba`
  and passed runtime-import and start-to-finish checks. This exploratory
  fixed-order single pass supports no speed or RSS claim and changes no model,
  API, default, or governed release-benchmark case. The frozen contract is in
  [`specs/experiments/M10_F_DYNAMIC_SBM_PRESOLVE_AB.md`](specs/experiments/M10_F_DYNAMIC_SBM_PRESOLVE_AB.md).

- M10-E source-qualified Charnes--Cooper--Huang--Sun finite polyhedral
  cone-ratio DEA. `PolyhedralConeRatioDEA` is a deliberately narrow public
  input-oriented CRS sum-form leaf with typed restriction provenance, one
  sparse LP per organization, native `theta`, solver-selected peers,
  original-coordinate composites, transformed cone residuals, and separately
  gated generator-coefficient and multiplier accounts. An independent direct
  multiplier/envelopment oracle reproduces the published 1990 Example 2; the
  unresolved Example 3 rows remain excluded. Identity generators reduce
  scores to CCR, unit recoding requires covariant generator updates, and no
  AR-I/II, common-weight, VRS/output, trade-off, or ordinary target-completion
  interface is implied.

- M10-A source-bound benchmark evidence. Aggregate benchmark reports now use
  schema 1.1 and include a deterministic path/size/SHA-256 ledger for the
  executable source, build metadata, benchmark surface, and machine registry.
  The runner verifies that ledger at suite start and finish, fails closed on
  source drift or unsafe paths, and proves that the benchmark subprocess
  imports the hashed `src/deapack` tree. Legacy schema 1.0 reports remain
  readable but are explicitly weaker evidence. This completed evidence-layer
  checkpoint has targeted test coverage; it is not a new source-bound
  38-case release run.

- M10-B mainstream-coverage audit. The existing 18-route Handbook backbone
  remains the editorial boundary: the audit authorizes no new Handbook
  chapter. It ranks finite sum-form CRS polyhedral cone-ratio DEA first and
  the Banker--Morey categorical peer restriction second for bounded package
  work, with deliberately no third priority. The decision and its
  source/oracle gates are recorded in
  [`specs/M10_MAINSTREAM_COVERAGE_AUDIT.md`](specs/M10_MAINSTREAM_COVERAGE_AUDIT.md);
  this ranking does not promote the remaining specialist variants into mother
  mechanisms. A subsequent access audit found only publisher metadata/abstract
  and an unlabelled raw data file for the categorical candidate, so the named
  method is explicitly deferred to the next version; the later source-neutral
  radial eligibility policy does not implement it.

- M10-C constant-memory benchmark observers for the network-radial and
  network-relational cases. The radial observer retains only its first problem
  and a solve count; the relational observer retains only fixed phase counts.
  In focused, same-workload 1,000-DMU observer A/B reruns, peak process-tree RSS
  changed from 267.4 to 133.2 MiB for network-radial (-50.2%) and from 196.8 to
  158.0 MiB for network-relational (-19.7%). Stdout contracts matched apart
  from elapsed time. These focused reruns do not replace the governed M9
  release baseline (267.36 and 196.75 MiB respectively), and they establish no
  runtime improvement: wall time did not improve.

- M10-D layered English-Handbook title system: *Data Envelopment Analysis*;
  *Efficiency, Productivity, and Environmental Performance with Python*; and
  *A Unified Theory-to-Practice Handbook*, with the short running title
  *DEAPack Handbook*. The strict PDF build and visual QA cover all 233 pages
  and 52 figures. The final local artifact is 5,960,693 bytes with SHA-256
  `859c2e5f9ccd1b35fda9a7663fec9c1058bc76aed7e3bb682cf0d4f3590dcac5`;
  its metadata title is exactly *Data Envelopment Analysis: Efficiency,
  Productivity, and Environmental Performance with Python*. This remains a
  local development-manuscript checkpoint, not a released edition.

- M9-A governed executable coverage. The benchmark manifest contains 37
  scripts and 38 registered cases because local returns to scale and scale
  elasticity are separate runs. A local release-tier run completed all 38
  cases as passed, with no blocking failure, timeout, or runner error. This
  inventory comprises 34 blocking public-coverage scripts and three
  informational prototype scripts; passing the latter does not promote them
  into supported public methods. The Handbook runner also classifies and
  executes all 41 active Python fences across 18 source sequences: 26 core
  examples and 15 visualization examples.

- M9-B scholarly dataset contracts for the audited 34-dataset baseline.
  Registry keys, deep-immutable metadata, normalized source kinds, citation
  identifiers or explicit absence, redistribution/license status, variable
  definitions and units, oracle/evidence status, and canonical SHA-256 content
  fingerprints are governed for that completed slice. Unknown redistribution
  or license status remains deliberately fail-closed rather than being
  inferred. Physical column roles are separated from topology and process
  labels while the earlier `roles` read path remains compatible. A subsequently
  added capstone dataset remains outside this historical 34-dataset audit and
  is accepted separately under M9-D below.

- M9-C illustrated result publication through `DEAResult.publish(...)` and
  `deapack.reporting.publish_result`. The deterministic atomic ZIP contains a
  standalone HTML reading layer, reusable SVG figures, a complete nested audit
  ZIP, a README, and a hashed manifest. Publication accepts only the exact
  built-in `DEAResult`, rejects subclasses and duck-typed extensions before
  accessing their hooks, records the trust boundary in the manifest, and
  performs no additional solver calls. A local BCC input-model QA archive was
  61,411 bytes with SHA-256
  `ef4d613f44d20a7dcf3ca55f2bc20ff560648b5d6b8e28080df715cbc829bc0b`;
  its three SVGs, script-free HTML, outer manifest, and 16-member nested audit
  archive passed structure and hash checks, with solver-call count unchanged
  at 16. This archive is local QA evidence, not a versioned release asset.

- M9-D applied capstone acceptance. The new
  `community_hospital_capstone` is the thirty-fifth bundled dataset and uses a
  stable PCG64 raw integer stream, fixed transforms, and packaged rounding; its
  canonical content SHA-256 is
  `f36aff2e248c2f3d08c042897c63154318e97df78ca5e9a9197944f074cd5463`.
  Its governed study population narrows from 64 raw records to 60 usable
  records, 52 district-general hospitals, and a 48-hospital main comparison
  group before scores are viewed. The exact H048 input-oriented BCC oracle is
  `1 / 1.12`, with H008 as its sole selected peer at unit weight. The applied
  chapter uses existing BCC, SBM, scale-efficiency, peer, target, sensitivity,
  and publication paths; it does not add a model family. Its four generated
  figures passed reader-ready and visual repair checks. The current Handbook
  execution inventory is 19 source sequences and 49 Python fences—33 core and
  16 visualization examples. The strict trees contain 27 book sources and 89
  Documentation sources, with 52 actively referenced Handbook SVGs. Current
  local verification completed 2,813 passed and one skipped test, Ruff, both
  strict Sphinx builds, and all reviewed Documentation and Handbook examples.

- Post-M9-D local English-Handbook PDF evidence: 233 pages,
  5,958,225 bytes, 543,497 normalized searchable-text characters, and SHA-256
  `286fff839bdd4faf3cb8d5f30a5cd1117846bc473913fa175c2c2cfd22e88c54`.
  All pages were rendered and reviewed in 20 contact sheets, with additional
  full-detail checks of the principal reader routes and repaired pages. The
  output and Sphinx-build copies are byte-identical, and no clipping, overlap,
  black block, table overflow, abnormal blank page, missing character,
  undefined reference or citation, oversized float, or fatal build condition
  was found. Chapter-number compounds are hyphenated from twenty-one onward;
  the generated locator is explicitly titled `Glossary Index` because its
  entries currently come only from the glossary. This is verified local
  development-manuscript evidence, not an edition or publication declaration.
  The final local release-candidate gate then completed 2,813 passed and one
  expected environment-branch skip, Ruff format and lint, both strict English
  Sphinx trees, every reviewed example, all 38 governed benchmark cases, a
  standard isolated build, Twine 7.0 strict checks, project archive validation,
  clean-environment wheel and sdist installation and smoke checks, and a full
  unpacked-sdist test reproduction of 2,813 passed and one skipped result. The
  final benchmark used 267.36 MiB peak process-tree RSS. This evidence belongs
  to an uncommitted working snapshot: the benchmark records a dirty tree with
  1,350 status entries, so the recorded Git commit cannot by itself identify
  the tested source. GitHub Actions, Read the Docs, release identity, DOI, and
  remaining maintainer approvals therefore remain pending.

- M8 local integration checkpoint for the existing English products and
  governed scientific surface. The strict Handbook tree now contains 25
  Sphinx sources, the same 18 reader-facing chapters, and 46 active generated
  SVGs; the strict package Documentation tree contains 89 sources. The shadow
  registry remains unchanged at 65 method records and 42 typed relations, and
  the installed catalog remains unchanged at 73 entries. No model, method,
  dataset, chapter, plot kind, or Handbook route was added.

- M8 reader and contributor lifecycle documentation: a manual legacy
  DEAPack/ProdPack migration guide; one software/result/bundle/registry/book
  versioning and deprecation policy; Python 3.10--3.13 installation and
  development/pre-release guidance; a unified solver/model/reporting/
  visualization extension page; and a public exception hierarchy that
  documents the existing core, visualization, and reporting branches without
  claiming a nonexistent common superclass. The Documentation home now links
  the maintained Handbook source, offers a mainstream managerial-question
  method-selection matrix, and surfaces contribution, changelog, citation,
  and release routes. Seven curated Documentation examples—reviewed Python
  fences from the quickstart and reference-frequency guide—execute in two
  stateful sessions, with inventory drift enforced by tests and execution
  wired into Documentation CI.

- M8 build and release-path integration. The Makefiles govern complete figure
  regeneration, strict English HTML, Sphinx LaTeX source, searchable-PDF, and
  curated-example targets; the pinned, least-privilege GitHub Actions paths
  add Python 3.10--3.13 and minimum-dependency tests, Ruff, book/docs HTML,
  figure drift, documentation examples, LaTeX/PDF, wheel/sdist construction,
  Twine/archive validation, and installed-wheel smoke checks. Both Read the
  Docs configurations use Python 3.12 with fatal warnings, and the Handbook
  hosted pre-build reuses the complete figure target. Local verification
  completed 2,760 passed and one skipped test, Ruff format/lint over 338
  Python files, both strict English HTML builds, and non-isolated wheel/sdist
  smoke construction through `setuptools.build_meta`. The source archive now
  retains the tests together with their governed benchmarks, specifications,
  Handbook/Documentation sources, figure generators, and release scripts,
  while its archive contract rejects generated builds and local caches. The
  local packaging smoke was not `python -m build`; the configured GitHub
  Actions jobs have not yet run, and a searchable Handbook PDF has not yet
  been successfully built and inspected locally. Formal software/book
  versions, tags, DOI deposits, publication dates, and final book/
  Documentation/figure/data license choices remain undecided, so this
  checkpoint is neither a stable release nor a book publication.

- M8 local release-candidate hardening, without adding a model, method,
  dataset, chapter, plot kind, or Handbook route. The 211-page searchable
  English PDF now preserves the complete cover/metadata title, uses concise
  running furniture, and keeps both portrait case figures inside their caption
  and footer budget; all pages were rendered and visually inspected. PDF
  verification now rejects missing compile logs, oversized floats, undefined
  references/citations, and missing glyphs. CI triggers cover every pull
  request, `main`, `v*` tag, and manual run; exact declared runtime floors,
  untracked generated figures, uploaded distributions, and unpacked-sdist
  tests/examples/figures/strict documentation are explicit gates. PEP 639
  metadata replaces deprecated license fields while retaining MIT and an
  explicit `LICENSE` file. The final local gate completed 2,774 passed and one
  skipped test, Ruff over 339 Python files, seven reviewed examples, both
  strict English HTML builds, isolated sdist-to-wheel construction, archive
  validation, strict Twine checks, offline installed-wheel smoke, and dependency
  checking. GitHub Actions and Read the Docs still require a committed remote
  revision; release identities, DOI deposits, dates, and final content-license
  scope remain unassigned.

- M7 bounded deterministic diagnostics begin with certified selected-plan
  reference frequency for static convex global cross-sections. The public
  procedure separates total, self, and other reported-active-edge counts
  strictly above the source result's `peer_tolerance` and reports
  `reference_rate = reference_frequency / n` without summing intensities or
  launching another solve. It fails closed on partial peer accounts and makes
  no alternate-optimum, global-reference-set, influence, outlier, ranking, or
  inference claim. The shadow registry now contains 65 method records at
  release `.56`, and the 73-entry catalog contains 60 public `method_id`
  entries, five specializations, and eight presets.

- M7 reporting and presentation now expose seven result-aware plot kinds,
  including the selected-plan peer-use view. Explicit readability gates stop
  metafrontier, trajectory, and network-process figures before labels or
  operating accounts become misleading, while the peer-use view displays at
  most 30 nonzero references and discloses selected and zero-frequency rows
  not drawn. The atomic deterministic audit bundle preserves metadata and
  every non-empty public result table in hashed JSONL and spreadsheet-safe CSV,
  together with a self-contained brief or diagnostic audit cover, and adds no
  solve. Its trusted internal report builder does not execute extension report
  methods; formula-like cell values and headings are neutralized, supported
  structured cells have a canonical representation, and large tables stream
  through bounded CSV chunks and JSONL records instead of accumulating every
  serialized table in memory. Reproducible generators now cover the four
  previously static
  `sbm-management-questions`, `dynamic-sbm-carryovers`,
  `metafrontier-management-account`, and `weak-disposal-technologies` SVGs;
  the new `reference-frequency-result` case figure is generated from the
  public result account. Paginated PDF, LaTeX, workbook, interactive, and
  geospatial output backends remain next-version work.

- M6 current-edition closure around one field-level heterogeneity route: the
  O'Donnell--Rao--Battese declared-group radial metafrontier. Heterogeneity,
  inference, and uncertainty records now fall under the machine publication-
  scope gate; the implemented radial account is `handbook_core`, while
  non-radial, conditional, latent-group, partial-frontier, bootstrap,
  second-stage, stochastic, fuzzy, robust, and Bayesian candidates remain a
  source/oracle/result-contract-gated next-version queue. MTR/TGR is recorded
  as an opportunity-proximity ratio (`higher_is_closer`), not another measure
  of managerial quality. The runtime preserves every strictly positive
  certified efficiency and MTR regardless of residual tolerance, separates
  group and pooled score/completion/target/peer/dual gates, retains semantic
  and backend/raw statuses, derives exact call counts from child results, and
  adds no certification solve. Both the dedicated metafrontier plot and the
  generic performance/report path now enforce the corresponding component
  gate. The shared classic RadialDEA base also reports `numerical_error` when
  a backend-optimal solution fails LP or economic certification while
  retaining the raw backend termination separately. The English chapter adds
  a reader boundary between known technology groups, discovered clusters, and
  continuously conditioned frontiers without adding a model chapter or
  implying that statistical inference is already implemented.

- M5 publication and runtime assurance for the retained Network/Dynamic
  handbook routes. Network, Dynamic, and Panel registry records now declare a
  machine-validated reader scope; the Handbook keeps two Network mother
  routes and one carry-over Dynamic route, while sequential, environmental-
  network, Dynamic-Network, accountable-link, free-adjusted-post, and
  Park--Park leaves remain Documentation-only. Network SBM and Dynamic SBM no
  longer reject valid small positive Charnes--Cooper scales, expose semantic
  versus backend solver status, certify original-unit operating accounts,
  gate targets, links or carry-overs, thresholded peers, and dual reports by
  claim, and report exact zero-extra-solve accounting. The Documentation-only
  Dynamic-Network implementation now uses the shared LP certificate and a
  transactional economic reconstruction gate, preventing tampered objectives,
  forged primals, invalid transforms, or stale marginals from leaking any
  semantic table. Missing-source non-SBM intertemporal and quasi-fixed-capital
  candidates are explicitly a next-version queue rather than blockers for the
  current edition.

- A no-network wheel release check for the current development tree. The
  resulting `deapack-2.0.0.dev0-py3-none-any.whl` installs into a clean target,
  imports from that installed location, loads a bundled productivity dataset,
  and completes a certified public FGNZ Malmquist fit rather than relying on
  the editable source checkout.

- Reference-technology membership assurance for the existing equality-based
  environmental DDF routes. The CRS common-factor and VRS activity-specific
  models no longer infer membership of an externally assessed observed plan
  from a positive directional target. Structural self inclusion and certified
  negative distances are resolved without another task; other certified
  external rows use a row-scaled beta-zero feasibility programme. Native
  distances and independently certified targets retain their own validity,
  while the bounded efficiency transform, classifications, and environmental
  improvement display fail closed unless membership is certified. The generic,
  common-factor, CFG-preset, and activity-specific machine records now expose
  the same self/mixed/external appraisal, result-field, and solver-call
  semantics as their public runtime contracts.
- Release and numerical assurance for the existing Kuosmanen VRS
  activity-specific weak-disposal DDF and separable strong-disposal
  undesirable-output SBM. Both use unit-stable production balances and
  solver-neutral LP plus original-quantity certificates with independent
  score, target, thresholded-peer, and complete original-unit dual gates. The
  SBM uses normalized Charnes--Cooper slack coordinates, reconstructs the
  dimension-weighted good/bad output account, and preserves its score and
  correctly transformed quantities and marginals under extreme independent
  rescaling. No method identity or handbook route was added.
- Narrow-column redesigns for the existing environmental DDF, undesirable
  SBM, and weak-disposal technology figures. The two result figures now place
  the managerial gap above the original-unit operating ledger; the technology
  map separates equality-only, common-factor, and activity-specific accounts
  and retains $\hat b$, common $r$, activity-level $r_j$, and CRS/VRS labels.
  Deterministic generation and 600-pixel readability checks enforce effective
  minimum text sizes of 9.28, 9.34, and 12 pixels. The technology map adds one
  conceptual figure to the existing environmental DDF chapter; the two result
  figures replace their previous layouts. No chapter, plot kind, or handbook
  route was added. The book Makefile and GitHub Actions now call the same six
  deterministic generators, so a local strict build cannot silently retain
  stale package-result assets.

- A radial-specific preparation and rendering branch for the existing
  `kind="improvement"` result plot. It reconstructs the phase-one
  $\theta x_o,y_o$ or $x_o,\phi y_o$ plan before applying every certified
  physical completion slack to the public final target, so `targets` cannot be
  mistaken for an unlabeled proportional point. Exact radial identity,
  orientation/RTS/reference semantics, in-technology membership, both solve
  phases, their LP/economic/publication certificates, and the physical and
  row-scaled aggregate slack ledgers fail closed. The English radial chapter
  replaces its abstract O--R--S geometry with the exact branch-C account:
  $\theta=1$, no common resource saving, service completion from 0.5 to 1, and
  radial but not strong efficiency. Discovery, preparation, and rendering use
  fitted result tables only and add no solve. No model, method identity,
  parameter, plot kind, dataset, figure count, chapter, variant, or handbook
  route was added. The detached table publishes the original-unit operating
  account only; it deliberately does not copy per-variable scaled-slack
  magnitudes whose exact scale depends on the fitted reference-set row maximum.
- A reader-facing three-programme account replaces the geometry-first DDF
  arrow diagram in the English handbook. It holds organization E's complete
  `slacks_2x2` record, eligible references, and VRS technology fixed while
  public ordinary-DDF fits declare resource-saving, service-expansion, and
  joint resource-and-service programmes. The existing certified directional
  preparer freezes native beta values 0.247253, 0.419355, and 0.247253 and
  reconstructs every original-unit first-stage commitment before the
  package-driven composite is rendered. The figure keeps zero-direction
  protection separate from later slack completion and explicitly prevents
  cross-programme beta ranking, causal, implementation, priority, or unique-
  prescription claims. Preparation and rendering add no solve, and no model,
  method identity, dataset, API, plot kind, chapter, variant, or handbook route
  was added.
- A reader-facing comparison-population account for the English study-design
  chapter. It holds Lakeside's hospital quantities fixed while two
  institutionally distinct, pre-declared rules admit either three
  same-contract hospitals or four hospitals sharing the wider district
  mission. Public score-only input-VRS fits return 0.9375 and 0.902778 and
  expose North versus $(4/9)North+(5/9)West$ as the certified selected
  phase-one peer evidence. The generated composite independently freezes the
  candidate ledger, service-contract context, eligible rosters, every score
  row, LP/economic/peer/dual certificates, peer intensities, and reconstructed
  peer activities. It separates candidate records, eligible references, and
  active peers; treats the 3.47 percentage-point difference as benchmark
  sensitivity;
  and withholds causal, quality, transferability, completed-target, and
  empirical-sample claims. No dataset, estimator, model, API, solve route,
  plot kind, chapter, or handbook route was added.
- A reader-first opening account for the English handbook, generated from the
  existing `economic_efficiency_4` data and public results. It keeps certified
  input-VRS technical efficiency, a deliberately declared equal-count
  service-throughput level, and return-to-dollar profitability in three
  separate columns. Plans A and B both attain the best radial score without a
  slack-completion claim, while A has the higher declared physical throughput
  and B has the higher revenue per unit of cost and observed profit at the supplied
  prices. The figure introduces no
  new dataset, model, API, plot kind, chapter, or productivity-change claim;
  the opening prose and notation now distinguish observed prices from DEA
  multiplier weights and profit from the revenue-cost ratio.
- A certificate-gated original-unit operating ledger for the existing
  ordinary `static.directional_distance` family, reached through the existing
  `kind="improvement"` result plot. Its independent directional preparation
  contract reconstructs the observed operation, the target promised by
  $\beta g$, any additional phase-two slack, and the selected completed target
  without borrowing an SBM account or displaying unlike quantities on one
  scale. Exact method, technology, direction, summary, two-phase LP/economic,
  public target, and aggregate-slack evidence fail closed; peer and dual
  publication remain independent because the figure displays neither claim.
  Ordinary DDF slack rows now expose their positive `slack_scale`, allowing
  the public account to verify `scaled_slack = slack / slack_scale` row by
  row. The visualization module adds the documented
  `DirectionalDDFImprovementPlotData` payload and
  `prepare_directional_ddf_improvement_data` preparer for users who need the
  detached ledger without rendering.
  Discovery is Matplotlib-lazy, groups the public ledgers once for near
  $O(NV)$ work, and neither discovery nor rendering invokes another solve. The
  English DDF case replaces its scalar beta ranking with one four-variable
  management ledger generated by the public call. No model identity, public
  parameter, existing result/model API signature, plot kind, chapter,
  dataset, variant, or handbook route was added.
- Evidence-aware transition and availability reporting for the existing
  generic `performance` plot. A facet is titled `base → comparison` only
  when every selected row proves one complete, coherent period pair whose
  comparison period matches the facet; incomplete, mixed, same-period, or
  third-party metadata falls back to the ordinary period label. Non-finite
  headlines remain unplotted and receive a bounded, input-order availability
  ledger derived from the selected measure's own certification and validity
  contracts. The footer names at most six affected organizations, gives one
  decisive status, and reports exact overflow without converting an
  unavailable result to zero or a diagnostic point. Preparation remains
  backend-lazy, duplicate-index safe, $O(N)$, and adds no solve. For Global
  Malmquist, Biennial Malmquist, and Oh GML, result-bound discovery now lists
  source-native `best_practice_change` once rather than advertising the equal
  `technical_change` compatibility column as another economic component.
  Explicit requests for that legacy column still work but carry the
  **Best-Practice Change** label; adjacent-period technical-change measures are
  unchanged.
- One certificate-gated, result-native adjacent-period environmental
  productivity screen for the existing Chung--Färe--Grosskopf
  Malmquist--Luenberger route. The bundled 2020--2021 electricity case reaches
  the existing `kind="performance"` interface only after the exact method and
  reference contract, four source programmes, environmental quantity
  certificates, positive multiplicative domain, and complete
  $ML=EC\times TC$ account have been reconstructed without another solve.
  Four plants have publishable transitions; North and West remain explicitly
  unavailable because one or both cross-period reference appraisals are
  infeasible, rather than being converted to zero change or poor performance.
  The English chapter now treats adjacent-period ML as its sole model line and
  confines the full-horizon GML result to a two-row reference-information
  sensitivity table: the former standalone GML derivation, figure, and
  circularity tutorial were removed. No model identity, public parameter, API
  signature, plot kind, chapter, variant, or handbook route was added.
- A certificate-gated original-unit operating ledger for the existing core
  CRS common-factor environmental DDF, reached through the existing
  `kind="improvement"` result plot. Its independent DDF preparation contract
  reconstructs the common $\beta g$ commitment, optional slack completion,
  and every published target without borrowing the SBM score account or
  inventing a common physical axis. Discovery requires certified primary and
  completion programmes and a valid target, but correctly remains independent
  of peer and dual disclosure because neither claim is displayed. Preparation
  reads fitted result tables and adds no solve. The family-level identity and
  its exact CFG source preset share this one reporting route; strong disposal,
  the deprecated equality selector, activity-specific weak disposal,
  by-production, and specializations are rejected. The existing English
  environmental DDF case gains one generated management-facing figure.
  Direction reconstruction preserves the fitted positive-direction invariant,
  result discovery prefilters impossible rows vectorially, and complex
  directions use one validated merge/pivot per role rather than repeated
  full-table scans. The existing SBM branch now reads the registry's canonical
  `specialization_id` as well as the legacy defensive spelling, so a technical
  leaf cannot enter a mother-family display. No model identity, public
  parameter, API signature, plot kind, chapter, variant, or handbook route was
  added.
- Claim-scoped, no-extra-solve release assurance for the existing direct
  Additive DEA and RAM routes. Each primary LP now passes the shared
  solver-neutral primal, bound, objective, KKT, complementarity, and strong-
  duality certificate, followed by separate raw and published original-unit
  resource, service, RTS, and weighted-slack accounts. Headline, target,
  thresholded-peer, and complete original-unit dual claims have independent
  validity and status fields; forged evidence remains auditable through the
  unchanged backend status, fails locally, and cannot leak partial tables from
  another organization. Stable empty schemas and measured execution metadata
  enforce one primary LP per observation and zero certificate solves. The
  existing English slack chapter now compares Additive, RAM, and SBM on one
  unchanged VRS operating plan through a generated original-unit ledger and
  three separate native score cards. No model identity, public parameter, API,
  plot kind, chapter, variant, or handbook route was added.
- No-extra-solve release assurance for the existing classic adjacent and
  full-horizon Global Malmquist operators. Each transition now requires four
  shared solver-neutral LP certificates, four raw and published radial
  production accounts, and complete raw and published multiplicative
  reconstructions before releasing distances, components, or the headline.
  Thresholded peers have a separate all-four-role gate; failed tasks preserve
  raw backend status, remain transition-scoped, and do not contaminate another
  organization. The consolidated benchmark independently counts cached solves
  and contemporaneous/global compilations and requires zero certification
  solves. After certification, cached radial tasks now keep sparse material
  peers and scalar status/objective/residual evidence only; primal and all
  marginal vectors are discarded, so the task cache no longer retains a
  reference-length solver payload per distance. The existing English reference-information case displays these
  validity gates without adding a chapter or decomposition. No model identity,
  public parameter, solve, figure, variant, or handbook route was added, and no
  new guarantee is claimed for biennial, FGNZ presets, Ray--Desli, or other
  special operators.
- No-extra-solve release assurance for the existing Färe--Grosskopf
  two-stage system-radial network model. Every input- or output-oriented LP now
  passes the shared solver-neutral primal, bound, objective, KKT,
  complementarity, and strong-duality certificate, followed by separate raw
  and published network-account reconstructions. Score, component, target, and
  link claims are released atomically per organization; a thresholded peer
  display has its own narrower reconstruction gate. Forged optima and malformed
  certificates fail closed while preserving raw backend status and allowing
  another organization to succeed. Tiny positive external-reference output
  factors remain invertible native values, bounded input negative-zero noise is
  cleaned before the published account is rechecked, and certification adds no
  solver call. No model identity, public parameter, solve, chapter, variant, or
  handbook route was added.
- Claim-scoped, no-extra-solve release assurance for the existing Network DEA
  relational-product and additive process-attribution accounts. The
  relational route now releases the system score, selected process
  decomposition, projection/link account, and thresholded peers through
  separate certificates. The closed two-stage additive route independently
  gates its system, process, split-link/target, and peer claims; the open-DAG
  additive route gates its system, process, and link accounts. Raw backend
  status remains auditable, failures stay local to one organization, and
  primary, secondary, and projection-fallback calls are counted separately.
  The English book compares the three mainstream Network reporting
  institutions on one unchanged graph, but the source leaves remain inside
  the existing Network family rather than becoming chapters or handbook
  routes.
- Certified local-RTS and scale-elasticity release chains for the existing
  Scale family. The analyses now require a certified VRS radial score,
  slack-completed projection, and target before solving two support
  programmes. Finite endpoints pass LP/KKT/dual and original-unit economic
  checks; an infinite endpoint is published only with an independently
  verified recession ray. Interval, RTS classification, and elasticity
  identities are atomic claims, and certificate work adds no fifth solve.
  The existing scale chapter gains one package-native scale-efficiency screen
  while refusing to turn that ratio into an operating-size recommendation;
  no named estimator, model identity, variant, chapter, or route was added.
- Two-account, no-extra-solve release assurance for the existing core
  by-production DDF. Intended production and residual generation now use
  independently row-scaled sparse LPs and pass solver-neutral primal, bound,
  objective, KKT, complementarity, strong-duality, returns-to-scale, and
  original-quantity account checks. The joint minimum and directional target
  require both component scores; thresholded peers and complete original-unit
  marginals have separate all-component gates. The English handbook now fixes
  the output-oriented source direction, explains costly disposal without
  inventing an abatement technology, and calls the smaller component a
  direction-specific limiting account rather than a physical bottleneck. No
  model identity, public parameter, solve, figure, chapter, variant, or
  handbook route was added.
- No-extra-solve postsolve release assurance for the existing core environmental DDF,
  Chung--Färe--Grosskopf Malmquist--Luenberger, and Oh Global
  Malmquist--Luenberger chain. Environmental phase-one quantity rows are now
  unit-stably scaled; LP, raw, cleaned, thresholded-peer, complete-dual, and
  optional completion claims have separate fail-closed gates. Each ML/GML
  transition requires four certified source programmes plus its complete
  multiplicative and economic-domain account before releasing distances,
  components, or the headline. The existing documentation-only APZ leaf shares
  the solver gate but reconstructs its distinct bad-output inequality and cap
  rather than inheriting CFG equality semantics. A distinct beta-zero
  membership task may still be required for an equality-based external
  appraisal; it is an economic-domain feasibility question, not a postsolve
  certificate call. CFG/Oh and APZ task caches retain only sparse material
  peer systems, and their public metadata now reconciles requested roles,
  unique solver calls, and zero additional certificate calls. Extreme
  coherent rescaling fixtures cover both equality and capped-bad-output
  production accounts. No model identity, public
  parameter, solver task, figure kind, chapter, or handbook route was added.
- Phase-scoped, no-extra-solve release assurance for the existing core
  directional-distance model. Numerically row-scaled primary and optional
  slack-completion LPs now pass solver-neutral primal, bound, objective, KKT,
  complementarity, and strong-duality checks followed by directional
  production, target, RTS, thresholded-peer, and complete-dual account
  reconstruction. Primary failure withholds every claim; completion failure
  preserves a certified native distance but withholds its secondary plan.
  Certified signed negative distances remain native values without a fabricated
  efficiency ratio. Nerlovian decomposition now consumes explicit DDF score and
  membership validity, so a forged finite beta cannot enter the technical or
  allocative account. No model identity, solver task, plot kind, or handbook
  route was added.
- Solver-neutral, no-extra-solve release assurance for the existing direct
  cost, revenue, and maximum-profit models. Each source LP must pass primal,
  bound, objective, KKT, complementarity, and strong-duality checks; a second
  gate reconstructs observed and target monetary accounts, gaps, and ratios.
  Failures are isolated by observation or cached price/reference task, and
  `score_valid`, `target_valid`, `peer_valid`, and `dual_valid` govern distinct
  claims. The certified raw account is now the published account, preventing a
  later numerical zeroing pass from breaking target-value or gap identities.
  Cost/revenue allocative and profit/Nerlovian consumers honor the direct score
  certificate. No model identity, decomposition, solver task, or handbook
  route was added.
- Tighter core-family enforcement in the English handbook without changing
  its 18-chapter route. Dynamic-SBM examples no longer expose the default
  source-level score selector, reader-facing trajectory figures replace
  registry and boundary-policy IDs with the canonical family, orientation,
  and RTS, and the introductory CRS/VRS figure no longer labels an observation
  as MPSS while that named estimator remains evidence-deferred. Technical
  selectors and source identities remain in package Documentation and the
  registry.
- No-extra-solve runtime release assurance for the existing core Luenberger
  productivity account. Each of its four signed directional-distance LPs now
  passes solver-neutral primal, bound, objective, KKT, complementarity, and
  strong-duality checks; a second gate reconstructs the two reference-period
  changes, $L$, $EC_L$, $TC_L$, and $L=EC_L+TC_L$. A failed task or additive
  account retains raw role diagnostics but atomically withholds the affected
  transition's distances, peers, components, and headline result without
  contaminating other transitions. The exact two-hospital English case now
  uses the existing `performance` plot around the additive neutral value zero.
  Quantity rows are unit-stably scaled, original-unit accounts are checked
  before release, displayed peers have an independent gate, cached solver
  vectors are compacted to scalar evidence, and task/solver counters require
  zero extra certificate calls. The case states that its values are absolute
  programme units, not cross-hospital
  productivity ratios. No solver task, model, method ID, plot kind, variant,
  or handbook route was added.
- No-extra-solve runtime release assurance for the existing core
  Hicks--Moorsteen quantity-productivity account. Each of its eight input or
  output distance LPs now passes solver-neutral primal, bound, objective, KKT,
  complementarity, and strong-duality checks, followed by radial-distance and
  complete $Q_y$, $Q_x$, and $HM=Q_y/Q_x$ reconstruction. A forged or
  uncertified backend optimum retains task diagnostics but releases no
  transition distances, peer intensities, quantity indexes, or headline score;
  another transition can still succeed. Very small positive radial factors
  remain valid economic quantities, every LP row is unit-stably scaled, and
  LP-only certification is reported separately from the original-unit
  distance gate. Displayed peers remain independent of the eight-distance
  score, cached certificates retain no reference-length solver vectors, and
  counters record 800 primary tasks with zero certificate solves in the
  100-DMU checkpoint. The existing `performance` kind now
  provides the certified English case figure and offers the two combined
  quantity indexes as descriptive no-change-at-one measures—input growth is
  never relabelled as improvement. No solver task, model, method ID,
  decomposition, plot kind, variant, or handbook route was added.
- A core Malmquist reference-information case that holds the organization,
  quantities, orientation, and CRS technology assumptions fixed while
  comparing the existing adjacent-period and full-horizon public results.
  The two-service transition gives adjacent productivity change 0.7746 and
  global change 1.0000, with a common efficiency-change component of one;
  paired public performance plots make the benchmark-policy difference
  visible. The handbook reference figure now gives independent visual status
  only to these two core policies. No model identity, plot kind, or handbook
  route was added.
- Phase-scoped, solver-neutral postsolve assurance for the existing classic
  radial DEA backbone. Phase one now requires LP/KKT/strong-duality and
  radial production-account certificates before releasing a proportional
  score; optional slack completion has its own LP and target/slack-account
  gate. A failed primary solve withholds every claim, while a failed
  completion preserves only a certified primary score and withdraws targets,
  slacks, peers, duals, and strong-efficiency status for that observation.
  Publication cleanup is checked in unit-stable row-scaled accounts, including
  very small physical units; thresholded peer displays and complete RTS dual
  accounts are certified separately, including the VRS convexity marginal.
  Scale and allocative consumers, the radial metafrontier, target-dependent
  analyses, frontier plotting, performance plotting, and reporting now honor
  the corresponding primary or completion validity fields. No optimization
  task, method identity, or handbook route was added.
- Solver-neutral postsolve assurance for the existing three classic static
  SBM orientations. Each programme now passes the shared primal, bound,
  objective, KKT, complementarity, and strong-duality certificate and a
  separate SBM target/RTS/normalization/score reconstruction before release.
  A failed or forged optimum keeps its raw diagnostic status but publishes no
  canonical score, slack, target, peer, or dual row for that observation; the
  gate adds no solve and does not stop later observations. The shared base
  also certifies the existing separable strong-disposal undesirable-output SBM
  balances; it makes no claim for the distinct non-separable hybrid.
- A result-native variable-improvement plot for those same classic static SBM
  results. It pairs comparable proportional resource/service gaps with an
  original-unit target ledger, distinguishes scored from feasibility-only
  sides under the selected orientation, reconstructs both operating accounts,
  and fails closed outside the exact classic method identities and dual
  certification contract. Tone's five-unit English case uses
  `DEAResult.plot(kind="improvement", ...)`; no model, method ID, or handbook
  route was added.
- The same result-native `improvement` kind for the retained standard
  separable, strong-disposal undesirable-output SBM. It keeps resource saving,
  desirable-service gain, and undesirable-residual reduction as distinct
  operating quantities, reconstructs the input and combined output-side
  accounts and headline score, and fails closed unless method, technology,
  role, target, slack, summary, and numerical-certificate evidence agree. The
  English two-plant case reconstructs $2/7=(1-1/2)/(1+3/4)$. Non-separable,
  weak-disposal, Network, and Dynamic SBM results remain outside this plot
  contract; no model, method ID, plot kind, variant, or handbook route was
  added.
- A result-native comparison plot for the existing core radial metafrontier
  account. It joins each certified declared-group efficiency to its pooled-
  opportunity efficiency, prints the MTR, and reconstructs the identity before
  rendering. Component failures are omitted, while a claimed certificate with
  inconsistent solver evidence, nestedness, bounds, or identity fails closed.
  The English six-organization case now uses
  `DEAResult.plot(kind="metafrontier")`; no model, method ID, named variant, or
  handbook route was added.
- A narrower handbook bibliography release rule: the published English
  reference page now lists only works actually cited by the frozen 18-route
  reader path. Uncited technical leaves remain available through package
  Documentation, registry evidence, and repository sources without appearing
  as an implicit handbook method catalogue.
- A result-native process and handoff plot for the existing classic,
  input-oriented Network SBM route. It reconstructs the declared-weight
  process account and system score, keeps internal flows in their original
  units, and labels fixed/free governance without treating process values as
  causal effects or free-link targets as unique prescriptions. Preparation
  requires the exact base method identity, both numerical certificates,
  independent graph topology, complete process/link rows, and scale-aware
  continuity and fixed-commitment checks. Other Network DEA reporting
  institutions and accountable-link specializations fail closed. The English
  Network-SBM case uses `DEAResult.plot(kind="process", ...)`; no model,
  method ID, or handbook route was added.
- A result-native trajectory plot for the existing classic Dynamic SBM route.
  It displays one carry-over's observed, selected outgoing, and next-period
  inherited quantities alongside the complete period operating-plan account
  and the native horizon result. The lower account combines every scored
  production and carry-over dimension and is explicitly not attributed to
  the variable selected above. The theory-led `dynamic_capacity_backlog`
  fixture adds a hand-reconstructable scored good/bad case: Strained has
  input account 0.75, output-expansion account 1.5, and period and horizon
  efficiency 0.5. Plot preparation requires both numerical
  certificates, complete result accounts, source-reconstructed period and
  horizon scores, slack-reconstructed carry-over targets and score-inclusion
  rules, the fitted period order, three certified handoffs in the teaching
  fixture, and a terminal row with no fabricated successor. Fixed carry-overs
  retain their source no-slack commitment semantics. The English Dynamic-SBM
  cases use the public `DEAResult.plot(kind="trajectory", ...)` path; no
  dynamic model, method identity, plot kind, or handbook route was added.
- Claim-scoped numerical assurance for the existing environmental DDF core.
  The shared common-factor/strong-disposal kernel now certifies both the primary
  distance LP and the optional slack-completion LP, reconstructs the declared
  environmental balances and RTS account, and releases score and projection
  claims independently. A failed primary certificate publishes no score or
  semantic tables; a failed completion preserves a certified primary distance
  but withholds peers, targets, and slacks. Cleaned projection accounts and
  thresholded peer displays have separate post-solve gates, so a display-only
  `peer_tolerance` can withhold peers without invalidating certified targets.
  A production-independent dense
  compiler covers a non-CFG common-factor direction and strong disposal under
  CRS, VRS, NIRS, and NDRS, with an exact bad-output-slack target. The English
  core chapter now states explicitly that the bad-output equality identifies
  the classic common-factor weak-disposal account only with its CRS construction;
  no new model identity or chapter was added.
- One reusable solver-neutral LP postsolve certificate for the existing Cook
  general-additive network, Tone--Tsutsui Network SBM, and Tone--Tsutsui
  Dynamic SBM implementations. It independently recomputes primal rows,
  arbitrary variable bounds, objectives, row/bound dual conditions, KKT
  stationarity, complementarity, and strong duality; each model then certifies
  its own
  additive, connected-network, or intertemporal operating account. Missing or
  forged marginals, malformed primals, objective/tau corruption, backend
  failure, and account-reconstruction faults now fail closed atomically:
  `solver_status` remains auditable, `score_valid=False`, canonical scores are
  missing, and no process, target, peer, slack, link, or dual table leaks. The
  shared gate adds no solver calls and all 100-DMU development benchmarks pass
  across the supported orientations and policies.
- Output orientation inside the existing Färe--Grosskopf system-radial network
  leaf. The open 1995/1996 primary paper freezes the two-node CRS technology,
  output distance, and inverse-distance LP; an independent dense compiler and
  exact analytical cases validate the implementation. Native output factor
  and reciprocal higher-is-better efficiency remain distinct, VRS is labelled
  as a composition with the separately sourced process-convex technology, and
  no new method identity or handbook route is created.
- A core-only handbook content pass that preserves the reviewed 18 chapter
  sources while removing narrow implementation routes from the reader path.
  The environmental case now uses the classic CFG DDF; activity-specific VRS
  weak disposal remains in package Documentation. Network SBM teaches fixed
  and free links; accountable-link specializations remain technical. The
  dynamic--network intersection is a boundary note, and one unified
  study/model-choice appendix replaces two overlapping appendices.
- An authoritative 18-route core-family delivery matrix. It audits the frozen
  handbook from reader questions back to canonical implementations,
  independent evidence, technical Documentation, and teaching cases. It
  records non-SBM dynamic DEA as the remaining partially closed core route and
  closes output-oriented system-radial network DEA inside its existing family.
  Congestion remains a conceptual boundary inside scale/slack analysis;
  its two audited named estimator routes are deferred to a later version. It
  explicitly rejects paper names, model-axis combinations, and application
  presets as automatic book gaps.
- A stricter merge-first handbook contract: the unit of inclusion is a core
  model family, not a named paper. Citation volume, a durable acronym, or a
  change to direction, orientation, weights, normalization, reference window,
  decomposition, or application constraints cannot promote a redundant
  formulation into a chapter. Tests freeze the 18-route book and reject
  paper/year section headings and named congestion sections.
- Deferred-release protocols for Färe--Grosskopf--Lovell congestion and the
  Cooper--Deng--Huang--Li (2002) one-model route. Partial primary evidence
  closes their economic distinction but not the complete defining programmes
  or independent numerical oracles. Both identifiers are now machine-checked
  non-public audit locators rather than planned presets; neither enters the
  executable registry, public API, or handbook model route.
- A primary-source protocol and exact analytical certificate for the
  Pastor--Lovell Global Malmquist index. A production-free dense CRS output
  compiler verifies all six own/global distances in a three-period panel,
  four exact GM/EC/BPC accounts, peer provenance, unit invariance, and
  fixed-vintage circularity; the public API is checked against the independent
  values. The certificate adds no model or handbook route and does not extend
  to VRS, alternative windows, environmental technology, or the unavailable
  published application.
- Deferred-release protocols for the Färe--Grosskopf intertemporal-production
  family and Nemoto--Goto quasi-fixed investment efficiency. Official source
  access confirms two distinct economic lineages but does not expose the
  complete defining equations or reproducible numerical evidence. Both remain
  conceptual boundaries inside the existing dynamic chapter, with no inferred
  programme, public API, or new chapter until their source gates close.
- Exact analytical certificates for standard FDH and the activity-specific
  weak-disposal environmental DDF. The FDH certificate exhausts a finite
  observed-activity technology and verifies both orientations, targets,
  peers, and slacks against the public API. The environmental certificate
  independently assembles the dense primal and dual programmes for a
  three-activity common-intensity fixture and verifies the exact DDF,
  efficiency, target, multipliers, and reduced costs used by the technical
  Documentation route.
- A shared slack-family teaching case in which Additive DEA, RAM, and SBM
  evaluate the same VRS operating plan and recover the same benchmark peers
  and physical slacks while reporting measure-specific values. A regression
  test freezes the complete numerical account used in the book.
- `economic_efficiency_4`, a deterministic four-plan teaching case that holds
  one resource, two services, and common prices fixed while reproducing the
  package's cost, revenue, profit, technical--allocative, and Nerlovian
  accounts. Exact reconstruction tests make it the shared computational case
  for the consolidated handbook chapter; it is explicitly synthetic rather
  than a published-data reproduction.
- `ZhouAngWangNonCHPEnergyCarbonDEA` (alias
  `NonCHPEnergyCarbonDEA`) as one narrow application-specialization preset
  for the three source-exact non-CHP energy, carbon, and integrated accounts.
  The required account selector has no default. The implementation fixes the
  source CRS global self-inclusive one-input/one-good/one-bad technology,
  reports the raw non-radial distance separately from EPI/CPI/ECPI, and offers
  optional optimal-face component/index ranges without claiming unique peers.
  An exact three-system dataset, independently assembled dense programmes,
  sparse benchmark, failure certificates, unit-invariance tests,
  visualization semantics, registry record, and technical Documentation close
  the claim. It is intentionally excluded from the companion book because it
  is a paper-specific preset rather than a foundational model family.
- The classic multiplicative DEA family as one public
  `static.multiplicative` machine method backed by one shared sparse log-space
  compiler and two source presets. The 1982 C2S2 log-conic preset retains its
  greater-than-one data domain and lack of unit invariance; the 1983
  free-intercept log-convex preset retains its strictly positive domain and
  unit invariance. An independent dense source-form oracle verifies scores,
  targets, peers, exponent-floor power, and the deliberately different unit
  behavior. The classical-foundations benchmark, model and API documentation,
  and a deterministic technical figure complete the current software claim.
  The former book draft is excluded from the published handbook under the
  family-level admission gate. This remains unreleased `2.0.0.dev0` work, not
  a stable or formal release.
- A source-equation protocol and production-free published-chain oracle for
  Tone--Tsutsui EBM-I-C. Examples 1--3 reproduce the ADD, affinity/PCA,
  epsilon, weight, score, radial-factor, slack, target, and peer accounts.
  Machine certificates expose a score-material repeated-eigenvalue ambiguity
  and the infeasible hospital-G transition between the printed raw and
  projected tables. The later M13 conditional evaluator admits only the
  source programme after epsilon and normalized input weights are declared;
  the unresolved automatic calibration chain and wider EBM identities remain
  next-version candidates.
- A result-native `frontier` visualization for certified one-input/one-output
  CRS and VRS radial DEA fits. It draws observed operations, the fitted
  frontier, and slack-completed targets while failing closed for
  multidimensional, cross-period, external-peer, incomplete, or oversized
  displays.
- A reproducible English-book case figure and matching visualization guide
  that interpret target arrows as benchmark opportunities rather than causal
  diagnoses or prescriptions.
- A reader-oriented rewrite of the Malmquist--Luenberger chapter, with an
  exact two-panel environmental productivity account, explicit four-distance
  result-field mapping, separate treatment of admissible negative distances
  and failed comparisons, and synchronized technical documentation.
- Four classic radial constructors—`CCRInput`, `CCROutput`, `BCCInput`, and
  `BCCOutput`—as catalog presets over the shared `static.radial` method. Each
  fixes RTS, orientation, the native score convention, and
  `compute_slacks=True` with DEAPack's row-scaled lexicographic slack/target
  completion.
- A shared embedded
  `evaluation.target_completion.pareto_koopmans` protocol for compatible
  radial, directional-distance, and generalized-distance phase-two solves.
  It uses zero-safe row-scaled slack completion, preserves each model's
  first-stage score, and reports generic strong-efficiency status only after
  the completed target is checked.
- `FGNZMalmquistProductivityIndex` (short alias `FGNZMalmquist`) as the
  source-qualified output-oriented CRS preset over the shared adjacent-period
  Malmquist kernel. It reports the two-component
  `productivity_change = efficiency_change * technical_change` core without
  implying that the distinct pure-efficiency/scale method has been run.
- `FGNZEnhancedMalmquistProductivityIndex` (short alias
  `FGNZEnhancedMalmquist`) as a distinct source-qualified six-task method.
  Four CRS tasks retain the adjacent geometric Malmquist headline; two
  own-period VRS tasks divide `efficiency_change` into
  `pure_efficiency_change` and `fgnz_scale_change`. An independent exact
  compiler verifies both multiplicative identities and proves that the FGNZ
  allocation is not Ray--Desli's allocation. The source certificate is
  strictly positive and matched; tested partial-zero cells with positive row
  aggregates and unbalanced `drop`/`raise` behavior are package extensions.
  No OECD/Penn World Table 5 empirical reproduction is claimed.
- `RayDesliMalmquistProductivityIndex` (short alias
  `RayDesliMalmquist`) as a distinct source-qualified method on balanced,
  strictly positive panels with exactly one desirable output. Four CRS and
  four VRS distances provide the headline Malmquist index, native
  `PEFFCH`, `TECHCH(v)`, and `SCH(v)` factors, and the source-defined partial
  account when a cross-period VRS programme is infeasible. An independent
  eight-task compiler, public-API comparison, technical worked example, and
  deterministic multiplicative-ledger figure close the package-documentation
  claim without claiming reproduction of the Penn World Table 5.6
  application. The named decomposition is not part of the published handbook.
- A claim-scoped analytical certificate for the source-native Coelli
  material-inflow account. An independent compiler checks exact CRS/VRS
  $TE$, $EE$, physical-content $EAE$, and $EE=TE\times EAE$ on a
  self-inclusive cross-section; it does not claim to reproduce the
  unsupplied unit-level 183-farm observations. The English case now includes
  a deterministic figure separating common resource saving from a
  lower-material input-mix opportunity.
- A claim-scoped analytical certificate and reader-oriented English case for
  Oh's Global Malmquist--Luenberger index. Independent dense LPs verify the
  four nonnegative own/global distances, exact $GML=EC\times BPC$
  decomposition, source-native best-practice gaps, fixed-vintage
  circularity, peer mapping, and unit invariance without claiming to
  reproduce the unavailable 26-country panel.
- `APZMalmquistLuenbergerProductivityIndex` (alias
  `APZMalmquistLuenbergerDEA`) as the public Aparicio--Pastor--Zofío preset.
  It composes the 2017 equations (5)--(6) capped-bad-output CRS technology
  with the standard four contemporaneous own-/cross-period
  Malmquist--Luenberger roles, the target observation's $(0,y,-b)$ programme,
  and a componentwise cap recomputed from each reference period. The
  source-qualified domain requires strictly positive inputs and undesirable
  outputs. A production-free exact compiler derives distances $2/5$,
  $3/11$, $3/5$, and $5/11$ and verifies $ML=(77/80)(8/7)=11/10$ on the
  2013 Table 1 fixture. This is not CFG post-processing or Oh GML;
  cross-period infeasibility is reduced rather than eliminated, and the 2017
  WIOD application is not reproduced. The canonical preset ID is
  `productivity.malmquist_luenberger.aparicio_pastor_zofio_2013`; `.apz` is
  a discovery-only lookup alias.
- A claim-scoped analytical certificate for the classic direct additive
  model. One source-displayed and one independently derived exact fixture
  verify the VRS/unit-weight scores, slacks, Pareto--Koopmans status, targets,
  peers, and distinction from radial DEA and SBM without claiming a
  published numerical-table reproduction.
- A source protocol and independent analytical certificate for the
  Cooper--Park--Pastor range-adjusted measure. The complete defining article
  freezes the VRS, positive-coordinate-range profile, while a separately
  compiled dense LP and exact upper bound verify RAM distance, efficiency,
  slacks, strong status, target, peer, signed-data translation, and unit
  invariance without claiming a published result-table reproduction.
- A primary-source protocol and exact oracle for the conventional
  by-production DDF. The packaged Murty--Russell--Levkoff five-DMU example
  reproduces equation (5.6) for DMUs 1--3, while an independent dense CRS
  compiler checks both component distances and their minimum for all five
  observations. The English book adds a managerial bottleneck figure.
- A separate primary-source protocol and exact oracle for the modified
  by-production FGL measure proposed by Murty--Russell--Levkoff. The source's
  printed DMU 2 and DMU 3 component/aggregate scores are reproduced, and two
  independently compiled scalar CRS programmes verify all five observations,
  targets, unique component peers, and the frozen Example 1 input-partition
  correction.

### Changed

- Completed the second-round editorial closure of the English handbook's five
  classical DEA chapters. Radial DEA, scale performance, Additive/RAM/SBM,
  DDF, and observed-price economic efficiency now form one reader-facing
  sequence organized around managerial commitments rather than model-name or
  geometric catalogues. Targets, score directions, the non-oriented SBM and
  Nerlovian symbols, and the separation between handbook interpretation and
  technical Documentation are synchronized across the book, Documentation,
  conventions, tests, and figures. Rendered-HTML review also corrected the
  site-header identity and redesigned the three densest Part II accounts for
  ordinary reading width. For external reference sets, `scale_efficiency()`
  still reports a valid CRS/VRS ratio but now withholds
  `is_scale_efficient` unless the evaluated plan belongs to both component
  technologies; component and composite membership fields make that
  classification domain explicit. This pass adds no model, method identity,
  dataset, plot kind, chapter, or handbook route.
- Deepened Part I of the English handbook into a three-question learning
  sequence. The opening chapter now separates technical efficiency,
  productivity level and change, profitability and relative-price recovery,
  and environmental performance before any ranking is attempted. The
  hospital study-design chapter then makes organizational responsibility,
  variable roles, peer eligibility, sampling support, and causal limits part
  of the comparison contract. The production-technology chapter finally
  explains observed feasibility, free disposal, convex virtual plans, FDH,
  CRS/VRS replication rights, and orientation as economic and managerial
  assumptions rather than diagram labels. Existing hospital and branch cases,
  datasets, and public calls remain in place. The study-composition map now
  uses decision, comparison-contract, and evidence language, while the existing
  three-account and peer-eligibility result figures use larger type and less
  visual clutter; all three were checked in the rendered HTML at ordinary page
  width. The pass adds no model,
  method identity, public API, optimization solve, dataset, figure, chapter,
  plot kind, or handbook route.
- Completed the professional-voice closure for the English handbook. Its front
  matter, notation, core explanations, and cases now lead with economic and
  managerial questions, decision context, interpretation, and limitations.
  The book states result availability in substantive terms, while field-level
  solver, certificate, validity, and release-pipeline details remain in package
  Documentation. Nineteen existing result figures now use reader-facing
  titles, legends, annotations, and qualifications; their fitted-result
  preparation and rendering retain the same fail-closed evidence gates and
  invoke no additional solve. This editorial pass adds no model or method
  identity, public API, optimization solve, dataset, chapter, plot kind, or
  handbook route, and leaves the active figure count unchanged at 44 (25 book
  sources and 18 chapter sources).
- Synchronized catalog evidence labels for adjacent-period Malmquist and Oh's
  Global Malmquist--Luenberger index with their primary-checked registry
  records and independent analytical oracles. Standard FDH's catalog evidence
  now likewise reflects its new primary-equation certificate, and the
  Pastor--Lovell Global Malmquist entry reflects its new exact source-form
  evidence.
- Kept the handbook's latest literature integration inside existing core
  families rather than promoting specialized formulations. The classical
  radial chapter now explains when unrestricted endogenous multipliers need
  defensible ex-ante value judgements, while assurance-region and cone-ratio
  recipes remain implementations of that appraisal choice rather than new DEA
  families. The study-design chapter distinguishes numerical precision from
  sample, influence, and inferential credibility without creating a statistics
  methods chapter. The dynamic and productivity chapters now separate
  carry-over accounting from quasi-fixed adjustment-cost questions,
  organization-level indexes from industry reallocation accounts, and
  quantity productivity from profitability and price recovery. No chapter,
  model route, package API, or executable claim was added by this pass.
- Locked the English handbook to its reviewed 18-chapter core-family route.
  Field recognition is now explicitly necessary but insufficient for an
  independent chapter: familiar changes to weights, directions, reference
  windows, ranking rules, variable treatment, or one constraint are absorbed
  into the smallest relevant family discussion or kept in package
  Documentation. A route regression test prevents an unreviewed source file
  from entering the public book. The contributor README is also excluded from
  the book-site build. A reader-facing editorial pass removed development and
  solver language from the active chapters, while generic productivity
  notation now reserves $r$ for desirable outputs, $\sigma$ for the evaluated
  plan's period, and $\tau$ for the reference technology's period across the
  book, conventions, figures, and package Documentation.
- Added a handbook admission gate separate from the software evidence gate.
  Chapters and appendices now require an independent, field-level,
  transferable mechanism and a necessary reusable lesson; paper-specific
  directions, weights, normalizations, score displays, and industry accounts
  remain in package Documentation even when their implementations are public
  and fully tested. The gate is being applied retroactively to the current
  English route before further expansion.
- Applied the gate in a first retroactive pass. The published route at that
  checkpoint contained 30 chapter
  sources and excludes eight paper-specific development pages plus the
  evidence-incomplete ordinary cross-efficiency draft. FCH/FRH, specialized
  scale directions, game cross-efficiency, directional super-efficiency,
  named Malmquist decompositions, APZ consistency, profitability/GDF
  decomposition, and other technical leaves were also removed from surviving
  reader-facing chapters, notation, and the appendix map. Their code,
  registry, tests, and package Documentation remain intact where public.
- Reorganized the English book's opening learning path. Production technology
  now introduces only attainable plans, free disposal, convexity, and CRS/VRS;
  classical radial DEA is the single home of radial programmes; the
  non-convex chapter retains mainstream FDH while FCH/FRH move to package
  Documentation; and the scale chapter retains scale efficiency, local
  returns, and ordinary scale elasticity without elevating one paper's
  relative-directional specification into the handbook route.
- Consolidated the English handbook from 30 to 18 published chapter sources.
  Cost, revenue, profit, allocative, and Nerlovian analysis now share one
  observed-price chapter and one tested four-plan case; radial, relational,
  additive, and open-network accounts now share one organizational chapter;
  and Dynamic SBM now has one carry-over and trajectory chapter without a
  separate dynamic-network route. Adjacent-period and global reference policies likewise share one
  conventional productivity chapter and one environmental productivity
  chapter. FDH is integrated into the radial chapter, additive DEA and RAM into
  the slack-based chapter, and by-production into environmental technology and
  DDF. Materials balance, non-separable undesirable-output SBM, and dynamic
  network SBM remain in package Documentation; super-efficiency is withheld
  until its mainstream radial source gate closes. The machine registry points
  only core family records to canonical pages and removes handbook placement
  from documentation-only or evidence-deferred leaves.
- Added a machine-readable `publication_scope` to every productivity method
  record and the public method catalog. The English handbook and Documentation
  navigation now expose exactly four primary productivity routes: adjacent
  radial Malmquist, ordinary Luenberger, CFG environmental
  Malmquist--Luenberger, and Bjurek Hicks--Moorsteen. Global Malmquist and Oh
  GML are explicitly supporting/sensitivity reference policies; enhanced
  FGNZ, Ray--Desli, Biennial, and APZ remain documentation-only technical
  leaves. The FGNZ core preset inherits the adjacent-Malmquist route rather
  than being counted as a fifth family.
- Compiled ordinary `RadialDEA` phase-one sparse structure once per unique
  reference set. Per-DMU work now binds row scales, the radial-factor column,
  and right-hand sides into an immutable CSC copy. Public equations and API
  are unchanged; metadata reports template and binding counts, and independent
  tests compare every LP array with the former direct constructor across both
  orientations, all RTS settings, and global/custom/contemporaneous references.
- Unified radial LP construction across adjacent, FGNZ core, enhanced FGNZ,
  global, biennial, and Ray--Desli productivity paths. The adjacent,
  enhanced-FGNZ, and Ray--Desli executors
  compiles period quantity references once and caches RTS-specific sparse
  templates separately; its metadata distinguishes requested role rows from
  unique binds and solver calls without merging the economic identities of
  the methods.
- Compressed cached productivity peer intensities to material local positions
  and weights. Generic, FGNZ core, enhanced FGNZ, Ray--Desli, global, and biennial public peer
  tables retain their fields, order, and reporting threshold without keeping
  a dense length-reference lambda vector alive for every cached distance
  task. Classic Malmquist, Luenberger, and Hicks--Moorsteen caches additionally
  discard primal and marginal vectors after all release checks, while retaining
  scalar backend and certificate evidence for diagnostics.
- Clarified that the named classic presets retain
  `method_id="static.radial"` and emit a `preset_id`; their phase-two target
  selector is an explicit DEAPack policy rather than a uniquely prescribed
  historical target.
- Made radial constructor identities fail closed at fit time: post-construction
  mutation cannot make a CCR/BCC specialization or complete preset report an
  identity that disagrees with the programme actually solved.
- Strengthened the release evidence gate: a candidate lacking either an
  original/authoritative source freeze or an independent numerical oracle
  remains in the next-version backlog and receives no current-release public
  identity.
- Applied that gate to the Banker-1984 MPSS and
  Färe--Grosskopf--Kokkelenberg-1989 physical-capacity reconstructions. Their
  tested code and benchmarks remain as non-public development prototypes,
  but the top-level exports, public catalog entries, executable book
  treatment, and API documentation are deferred until the defining full
  texts can be audited equation by equation.
- Applied the same gate to the Andersen--Petersen radial super-efficiency and
  ordinary CRS cross-efficiency identities. Later sources and internal
  numerical checks support their development implementations, but the
  defining full texts were not obtainable for equation-level audit; their
  public exports and catalog identities are therefore deferred to the next
  version while the independently source-qualified game cross-efficiency
  protocol remains public.
- Aligned `ByProductionFGL` defaults with the source CRS/CRS profile and
  labelled VRS, one-sided returns, panels, custom references, and
  `distance = 1 - efficiency` as package extensions. Result metadata now
  states whether the equation-level source profile matches and clarifies that
  the native unit score exhausts output-vector adjustments but can retain
  input slack. Numeric controls reject non-finite values, and both components
  fail closed unless the actual returned incumbent, cleaned targets, peers,
  factor bounds, RTS restriction, and optimality interval pass a post-solve
  certificate.
- Narrowed the Charnes et al. (1985) additive identity to equations
  (4.5)--(4.6), VRS, unit weights, and a self-inclusive cross-section.
  Fixed non-unit user weights, CRS/NIRS/NDRS, and panel/non-global reference
  policies remain configurable package extensions; equation (5.7) and
  separately named unsupported leaves are deferred. Explicit all-one weights
  retain the algebraically identical source profile.
- Recompiled additive/RAM LPs with reference-anchored VRS balances, level-scaled other
  RTS balances, reference-deviation strong-status scales, and one common
  objective scale. Translations and reciprocal unit/weight changes retain
  their result, effective solver tolerances guard extreme weight ratios,
  small common weights no longer create false efficiency, and a small
  intensity is retained when it materially explains the reported target.
- Added an independent additive/RAM postsolve account check covering
  incumbent shape and finiteness, scaled balances, bounds, backend-reported
  violation, objective consistency, cleaned physical resource/service
  accounts, and RTS identity. A corrupted nominally optimal incumbent now
  fails closed before any score, slack, target, peer, or dual is published.
- Source-checked RAM's zero-range boundary: Cooper--Park--Pastor allow the
  inactive coordinate to be omitted with zero slack contribution, and the
  retained zero-weight balance is equivalent under the matched
  self-inclusive VRS population. Pooled-panel execution remains a package
  extension; the historical source profile remains cross-sectional.
- Recompiled BAM in bounded normalized slack variables with row-scaled
  balances, material-peer reporting, and optimal-only dual publication. This
  closes the absolute-slack cleanup failure under extreme unit changes.
- Aligned `ByProductionDDF` defaults with its defining source: CRS in both
  subtechnologies and one fixed unit direction. VRS/NIRS/NDRS,
  observation-scaled directions, and temporal/non-global references remain
  configurable extensions and are identified by runtime source-profile
  metadata. Documentation now states that the source criticizes BP-DDF and
  proposes the distinct FGL measure; `1/(1+distance)` is a package display
  transform only.
- Corrected the 2.0 compatibility contract: historical misspelling `BBC` is
  not an exposed alias, and NIRS/NDRS remain tested `RadialDEA` parameter
  paths rather than a standalone `static.radial.restricted_rts` literature
  leaf.
- Separated the source-qualified Färe--Grosskopf--Norris--Zhang output-CRS
  core from configurable input-oriented or non-CRS Malmquist sensitivity
  paths, and attached an explicit decomposition identity only to the named
  preset.
- Corrected the Coelli evidence boundary: environmental allocative efficiency
  uses physical material-content coefficients and requires no price data.
  The source defines weighted multiple pollutants in equations (18)--(21),
  but their independent validation remains deferred, together with NIRS/NDRS,
  heterogeneous/estimated coefficients, panel/custom/external source
  equivalence, farm-data reproduction, and welfare, causal, damage, or
  actual-emission claims.
- Corrected the pre-release Oh result semantics so
  `base_best_practice_gap` and `comparison_best_practice_gap` follow Eq. (9),
  $(1+D^r)/(1+D^G)\in(0,1]$, and `best_practice_change` is the comparison
  gap divided by the base gap. The headline GML, EC, and BPC values were
  already numerically correct. Own/global distances now fail closed to the
  nonnegative source domain, and metadata distinguishes the pooled CRS
  conical envelope from a literal union and source pairwise theory from the
  package's adjacent-transition enumeration.

The first release entry will distinguish:

- public API additions and compatibility boundaries;
- numerical or semantic changes;
- newly closed literature/oracle claims;
- datasets and reproducible figures;
- documentation and companion-book changes;
- migration notes and known limitations.

No DOI, publication date, or release status is assigned by this development
entry.
