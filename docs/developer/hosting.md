# Documentation Hosting

DEAPack keeps the companion book and package reference as two independent
Sphinx source projects in one GitHub repository. The bilingual Handbook needs
two hosted builds, while the English package reference needs one, so the
public layout contains three hosted projects without manufacturing a third
Sphinx source tree.

## Recommended Read the Docs layout

Use three Read the Docs Community projects connected to the same GitHub
repository:

| Hosted project | Source | Configuration file | Role |
|---|---|---|---|
| `deapack` | `docs/` | `.readthedocs.yaml` | primary English package Documentation |
| `deapack-handbook` | `book/` | `book/.readthedocs.yaml` | English Handbook |
| `deapack-handbook-zh` | `book/` | `book/.readthedocs-zh.yaml` | Chinese Handbook |

The root configuration makes the primary Documentation project discoverable
during the initial Read the Docs import. The two Handbook projects can be
added later with their explicit subdirectory configuration paths. They remain
separate because the package reference is English-only while both Handbook
languages are maintained publications.

The repository configuration pins the build operating system and Python
minor version, installs the package with its documentation extra, and treats
every Sphinx warning as a failure. The book project additionally installs the
visualization extra and regenerates both dependency-free diagrams and
package-native result SVGs before Sphinx reads the manuscript. This keeps
frontier, performance, productivity, and network case figures on the same
public result API exercised by tests.

## One-time project setup

Repository configuration alone cannot create or connect external Read the
Docs projects. A project maintainer must:

1. install or authorize the Read the Docs GitHub App;
2. import this repository as each of the three projects above;
3. let the primary `deapack` project discover `.readthedocs.yaml` at the
   repository root;
4. set each Handbook project's configuration-file path to the corresponding
   file in the table;
5. enable pull-request builds for all three projects.

Until those actions have been completed and verified, repository links must
not claim that a public Read the Docs URL is live.

## Versions

During development, publish only `latest` from `main`. After the first stable
software and handbook release, activate matching semantic-version tags and
let `stable` resolve to the highest non-prerelease version. Keep the language
component in hosted Handbook URLs because the English and Chinese editions
are both maintained. Package Documentation uses an English route for rc1.

## Division of responsibility

Read the Docs supplies versioned hosting, pull-request previews, and
parent/subproject navigation. GitHub Actions remains the independent release
gate: it builds both Sphinx projects from a fresh environment, checks
committed figure drift, and runs the package tests. A successful hosted build
does not replace those checks.

The three configuration files deliberately use the lower-bound dependency
contract from `pyproject.toml` during active development. Before the first
archival release, generate and test a fully pinned documentation lock for
reproducible historical builds; do not hand-maintain an incomplete list of
transitive versions.
