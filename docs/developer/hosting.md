# Documentation Hosting

DEAPack publishes one package-Documentation project from this repository. The
Read the Docs project name is `deapack`, and its Sphinx source is `docs/`.

## Read the Docs configuration

The repository-root `.readthedocs.yaml` is the only hosted-documentation
configuration. It points Read the Docs to `docs/conf.py`, pins the build
operating system and Python minor version, installs the reviewed Documentation
requirements, and treats every Sphinx warning as an error.

Repository configuration cannot create or connect the external project. A
maintainer must:

1. install or authorize the Read the Docs GitHub App;
2. import this repository as the `deapack` project;
3. keep the configuration-file path at `.readthedocs.yaml`;
4. set `main` as the default branch; and
5. enable pull-request builds if preview builds are wanted.

The repository contains other project material, but Read the Docs does not
need a documentation-only repository. The root configuration explicitly
selects `docs/conf.py`, so only the package Documentation becomes the hosted
site.

## Versions

Publish `latest` from `main`. For stable software releases, activate the
matching semantic-version tag and let `stable` resolve to the highest current
non-prerelease version. Hosted Documentation follows the software version
because its calls, fields, and behavior are version-dependent.

## Verification

Read the Docs supplies versioned hosting and optional pull-request previews.
GitHub Actions is an independent verification lane for the same Documentation
source. A hosted build does not replace the strict local or CI build, and a
Documentation workflow should not depend on unrelated publication artifacts.

Before an archival software release, generate and test a fully pinned
Documentation lock for reproducible historical builds. Do not hand-maintain an
incomplete list of transitive versions.
