# Environmental-network project-case oracle

The public `KalhorKazemiMatinNetworkDEA` implementation is checked against a
separate dense NumPy/SciPy compiler on two project-authored datasets:
`environmental_recovery_chain` and `environmental_circular_chain`. Neither
fixture reproduces a table from Kalhor and Kazemi Matin (2018).

The compiler independently constructs the corrected process technology and
input-radial programme, including separate process intensities, ordinary
intermediate balances, desirable-output accounts, undesirable-output
accounts, and the declared process-level RTS restrictions. It does not import
the production model's layout, reference compiler, LP builder, or result
helpers.

Executable evidence is in
`tests/test_kalhor_matin_environmental_network_2018_oracle.py`. It checks:

- VRS and CRS project-case parity with the independent compiler;
- NIRS and NDRS process-level restrictions without describing them as
  published numerical reproductions;
- whole-account unit invariance and cyclic intermediate balances;
- custom-reference exclusion without silent peer re-entry;
- sparse programme construction and fail-closed solver behavior; and
- method identity, source citation, and result-contract metadata.

The certificate does not ship the paper's numerical examples, score vectors,
targets, or intensity tables. It does not cover the paper's directional
distance formulation or airport application.

Primary source: Kalhor and Kazemi Matin (2018),
[DOI 10.1051/ro/2017022](https://doi.org/10.1051/ro/2017022), with an
[open Numdam article](https://www.numdam.org/item/10.1051/ro/2017022/).
