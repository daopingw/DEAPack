# Benchmark contract

The scripts in this directory provide repeatable evidence about how a public
DEAPack method executes. They measure performance and check execution
contracts such as reference compilation, optimization-task counts, sparse
structure, result reconstruction, and numerical residuals.

A benchmark is not defining evidence for a method. It does not replace the
primary literature that fixes the feasible set and economic interpretation,
and it does not replace an independent numerical oracle. Source and oracle
status remain separate fields in the
[machine method registry](../specs/registry/README.md). The implementation and
scalability requirements that benchmarks exercise are defined in the
[performance contract](../specs/PERFORMANCE.md).

## Registry boundary

A script may appear in a method record's `validation.benchmarks` list only
when it directly constructs or calls that complete public API and fits it.
Calling a lower-level component is not method-level benchmark evidence for a
composition. For example, separate radial and economic-component runs do not
benchmark an allocative decomposition, and separate profitability and
generalized-distance runs do not benchmark their joint decomposition.

Shared compilers, estimators, distance tasks, or solver templates likewise do
not transfer benchmark coverage between methods. A composed method may cite a
script when the script calls the composed public API itself and checks the
resulting task graph or reconstruction identities.

Every `benchmark_*.py` script must be referenced by at least one machine
method record. Conversely, every machine benchmark locator must name an
existing `benchmarks/benchmark_*.py` script. Tests enforce this two-way
coverage so that orphan scripts and stale locators fail validation.

## Data and measurements

Benchmark fixtures must be deterministic. Prefer explicit analytical
sequences or fixed synthetic constructions. If a randomized procedure is
intrinsic to the method, freeze independent random streams and report a
fingerprint that detects accidental changes.

Elapsed time alone is insufficient. Each script should report and, where
possible, assert the structural quantities that explain the workload:

- distinct reference and sparse-block compilations;
- primary, secondary, feasibility, target-completion, or integer solve counts;
- requested and deduplicated task counts for productivity operators;
- matrix dimensions, nonzero counts, graph width/depth, periods, or appraisal
  rows when these determine complexity;
- resolved, failed, infeasible, unbounded, and skipped task counts;
- score-identity, reconstruction, balance, feasibility, certificate, or
  economic-account residuals relevant to the method;
- peak memory or bounded materialization evidence when memory growth is part
  of the execution contract.

The checks must fail closed when an expected count, status, or numerical
certificate is violated. Timing changes are accepted only when scores,
diagnostics, targets, and relevant residuals remain consistent with the
correctness baseline.

## Scale tiers

Use the common tiers in `specs/PERFORMANCE.md` unless a method-specific
integer, network, dynamic, panel, or appraisal workload justifies a smaller
declared case:

| Tier | Typical DMUs | Intended use |
|---|---:|---|
| tiny | 10 | correctness and profiling sanity |
| small | 100 | routine CI regression |
| medium | 1,000 | scheduled or release-candidate benchmarking |
| large | 10,000 | manual scalability study on dedicated infrastructure |

Tiny and small cases may run in normal CI. Medium cases should not lengthen
ordinary contributor feedback, and large cases are not routine CI gates.
Method-specific scripts should expose size and workload options rather than
silently changing their deterministic fixture.

## Reporting environment

Absolute timings are observations from one environment, not portable speed
guarantees. Any recorded baseline or release comparison must include:

- processor and core count;
- memory capacity;
- operating system and architecture;
- Python, NumPy, SciPy, solver, and DEAPack versions;
- solver thread settings and DEAPack parallel settings;
- command-line arguments and benchmark tier.

CI thresholds should be generous enough to detect algorithmic regressions
without treating ordinary machine noise as a failure. Comparisons across
different hardware or software environments must be labeled as such.

## Frozen suite and release report

