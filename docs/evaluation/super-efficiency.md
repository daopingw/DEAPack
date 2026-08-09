:orphan:

# Andersen--Petersen radial super-efficiency research status

Andersen--Petersen radial super-efficiency remains a non-public development
prototype in this evidence version. The defining 1993 article has been
identified, but its complete text was not obtained in the audited environment.
The source-native equations, orientation and returns-to-scale boundary, data
domain, slack convention, numerical illustration, and infeasibility policy
therefore have not been frozen together.

For a source-qualified public leave-one-out method in this release, see
{doc}`directional-super-efficiency`. Ray's method fixes VRS and the observed
input--desirable-output direction; it should not be relabeled as an
Andersen--Petersen implementation.

Later primary work and an indirectly reprinted five-unit example provide
useful engineering checks for a radial leave-one-out reconstruction. They do
not establish that input and output orientation, CRS/VRS/NIRS/NDRS, panel or
custom reference policies, reciprocal output reporting, solver-selected
targets, or DEAPack's fail-closed solver policy all belong to the 1993 source
identity.

This page intentionally contains no public API example, equation, score
interpretation, result contract, or target claim. The prototype remains
directly testable inside the repository, but it is not part of the current
catalog or supported import surface. The evidence needed to reopen the method
is tracked in the
[Andersen--Petersen source protocol](https://github.com/daopingw/DEAPack/blob/main/specs/source_protocols/andersen_petersen_1993_super_efficiency.md).
