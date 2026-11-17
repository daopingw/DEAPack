(share-a-result-without-losing-its-meaning)=
# Saving and sharing results

A short report is useful for reading and sharing a fitted analysis. A complete
export is useful when another analyst needs all the result tables. Neither
requires fitting the model again.

Start with `result` from the {doc}`../getting-started/quickstart`, or from your
own fitted model. Run the following two examples in the same session. The
later panel example requires a separate panel result, as explained there.

## View a short report

```python
brief = result.report()
brief
```

In a notebook, the final expression displays a compact HTML report. The
report identifies the fitted method and study settings when they were
declared, uses the result's registered performance semantics, and reports
solver coverage separately from performance. It does not turn a failed solve
into an inefficient observation.

The reading table is limited to 24 rows. Use the complete export below when
you need every observation rather than a compact overview.

(save-one-self-contained-file)=
## Save an HTML report

The brief contains its own styling and has no JavaScript or external asset
dependency:

```python
brief.save("bcc-result-brief.html")
```

Open the saved file in a browser, or send it to a colleague. This saves a
local file; it does not upload or publish anything online.

<details>
<summary>Technical details: HTML output and embedding</summary>

`save()` accepts `.html` and `.htm` paths only. It returns the path after the
file has been written. The document is encoded before the destination is
replaced, and the replacement is atomic on the local filesystem; an encoding
failure therefore does not first empty an existing report. Preparing a report
does not write anything:

```python
html = brief.to_html()                    # complete HTML document
fragment = brief.to_html(full_document=False)  # embeddable fragment
```

All labels and result values are escaped before insertion into the document.
This matters when DMU identifiers or metadata originated outside the
application.

</details>

(select-a-declared-measure-period-or-organization)=
## Select a measure, period, or organization

The default report selects the model's declared performance measure. You can
request another supported measure explicitly; for example, with a BCC result:

```python
brief = result.report(metric="efficiency")
```

For panel results, select a period, optionally followed by one organization.
Here `panel_result` means a fitted panel analysis containing 2024 and
`"Hospital A"`, not the Quickstart's cross-sectional result. Replace those
selectors with values from your study:

```python
period_brief = panel_result.report(period=2024)
hospital_brief = panel_result.report(period=2024, dmu_id="Hospital A")
```

An unknown selection or a selection with no valid performance value raises an
error instead of producing a misleading report. The detailed selection rules
are below.

<details>
<summary>Technical details: measure validity and panel coverage</summary>

An explicit metric must have declared result semantics. DEAPack does not guess
whether an arbitrary numerical column is a score, whether larger or smaller
is better, or which value denotes efficiency. It also respects row-level
validity evidence supplied by the fitted result. When `score_valid` or
`score_status` says that a finite numerical account is undefined, that row is
excluded from substantive ordering. It appears in the diagnostic part of a
brief only when the same selected report also contains at least one valid,
finite, optimal substantive row. An explicit period, DMU, or metric selection
that leaves only undefined values raises `ReportNotAvailableError` instead of
presenting a diagnostic-only brief. `invalid_metric_count` records how many
undefined rows accompany an available report.

“Optimal” here is measure-specific. For a classic radial result, a certified
phase-one score may remain reportable even when the secondary target
completion has another final status. The report keeps that completion status
in its solver-coverage audit while requiring `primary_solver_status="optimal"`
and `score_valid=True` for the performance table.

Unlike the performance plot, a brief is not limited to four periods. It can
summarize the complete selected panel and samples its 24 displayed finite
rows across periods so a later period does not disappear merely because
earlier periods filled the row budget. Missing and non-finite metric values,
finite non-optimal values, and finite-but-undefined values remain separate
audit categories.

Unknown periods, DMUs, report kinds, themes, details, and undeclared metrics
fail with `ReportNotAvailableError`. Available values are included in
selection errors where that is safe and useful.

</details>

## What the brief deliberately does not claim

The first reporting contract is descriptive. It does not infer:

