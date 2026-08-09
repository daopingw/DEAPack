# Performance and scalability contract

DEA commonly requires one optimization problem per evaluated DMU, with one
intensity variable per reference DMU. Avoidable Python and model-construction
overhead can therefore dominate runtime long before the LP solver itself does.

## 1. Non-negotiable implementation rules

1. Convert input tables to validated numerical arrays once.
2. Use `float64` in the numerical core unless a backend explicitly supports a
   different precision with tests.
3. Represent large constraint matrices with SciPy sparse matrices.
4. Compile each distinct reference technology once, including immutable
   account-wise scale statistics used by repeated observation-level tasks.
5. Do not create Python expression objects for every matrix coefficient.
6. Do not access pandas `.iloc` or labels inside the per-DMU solver loop.
7. Batch tasks by reference technology and measure.
8. Preserve input ordering only for presentation; use identifiers for joins.
9. Keep solver logging off by default and retain structured diagnostics.
10. Make parallel execution opt-in, deterministic, chunked, and resistant to
    thread oversubscription.
11. Build productivity indexes as deduplicated distance-task graphs so the
    same observation/reference/measure task is never solved twice.
12. Assemble network and dynamic models from block-sparse graph components;
    never densify a system merely to concatenate stages or periods.
13. Materialize cross-efficiency appraisal matrices in bounded chunks and
    permit streamed summaries when the full $n \times n$ matrix is not
    requested.
14. Bootstrap procedures cache estimator templates, use reproducible
    independent random streams, and batch only statistically exchangeable
    resamples.
15. Complete audit exports serialize one public table at a time, write CSV in
    bounded row chunks and JSONL record by record, and hash bytes while they
    enter the temporary archive. They must not retain every table's CSV and
    JSONL payload in memory before compression.

## 2. Parallel policy

Serial execution is the correctness baseline. Parallel execution uses
processes only for sufficiently large task batches. Each worker uses one
solver thread unless a backend documents a safe alternative.

The scheduler groups tasks sharing immutable compiled matrices. It avoids
serializing the same large matrices once per DMU where platform facilities
allow safe reuse. `n_jobs="auto"` must leave capacity for the operating system
and must not default to every logical CPU unconditionally.

## 3. Large-reference strategies

Sparse matrices and parallelism do not change the fundamental growth in
reference intensity variables. Later performance work may add exact,
validated strategies such as:

- dominance and duplicate screening;
- candidate reference-set reduction;
- efficient-frontier pre-screening where theoretically valid;
- decomposition or column-generation backends;
- direct HiGHS model reuse and basis-aware repeated solves.

No screening rule is enabled unless it is proven valid for the relevant
technology and measure and is regression-tested against the unscreened model.

Approximate methods, if added, are explicitly named and never substituted for
an exact solve without user choice.

## 4. Family-specific execution plans

One optimization loop is not suitable for the whole method universe:

- radial, additive, SBM, DDF, and economic black-box models share sparse
  envelopment templates but keep distinct objective and result assembly
  policies;
- ordinary radial tasks compile the input/output row maxima once for each
  distinct comparison population and reuse them in phase one, slack
  completion, exact reductions, and downstream analyses. The ordinary
  `RadialDEA` phase-one path additionally compiles one immutable CSC structure
  per distinct comparison population. Each evaluated organization receives a
  private numeric copy whose row scales, radial-factor column, and right-hand
  side are bound without rebuilding `diags`/`hstack`/`vstack` reference
  blocks. The orientation and returns-to-scale assumption belong to the model
  instance and therefore to the template identity. This first bounded
  optimization deliberately leaves the phase-two target-completion builder
  unchanged. The signed-data RDM path lazily compiles and reuses a separate
  absolute-maxima group. A reference that never requests either scale group
  performs no maxima reduction, and ordinary radial DEA does not pay for the
  absolute group. Consumers must not rescan the sparse reference matrices for
  every evaluated organization. `benchmark_radial.py` asserts one ordinary-
  statistics compilation and one phase-one template compilation per unique
  reference, one phase-one binding per evaluated organization, zero absolute-
  statistics compilations, CSC solver matrices, and the exact one- or two-
  solve-per-observation budget. It reports reference compilation, template
  compilation, phase-one binding, solver, and remaining elapsed time without
  imposing a machine-dependent CI timing threshold. The radial benchmark's
  `PeerEligibility` path first resolves one declared candidate relation, then
  intersects it with the base temporal/custom policy. It never materializes an
  unconditional Boolean $N\times N$ matrix. Equal effective row vectors are
  content-deduplicated to dense cache IDs, so $K$ repeated comparison
  populations require exactly $K$ quantity and phase-one-template
  compilations, $N$ task bindings, and $N$ score-only solves. The positional
  or keyed declaration itself still contains $E$ edges; a dense all-to-all
  declaration is honestly $O(N^2)$ input. The maintained radial benchmark has
  a separate repeated-cohort case. In the 4 August 2026 source-bound M11
  release-tier run, the 1,000-DMU, 20-cohort score-only case retained 50,000
  eligibility edges, compiled exactly 20 references and 20 templates, bound
  and solved exactly 1,000 tasks, and observed a largest solver constraint
  matrix with 152 nonzeros. The benchmark-internal elapsed time was 2.597
  seconds, including 0.002918 seconds of reference compilation, 0.007142
  seconds of template compilation, 0.065630 seconds of task binding, and
  1.927980 seconds in the solver; the independent suite wall observation was
  3.551 seconds. These timings describe one local environment and are not
  portable thresholds;
- `benchmark_core_peer_eligibility.py` extends the same comparison-right
  workload to Additive, RAM, the three ordinary SBM orientations, and
  score-only DDF without transferring the radial benchmark's evidence. For
  $N$ evaluated organizations divided into $K$ repeated, self-inclusive
  cohorts, each model must retain $E=N^2/K$ effective eligibility edges,
  compile exactly $K$ distinct reference populations, and make exactly $N$
  primary solver calls. Across the six governed model cases this is $6K$
  compilations and $6N$ solves. Every solver matrix must remain sparse, every
  published peer must remain inside its declared cohort, and the compact audit
  must agree between top-level metadata and the expanded reference axis
  without serializing the full relation. RAM additionally computes its common
  coordinate ranges once from the full $N$-row data before eligibility and
  records the restricted result as `deapack_ram_extension`. The blocking smoke
  workload uses $N=24$, $K=4$; the release workload uses $N=1000$, $K=20$.
  The focused release-scale run passed all six model cases at the latter
  dimensions: 20 compilations, 1,000 solves, 50,000 effective edges, and an
  881-byte compact audit per model, or 120 compilations and 6,000 solves in
  total. This is not a full aggregate-suite result. These are structural
  workload gates, not elapsed-time thresholds;
