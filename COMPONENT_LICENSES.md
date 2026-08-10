# Component Licensing and Rights Boundary

DEAPack is a coordinated repository, not a single undifferentiated work. This
map records the adopted outgoing policy for each component while preserving a
fail-closed rule: a license applies only to material for which the stated
licensor has authority to grant it. A path match is not evidence of
authorship, ownership, employment clearance, or permission to relicense
third-party material.

| Component | Repository scope | Adopted terms | Current boundary |
|---|---|---|---|
| Software | Project-owned Python source, software build and validation code, and software-distribution metadata | `GPL-3.0-only` | Daoping Wang confirmed publication authority; separately marked material is excluded |
| Package Documentation prose | Project-owned original prose and original visual expression under `docs/` | `CC-BY-NC-SA-4.0` | Embedded code is software, not CC-licensed; third-party quotations, logos, fonts, and assets retain their own terms |
| Documentation code | Executable examples, code blocks, snippets, and API signatures | `GPL-3.0-only` | Same authority and third-party exclusions as the software component |
| Project-created datasets | The 29 project-origin records and independently selected Zhou fixture mapped by exact hash in `DATA_LICENSES.md` | `CC-BY-4.0` | Attribute Daoping Wang / DEAPack and identify modifications; any content-hash change requires a new mapping |
| External or source-derived datasets | The three exact externally sourced records in `DATA_LICENSES.md` | Source-specific | Ren retains CC BY 4.0; the two revenue fixtures retain their upstream MIT notices |
| Third-party material | Named copied, embedded, or adapted material | Upstream terms | See `THIRD_PARTY_NOTICES.md`; no DEAPack component license overrides those terms |

## Software distribution boundary

The wheel and source distribution are configured as the software publication
surface: package Documentation, repository governance material,
figures, tests, benchmarks, and standalone data files are excluded. Their
license texts are therefore not folded into the PEP 639 software expression.
Numerical datasets represented inside Python source remain separately
licensed content even though the archive member is a `.py` file. The release
audit verifies every exact item-level mapping rather than treating GPL as a
blanket data license.

The PEP 639 expression for the archive is
`GPL-3.0-only AND CC-BY-4.0 AND MIT`: GPL covers the software component, CC BY
covers the 31 exact mapped CC BY dataset payloads, and MIT covers the two
exact revenue payloads. It is not a blanket license for Documentation,
third-party dependencies, names, or trademarks.

## Documentation attribution

Attribute Documentation material under CC-BY-NC-SA-4.0 to
“Daoping Wang / DEAPack,” link to the repository and version or commit used,
retain the license notice, and identify modifications.

## No retroactive conclusion

This map adopts the component policy for the prepared 2.0 release surface.
The maintainer confirmed that no DEAPack 2.0 copy was delivered to a third
party under the earlier MIT development metadata.