[`cases.json`](cases.json) is the maintained workload manifest. It names every
`benchmark_*.py` script and freezes explicit arguments and timeouts for two
tiers. `smoke` keeps contributor feedback bounded; `release` exercises the
method-specific release scale. Script defaults are deliberately not the suite
contract, because changing a default must not silently change a historical
baseline.

Run the complete tiers from the repository root after installing the benchmark
extra:

```bash
python -m pip install -e '.[benchmark]'
make benchmark-smoke
make benchmark-release
```

The runner launches every case in an independent process and writes one
timestamped directory under `benchmark-results/`. It contains raw stdout and
stderr logs, a normative `report.json` conforming to
[`report-schema.json`](report-schema.json), and a readable `report.md`. The
report records complete commands, exit and timeout status, wall time, sampled
peak resident memory for the process tree, the executed script's SHA-256 hash,
log byte counts and SHA-256 hashes, a whitelist of execution settings, Git
revision/dirty state, hardware, Python, and dependency versions. It never
serializes the caller's complete environment.

Report schema 1.1 also binds the run to the source bytes that can affect it.
The source-tree ledger includes every regular non-cache file under
`src/deapack`, `pyproject.toml`, `MANIFEST.in`, a supported root lock file when
present, the benchmark manifest, report schema, runner and every
`benchmark_*.py` script, plus every JSON registry record and schema under
`specs/registry`. It deliberately excludes Git metadata, build and cache trees,
generated benchmark results and logs, tests, documentation prose, and
unrelated specification assets. Those exclusions keep the identity tied to
the executable and governed method surface rather than to incidental outputs.

Every ledger entry contains a Unicode-NFC, repository-relative POSIX path, byte
count, and SHA-256 digest. Entries are ordered by their UTF-8 path bytes. The
aggregate `deapack-source-tree-sha256-v1` digest hashes its ASCII format tag and
NUL byte followed, for every entry, by an unsigned 64-bit big-endian path-byte
length, the UTF-8 path, an unsigned 64-bit big-endian file size, and the raw
32-byte content digest. Absolute paths never enter the aggregate. Duplicate,
case-colliding, escaping, symbolic-link, and non-regular paths fail closed.
Consequently a dirty worktree still has a unique source identity; Git revision
and dirty state remain complementary provenance rather than the sole identity.

The runner places this repository's `src` directory first on `PYTHONPATH` and
uses the benchmark interpreter to verify that `deapack` resolves to the
ledger-bound `src/deapack/__init__.py` before any case runs. It computes and
verifies the complete ledger both before and after the suite. Any path, size,
file-hash, or aggregate difference between those two captures sets
`source_changed_during_run`, produces a configuration-error report, and blocks
the gate. This detects start-to-finish drift; a clean, isolated CI checkout
remains the stronger protection against a transient edit that is reverted
before the final capture. The schema continues to parse legacy 1.0 reports
only when `source_tree` is absent; those reports predate complete source
binding and are not equivalent release evidence.

The manifest's gate boundary is derived from the machine registry. Thirty-six
scripts exercise at least one implemented public method and are release
blocking. The MPSS, physical-capacity, and Andersen--Petersen radial
super-efficiency scripts guard source-gated prototypes only; their failures are
reported as informational and cannot redefine the public release surface. A
script covering both public and prototype routes remains blocking for its public
route.

The `core-peer-eligibility` workload is a structural comparison-population
case rather than a timing contest. With (N) evaluations and (K) repeated
declared populations, it requires Additive, RAM, all three ordinary SBM
orientations, and score-only DDF to compile exactly (K) reference blocks,
make exactly (N) primary solves per model, retain compact provenance, and
publish no intensity outside the effective population. The release workload
uses (N=1{,}000) and (K=20).

The first report establishes a baseline. No absolute wall-time threshold is
portable across machines, so the runner initially fails only on a blocking case
error, timeout, or orchestration error. Structural counts and numerical
certificates remain hard assertions inside each script. Later regression limits
must compare like-for-like environment fingerprints and retain the raw reports
from which they were derived.