- ordinary directional-distance tasks use the same compiled row maxima to
  scale every primary resource and service constraint before optimization.
  Each primary solve and optional slack-completion solve then receives a
  solver-neutral LP certificate and a separate direction/target account
  reconstruction. Cleanup, thresholded peers, and complete RTS duals are
  checked from the returned vectors, so the contract remains exactly $N$
  solves in score-only mode and $2N$ when completion is requested, with zero
  additional certificate solves;
- maximum-profit tasks cache the complete solution by reference rows and
  joint price vector because they have no evaluated-DMU capacity/commitment
  right-hand side; a common price/reference task is solved once, while a
  Nerlovian composition shares compiled references with its observation-level
  DDF tasks;
- return-to-dollar profitability uses the exact maximum reference ratio when
  all candidate costs are positive. It caches candidate costs, revenues,
  ratios, and the selected maximizer by reference rows plus joint price
  vector only when that task recurs. Unique observation-price tasks are
  released after result assembly, preventing avoidable quadratic resident
  memory; the method does not launch one nonlinear or LP solve per
  observation;
- Chavas--Cox GDF under CRS uses its exact input-radial LP reduction for every
  bearing parameter. The VRS endpoints reuse exact radial programmes, whereas
  an interior bearing parameter currently uses a monotone sequence of
  fixed-score feasibility LPs. Benchmarks must therefore report feasibility
  solve counts as well as elapsed time; the interior-VRS path is a documented
  optimization target rather than being presented as equal in cost to the
  exact reductions;
- standard FDH uses vectorized dominance screening rather than one LP per
  observation;
- the free-replicability hull compiles one sparse integer-replication matrix
  per comparison population and solves one radial MILP per evaluated DMU.
  Input and output orientations use the same integer technology; only the
  evaluated resource/service right-hand side and radial objective differ.
  Finite replication bounds are derived from positive coefficients and the
  evaluated limits for computation, recorded separately, and never relabeled
  as managerial capacity constraints. An optional slack-completion phase adds
  one compatible MILP while holding the radial optimum. Benchmarks must report
  certified integer-optimum counts, gaps, node/time-limit outcomes, and
  FDH--FRH--CRS nesting in addition to elapsed time. Column generation remains
  a later large-reference optimization rather than a hidden change in the
  first public method. The deterministic two-input/two-output benchmark
  records the current development baseline: 12-DMU score-only input and output
  fits took about 0.13 and 0.16 seconds, respectively, using 12 sparse MILPs,
  one compiled reference set, zero reported MIP gap, and replication counts as
  high as three. A 10-DMU input fit with strong slack completion took about
  0.27 seconds and used exactly 20 sparse MILPs. These are regression
  observations on one development machine, not hardware-independent
  guarantees;
- input-, output-, and non-oriented Tone SBM share one sparse balance/RTS
  compiler while keeping separate objective and score-reconstruction
  policies. A global fit compiles the reference arrays once and solves exactly
  one primary LP per observation for each requested orientation. Input and
  output orientations are direct LPs with the identity scale; only the
  non-oriented fractional account uses Charnes--Cooper normalization. The
  dedicated deterministic benchmark has five inputs and three outputs and
  reports score-identity residuals as well as compilation and solve counts.
  On the development
  machine, 100-DMU input/output/non-oriented runs took about
  0.26/0.26/0.26 seconds, while 1,000-DMU runs took about
  8.85/9.13/9.02 seconds. Every run compiled one global reference set, used
  one LP per DMU, and reconstructed its score identity with zero displayed
  residual. These timings are regression observations, not
  hardware-independent guarantees;
- BAM compiles the frozen global input/output reference arrays and, under
  VRS, one anchored reference matrix once, then solves exactly one LP in
  bounded normalized slack variables per observation. Only the
  observation-specific one-sided-room coefficients and bounds change; no
  dense per-DMU reference copy is constructed. The deterministic
  `benchmark_bam.py` fixture uses three inputs and two outputs, asserts one
  solver call per DMU and one compiled reference set, and exercises
  CRS/VRS/NIRS/NDRS. The 100-DMU case is the routine smoke run and the
  1,000-DMU case is reserved for scheduled or release benchmarking;
- the non-public MPSS development prototype compiles each comparison
  population once and solves three sparse LPs per resolved observation. Its
  deterministic `benchmark_mpss.py` fixture remains an internal performance
  guard; it is not evidence that the source-gated method is public;
- the non-public physical-capacity development prototype compiles one
  full-input reference and one fixed-input view per comparison population,
  then solves two matched output-oriented CRS LPs per observation. Its
  deterministic `benchmark_physical_capacity.py` fixture likewise remains an
  internal performance guard pending the next-version source audit;
- multiplier-based restrictions and the non-public ordinary cross-appraisal
  prototype reuse normalized multiplier templates, then solve secondary
  objectives only when required;
- the non-public Andersen--Petersen development prototype solves exactly one sparse
  leave-one-out LP per observation. The preflight checks reference
  cardinality without materializing all $n$ effective row arrays, and a
  self-excluded reference is compiled, used, and released inside the
  observation loop. Effective reference sets that do not contain the
  evaluated row are cached by the immutable `ReferencePlan` set ID. This
  avoids retaining $n$ near-global sparse matrices while preserving exact
  row-level exclusion. The deterministic `benchmark_super_efficiency.py`
  fixture uses three inputs and two outputs; its 100-DMU input/CRS run
  completed 100 certified LPs in about 0.56 seconds, with one base reference
  population and 100 necessarily distinct self-excluded compilations on the
  development machine. This remains an internal performance guard rather
  than evidence of a current public source-qualified method;
