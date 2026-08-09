# Kalhor--Kazemi Matin environmental-network source protocol

## Source identity

The method authority is Kalhor and Kazemi Matin (2018),
[DOI 10.1051/ro/2017022](https://doi.org/10.1051/ro/2017022), available from
[Numdam](https://www.numdam.org/item/10.1051/ro/2017022/). DEAPack preserves
the corrected network technology, its process-level intensity restrictions,
and the input-radial programme. It does not redistribute the article's
illustrative numerical tables or printed results.

## Model boundary

Each process has its own nonnegative intensity system. External inputs are
contracted by one common radial factor. Ordinary intermediate products close
through producing-process and consuming-process balance equations, while
desirable and undesirable final products keep distinct accounts. The
corrected technology prevents an intermediate product from being silently
aggregated across economically distinct chains.

CRS omits process convexity restrictions. VRS imposes equality restrictions
for every process; NIRS and NDRS impose their corresponding one-sided
process-level restrictions. These choices are explicit model variants, not
post-processing labels.

## Executable evidence

The public, project-authored fixtures are `environmental_recovery_chain` and
`environmental_circular_chain`. A separate dense compiler in
`tests/test_kalhor_matin_environmental_network_2018_oracle.py` verifies the
production implementation across the supported RTS variants, internal
balances, unit conversions, custom references, sparse compilation, solver
failure, and metadata identity. The project-case certificate is
`specs/oracles/environmental-network-project-cases.md`.

This evidence supports implementation fidelity to the stated equations. It
does not claim a reproduction of the source tables, the paper's directional
distance extension, its airport application, target uniqueness, causal
interpretation, or policy optimality.