- a causal responsibility for an efficiency shortfall;
- the economic desirability of an input, output, or intermediate flow;
- a unique target or peer plan when the fitted programme has alternative
  optima;
- component, link, or process attribution absent from the method's public
  result contract; or
- implementation feasibility outside the declared production model.

Use the result's tables and metadata for the full audit:

```python
result.summary()
result.slacks
result.targets
result.intensities
result.diagnostics
result.metadata
```

The brief is therefore a reliable entry point to the result, not a replacement
for the empirical study record.

(publish-an-illustrated-result-in-one-call)=
## Save a package with figures

When readers need both an attractive entry point and the evidence behind it,
create a publication bundle directly from the fitted result:

```python
publication_path = result.publish("bcc-result-publication.zip")
```

Despite the method name, `publish()` creates a local ZIP file; it does not
upload the study. Extract it, then open `index.html` to read the report with
its figures. The archive also includes the complete result tables.

Install plotting support if you have not already done so:

```bash
python -m pip install 'DEAPack[viz]'
```

To include applicable plots for one selected organization:

```python
focused_path = result.publish("bcc-result-publication-E.zip", dmu_id="E")
```

Only plots supported by the fitted result are included. Plots needing a
period, organization, or carry-over choice are not silently guessed; supply
those choices when they are part of your study. The archive records why a
plot was included or omitted.

<details>
<summary>Technical details: publication contents, selection, and safe export</summary>

That single call creates an atomic ZIP containing:

- `index.html`, a styled, JavaScript-free reading page;
- one reusable SVG for each safely selectable declared plot;
- `manifest.json`, which records every registered plot as included or skipped,
  the reason for that decision, selectors, and SHA-256 hashes;
- `README.txt`; and
- `audit/result-audit.zip`, the complete ordinary audit bundle described in
  the next section.

The default is deliberately conservative. DEAPack uses
`result.available_plots()` as the semantic authority and includes only views
that need no unreported analyst choice. It does not silently choose an
organization, period, or carry-over.

For an applicable panel or dynamic result, the same API accepts `period=` and
`variable=`. `metric=` selects a registered performance measure; it does not
change the independent quantity semantics of frontier, process, trajectory,
or operating-plan figures. Unknown result selectors, undeclared metrics, and
selectors with no declared plot consumer fail with
`PublicationBundleNotAvailableError` rather than producing a misleading
chart. If a known selected observation does not pass one plot's own
certificate, the rest of the publication can still be written and that plot's
manifest record gives the precise omission reason. The manifest also makes
missing analyst choices inspectable, for example
`reason="requires_explicit_dmu_id"`.

Publication is a zero-solve reporting operation. It reuses the result tables,
the existing audit exporter, and the plotting declarations; it never refits a
model. This claim is deliberately scoped to the exact built-in `DEAResult`
type. `publish` rejects subclasses and duck-typed extension results before
calling their methods, because DEAPack cannot verify whether a third-party
`available_plots()` or `plot()` hook solves another model. The manifest records
that trust boundary together with the scoped zero-solve declaration. SVG
generation uses deterministic identifiers and omits generated dates, figures
are not displayed, and every created figure is closed. Like the brief, all
entry-page text is escaped. Archive member names are generated from the
controlled plot registry and checked against absolute paths and traversal.
Writing is atomic, so a failed render does not damage an existing destination.

The figures remain descriptive. They show performance against the declared
technology and selected fitted account. They do not establish why a shortfall
occurred, which operating change managers prefer, whether a displayed selected
optimum is unique, or whether its implementation is feasible outside the
model.

</details>

(hand-off-the-complete-audit-record-in-one-file)=
## Export all result tables

The brief is intentionally compact: its reading table is bounded at 24 rows.
When another analyst needs the complete fitted record, create a deterministic
audit bundle instead:

```python
bundle_path = result.export_bundle("bcc-result-audit.zip")
```

