# DEAPack and ProdPack legacy audit

This audit records what the two prototype packages contribute to DEAPack 2.0.
They are sources of research intent, terminology, workflows, and continuity
data. They are not the specification for the new numerical kernel.

## Audited sources

- the historical `DEAPack/` source at base commit
  `e2cb37f509496f130ebe0a4f51caf5805839e7c1`, dated 2024-08-24 and retained in
  Git history rather than the current 2.x tree;
- `daopingw/ProdPack` at commit
  `f4763f810d616851bbe0deb5f8f66a7b869fd773`, dated 2024-08-24;
- the provincial capital, labour, energy, output, and carbon-dioxide panel
  distributed with the historical DEAPack.

The ProdPack audit covered its public example and the complete `ProdNP`
implementation. A future compatibility release must repeat the audit against
the exact published package artifacts, not assume that the repository and
package index contain identical files.

## Ideas that should survive

The prototypes contain several sound architectural instincts:

1. use a directional improvement programme to reuse compatible static and
   environmental distance tasks;
2. treat contemporaneous, global, sequential, window, and biennial comparison
   populations as explicit productivity choices;
3. return productivity change together with operating-efficiency and
   best-practice-opportunity components;
4. allow desirable and undesirable outcomes in the same empirical workflow;
5. preserve knowledge of the provincial panel as a continuity and migration
   lead, subject to a separate provenance and rights review before any public
   data reuse.

DEAPack 2.0 generalizes those ideas. Directional distance is an important
performance compiler, but it no longer defines the class hierarchy or stand
in for every technology, measure, and productivity identity.

## Migration map

| Prototype concept | DEAPack 2.0 destination |
|---|---|
| mutable `DMUs`, `x_vars`, `y_vars`, `b_vars`, and `time` attributes | validated immutable `DEAData` with named roles, identifiers, periods, and period order |
| `g_x`, `g_y`, and `g_b` DataFrames | named, global, or observation-specific direction specifications with stable parameter fingerprints |
| `return_to_scale` string | typed technology specification |
| `CCR` and misspelled `BBC` subclasses | retain `CCR`/`BCC` as RTS specializations over one radial engine; migrate `BBC` to normative `BCC` because 2.0 exposes no `BBC` alias; use the separate I/O preset constructors when a complete classic recipe is intended |
| `radial` boolean | an explicit radial, directional, additive, SBM, or other performance criterion |
| a bad-output equality inside generic DDF | a source-qualified environmental technology with its disposability and joint-production assumptions recorded |
| `ref_type` and `window` | reusable `ReferenceSpec`, independent of the fitted measure |
| `ProdNP(index_type=...)` | distinct, source-qualified Malmquist, Luenberger, environmental, global, biennial, and later productivity operators |
| `prod_ch`, `eff_ch`, and `te_ch` mutable series | identifier-aligned result tables with explicit native direction, component identity, benchmark vintage, and diagnostics |
| optional multiprocessing over PuLP objects | sparse compiled tasks, a zero-configuration HiGHS backend, and parallelism only after serialization and performance validation |

## Behaviors that are not compatibility requirements

Some prototype behavior changes the estimand or makes results difficult to
audit and therefore must not be preserved silently:

- constructing a separate pandas/PuLP expression graph for every observation;
- matching transitions by row position or by arithmetic such as
  `period - 1` rather than by DMU identifier and declared period order;
- treating one available one-sided productivity ratio as a fallback for a
  missing two-sided geometric or arithmetic index;
- transforming every distance with one generic efficiency formula;
- calling one bad-output equality universal weak disposability;
- collapsing radial and variable-specific measures behind a boolean;
- returning objective values without solver status, feasibility, reference
  membership, peers, targets, residuals, or the expanded study specification.

Where a historical numerical value remains theoretically valid, a regression
test may preserve it. Where the old and new values differ because the new
implementation corrects a sign, score transformation, panel match, reference
set, infeasibility rule, or production assumption, the release supplies a
migration explanation rather than a compatibility switch that recreates an
unlabeled result.

## Continuity data

The historical provincial panel is useful for a full applied case because it
contains multiple inputs, one desirable output, carbon emissions, named
regions, and repeated years. Before public reuse it needs:

- a source and license record for every variable;
- units, price basis, deflators, and any transformations;
- a complete observation-key and missing-value audit;
- a statement of the production account and comparison population;
- versioned raw and analysis-ready files.

Until that provenance is complete, synthetic theory laboratories remain the
release tests. The provincial panel remains only a migration question in this
audit, not a releasable continuity dataset or an unquestioned empirical
benchmark.

### RC1 disposition of the historical source tree

The base commit contained `DEAPack/data/example_data.csv`, with audit identity
`legacy_provincial_panel`, alongside the uppercase 0.1.x runtime. Neither the
CSV nor the old runtime is retained in the current 2.x tree. The current
package uses only `src/deapack`, and the historical data is not returned by
`list_datasets()` or exposed through a renamed alias.

The former panel's source, variable-level construction chain, and
redistribution license were not established for this release, so removing it
from the current public tree is the fail-closed disposition. The old source
remains recoverable from Git history for audit and migration research. A later
version may introduce an empirical panel only after an approved source and
license record, or use a genuinely project-created teaching panel under
separate provenance.
