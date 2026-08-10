# Versioning and deprecation policy

DEAPack versions related contracts without pretending they are one schema:
the software package, fitted-result tables and audit bundles, the method
registry, and the package Documentation. This page is the navigation policy;
the architecture, registry, changelog, and release checklist remain the
normative records.

## Contract map

| Contract | Version authority | What the version governs |
|---|---|---|
| Python package and public API | the package version in `pyproject.toml` and `deapack.__version__` | importable public objects, call signatures, documented behavior, and package-owned result tables |
| Fitted registry provenance | `result.metadata["registry_schema_version"]` | the compact eleven-axis `expanded_spec` attached to a fitted result |
| Audit ZIP | `manifest.json["bundle_schema_version"]`, plus its recorded package version | archive layout, table serialization, and manifest fields |
| Static method ontology | `ontology_schema_version` in registry records | the machine method/relation record structure, independently of fitted results |
| Registry inventory checkpoint | `registry_release` in `specs/registry/registry-manifest.json` | one auditable shadow inventory; it is not a software release number |
| Package Documentation | software version and documentation build commit | version-dependent calls, fields, examples, and behavior |

The current checkout is the stable `2.0.1` software release. The current
ontology record schema is `1.0.0`, the fitted compact registry schema is `2`,
and audit bundles use their own integer schema version. Consumers must read
these fields rather than infer one from another.

## Software versions

DEAPack follows Semantic Versioning for stable software releases and uses
PEP 440 development and pre-release suffixes while a release is being
prepared.

- A **patch** release corrects behavior without intentionally breaking a
  supported public contract.
- A **minor** release adds backward-compatible public behavior and may begin
  a documented deprecation.
- A **major** release may remove deprecated behavior or deliberately change a
  public contract.
- A `.devN`, alpha, beta, or release-candidate build is not a stable release.
  Its exact package version and commit should accompany research outputs.

Beginning with `2.0.0`, supported public APIs follow the deprecation lifecycle
below. Every change belongs in the changelog and migration guide; a
pre-release suffix is not permission to silently change the mathematical
meaning of an existing method identity.

## What counts as public Python API

The supported surface is the set of objects documented in this site and
exported by their documented public modules. A filename under `src/deapack`
is not automatically public. Names beginning with an underscore, registry
implementation details, prepared plotting internals, and undocumented helper
functions can change without a deprecation window.

An exception hierarchy is documented in {doc}`../api/exceptions`. Some
argument checks currently raise ordinary `TypeError` or `ValueError`; their
messages are useful diagnostics but are not individually versioned APIs.

## Deprecation lifecycle

After the first stable release, an ordinary public-API retirement follows
this sequence:

1. announce the replacement and semantic reason in the API documentation,
   migration guide, and changelog;
2. emit an appropriate runtime warning where the deprecated path is still
   executable;
3. retain the path for at least one subsequent minor release; and
4. remove it only in a major release unless continuing it would publish a
   scientifically invalid or unsafe result.

A correctness withdrawal is different from an ordinary rename. DEAPack does
not preserve a mathematically incorrect result silently. The release notes
must identify the affected estimand and versions, and result publication must
fail closed when a claim can no longer be certified.

Not every historical spelling enters this lifecycle. The old `BBC` typo was
never a 2.x public alias, so migration is manual and no 2.x deprecation warning
is promised. The current environmental `disposability="weak"` compatibility
spelling is executable, emits `FutureWarning`, and points users to named
weak-disposal technologies.

## Result tables and archive schemas

`DEAResult` has a common set of named public tables, but the project does not
currently claim one independent, global “result schema version.” Table
columns are method-dependent and version with the software package. Robust
consumers should:

- retain the exact package version and `method_id`;
- select columns by name, never by position;
- inspect method-specific validity and status columns before using a finite
  value;
- tolerate additional columns within the same major version; and
- consult release notes before accepting a removed column or changed field
  meaning.

The deterministic audit archive has a separate
`bundle_schema_version`. A backward-incompatible change to archive paths,
serialization rules, or required manifest fields increments that version.
The manifest also records the DEAPack version that produced the files. Equal
bundle-schema numbers do not promise byte identity across arbitrary Python,
pandas, or compression-runtime changes.

## Method identities and catalog semantics

A fitted result can contain four distinct registry fields:

- `method_id`: the canonical numerical/economic method family;
- `specialization_id`: an optional constructor that fixes part of the
  composition, such as RTS;
- `preset_id`: an optional complete validated recipe; and
- `expanded_spec`: the complete compact composition used for the fit.

Aliases and presets can share one numerical engine and `method_id`. A direct
call with numerically matching arguments does not retrospectively acquire a
historical `preset_id`, and an alias cannot reliably reveal which spelling a
caller typed.

Once public, a canonical ID is not reassigned to a different economic
question, technology, performance account, or result meaning. A materially
different method receives a new ID or an explicitly typed relation. Internal
editorial metadata does not change a method's numerical identity. Prototype
and planned records are inventory, not public catalog entries.

The static ontology's semantic version governs the JSON record structure.
`REGISTRY_SCHEMA_VERSION` separately governs fitted `expanded_spec` metadata.
The shadow registry `registry_release` label identifies the exact inventory audited at
one checkpoint; it neither promotes prototypes nor replaces the package
version.

## Documentation versions

Package Documentation follows the software release because it specifies
version-dependent calls, fields, and behavior. The `latest` hosted version
tracks `main`; stable hosted versions correspond to non-prerelease software
tags. Runnable examples should identify the compatible package version when
they are copied outside the versioned site.

## Maintainer sources

Use the repository's
[architecture](https://github.com/daopingw/DEAPack/blob/main/specs/ARCHITECTURE.md)
for identity and documentation boundaries, the
[registry guide](https://github.com/daopingw/DEAPack/blob/main/specs/registry/README.md)
for ontology semantics, the
[changelog](https://github.com/daopingw/DEAPack/blob/main/CHANGELOG.md) for
version history, and {doc}`hosting` for Documentation publication boundaries.
A policy change should update those sources in the same reviewed change rather
than create a competing version rule on this page.
