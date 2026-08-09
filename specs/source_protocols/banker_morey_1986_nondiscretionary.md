# Banker--Morey (1986) nondiscretionary variables

## Readiness record

| Field | State |
|---|---|
| Candidate identifier | `static.radial.nondiscretionary.banker_morey_1986` |
| Source status | `primary_record_located_full_text_not_obtained` |
| Implementation status | `deferred_source_audit` |
| Equation-freeze status | `not_frozen` |
| Numerical-oracle status | `not_located` |
| Release disposition | `deferred_to_next_version` |
| Public API | none |
| Registry status | do not register |
| Last access audit | 2026-07-30 |

This is the controlling source-gate record for the proposed
Banker--Morey nondiscretionary-variable leaf. The current release must not
implement, register, or document the candidate as executable support.

## 1. Defining source and access boundary

Rajiv D. Banker and Richard C. Morey (1986), “Efficiency Analysis for
Exogenously Fixed Inputs and Outputs,” *Operations Research*, 34(4),
513--521. [DOI](https://doi.org/10.1287/opre.34.4.513);
[INFORMS record](https://pubsonline.informs.org/doi/10.1287/opre.34.4.513);
JSTOR stable identifier `170597`.

The bibliographic and publisher records identify the defining article, but a
complete, legally accessible copy of its nine-page text was not obtained in
the audited environment. Secondary discussions indicate that a
constant-returns nondiscretionary-input expression on page 516 may contain a
typesetting error. That report cannot be used to select, repair, or silently
replace the primary equation. Neither a familiar modern formulation nor a
secondary correction is sufficient evidence for a source-qualified
implementation.

This protocol concerns only the 1986 article named above. It makes no claim
that a separate categorical-variable article or model family has been
source-audited.

## 2. Items not yet source-frozen

The following details remain unresolved:

1. the exact input- and output-oriented programmes, including every
   discretionary and nondiscretionary constraint;
2. the article's returns-to-scale variants and the correct interpretation of
   the reported constant-returns expression;
3. multiplier domains, convexity or conicity restrictions, and disposability
   assumptions;
4. whether nondiscretionary inputs and outputs may enter one programme
   simultaneously and, if so, under which conditions;
5. the complete slack stage, including its objective, priorities, and
   relationship to the radial score;
6. target semantics for nondiscretionary quantities, especially whether a
   reported benchmark is an equality requirement, an inequality, a
   conditional comparison, or only an accounting result;
7. the definitions and relationship of technical, pure technical, and scale
   efficiency, where applicable;
8. zero-data, infeasibility, degeneracy, and unboundedness rules; and
9. a primary numerical example with all observations, classifications,
   scores, slacks, targets, and peer intensities, or an exact synthetic
   source-equation oracle, suitable for independent recomputation.

Until these items are frozen from the complete primary text, no solver
compiler, convenience preset, catalog row, machine registry record, book
recipe, or public class should be created.

## 3. Non-equivalence boundary

The proposed method must not be treated as an alias for:

- ordinary input- or output-oriented radial DEA, which assumes that every
  quantity on the contracted or expanded side is under the manager's control;
- a generic subvector model, unless the primary programme and its conditional
  equality or inequality semantics are shown to coincide exactly;
- conditional DEA or environmental-variable methods that redefine the
  comparison set using external conditions;
- regression, two-stage, or Ruggiero-style adjustments of DEA scores; or
- a model that merely excludes selected variables from the objective while
  leaving the technology and target account otherwise unchanged.

Shared language about “fixed,” “environmental,” or “non-controllable”
variables does not establish mathematical or managerial equivalence.

## 4. Gate for the next version

The candidate may be reopened only after all of the following are available:

1. a complete, authorized copy of the defining article;
2. a page-by-page transcription and independent review of every relevant
   equation, including resolution of the reported constant-returns
   typesetting issue from primary or authoritative evidence;
3. a frozen contract for returns to scale, orientation, disposability,
   discretionary status, slacks, targets, and failure conditions;
4. at least one complete primary-source numerical oracle that can be
   independently reproduced, or an exact synthetic oracle certified by a
   separately written source-equation compiler; and
5. explicit non-equivalence tests against ordinary radial DEA, generic
   subvector specifications, and conditional or adjusted-score approaches.

Passing this gate would permit a normal machine method record and executable
documentation in a later version. Until then,
`deferred_to_next_version` is the final release disposition.
