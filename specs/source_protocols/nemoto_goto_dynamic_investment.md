# Nemoto--Goto dynamic investment efficiency: deferred release protocol

## Readiness record

| Field | State |
|---|---|
| Candidate identifier | `dynamic.investment.nemoto_goto` |
| Source status | `defining_articles_identified_full_text_not_obtained` |
| Implementation status | `none` |
| Equation-freeze status | `economic_lineage_only` |
| Numerical-oracle status | `not_located` |
| Release disposition | `deferred_to_next_version` |
| Public API | none |
| Book placement | conceptual contrast inside the existing dynamic chapter only |
| Last access audit | 2026-08-02 |

This protocol prevents the economics of quasi-fixed capital adjustment from
being reconstructed by analogy with Dynamic SBM. The route is important to
the dynamic-efficiency literature, but its current evidence supports only a
conceptual boundary. It does not support executable equations, a public
estimator, or a numerical book recipe.

## 1. Defining sources and access boundary

The defining sources are:

- Jiro Nemoto and Mika Goto (1999), “Dynamic Data Envelopment Analysis:
  Modeling Intertemporal Behavior of a Firm in the Presence of Productive
  Inefficiencies,” *Economics Letters*.
  [DOI](https://doi.org/10.1016/S0165-1765(99)00070-1).
- Jiro Nemoto and Mika Goto (2003), “Measurement of Dynamic Efficiency in
  Production: An Application of Data Envelopment Analysis to Japanese
  Electric Utilities,” *Journal of Productivity Analysis*.
  [DOI](https://doi.org/10.1023/A:1022805500570).

The official publisher pages expose bibliographic metadata and abstracts but
not the complete articles in the audited environment. Nagoya University's
Economic Research Center catalogue identifies the 1999 discussion-paper
series entry but supplies no corresponding downloadable paper. An
author-upload record for the 2003 article was located, but direct file access
returned an authorization failure. No complete, legally accessible copy was
therefore page-frozen.

The current audit cannot verify the full technology, optimization programme,
normalizations, boundary conditions, or numerical application. Publisher
metadata and abstracts are not an equation source.

## 2. Economic claim that is currently supported

The accessible primary metadata supports a bounded distinction. A
quasi-fixed productive asset cannot be moved costlessly to its desired level
within one period. Management allocates current resources between producing
current services and maintaining or changing future capacity. Ending capital
is consequently part of the current production account and a condition on
later production. Adjustment costs and intertemporal substitution make the
chosen investment path economically relevant.

That question is not a parameterization of Tone--Tsutsui Dynamic SBM.
Dynamic SBM links periods with typed carry-over identities and values
non-radial input, output, and carry-over slacks. The Nemoto--Goto lineage asks
whether variable-input, investment, and capital paths satisfy a dynamic
production or cost account in which changing quasi-fixed capacity is itself
costly. Changing a Dynamic SBM direction, period weight, or carry-over label
does not create investment costs, a capital transition law, shadow values,
Euler conditions, or a terminal-value policy.

The active book may explain this distinction because it protects economic
interpretation. It must not display a Nemoto--Goto programme or call the
package's carry-over estimator an implementation of this route.

## 3. Items not yet source-frozen

Implementation is blocked until the defining texts settle all of the
following:

1. the exact intertemporal production possibility set, envelopment
   constraints, returns-to-scale restrictions, and disposability assumptions;
2. the roles and timing of output, variable inputs, investment, and
   quasi-fixed capital;
3. the stock-transition identity, including depreciation and the distinction
   between gross and net investment;
4. the form and units of adjustment costs and whether they enter the
   technology, the economic objective, or both;
5. the information set, discount timing, initial capital, and terminal-stock
   or terminal-value condition;
6. the definitions and normalizations of overall, static, and purely dynamic
   inefficiency, including their direction and admissible range;
7. the required price, cost, or shadow-value information and the conditions
   under which a linear rather than nonlinear solve is valid;
8. zero, irreversibility, infeasibility, degeneracy, and nonunique-path rules;
   and
9. application data or a complete numerical table from which every claimed
   account can be recomputed independently.

Neither a later review nor an independently plausible capital-accumulation LP
can fill these source-specific gaps.

## 4. Gate for a later version

Reopen `dynamic.investment.nemoto_goto` only after all of the following are
available:

1. authorized complete copies of the 1999 and 2003 articles;
2. page-level transcription and independent review of the production,
   transition, adjustment-cost, objective, and efficiency equations;
3. a frozen source profile covering timing, scale, disposal, discounting,
   information, initial and terminal conditions, and failure behavior;
4. a separately implemented source-form oracle and, where the source supplies
   sufficient information, reproduction of the Japanese electric-utility
   account;
5. tests proving that the implementation is not a Dynamic SBM alias, a static
   quasi-fixed-input model, physical capacity utilization, or a repeated
   period cost score; and
6. reviewed economic-language Documentation and one case that makes the
   investment-versus-current-production tradeoff auditable.

Until that gate closes, the release disposition is
`deferred_to_next_version`; there is no public API or executable book recipe.
