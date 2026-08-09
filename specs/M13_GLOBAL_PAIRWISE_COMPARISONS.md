# M13 fixed-vintage global productivity comparison pairs

## Decision question

When one retrospective production benchmark is held fixed, how did an
organization's productive performance change between two selected dates, and
how much of that change belongs to operating performance versus the distance
between contemporaneous best practice and the common benchmark?

This milestone completes the comparison horizon of two already admitted
mother operators:

- Pastor--Lovell Global Malmquist productivity; and
- Oh's Global Malmquist--Luenberger productivity.

It does not create another productivity-index identity.  The economic account,
technology, directions, decomposition, information vintage, and source names
remain those of the existing operators.

## Source boundary

The controlling source protocols are:

- `source_protocols/pastor_lovell_2005_global_malmquist.md`; and
- `source_protocols/oh_2010_global_malmquist_luenberger.md`.

Both global ratios can compare two dates inside one unchanged full-sample
information vintage.  Their circularity follows because the same observation-
specific common-reference term appears in every ratio and therefore cancels
when compatible comparisons are chained.  Adjacency was a package output
policy, not a mathematical restriction of either source account.

The independent three-period certificates already derive the direct first-to-
last comparison and the adjacent chain without calling a DEAPack production
compiler:

- `oracles/pastor-lovell-2005-global-malmquist-analytical.md`; and
- `oracles/oh-2010-global-malmquist-luenberger-analytical.md`.

Changing the sample, adding a period, changing a global reference member, or
combining results from separately fitted vintages breaks the frozen-information
condition.  The implementation must never present such a splice as a circular
chain.

## Public comparison contract

The two named constructors expose one keyword-only `comparison_pairs`
argument.  Its default remains `"adjacent"`, preserving the existing output.

The admitted forms are:

1. `"adjacent"`: every neighboring pair in declared `period_order`;
2. `"all"`: every forward pair `(period_order[i], period_order[j])` for
   `i < j`; or
3. an explicit non-empty sequence of unique `(base_period,
   comparison_period)` pairs, each ordered forward in the same declared period
   order.

The contract rejects an unknown period, a self-pair, a reverse pair, a
duplicate pair, an empty explicit selection, a malformed pair, or an
unrecognized string.  It does not silently sort, reverse, deduplicate, or infer
period labels.  `unbalanced="drop"` or `"raise"` applies independently to each
selected pair.

Reverse-time ratios remain mathematically recoverable as reciprocals of a
certified forward comparison.  They are not emitted as additional transition
rows because the package's productivity-change convention assigns the first
date the base role and the later date the comparison role.

## Mathematical account

For a selected pair `(r, s)` with `r` earlier than `s`, Pastor--Lovell uses the
same four roles already certified for adjacent output:

$$
d_r^r,\qquad d_s^s,\qquad d_r^G,\qquad d_s^G.
$$

The public multiplicative account remains

$$
GM^{r,s}=\frac{d_s^G}{d_r^G},\qquad
EC_G^{r,s}=\frac{d_s^s}{d_r^r},\qquad
BPC_G^{r,s}
=\frac{d_s^G/d_s^s}{d_r^G/d_r^r},
$$

with `GM = EC_G * BPC_G`.

Oh's account likewise retains only its existing four own/global directional
roles.  With `F_q^R = 1 + D^R(z^q; y^q, b^q)`, it reports

$$
GML^{r,s}=\frac{F_r^G}{F_s^G},\qquad
EC^{r,s}=\frac{F_r^r}{F_s^s},\qquad
BPC^{r,s}=\frac{F_s^s/F_s^G}{F_r^r/F_r^G},
$$

with `GML = EC * BPC`.  No off-diagonal contemporaneous distance is introduced.

Every result row remains keyed by `(dmu_id, base_period,
comparison_period)`.  Summary, diagnostics, and intensity records carry the
same pair.  Atomic release, score certification, peer certification, and
failure fields are unchanged.

## Execution contract

Pair enumeration and mathematical task identity are separate:

- output assembly may request four roles per emitted row;
- each own-period or global appraisal of one observation is solved once and
  cached by evaluated row plus reference identity; and
- reusing one certified appraisal in several pair accounts adds no LP solve.

For a balanced panel with `D` organizations and `P` periods:

- adjacent output has `D(P-1)` rows;
- all-pairs output has `DP(P-1)/2` rows;
- both require at most `2DP` unique own/global distance solves once every
  period participates; and
- all-pairs result, diagnostic, and peer-table materialization is explicitly
  quadratic in `P` even though the solve graph is not.

Metadata must distinguish requested role appearances from unique distance
solves and solver calls.  It must record the comparison policy, selected period
pairs, pair count, emitted transition-row count, fixed global periods and
observations, and the all-pairs output-growth warning.  Existing adjacent
metadata remains readable for backward compatibility.

## Verification gate

The milestone is not complete until tests establish all of the following:

1. default output is exactly equivalent to the pre-M13 adjacent result;
2. explicit first-to-last output reproduces both independent three-period
   analytical certificates;
3. all-pairs output contains the two adjacent pairs and the direct endpoint;
4. `index(0,1) * index(1,2) = index(0,2)` for the headline and both certified
   components within one result vintage;
5. all-pairs and adjacent fits use the same unique solve count on a balanced
   three-or-more-period panel;
6. pair-specific unbalanced `drop` and `raise` behavior is exact and audited;
7. invalid pair declarations fail closed before any optimization call;
8. row-order and coherent-unit invariance are preserved; and
9. source protocols, machine registry, package Documentation, Handbook case,
   benchmarks, changelog, and roadmap state the same boundary.

## Placement and exclusions

The Handbook receives only a short direct-endpoint demonstration inside the
existing productivity routes.  It does not gain another chapter.  Complete
parameter, validation, result-field, and scaling behavior belongs in package
Documentation.

This milestone does not authorize arbitrary pairs for conventional Malmquist,
CFG Malmquist--Luenberger, biennial, sequential, rolling, Hicks--Moorsteen,
Luenberger, dynamic, network, or other productivity operators.  Their reference
systems and comparison identities do not inherit fixed-vintage circularity
from these two global methods.
