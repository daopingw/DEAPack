# Preface

Efficiency and productivity analysis lies at the intersection of production economics,
operations research, and empirical measurement. Modern software can solve a large DEA
program quickly; the harder task is to specify a defensible production technology,
choose a measure consistent with the decision problem, and explain what the resulting
benchmark does and does not establish. This book is written around that harder task.

The intended audience includes readers encountering frontier methods for the first
time, applied researchers who need a reproducible workflow, and specialists who want a
consistent reference across classical, productivity, and environmental DEA. The
exposition begins with production plans, technologies, efficiency, and distance
functions before introducing individual linear programs. Advanced chapters retain the
same notation and distinguish changes in the technology from changes in the measure or
reference sample.

A new reader should leave with more than a catalogue of acronyms: the aim is to make it
possible to state a performance question in economic terms, choose assumptions that fit
the organization, and interpret a score without claiming more than the comparison can
support. Applied readers can use the worked cases to move from a defensible study design
to targets, decompositions, sensitivity analysis, and reporting. Researchers can use the
common notation to compare methods whose historical names sometimes conceal the same
idea---or suggest equivalence where an economically important difference remains.

## Organization by economic substance

The DEA literature contains many names for formulations that are mathematically
equivalent, as well as similar names for methods that impose different production
assumptions. This book organizes the field around the economic question being asked
and the assumptions needed to make the comparison meaningful:

- the roles and units of observed variables;
- the axioms defining the production technology;
- the efficiency or productivity measure;
- the reference technology and comparison population;
- the internal structure of production;
- the inferential and substantive purpose of the analysis.

Historical names such as CCR and BCC are retained because they connect readers to the
literature, but they do not determine the taxonomy. Equivalent multiplier and
envelopment formulations are treated together. Methods remain separate when
disposability, convexity, returns to scale, direction, or reference technology changes
the managerial counterfactual or the economic quantity being measured.

The main text is deliberately DEA-centered rather than a survey of every frontier
method. Index-number theory, stochastic frontier analysis, robust nonparametric
frontiers, and statistical inference are mentioned where they clarify the scope or
limitations of DEA-based conclusions. Appendices synthesize relationships among the
principal families; paper-specific extensions and exhaustive implementation details
remain in the separate package Documentation.

## The book and DEAPack

DEAPack is the computational companion to the book, not its organizing subject. A
chapter first defines a production problem and develops its theoretical measure. Code
then reproduces a claim, reveals the targets or decomposition behind a score, and
shows whether the conditions needed to interpret that comparison are satisfied. Complete signatures,
parameter inventories, exceptions, and compatibility guidance belong in the separate
package Documentation.

This project extends earlier work on directional-distance efficiency and green
productivity software, including the Stata implementation by Wang, Du, and Zhang
{cite:p}`wang2022`. DEAPack broadens that computational setting to classical DEA,
productivity change, undesirable outputs, and structured production systems. Its role
here is to make the theory inspectable. A reader can reproduce the numerical result,
open the operating quantities behind it, and see how a different orientation, scale
assumption, direction, or reference technology changes the conclusion.

The book and its computational companion therefore use the same notation, datasets,
worked examples, and visual language. This continuity lets equations, code, tables, and
figures describe one empirical argument rather than four disconnected versions of it.
It also keeps the distinction between a mathematically valid benchmark and a credible
management conclusion visible throughout the analysis.

## Reproducible evidence

Every numerical statement, table, and figure is expected to be reproducible from the
repository. Small theoretical datasets are deterministic and isolate questions such as
proportional resource saving, output shortfall, unit invariance, infeasible historical
comparisons, or productivity-index circularity. Empirical datasets retain provenance,
processing steps, variable definitions, units, and version information. A result that
cannot be regenerated reliably will not be used as a teaching conclusion.

The project is designed to provide open access to the manuscript, computational
examples, and every dataset whose redistribution rights have been cleared. This allows
readers to inspect how each conclusion was obtained and to challenge the assumptions
that produced it. Reproducibility is not treated as proof that those assumptions are
correct. It is a way to separate numerical agreement from the harder questions of
comparability, measurement, economic interpretation, and external validity.

## An open scholarly project

The Handbook and DEAPack are developed in public. Readers may suggest a model, identify
an equivalence that should be made clearer, report a numerical discrepancy, contribute
code or a teaching case, improve a figure, or refine the Chinese translation. A
well-documented question or counterexample is valuable even when the contributor does
not implement a solution. The {doc}`project-contributions` page explains the available routes,
the evidence expected for a new executable method, and how contributions are credited.

## Prerequisites

No previous course in linear programming or production economics is assumed. Each
method begins with a production or management problem; the required mathematics is
introduced only after the reader knows what is being compared and why. Figures help
connect operating data, benchmarks, and decision consequences. Familiarity with basic
Python and pandas will make the computational sections easier to reproduce, but the
theoretical sequence can be read independently of the code.
