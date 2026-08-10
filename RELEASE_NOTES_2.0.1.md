# Release Notes — DEAPack 2.0.1

DEAPack 2.0.1 is a focused compatibility and release-safety update to the
stable 2.x API.

## Installation

```bash
python -m pip install --upgrade "DEAPack==2.0.1"
```

DEAPack supports CPython 3.10, 3.11, 3.12, and 3.13. Existing 2.0 code does
not require an API migration.

## Fixed

- Restored top-level imports on Python 3.11 by constructing
  `DatasetInfo` mapping defaults per instance before freezing them as
  read-only mappings.
- Replaced the `datetime.UTC` benchmark spelling introduced in Python 3.11
  with `timezone.utc`, restoring benchmark execution on Python 3.10.
- Raised the SciPy floor to 1.15. Earlier SciPy releases can incorrectly have
  HiGHS presolve classify feasible FRH/FCH mixed-integer programmes as
  infeasible; the affected fixed nesting cases pass from SciPy 1.15 onward.
- Made audit-bundle CSV output quote every field so embedded carriage returns
  and line feeds remain one spreadsheet-safe cell on every supported Python
  version.
- Stopped the default `EnvironmentalDDF` configuration and the explicit
  `BadOutputDisposability.WEAK` enum from warning about their own supported
  behavior. The legacy string spelling `disposability="weak"` still emits its
  compatibility warning.
- Updated visualization regressions to use the current licensed
  `sbm_slack_contrast` teaching fixture and the current Documentation
  navigation.

## Verification metadata

- Aligned the public method catalog's `verification` labels with the
  maintained machine registry.
- Replaced obsolete published-table claims with claim-scoped analytical or
  independent cross-implementation checks. These corrections change evidence
  metadata, not estimator availability or numerical method semantics.

## Release validation

The production PyPI workflow now installs and smoke-tests the same built wheel
on CPython 3.10, 3.11, 3.12, and 3.13 before publication. The smoke test covers
the documented top-level `BCCInput`, `DEAData`, and `load_dataset` import and a
fitted model result.

See the maintained [Documentation](https://deapack.readthedocs.io/) for the
public API and usage guidance.
