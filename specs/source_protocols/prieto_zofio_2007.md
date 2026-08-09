# Prieto--Zofío (2007) input--output network DEA

## Readiness record

| Field | State |
|---|---|
| Candidate identifier | `network.input_output.prieto_zofio_2007` |
| Source status | `source_not_frozen` |
| Implementation status | `blocked_on_primary_source` |
| Numerical-oracle status | `not_located` |
| Release disposition | `deferred_to_next_version` |
| Public API | none |
| Registry status | do not register |
| Last access audit | 2026-07-30 |

This protocol is the controlling readiness record for Prieto--Zofío (2007).
Until the primary article is available at equation and table level, its three
status tokens above supersede the broader provisional wording in
[`NETWORK_DYNAMIC.md`](../reviews/NETWORK_DYNAMIC.md). That review remains
useful for the family comparison; it must not be read as evidence that the
Prieto--Zofío programme is source-frozen or executable.

The current release will not continue source retrieval or implementation for
this candidate. A future version may reopen the freeze gate only after the
complete primary article has been obtained through authorized access.

No equation is reconstructed in this record. Similarity to a familiar
activity-analysis or network DEA programme is not sufficient evidence for an
implementation.

## 1. Defining source and access boundary

**Primary source**

Angel M. Prieto and José L. Zofío (2007), “Network DEA efficiency in
input--output models: With an application to OECD countries,” *European
Journal of Operational Research*, 178(1), 292--304.
[DOI](https://doi.org/10.1016/j.ejor.2006.01.015);
[publisher record](https://www.sciencedirect.com/science/article/pii/S0377221706000440);
[Erasmus University metadata record](https://repub.eur.nl/pub/131052).

The publisher preview and repository metadata expose the abstract,
introduction, bibliographic record, and selected section snippets. They do not
provide a stable, complete article text or PDF in the audited environment.
Repository and open-access discovery checks did not locate an open primary
copy. The publisher download is subscription-restricted, and an automated
HTML retrieval returned an access shell rather than the article body.

Consequently, the audit could confirm the economic purpose and broad account
structure, but it could not verify every programme, constraint, score
transformation, table, or reported value. Publisher snippets are discovery
evidence, not a substitute for reading the complete primary source.

## 2. Economic problem confirmed from the primary abstract and introduction

The unit being assessed is a country, region, or local economy represented by
an input--output system. Its sectors are interdependent production units, not
an acyclic sequence of departments. Each sector uses primary resources and
goods supplied by sectors to produce goods used by other sectors and to
satisfy final demand.

The managerial and economic question is:

> Relative to technologies observed in comparable economies, how much better
> could an economy use its capital and labour endowments, coordinate
> intermediate production and use across sectors, and satisfy final demand?

The paper therefore joins three decisions that black-box DEA separates:

- which observed sector processes constitute best practice;
- how national primary resources are allocated across sectors; and
- how intersectoral production and use support final demand.

The primary introduction describes the input--output production structure as
a linear Leontief transformation exhibiting constant returns to scale. It
also says that the comparison may use an individual economy or combinations
of economies as benchmarks. These statements establish the economic lineage,
but not the exact convexity, intensity, normalization, or returns-to-scale
constraints of every DEA programme in the paper.

The analysed open economy does not freely redesign trade. Observed net exports
are held exogenous so that the reported opportunity concerns domestic
resource use and access to best-practice technologies, excluding gains from
an optimized trade pattern.

## 3. Account roles confirmed at concept level

| Account | Confirmed economic role | Source-freeze caveat |
|---|---|---|
| Capital and labour | Primary inputs or national endowments entering sector production | Exact aggregation and programme bounds remain unverified |
| Intermediate flows | Goods produced by one sector and used in sector production | Exact balance relation, target variables, and disposability remain unverified |
| Final demand | External use that the economy seeks to satisfy or expand | Exact expansion objective and score convention remain unverified |
| Net exports | Observed transactions with the rest of the world, treated as exogenous in the analysed model | Sign convention and precise balance placement remain unverified |
| Sector technology | Best-practice production process formed from comparable observed economies | Intensity indexing, mixing restrictions, and normalization remain unverified |

Input--output tables can include self-use, reciprocal trade among sectors,
and signed adjustment or trade accounts. These are accounting semantics, not
ordinary “input,” “link,” and “output” column labels.

## 4. What is deliberately not frozen

The following items require the complete primary article. They must not be
inferred from the abstract, later papers, or a generic network LP:

1. the exact primal programme or programmes and every variable domain;
2. whether sector accounts use equality, at-least, or at-most balances;
3. whether gross sector output is explicit, derived, or only implicit;
4. the precise treatment of intermediate production, use, surplus, and
   disposal;
5. the placement and sign convention of imports, exports, and net exports;
6. the exact final-demand expansion or primary-input contraction objective;
7. the native efficiency score, its reciprocal if any, and the package-facing
   higher-is-better transformation;
8. the reference-set structure, including whether intensities are sector
   specific and how technologies from different economies may be combined;
9. all scale, convexity, and normalization restrictions;
10. sector-level versus economy-level results and any valid decomposition;
11. target reconstruction, alternate-optimum policy, and balance residuals;
12. the exact empirical sample, year, price basis, sector aggregation, input
    values, output values, and published scores.

The implementation remains `blocked_on_primary_source` until these items are
resolved. No source leaf, solver preset, registry record, catalog entry, or
public class should be created before that gate is passed.

## 5. Non-equivalence boundary

“Network DEA” is a discovery label, not an alias. The Prieto--Zofío economic
system must remain distinct from the following implemented or reviewed
families:

- **Lewis--Sexton sequential DEA:** solves node programmes and propagates
  hypothetical quantities through an acyclic organizational order.
  Prieto--Zofío coordinates a cross-sector economy jointly; feedback and
  reciprocal sector use are economically normal.
- **Kao--Hwang relational DEA:** decomposes an overall multiplier-ratio
  account through shared values for intermediate products. Prieto--Zofío is
  an input--output activity and resource-allocation system, not that ratio
  identity.
- **Cook--Zhu--Bi--Yang additive DEA:** values or aggregates process
  performance under a particular additive construction. That objective is
  not evidence for the input--output programme.
- **Tone--Tsutsui network SBM:** normalizes slacks to obtain system and
  divisional efficiency. Nothing currently establishes that Prieto--Zofío
  uses this loss function or its divisional score contract.
- **Färe--Grosskopf network activity analysis:** supplies an important
  technology lineage, but Prieto--Zofío adds national input--output accounts,
  sector resource allocation, final demand, and fixed foreign-trade
  treatment. It is a source-qualified relative, not an exact alias.

Shared sparse-matrix machinery does not establish equivalence of economic
technology, objective, targets, or results.

## 6. Structural audit of the current DAG network layer

The current general network surface is intentionally designed for an acyclic
process graph:

- [`network/data.py`](../../src/deapack/network/data.py) stores one flat
  DMU-by-variable matrix and its nonnegative-data check rejects signed
  quantities;
- [`network/specs.py`](../../src/deapack/network/specs.py) prohibits
  self-links, assigns a variable to at most one link, and requires a linked
  variable to be one source output and one target input;
- [`network/_layout.py`](../../src/deapack/network/_layout.py) rejects cycles
  and requires a linked variable to occur exactly twice;
- [`network/_general_additive.py`](../../src/deapack/network/_general_additive.py)
  compiles a particular additive/multiplier network account, not the
  Prieto--Zofío programme.

Those invariants are useful for the models they support. They are
structurally incompatible with a dense input--output account, where:

- a sector can consume some of its own output;
- sectors can supply one another in both directions;
- one commodity output can be allocated among many using sectors and final
  demand;
- primary-resource totals may be shared national constraints;
- gross output and total use require sector or commodity accounting
  identities; and
- net exports or statistical adjustments may be signed.

Flattening every sector-to-sector flow into ordinary columns would hide the
supplier/user axes and would not create conservation, gross-output, or trade
semantics. The current `NetworkData` and `NetworkSpec` must therefore not be
used as the source model merely because a sufficiently wide table can be
constructed.

The generic solver-neutral sparse LP and HiGHS layers remain potentially
reusable. That is an implementation-layer observation only; it says nothing
about the still-unverified programme.

## 7. Provisional architecture after source freeze

This section is a design hypothesis, **not** a public API commitment.

### 7.1 Input--output-specific data

An `InputOutputNetworkData`-type object will probably need labelled arrays
whose axes preserve the national accounts:

```text
intermediate[observation, supplying_sector, using_sector]
primary_inputs[observation, factor, using_sector]
final_demand[observation, commodity, demand_category]
net_exports[observation, commodity]
```

It may also need observed gross output for validation, sector/factor/category
labels, time, currency or physical units, valuation basis, and price-year
metadata. Signed accounts must be admitted only where the source and account
schema assign them a signed role.

### 7.2 Source-qualified specification

An input--output-specific spec should name, rather than infer:

- the source preset and score objective;
- sector and commodity correspondence;
- primary-resource control;
- intermediate and gross-output balance rules;
- final-demand treatment;
- foreign-trade treatment;
- returns to scale and technology mixing;
- target and alternate-optimum policy; and
- tolerance for observed accounting residuals.

Fields for which the paper has not yet supplied evidence should stay locked,
not default to convenient generic DEA settings.

### 7.3 Dedicated compiler

A dedicated sparse compiler should map the labelled accounts to the verified
source programme and then emit the existing solver-neutral linear-program
representation. It should not be routed through the DAG layout compiler.
Available secondary evidence suggests a continuous piecewise-linear activity
model; there is currently no evidence that a mixed-integer formulation is
part of the source method.

## 8. Provisional result and failure contract

Once the primary equations are frozen, the result should at minimum make
accounting feasibility inspectable. Candidate fields are:

- solver status, message, raw objective, and source-defined reported score;
- final-demand, primary-resource, intermediate-flow, gross-output, and
  fixed-net-export targets where the source programme defines them;
- sector-by-benchmark intensities and benchmark membership;
- observed-account and optimized-account balance residuals;
- solver primal/dual residuals and tolerance metadata; and
- a flag or diagnostic for non-unique targets.

Sector efficiencies or a decomposition must be returned only if the primary
source defines them. They may not be reverse-engineered from a system score.

The future implementation should fail closed for:

- incompatible sector or commodity classifications;
- inconsistent units, valuations, years, or price bases;
- invalid tensor dimensions or missing account labels;
- observed accounts outside the documented balance tolerance;
- unsupported signed quantities or ambiguous import/export signs;
- a zero or invalid improvement base;
- infeasible or unbounded programmes, including cases induced by fixed trade;
- solver limits, numerical failure, or memory-budget limits; and
- unresolved alternate target plans when a unique operational plan is
  requested.

## 9. Numerical-oracle acquisition checklist

The publisher data snippet identifies a source-data universe of ten OECD
country tables, 35 sector codes, 1970--1990, at current and constant prices.
That is not yet the implemented empirical sample.

A later source reports that the 2007 application used four aggregated sectors
(agriculture, manufacturing, construction, and services) for five OECD
countries. This is a useful retrieval lead, not an oracle: it does not reveal
the five countries, observation year, price basis, aggregation bridge, input
table, or reported results.

To change `oracle_status` from `not_located`, capture from the primary article:

1. the selected countries, year, and current/constant-price choice;
2. the 35-code-to-four-sector aggregation, including treatment of
   classifications that do not map cleanly;
3. the exact capital, labour, intermediate, final-demand, and trade data used;
4. every table containing efficiency, target, benchmark, or decomposition
   results;
5. the score direction, display rounding, and any normalization; and
6. at least one hand-reconstructable economy/sector case with enough digits
   to distinguish alternative formulations.

The repository oracle should preserve source values separately from
machine-readable fixtures and record every transcription or rounding
decision.

## 10. Freeze gate

Promotion is allowed only when one auditable change set contains:

- a legally accessible complete primary copy or a page-level research note
  made from authorized access;
- equation-by-equation transcription with page and equation references;
- a variable/constraint table connected to the economic accounts above;
- a verified native-score and package-score mapping;
- at least one published numerical oracle or a documented reason none exists,
  plus independent analytic/property tests;
- explicit comparison with the DAG, sequential, relational, additive, and SBM
  neighbours;
- input--output-specific data, spec, compiler, result, and failure contracts;
  and
- synchronized registry, package documentation, and book treatment.

Until all applicable items pass, retain:

```text
source_status = source_not_frozen
implementation_status = blocked_on_primary_source
oracle_status = not_located
release_disposition = deferred_to_next_version
```

## 11. Secondary discovery and critique ledger

Secondary sources can identify questions to check in the original paper; they
cannot supply missing source equations.

- Tone and Tsutsui (2009), “Network DEA: A slacks-based measure approach,”
  describes the earlier input--output line as optimizing primary inputs,
  intermediates, and final-demand products.
  [DOI](https://doi.org/10.1016/j.ejor.2008.05.027).
- Färe, Grosskopf, and Pasurka (2026), “Productivity change with bad outputs:
  Data envelopment analysis aggregate joint production vs. data envelopment
  analysis input--output models,” describes the earlier technology as
  sector-specific piecewise-linear combinations and reports the
  four-sector/five-country operationalization. It extends the model to
  non-freely disposable bad output; that extension is not part of the 2007
  source.
  [DOI](https://doi.org/10.1016/j.ejor.2025.07.019).
- Wang et al. (2024), “Multi-sector environmental efficiency and
  productivity: A general Leontief optimization method,” criticizes the
  earlier network model for computational burden and for not ensuring an
  optimal gross-input/gross-output balance by sector. This is a later
  critique to test and disclose, not permission to rewrite the original
  technology.
  [Publisher record](https://www.sciencedirect.com/science/article/pii/S0305048324000197).

Any future implementation must distinguish “faithful reproduction of
Prieto--Zofío (2007)” from a DEAPack extension that repairs or changes an
accounting property identified by later work.