- Tone slacks-based super-efficiency first solves one ordinary non-oriented
  SBM screening LP per observation against each compiled base reference set.
  Only observations certified as strongly SBM-efficient then receive one
  source-qualified leave-one-out super-SBM LP. Thus the exact solve budget is
  $n+n_e$, where $n_e$ is the number of eligible observations; an ineligible
  observation never receives a substitute score or a hidden super solve.
  Under one global comparison population, the ordinary SBM reference is
  compiled once, while each eligible appraisal compiles and releases its own
  necessarily distinct self-excluded reference. The deterministic strictly
  positive `benchmark_super_sbm.py` fixture uses three inputs and two outputs
  and asserts actual solver calls equal $n+n_e$. Its 200-DMU non-oriented/CRS
  run found 23 eligible observations, used 200 screening LPs plus 23 super
  LPs (223 total), compiled one global screening reference and 23
  leave-one-out references, and completed in 0.629 seconds. The maximum
  postsolve certificate violation was $5.684\times10^{-14}$ and the maximum
  recovered economic-account violation was $2.990\times10^{-16}$. This
  observation was recorded on an Apple M1 MacBook Air (8 cores, 16 GB,
  macOS 14.6, arm64) using Python 3.12.11, NumPy 2.4.6, SciPy 1.18.0 with
  HiGHS, and DEAPack 2.0.0.dev0; it is a regression observation, not a
  hardware-independent guarantee;
- the O'Donnell--Rao--Battese radial metafrontier leaf reuses the ordinary
  sparse radial engine but keeps comparison populations explicit. A
  score-only fit solves each observation once against its declared group and
  once against the pooled meta population, so the exact budget is $2n$
  phase-one LPs. With $K$ declared groups, it compiles $K$ group
  references plus one pooled reference; it does not materialize an
  observation-specific copy of either. Optional strong-target refinement
  adds another $2n$ LPs and is reported separately because it is not needed
  for the source MTR identity. Primary, secondary, total, additional, and
  certificate-extra calls are aggregated from the child radial result
  metadata rather than inferred from diagnostic-row counts; both postsolve
  certificates add exactly zero LPs. The deterministic
  `benchmark_metafrontier.py` fixture uses four groups, three inputs, and two
  outputs and checks every score/peer/dual claim gate, solver and compilation
  counts, nesting, and reconstruction. Its 200-DMU output/VRS score-only run
  completed 400 LPs in 1.044 seconds, compiled five reference populations,
  and retained maximum
  solver, nesting, and identity residuals of
  $4.086\times10^{-14}$, $2.687\times10^{-14}$, and
  $1.110\times10^{-16}$, respectively. A 1,000-DMU/10-group release run
  completed 2,000 LPs in 7.903 seconds with 11 compilations; every claim gate
  passed, the maximum solver violation was $9.369\times10^{-13}$, and the
  maximum identity residual remained $1.110\times10^{-16}$. These observations
  were recorded on an
  Apple M1 MacBook Air (8 cores, 16 GB, macOS 14.6, arm64) using Python
  3.12.11, NumPy 2.4.6, SciPy 1.18.0 with HiGHS, and DEAPack 2.0.0.dev0; it
  is a regression observation, not a hardware-independent guarantee;
- the Portela--Thanassoulis--Simpson range-directional leaf reuses the sparse
  directional phase-one compiler under VRS. Each distinct reference
  population is compiled once and supplies both its coordinatewise extrema
  and technology matrix; every focal row with at least one positive active
  range requires exactly one LP. An all-zero active direction is reported as
  `unbounded_direction` without launching a solver task. There is no hidden
  slack-completion or Pareto-target LP: directional targets, peer activity,
  residual slacks, and lambdas all come from the unthresholded phase-one
  primal. Quantity rows and postsolve residuals use the same account-wise
  positive scale, preserving the source's unit property without comparing raw
  physical residuals to a dimensionless tolerance. The deterministic signed
  `benchmark_range_directional.py` fixture uses three inputs and two outputs
  and checks solve counts, compilation reuse, the $[0,1]$ beta certificate,
  and retained phase-one accounts. Its 200-DMU non-oriented run completed 200
  LPs in 0.589 seconds, compiled one global reference population, and retained
  maximum solver and postsolve-certificate violations of
  $4.091\times10^{-10}$ and $9.232\times10^{-10}$, respectively. This
  observation was recorded in the same development environment described
  above and is not a hardware-independent guarantee;
- other integer/discrete technologies compile sparse MILP tasks, report
  relaxation bounds and termination gaps, and never substitute rounded LP
  targets; their variable-level integrality semantics are not inherited from
  FRH's integer reference-template counts;
- network and dynamic models compile node/link/carry-over blocks once per
  graph and reuse them across evaluated systems;
- the Tone--Tsutsui Network SBM, Dynamic SBM, and Documentation-only
  Dynamic-Network SBM kernels run one shared solver-neutral primal/dual
  certificate and one model-account reconstruction certificate after each
  primary solve. The Dynamic-Network gate additionally reconstructs the
  process-by-period score, targets, link and carry-over continuity, fixed
  accounts, and component aggregation before atomically releasing any
  semantic table or dual. A backend-optimal result rejected by either gate is
  a semantic `numerical_error` while its backend/raw status remains available.
  These checks are sparse matrix/vector operations and add no optimization
  tasks. On the 100-DMU development fixtures, every applicable Network-SBM
  orientation/link-policy combination completed 100 certified fits in about
  0.36--0.52 seconds, while the four-period VRS Dynamic-SBM
  input/output/non-oriented runs completed 100 certified trajectories in
  about 0.55--0.67 seconds. All three dynamic runs and all eight applicable
  network runs compiled once and solved exactly one primary LP per assessed
  organization. The dedicated Dynamic-Network benchmark likewise requires one
  compilation, exactly one primary solve per trajectory, both certificates,
  and zero additional or certificate solves across all three orientations.
  Its reduction and synthetic-property checks are runtime consistency
  evidence, not an independent published numerical oracle. These are
  regression observations, not hardware-independent guarantees. The 3 August
  M5 gate adds original-unit normalized accounts and independent target,
  link/carry-over, thresholded-peer, and complete finite dual-row release
  checks. A 300-DMU, five-process, six-link non-oriented/free Network-SBM run
  compiled once, made 300 primary calls and no certificate calls, certified
  every claim in 2.586 seconds, and retained a largest normalized original-
  unit violation of $1.687\times10^{-11}$. The matched four-period Dynamic-SBM
  100-DMU input/output/non-oriented runs completed in 0.611--0.706 seconds;
  every score, target, peer, dual, and carry-over claim passed. Its 1,000-DMU
  release run compiled once, made exactly 1,000 primary calls and no extra
  calls, certified every claim in 50.875 seconds, and retained unit invariance
  under independent $10^{-12}$--$10^{12}$ quantity rescaling;
