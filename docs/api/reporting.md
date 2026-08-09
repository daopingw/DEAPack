# Reporting API

The reporting layer prepares immutable, self-contained views from the unified
`DEAResult` contract. It does not fit models, alter result tables, or infer
undeclared performance semantics.

```{eval-rst}
.. autoclass:: deapack.reporting.ResultReport
   :members:
```

`ResultReport` instances are created only through `DEAResult.report(...)` or
the source-independent builder below. Its public constructor accepts no
prepared HTML, so notebook rendering and file saving retain the escaping
boundary established by the builder.

```{eval-rst}
.. autoclass:: deapack.reporting.ReportNotAvailableError
```

The ordinary entry point is:

```{eval-rst}
.. automethod:: deapack.results.DEAResult.report
```

To create a reader-facing illustrated hand-off and retain the complete audit
record in the same file, publish one deterministic ZIP:

```{eval-rst}
.. automethod:: deapack.results.DEAResult.publish

.. autofunction:: deapack.reporting.publish_result

.. autoclass:: deapack.reporting.PublicationBundleNotAvailableError
```

The publication archive contains `index.html`, reusable SVG files under
`figures/`, `README.txt`, a SHA-256 `manifest.json`, and the complete ordinary
audit archive at `audit/result-audit.zip`. Plot discovery comes exclusively
from `result.available_plots()`. The manifest records every registered plot
as `included` or `skipped` and gives the reason. Performance and other
unambiguous whole-result views are included by default. A process,
variable-improvement, or trajectory view is not silently assigned to an
organization: `dmu_id` must be supplied. A multi-period view that cannot show
the complete panel safely requires `period`; a trajectory with several
carry-overs additionally requires `variable`.

Publication rendering reads the fitted result and performs no optimization.
Matplotlib remains an optional dependency; install `DEAPack[viz]` when using
`publish`. SVG identifiers use a fixed hash salt, generated dates are omitted,
figures are never displayed and are closed after serialization, and ZIP
metadata is fixed for repeatable output in the same runtime environment. The
HTML page presents the figures as descriptive DEA evidence and explicitly
rejects causal, prescriptive, preference, and target-uniqueness claims.

The publication trust boundary is intentionally narrower than the report and
audit extension protocols: `publish_result` accepts only the exact built-in
`deapack.results.DEAResult` type, not a subclass or a duck-typed extension.
Discovery and rendering dispatch through the built-in `DEAResult` methods.
This prevents an extension's `available_plots()` or `plot()` implementation
from hiding optimization or other side effects behind an unconditional
zero-solve claim. The manifest records
`trusted_result_type="deapack.results.DEAResult"`,
`third_party_result_extensions_supported=false`, and scopes
`additional_solver_calls=0` to
`deapack_publication_exporter_on_exact_dearesult`.

For a complete hand-off rather than a compact reading view, export one
deterministic audit archive:

```{eval-rst}
.. automethod:: deapack.results.DEAResult.export_bundle
```

The archive contains `report.html`, `metadata.json`, `manifest.json`, and
every non-empty public result table in JSON Lines and spreadsheet-safe CSV
form. When no substantive brief is reportable, `report.html` contains a
diagnostic audit view (or a safe cover if that view is unavailable) and the
manifest records `substantive_brief=false`; failed or undefined rows remain
available only as diagnostic evidence. The manifest also records row and
column schemas, file sizes, SHA-256 hashes, method
identity, package version, solver label, and the zero-additional-solve
contract scoped to the DEAPack exporter. HTML truncation never truncates the
bundle tables. JSONL preserves external string values exactly and canonically
encodes supported structured values. CSV stores structured cells as canonical
JSON text and prefixes formula-like cell values and column headings with an
apostrophe. The protected prefixes are `=`, `+`, `-`, `@`, tab, carriage
return, and line feed; the manifest retains the original and escaped headings.

CSV is written in bounded row chunks and JSONL is streamed record by record,
so serialized copies of all tables are not held in memory together. The
manifest hashes every other archive member but cannot hash itself; SHA-256
provides an integrity check, not publisher authentication. Archive bytes are
repeatable for the same fitted result under the same DEAPack, Python, pandas,
and compression environment, not across arbitrary runtime-version changes.

```{eval-rst}
.. autofunction:: deapack.reporting.export_result_bundle

.. autoclass:: deapack.reporting.ResultBundleNotAvailableError
```

The compact `report()` output remains HTML. The illustrated `publish()` layer
adds reusable SVG files while preserving the audit bundle as a nested archive;
it does not create a paginated report. LaTeX reports, Excel workbooks,
paginated PDF reports, interactive graphics, and maps are explicitly
next-version output backends.

For extension authors, the source-independent constructor is available as
`deapack.reporting.create_result_report`. Public applications should normally
call `result.report(...)` so the report remains coupled to the result that
supplies its tables and metadata.

```{eval-rst}
.. autofunction:: deapack.reporting.create_result_report
```

An extension result must provide `summary(copy=True)` returning a DataFrame
with unique columns containing all eight required fields: `dmu_id`, `period`,
`score`, `efficiency`, `distance`, `is_efficient`, `solver_status`, and
`model_family`. It must also expose a mapping-like `metadata` attribute.
Candidate measures still require registered `MeasureSpec` semantics. If the
summary contains `score_valid` or `score_status`, the shared validity contract
is applied before a value can enter the substantive report.

For `export_result_bundle`, an extension must additionally expose all ten
named public table attributes: `slacks`, `targets`, `intensities`, `duals`,
`components`, `multipliers`, `links`, `diagnostics`, `appraisals`, and
`history`. Empty DataFrames are valid. Accessors must return an already-fitted,
side-effect-free snapshot and tables must not be mutated concurrently during
export. The exporter calls `summary(copy=True)` once, copies each table before
serializing it, and uses the internal safe report builder rather than calling
an extension's `report()` method. Thus the manifest's zero-solve declaration
is about DEAPack's exporter; Python cannot certify side effects hidden inside
third-party properties.

Those extension contracts do not apply to `publish_result`. An extension can
export its complete audit record with `export_result_bundle` and create plots
under its own explicitly scoped trust statement, but cannot ask DEAPack's
publication exporter to certify those plot hooks as zero-solve.