Use `export_bundle` when the recipient primarily needs a compact forensic
record or when Matplotlib is not installed. It exposes the tables directly and
imports no plotting backend. Use `publish` when the recipient needs an
illustrated reading layer as well: the publication ZIP is larger, but embeds
that same complete audit bundle unchanged rather than replacing it with
figures. In both cases the numerical result is fitted only once.

This is also the appropriate export for investigating a failed fit: it keeps
the available diagnostics without presenting failed values as performance.

<details>
<summary>Technical details: archive contents and reproducibility</summary>

The archive contains:

- `report.html`, the same self-contained human-readable brief, or a safe audit
  cover when no substantive measure is reportable;
- `metadata.json`, preserving the fitted method and study assumptions;
- `manifest.json`, with table schemas, file sizes, SHA-256 hashes, method and
  solver identity, and the exporter-scoped zero-additional-solve declaration;
  and
- `summary` plus every non-empty public result table under `tables/`, in both
  JSON Lines and CSV.

JSONL preserves string values exactly and gives supported structured values a
canonical JSON representation. The CSV copy is intended for ordinary table
tools. It represents structured cells as canonical JSON text and prefixes
formula-like cell values and column headings with an apostrophe. The protected
prefixes are `=`, `+`, `-`, `@`, tab, carriage return, and line feed. The
manifest retains the original headings alongside the spreadsheet-safe CSV
headings. Missing values are `null` in JSONL and empty in CSV; positive and
negative infinity use an explicit tagged object in JSONL rather than invalid
JSON tokens. Ordinary numeric CSV columns retain the text `inf` or `-inf`;
structured CSV cells use the same canonical tagged JSON text as their JSONL
account.

Export is atomic, imports no plotting backend, performs no optimization, and
does not mutate the result. Tables are serialized one at a time; CSV is written
in bounded row chunks and JSONL is streamed record by record, so the exporter
does not keep every serialized table in memory. Re-exporting the same fitted
result under the same DEAPack, Python, pandas, and compression environment
produces the same archive bytes. Byte identity is not promised across changes
to that serialization environment.

The manifest hashes every other archive member but does not hash itself, which
would be self-referential. Those SHA-256 values detect file changes; they do
not authenticate the publisher. A bundle is still a
descriptive record of the declared DEA study: it is neither a causal analysis
nor an implementation order.

A failed or wholly undefined fit can still be handed off for diagnosis. In
that case `report.html` contains only a diagnostic audit view (or a safe cover
if even that view cannot be prepared), while the complete public tables and
metadata remain in the archive; the manifest records
`substantive_brief=false`. The audit view does not promote a failed numerical
value into a performance result.

</details>

(stable-first-version-boundary)=
## Advanced interface and extension reference

<details>
<summary>Reporting defaults, supported outputs, and third-party results</summary>

Version 1 of the reporting interface has one kind, detail level, and theme:

```python
result.report(kind="brief", detail="brief", theme="deapack")
```

This deliberately small contract keeps installation simple and output
deterministic. It uses pandas and the Python standard library already required
by DEAPack. Plotting remains a separate optional layer; creating or saving a
brief does not import Matplotlib.

The audit bundle retains that backend-independent boundary. The optional
publication bundle composes the same audit record with deterministic SVG
figures; it does not turn the HTML page into a paginated publication format.
LaTeX reports, Excel workbooks, paginated PDF reports, interactive dashboards,
and geospatial maps remain next-version output backends.

The top-level `deapack.reporting.export_result_bundle` also accepts an
extension result that implements the complete version-one bundle source
contract: `summary(copy=True)`, mapping-like metadata, and all ten named public
table attributes (empty DataFrames are valid). These accessors must expose an
already-fitted, side-effect-free snapshot. DEAPack never calls an extension's
`report()` method; it builds the HTML view internally from a detached summary
and metadata. Accordingly, `additional_solver_calls=0` describes the DEAPack
exporter itself, not arbitrary code hidden inside a third-party property. Do
not mutate result tables concurrently while an export is running. This
extension protocol applies to `export_result_bundle`, not `publish_result`;
illustrated publication remains restricted to the exact built-in `DEAResult`.

</details>