- the separate M10-F Dynamic-SBM HiGHS-presolve experiment is a governed
  correctness comparison, not a release benchmark or optimization claim. Its
  18 cases launched 36 independent arms across input/output/non-oriented,
  CRS/VRS, oracle/realistic/extreme data, and all good/bad/free/fixed
  carry-over roles. All 36/36 arms were optimal and passed every score, target,
  peer, dual, and carry-over certificate, with a largest headline score-family
  difference of $5.218\times10^{-15}$. Only 6/18 cases were fully
  equivalent: the other 12/18 selected different non-headline accounts,
  targets, alternative optimal peers, or published original-unit residuals. The
  existing `presolve=True` default is therefore retained. The source-bound
  record covers 285 files and 5,173,553 bytes under
  `deapack-source-tree-sha256-v1`, with SHA-256
  `bf95c8aac1c4fcdc08e6841121c223d727de5d618195351637c263c46f00e6ba`;
  runtime-import and start-to-finish verification passed. Its fixed-order,
  single-pass elapsed and sampled RSS observations are exploratory and support
  no speed, memory, or default-switch conclusion. The experiment changes no
  model, API, default, or `benchmarks/cases.json` entry; its frozen contract is
  [M10-F experiment contract](https://github.com/daopingw/DEAPack/blob/main/specs/experiments/M10_F_DYNAMIC_SBM_PRESOLVE_AB.md);
- the shared environmental DDF kernel row-scales input, desirable-output, and
  undesirable-output phase-one rows while leaving RTS rows at unit scale. The
  returned solution then passes the solver-neutral LP gate plus raw and
  published environmental balance/objective/RTS reconstruction. Thresholded
  peers and the complete original-unit dual account have independent gates;
  optional slack completion retains its own certificate. On the 100-DMU
  development fixture, strong-disposal VRS completed 100 certified score-only
  fits in 0.336 seconds and 100 certified two-phase fits in 0.937 seconds; the
  classic CFG path took 0.334 and 0.884 seconds, and the generic CRS
  common-factor path took 0.319 and 0.866 seconds. Every run compiled one
  reference set and used exactly one or two LPs per observation. Certification
  adds no optimization task. These timings are regression observations, not
  portable guarantees;
- the Kao--Hwang two-stage relational leaf compiles one sparse
  $2n \times (m+q+s)$ multiplier block per distinct reference set and
  rescales columns and constraint rows before repeated solves. System-only
  evaluation needs one LP per DMU; either source-qualified stage attribution
  needs a second LP; complete stage-attribution bounds need two secondary
  LPs. Lim--Zhu projections are recovered from certified primary dual
  marginals when the backend supplies them and otherwise use one explicit
  envelopment fallback. These solve counts are part of the public performance
  contract rather than hidden post-processing. The benchmark additionally
  requires separate system, decomposition, target/link, and displayed-peer
  release gates; reconstructs raw and published original-quantity accounts;
  and verifies that certification adds no solve. On the deterministic
  development fixture, 100 complete stage-1-selection/projection evaluations
  compiled once, used 100 primary plus 100 secondary LPs and no fallback,
  certified all four claims in 0.466 seconds, and retained a largest checked
  residual of $3.43\times10^{-13}$. A 1,000-DMU score-only run compiled once,
  made exactly 1,000 primary calls, certified 1,000 scores in 7.592 seconds,
  and retained a largest residual of $1.93\times10^{-14}$. These are
  development observations, not portable guarantees;
- the Färe--Grosskopf two-stage radial leaf compiles one scaled quantity block
  and one sparse constraint template per distinct comparison population. An
  evaluated organization changes only the input-contraction column and
  final-output right-hand side; the reference blocks and the two VRS
  convexity rows are reused. It solves exactly one sparse envelopment LP per
  organization. Upstream and downstream intensities remain separate, and no
  secondary stage-attribution or common-link-target solve is hidden in result
  assembly. The shared solver-neutral LP gate and the raw, published-target,
  and thresholded-peer network accounts reuse the solved primal and add no
  optimization task. The benchmark independently counts compilations and
  solver calls, rejects dense programme matrices, checks the native-factor
  efficiency identity, and fails closed on any non-finite or excessive
  account residual. On the current development environment, the deterministic
  100-DMU input-CRS and output-VRS runs completed in about 0.206 and 0.230
  seconds, respectively. Both produced 100 certified scores, targets, and peer
  accounts from 100 primary LPs, one compiled global reference set, and zero
  additional solves; their largest checked residuals were below
  $3.3\times10^{-14}$. The 1,000-DMU input-CRS run completed in about 7.766
  seconds with 1,000/1,000 certified score, target, and peer accounts, one
  compilation, 1,000 primary LPs, zero additional solves, and a largest
  checked residual of $4.6\times10^{-11}$. These are regression observations,
  not hardware-independent guarantees;
- the Kalhor--Kazemi Matin environmental general-network leaf compiles the
  process-specific active $\alpha$ blocks and only the required
  undesirable-producing-process $\beta$ blocks once per distinct reference
  population. Input, final good, final bad, producer-specific ordinary-
  intermediate, and process-RTS rows remain sparse. Each evaluated
  organization changes only the input-factor column and final-output
  right-hand sides, then requires exactly one certified primary LP; there is
  no hidden process-efficiency or slack-completion solve. The deterministic
  three-process benchmark includes an ordinary intermediate, an internal
  desirable product, and an internal undesirable product. In the same
  development environment described above, a 100-DMU VRS run completed 100
  certified LPs in 0.421 seconds and a 500-DMU CRS run completed 500 in 4.308
  seconds; both compiled one global reference set and retained sparse solver
  matrices. These are regression observations, not hardware-independent
  guarantees;
- the Lewis--Sexton forward-quantity sequential leaf compiles the DAG and
  process-specific reference blocks once per declared comparison population.
  It first solves every observed process appraisal, then solves only the
  process programmes whose evaluated operating conditions change during
  propagation. In the two-source/one-sink deterministic benchmark, output
  orientation therefore uses four primary LPs per organization and input
  orientation uses five; source or sink solutions unaffected by propagation
  are reused rather than solved again. The 100-DMU output/CRS run completed
  400 certified LPs in about 2.19 seconds with one global comparison
  population and zero displayed link-balance residual on the development
  machine;
- the Park--Park multi-period aggregative leaf compiles all contemporaneous
  technologies once as one shared block-diagonal sparse matrix. For $n$
  organizations, $T$ periods, $m$ inputs, and $s$ outputs, phase 1 has
  $nT+1$ variables and $T(m+s)$ production rows; phase 2 has
  $nT+T(m+s)$ variables and $T(m+s)$ production-account equations.
  Successful appraisal uses exactly two LPs per organization: one common
  radial factor programme and one fixed-factor raw-total-slack completion.
  VRS adds $T$ convexity equations to each phase; CRS adds none. The
  deterministic four-period, two-input, two-output
  `benchmark_multiperiod_aggregative.py` fixture checks solve counts,
  compilation counts, certification, and economic residuals. Its 100-DMU
  output/VRS run solved 200 certified LPs in about 1.72 seconds, compiled four
  period technologies once, and retained a maximum recomputed economic
  violation of $1.98\times10^{-14}$ on the development machine. This is a
  regression observation, not a hardware-independent guarantee;
- the Chen--Cook--Li--Zhu additive leaf likewise compiles one scaled sparse
  two-process block per distinct reference set, with two additional bounded
  or free process-intercept columns for CRS or VRS. System-only evaluation
  uses one LP per DMU; either process-priority account adds one secondary LP,
  and the default two-priority diagnostic adds two. Split-link Lim--Zhu
  projections are recovered from certified primary dual marginals when
  available, so requesting targets need not add an LP. The release benchmark
  now requires separate system, process, split-link/target, and displayed-peer
  certificates, reconstructs raw and published original-quantity accounts,
  and reconciles metadata with a counting backend. On the deterministic
  development fixture, 100 complete CRS evaluations certified all four claims
  in 1.544 seconds after one compilation, 100 primary plus 200 secondary LPs,
  no projection fallback, and zero certificate solves. The largest checked
  residual was approximately $10^{-13}$ or smaller. This timing is a
  development observation, not a portable guarantee;
- the Cook--Zhu--Bi--Yang general additive CRS leaf compiles the semantic DAG
  once per distinct reference set. For $P$ processes, $V$ observed
  variables, $L$ link variables, and $n_r$ reference DMUs, its process
  matrix has shape $P n_r \times V$. Because an external variable occurs in
  one process account and a link occurs in its source and target accounts,
  compilation stores at most $n_r(V+L)$ role coefficients and therefore
  takes $O(n_r(V+L))$ coefficient work and storage rather than constructing
  a dense $P n_r V$ block. Each evaluated observation changes only the
  objective, total-process-input normalization, and any explicit process-share
  rows, then requires exactly one primary LP. System, process, link, and
  constraint-slack accounts are independently reconstructed from the returned
  solution; certificate work adds no optimization task. The dedicated deterministic
  benchmark uses a five-process, six-link, 18-variable open DAG with branching,
  merging, a non-adjacent link, mid-network resources, and early final
  services. A 100-DMU global run compiled one $500\times18$ block with 2,400
  nonzeros once and solved and independently certified 100 LPs in 0.708
  seconds; a 1,000-DMU run
  compiled one $5{,}000\times18$ block with 24,000 nonzeros once and solved
  1,000 LPs in 23.168 seconds on the development machine. Both runs released
  all requested accounts, used one compilation and exactly one primary solve
  per organization, added zero certificate solves, and retained maximum
  residuals at approximately $10^{-13}$ or smaller. The 100-DMU case
  is suitable for routine smoke/regression work; the 1,000-DMU case is a
  scheduled or release benchmark. Timings are regression observations, not
  hardware-independent guarantees;
- `ReferencePlan` assigns every distinct immutable row array an integer set
  ID. Per-observation caches use that ID rather than constructing a
  length-$n$ Python tuple, preventing avoidable $O(n^2)$ key conversion
  under a single global frontier;
- a shared `CompiledReference` cache is bound to the originating `DEAData`
  object and validates the exact ordered rows once when each unique set is
  first reused by a new plan. Later observations on that plan take an
  object-identity fast path, so a global frontier does not rescan all peer
  rows for every DMU. For sequential, window, or biennial plans with many
  overlapping populations, the one-time validation work is proportional to
  $\sum_k |R_k|$ and can itself be quadratic in the number of periods or
  observations; it remains separate from, and cheaper than, recompiling the
  sparse quantity matrices. This cache is an internal single-composition
  optimization, not a concurrent or cross-data public cache API;
- productivity operators create a task DAG keyed by observation, estimator,
  technology, reference, measure, and direction, solve unique nodes in
  batches, and reconstruct every named index with a residual check;
- cached radial productivity solutions store only material peer positions and
  weights above the numerical-noise tolerance, in stable local-reference
  order. Once the LP, economic, and peer checks finish, cached solver and LP-
  certificate evidence is compacted to scalar status, objective, iteration,
  and residual fields; the primal and all marginal vectors are discarded.
  Public peer tables apply their separate reporting threshold when
  reconstructed. The cache payload therefore grows with retained peer
  activity rather than storing reference-length primal or marginal vectors
  for every distance task. A structural regression fixture holds two peer
  weights at 32 bytes when the reference population grows from 64 to 512
  observations, requires every retained solver vector to be absent, and
  verifies that a repeated task still performs only one solver call;
- the adjacent-period Bjurek Hicks--Moorsteen leaf compiles every
  contemporaneous technology once and deduplicates tasks by orientation,
  technology period, input row, and output row. A two-period panel with $n$
  matched organizations has exactly $8n$ unique Shephard-distance tasks for
  its $n$ transitions. Every quantity row is scaled before solution, while
  the raw, published, and thresholded-peer accounts are reconstructed in
  original units. Only material certified peer positions are retained in the
  cache, and the complete output-quantity/input-quantity identity is released
  independently of that peer gate. The deterministic
  `benchmark_hicks_moorsteen.py` fixture checks both the task count and the
  output-index/input-index reconstruction, all eight LP/economic/peer
  certificates, uniform solver counters, and zero extra solves. Its 100-DMU
  CRS run compiled two period technologies, solved 800 unique LPs in 3.454
  seconds, retained a maximum displayed identity residual of
  $2.22\times10^{-16}$, and kept the largest checked certificate residual at
  $1.525\times10^{-13}$ on the development machine;
- bootstrap and Monte Carlo procedures parallelize at the resample level only
  after the inner deterministic estimator has an efficient serial baseline.

This policy allows mathematical kernels to be shared without pretending that
the corresponding economic estimands are aliases.

### 4.1 Direct benchmark coverage

Shadow registry release `2026-08-03-shadow.56` links every one of the 61
implemented/public method records to at least one benchmark that directly
executes that complete public API. The four retained source-gated prototypes
also keep internal benchmark guards, without being counted as public API
coverage. The 38 benchmark scripts are checked in the reverse direction, so
an orphan script or stale locator fails the test suite. This is an
execution-coverage statement, not a claim that all methods have a published
numerical oracle.

The consolidated benchmark suites close the main cross-family gaps:

- `benchmark_reference_frequency.py` constructs a deterministic complete
  5,000-organization selected peer plan with 20 active peers per organization
  (100,000 edges), checks total frequency as the exact self-plus-other count,
  verifies `reference_rate = reference_frequency / 5,000`, and requires zero
  additional solver calls. A development-machine run completed the account in
  0.030 seconds (about 3.37 million edges per second); the script records this
  throughput without enforcing a brittle wall-clock threshold on CI machines;
- `benchmark_classical_foundations.py` checks additive DEA, RAM,
  multiplicative DEA, generic DDF, direct-scan FDH, and the matched CRS/VRS
  scale-efficiency ratio. It records
  actual solver and compiler calls, reconstructs scores and complete target
  accounts, and checks FDH agreement across chunk sizes. The additive
  benchmark deliberately uses fixed non-unit weights: it is execution and
  scaling evidence for the configurable package extension, not an expansion
  of the VRS/unit-weight Charnes et al. certificate. The Additive and RAM paths
  require every LP, raw and published original-unit account, thresholded-peer
  reconstruction, and complete dual account to certify. They also reject a
  missing or nonfinite certificate field and independently compare measured
  solver/compiler calls with the result ledger. On the 100-DMU development
  checkpoint, Additive and RAM completed in 0.260 and 0.258 seconds,
  respectively. Each compiled one global reference, executed 100 primary LPs,
  certified 100/100 score, target, peer, and dual claims, and executed zero
  secondary, additional, or certificate LPs. Their largest published-account
  residuals were $1.335\times10^{-12}$ and $6.350\times10^{-15}$; their largest
  original-unit dual-account residuals were $1.364\times10^{-12}$ and
  $1.110\times10^{-15}$. These timings are regression observations, not CI
  thresholds. The DDF path rejects
  dense LP matrices, compares measured and result-reported execution counts,
  and runs both the $N$-solve score-only budget and the $2N$-solve full
  completion budget against one shared global compilation. Both paths require
  every primary score, reported peer, and complete dual account to certify;
  the full path additionally requires every completion and target account.
  On the 100-DMU development checkpoint, score-only and full DDF used exactly
  100 and 200 solves after one reference compilation, completing in 0.392 and
  0.742 seconds. Their largest economic-account violations were
  $3.664\times10^{-15}$ and $1.714\times10^{-12}$; these elapsed times are
  observations on the development machine, not CI timing guarantees.
  A separate
  contemporaneous-panel contract verifies that $K$ period technologies
  compile exactly $K$ times and are reused by both phases. Scale efficiency
  retains two distinct score-only component fits but reuses each matched
  comparison population's immutable quantity-matrix compilation: $K$
  distinct populations require $K$, not $2K$, compilations and still require
  $2N$ CRS/VRS LPs for $N$ evaluated observations. The multiplicative path
  uses one immutable sparse log-space template and one LP per observation;
  its benchmark verifies $E=\exp(-D)$, original-unit target factors, primal
  and multiplier accounts, sparse matrices, and one compilation for one
  global comparison population;
- `benchmark_polyhedral_cone_ratio.py` exercises the public finite sum-form
  input-oriented CRS cone-ratio leaf on a positive three-input/two-output
  population. It requires one sparse compiled reference structure, exactly
  one LP per organization, zero completion or certificate solves, certified
  primal/dual/economic accounts, and retained original-coordinate composites
  plus transformed cone residuals;
- `benchmark_local_rts.py` exercises the existing local RTS and scale-
  elasticity operators in both input and output orientations. Each
  organization uses exactly four LPs: VRS radial projection, Pareto slack
  completion, and two support endpoints. The benchmark separately counts one
  projection-reference compilation, one support-reference compilation, and
  one phase-one template, then requires projection/target/peer, finite
  endpoint LP/KKT/dual/economic or unbounded-ray, interval/classification,
  and elasticity certificates with `additional_solver_calls=0`. On the
  100-DMU development checkpoint, local RTS input and output runs certified
  100/100 accounts from 400 solves in 1.681 and 1.771 seconds, with two and one
  unbounded endpoints and maximum finite-endpoint residuals of
  $6.759\times10^{-11}$ and $6.270\times10^{-11}$. The corresponding scale-
  elasticity runs used the same 400-solve budgets and certified 100/100 in
  2.402 and 1.881 seconds; maximum elasticity-transform residuals were
  $3.483\times10^{-14}$ and $2.763\times10^{-13}$. The timings are
  development observations, not CI guarantees;
- `benchmark_directional_super_efficiency.py` exercises Ray's fixed VRS
  leave-one-out programme with one compiled sparse base population and one
  zero-fixed focal intensity per solve. Its 100-DMU development run made 100
  certified solver calls after one compilation in about 0.27 seconds;
- `benchmark_zhou_ang_wang_non_chp.py` requires the source account explicitly
  and exercises the specialized non-CHP CRS programme. The default path uses
  one primary LP per organization; optional multiplicity diagnostics add two
  optimal-face LPs per active component. Its 100-DMU integrated-account run
  compiled the global reference once, made 100 certified calls in about 0.20
  seconds, and retained a maximum constraint violation near
  $1.1\times10^{-16}$;
- `benchmark_economic_allocative.py` directly exercises cost, revenue, and
  both matched technical--allocative decompositions under common and
  organization-specific prices. Direct value models use one LP per
  organization and the decompositions add one matched radial LP; compiler
  reuse and price-objective cache cardinality are measured separately. It now
  also requires every direct LP and economic-account certificate, score,
  target, peer, and dual release gate to pass with zero additional solves.
  On the 100-DMU common-price checkpoint, direct cost and revenue used exactly
  100 solves each and their decompositions exactly 200 each after one reference
  compilation. Elapsed times were 0.181, 0.389, 0.207, and 0.409 seconds,
  respectively; the largest economic-account residual was
  $3.411\times10^{-13}$ and the largest decomposition residual was
  $9.104\times10^{-15}$;
- `benchmark_profit.py` requires a common VRS reference and joint price vector
  to solve and certify exactly once, then reuse the complete target account
  across observations while independently reconstructing every observed
  profit gap. Its 100-DMU direct-profit checkpoint made one solver call,
  certified all 100 scores and semantic-table claims in 0.009 seconds, added
  no solver calls for certification, and retained a zero displayed maximum
  economic-account residual;
  its Nerlovian path separately requires certified profit and directional
  scores, explicit DDF completion validity when requested, the exact $N$ or
  $2N$ directional solve budget, and zero additional release-check solves;
  the 100-DMU full checkpoint reused one common profit solve, made 200
  directional solves, and completed in 0.755 seconds on the development
  machine;
- `benchmark_environmental_foundations.py` directly exercises the public
  joint-production, two named weak-disposal, by-production DDF/FGL,
  material-inflow, and undesirable-output SBM leaves. The FGL budget is
  reconstructed from its actual cutting-plane iterations rather than frozen
  to a nominal LP count. Its environmental DDF paths reject dense constraint
  matrices and run both the score-only $N$-solve budget and the full
  two-phase $2N$-solve budget. The shared environmental compiler is invoked
  once per distinct reference population, while the CFG path also checks the
  solver-call counts reported in result metadata. The retained by-production
  DDF path separately certifies both row-scaled component LPs, both original
  quantity accounts, the minimum aggregation, thresholded component peers,
  and complete original-unit component marginals. On the 100-DMU development
  checkpoint it compiled one common reference, made exactly 200 primary
  solves, added no certification solve, recorded a five-run median of 0.597
  seconds, and kept
  the largest LP or economic-account certificate residual at
  $6.661\times10^{-16}$. The elapsed time is an observation, not a
  hardware-independent guarantee;
- the same environmental benchmark now treats the documentation-only
  activity-specific DDF and the handbook's separable undesirable-output SBM as
  certified runtime routes rather than solve-count-only smoke tests. The
  activity-specific full run requires score, target, thresholded activity,
  complete original-unit dual, and structural self-membership claims; its
  100-DMU checkpoint compiled once, made exactly 200 phase-one/phase-two calls
  with zero membership call, certified 100/100 rows in 0.726 seconds, and kept
  the largest checked certificate residual at $3.775\times10^{-15}$. The
  separable SBM requires independently certified score, target, peer, dual,
  and membership claims; its 100-DMU checkpoint compiled once, made exactly
  100 primary calls, certified 100/100 rows in 0.342 seconds, and kept the
  largest checked certificate residual at $5.551\times10^{-15}$. These elapsed
  times are development observations, not hardware-independent guarantees;
- `benchmark_productivity_operators.py` and
  `benchmark_environmental_productivity.py` use four-period balanced panels
  to distinguish requested from deduplicated distance tasks and to count
  actual contemporaneous, global, and biennial reference compilations.
  The former also exercises enhanced FGNZ's four CRS plus two own-period VRS
  roles and Ray--Desli's four CRS plus four VRS roles. For $n$ units and $T$
  periods, enhanced FGNZ requests $6n(T-1)$ role rows, deduplicates them to
  $n(4T-2)$ distinct solves, and compiles one quantity reference and two
  RTS-specific sparse templates per period. Ray--Desli requests $8n(T-1)$
  role rows, deduplicates them to $2n(3T-2)$ distinct radial solves, and uses
  the same per-period reference/template budget. Each three-factor account is
  reconstructed independently of the reported residual. Other
  aggregate decompositions are likewise recomputed independently of their
  reported residual columns. The classic adjacent, full-horizon Global, and
  documentation-only pair-specific Biennial Malmquist paths additionally
  require every requested role to pass the shared LP certificate and its raw,
  published, and thresholded-peer original-unit radial accounts; every
  transition must then pass its complete raw and published multiplicative
  account. The benchmark compares actual counting-backend calls and intercepted
  compilations with result metadata and requires zero additional certification
  solves. On the 100-unit, four-period development checkpoint, adjacent
  Malmquist retained 1,200 role rows, made exactly 1,000 unique cached solves
  against four contemporaneous compilations, certified all 300 transitions in
  2.126 seconds, and kept the largest LP, radial, peer, or multiplicative
  residual at $1.426\times10^{-13}$. Global Malmquist retained the same 1,200
  role rows, made exactly 800 unique cached solves against four contemporaneous
  and one full-horizon compilation, certified all 300 transitions in 2.143
  seconds, and retained the same largest checked residual. Biennial Malmquist
  retained 1,200 role rows, made exactly 1,000 unique cached solves against four
  contemporaneous and three adjacent-pair compilations, certified all 300
  transitions in 2.405 seconds, and kept the largest checked residual at
  $1.426\times10^{-13}$. These runtime gates do not change Biennial Malmquist's
  `documentation_only` publication scope and do not confer the same release
  contract on the FGNZ presets or Ray--Desli. The Luenberger path additionally
  requires all
  four signed-distance LP certificates and the complete additive account to
  pass without another solve. Its 100-unit, four-period run retained 1,200
  requested roles, made exactly 1,000 unique cached solver calls against four
  compiled references, certified all 300 transitions in 1.734 seconds, and
  kept its largest LP or economic certificate residual below
  $5.0\times10^{-13}$. On the development machine, the enhanced FGNZ
  benchmark with 100 units and four periods retained 1,800 requested role
  rows, performed exactly 1,400 unique solver calls against four compiled
  period references, completed in about 2.11 seconds, and kept the maximum
  reconstruction residual below $5.33\times10^{-15}$;
- the dedicated environmental-productivity benchmark additionally requires
  every CFG ML and Oh GML distance task to pass the shared LP and
  source-production certificates, every transition to pass its source-specific
  multiplicative account, every displayed peer system to reconstruct after
  thresholding, and `additional_solver_calls=0`. On the 100-unit, four-period
  development checkpoint, ML retained 1,200 requested roles, made 1,000 unique
  solves against four compiled references, and completed in 2.729 seconds with
  maximum certificate residual $3.109\times10^{-15}$. GML made 800 unique
  own/global solves against five references and completed in 2.633 seconds with
  maximum certificate residual $7.583\times10^{-14}$. These timings are not
  hardware-independent guarantees;
- the same consolidated productivity benchmark executes the public APZ
  capped-bad-output preset on a strictly positive, multi-input, multi-good
  environmental panel. For $n$ units and $T$ periods, APZ retains
  $4n(T-1)$ requested own/cross role rows, deduplicates them to
  $n(3T-2)$ unique sparse LPs, compiles exactly $T$ contemporaneous references,
  and derives each pollutant cap once from its immutable period reference.
  The same shared LP gate is followed by the APZ-specific input, good-output,
  bad-output-inequality, and contemporaneous-cap account; the four-task
  multiplicative and peer gates add no solve. The 100-unit, four-period smoke
  run retained 1,200 requested roles, made exactly 1,000 solver calls against
  four references, completed in 2.746 seconds, reconstructed $ML=EC\times TC$
  with zero displayed residual, and retained a maximum certificate residual of
  $1.421\times10^{-14}$. This
  observation was recorded in the same development environment described
  above and is not a hardware-independent runtime guarantee;
- `benchmark_profitability_decomposition.py` invokes the complete
  return-to-dollar/GDF composition, accounts separately for exact CRS,
  iterative VRS, and target-completion solves, and verifies that the CRS and
  VRS components share one compiled comparison population.

The repository-level benchmark contract and contribution boundary are
documented in `benchmarks/README.md`. A script can support performance and
execution claims, but it cannot replace the defining literature, a source
equation freeze, or an independent numerical oracle.

## 5. Benchmark matrix

Benchmarks cover cross-sectional and panel data, narrow and wide variable
sets, and both sparse and dense technologies.

Initial gates:

| Tier | DMUs | Inputs | Good outputs | Bad outputs | Purpose |
|---|---:|---:|---:|---:|---|
| tiny | 10 | 2 | 1 | 0 | correctness and profiling sanity |
| small | 100 | 3 | 2 | 1 | CI regression benchmark |
| medium | 1,000 | 5 | 3 | 1 | release performance benchmark |
| large | 10,000 | 5 | 3 | 1 | scalability study, not routine CI |

Panel benchmarks vary the number of distinct reference technologies so that a
fast global model does not conceal inefficient contemporaneous compilation.
Separate suites cover network graph width/depth, dynamic period count,
cross-appraisal matrix size, and bootstrap replication count; a black-box
benchmark cannot certify those execution paths.

## 6. Metrics

Each benchmark records:

- validation and data-conversion time;
- reference-technology compilation time;
- solver time;
- result assembly time;
- peak resident memory;
- number of optimal, infeasible, unbounded, failed, and skipped tasks;
- serial/parallel speedup;
- maximum feasibility residual;
- agreement with the correctness baseline.
- fixed-score feasibility and target-completion solve counts for path models;
- unique versus requested distance tasks for productivity operators;
- compiled block count and sparse-matrix density for network/dynamic models;
- peak materialized appraisal rows for cross-efficiency;
- deterministic random-stream fingerprint for inferential procedures.

Performance improvements are accepted only when numerical agreement and
diagnostic completeness are preserved.

## 7. CI and release policy

- Tiny and small correctness/performance checks run in normal CI.
- Medium benchmarks run on release candidates or a scheduled workflow.
- Large benchmarks run manually or on dedicated infrastructure.
- CI uses generous regression thresholds to detect algorithmic slowdowns, not
  noisy microsecond changes.
- A release report records hardware, Python, NumPy, SciPy, solver, and DEAPack
  versions.

The maintained aggregate suite is frozen in `benchmarks/cases.json`. Every
benchmark script has explicit smoke and release arguments plus a timeout; the
suite never relies on a script's mutable CLI defaults. Each case runs in an
independent process. Its complete command, gate status, exit or timeout status,
wall time, sampled process-tree peak RSS, executed-script hash, raw stdout/stderr
paths and hashes, and a privacy-bounded environment fingerprint enter the
schema-versioned JSON report. A Markdown view is derived from the same report
rather than maintained as a second evidence source.

Schema 1.1 additionally freezes the executable source surface as a sorted
per-file ledger and canonical aggregate SHA-256. The ledger covers
`src/deapack`, package/build and supported lock metadata, every benchmark
script plus its manifest/schema/runner, and the JSON machine-registry records
and schemas. Git, build/cache/result trees, logs, tests, documentation prose,
and unrelated specification assets are excluded. Each included record is a
Unicode-NFC repository-relative POSIX path, byte count, and content SHA-256;
absolute host paths never affect the aggregate. The runner rejects ambiguous,
escaping, symbolic-link, and non-regular entries, probes the benchmark
interpreter's `deapack` import against the recorded `src/deapack` tree, and
recomputes the ledger after execution. Any path, size, digest, or aggregate
difference between the start and finish captures is explicitly recorded as
`source_changed_during_run` and blocks the suite. This gives an uncommitted
tree a precise content identity without weakening the separate clean,
isolated-revision release requirement; only the latter also guards against a
transient edit reverted before the finish capture. Legacy schema 1.0 reports
remain parseable but do not provide equivalent source-bound evidence.

The 3 August 2026 local M10-G release-tier checkpoint passed all 39/39 cases.
Its ledger covered 283 files and 5,135,753 bytes with aggregate SHA-256
`d2d9a3314a077541a8670ce6d5ded935f3c8dbea83e0dbbabf376fbf52d2e104`;
the runtime import matched the recorded source tree and the finish ledger was
unchanged. Peak sampled process-tree RSS was 233.28 MiB in the Dynamic-SBM
case. These values describe one recorded machine and do not create absolute
elapsed-time or memory thresholds. The report also records a dirty worktree,
so it remains local source-bound evidence rather than clean committed release
evidence.

M11 added a fortieth governed case by running the existing radial benchmark
with repeated source-neutral eligibility cohorts. The 4 August 2026 local
smoke and release-tier reports both passed 40/40 cases with no failure,
timeout, or runner error. Both captured the same unchanged 284-file,
5,182,265-byte executable ledger with aggregate SHA-256
`2fa663c1681f729d04d0f2c2d1ceb840f3d4fbaecdfc3f2b49770455441b461e`;
runtime import resolved to the recorded source tree. Release-tier peak sampled
process-tree RSS was 263.7 MiB in the Dynamic-SBM case. These reports supersede
the local 39-case M10-G baseline for current source-bound integration evidence,
but they still record a dirty worktree and therefore are not clean committed
release evidence.

A script that exercises any implemented public method is release blocking.
Scripts attached only to source-gated prototypes remain informational. This
distinction is checked against the machine registry and does not turn a working
prototype into public evidence. The scheduled/manual/tag workflow preserves the
JSON, Markdown, and raw logs as one artifact. Release runs additionally require
a clean committed revision.

The first comparable report establishes the baseline. Absolute elapsed-time
limits are not release gates across unlike machines. A later regression limit
must name its source reports, compare compatible environment fingerprints, and
remain secondary to structural workload counts, numerical agreement, and
diagnostic completeness.
