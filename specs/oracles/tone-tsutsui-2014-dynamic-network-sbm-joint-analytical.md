# Tone--Tsutsui (2014) dynamic-network SBM: joint analytical oracle

**Method ID:** `dynamic.network_sbm.tone_tsutsui_2014`  
**Validation kind:** `analytically_derived`  
**Published reproduction:** no  
**Production compiler reused:** no

This certificate closes one deliberately narrow but genuinely joint case of
the public dynamic-network SBM. It does not use a one-process dynamic
reduction or a one-period network reduction. Two operating processes are
coordinated in each of two periods, while state accounts also connect each
process across the two periods.

## Management setting and fixture

An organization has a supplying process $S$ and a recipient process $R$.
Each process uses one external input and delivers one external output. A
handoff $h$ runs from $S$ to $R$ and is accountable as an input of the
recipient. Each process also manages one good carry-over $c^k$. The public
base account therefore includes the recipient's handoff shortfall in its
input account and includes each good carry-over shortfall in its owner's
output account.

Two complete organizational trajectories form the self-inclusive global
reference cohort. `O` is the organization being assessed and `P` is the
alternative practice trajectory. All quantities are strictly positive and
synthetic.

| Period | Organization | $x^S$ | $y^S$ | $x^R$ | $y^R$ | $h$ | $c^S$ | $c^R$ |
|---:|:---|---:|---:|---:|---:|---:|---:|---:|
| 1 | P | 1 | 1 | 2 | 1 | 1 | 1 | 2 |
| 1 | O | 3 | 1 | 1 | 1 | 1 | 1 | 1 |
| 2 | P | 1 | 1 | 1 | 2 | 3 | 1 | 3 |
| 2 | O | 3 | 1 | 1 | 1 | 3 | 1 | 3 |

The certified specification is non-oriented, CRS for both processes, the
base score, equal period weights, equal division weights, and source-equal
weights within every account. The period and division weights are therefore
$W_t=w_k=1/2$.

## Source-form programme

Let $\lambda_j^{tk}\geq 0$ be the CRS intensity on trajectory
$j\in\{P,O\}$ for period $t\in\{1,2\}$ and process
$k\in\{S,R\}$. For any external or state quantity $q$, write

$$
\widehat q^{tk}=\sum_{j\in\{P,O\}}q_j^{tk}\lambda_j^{tk}.
$$

The external balances are

$$
\widehat x^{tk}+s_{x}^{tk,-}=x_O^{tk},
\qquad
\widehat y^{tk}-s_{y}^{tk,+}=y_O^{tk}.
$$

The recipient owns the as-input handoff balance,

$$
\sum_j h_j^t\lambda_j^{tR}+s_h^{t,-}=h_O^t,
$$

while the supplying and receiving plans must name the same within-period
handoff target,

$$
\sum_j h_j^t\lambda_j^{tS}
=\sum_j h_j^t\lambda_j^{tR},
\qquad t=1,2.
$$

Each good carry-over has the balance

$$
\widehat c^{tk}-s_c^{tk,+}=c_O^{tk}.
$$

Under the public `tone_tsutsui_2014_core` boundary policy, the one adjacent
transition uses the period-1 carry-over vector on both sides of its
continuity equation:

$$
\sum_j c_j^{1k}\lambda_j^{1k}
=\sum_j c_j^{1k}\lambda_j^{2k},
\qquad k=S,R.
$$

This is not an equality between two independently evaluated terminal balance
rows. Period 2 still has its own observed carry-over balance, and there is no
outgoing period-3 continuity equation.

The supplying process has one scored input item and the recipient has two
(external input plus accountable handoff), so $m_S=1$ and $m_R=2$.
Each process has two scored output-side items (external output plus good
carry-over), so $s_S=s_R=2$. Its period-process accounts are

$$
A_{tk}=1-\frac{1}{m_k}
\left(
\frac{s_x^{tk,-}}{x_O^{tk}}
+\mathbf 1_{\{k=R\}}\frac{s_h^{t,-}}{h_O^t}
\right),
$$

and

$$
B_{tk}=1+\frac{1}{2}
\left(
\frac{s_y^{tk,+}}{y_O^{tk}}
+\frac{s_c^{tk,+}}{c_O^{tk}}
\right).
$$

The system objective is the joint ratio

$$
\rho=
\frac{\tfrac14\sum_{t,k}A_{tk}}
     {\tfrac14\sum_{t,k}B_{tk}}.
$$

## Independent Charnes--Cooper programme

The executable oracle in
`tests/test_dynamic_network_sbm_independent_oracle.py` writes the equations
above directly as a dense Charnes--Cooper LP. It imports only the public API
for the final comparison; its source programme does not import or call
`_dynamic_network_sbm`, `_layout`, either production compiler, or a compiled
package reference. A fail-closed AST and runtime-closure test permits the
module's public API imports for the comparison fit but rejects any private
DEAPack import, forbidden compiler symbol, or DEAPack runtime dependency of
the independent source compiler and its dense solver method.

Let

$$
D=\tfrac14\sum_{t,k}B_{tk},
\qquad
\tau=D^{-1},
$$

and multiply every intensity and slack by $\tau$. The dense LP minimizes

$$
\tau
-\frac14\sum_{t,k}
\frac{S_x^{tk,-}}{m_kx_O^{tk}}
-\frac14\sum_t\frac{S_h^{t,-}}{2h_O^t},
$$

subject to the transformed source balances and continuities and the
normalization

$$
\tau
+\frac14\sum_{t,k}\frac{1}{2}
\left(
\frac{S_y^{tk,+}}{y_O^{tk}}
+\frac{S_c^{tk,+}}{c_O^{tk}}
\right)=1.
$$

The variable order is eight transformed intensities, four external-input
slacks, four external-output slacks, two accountable-handoff slacks, four
good-carry-over slacks, and $\tau$: 23 nonnegative variables in total. The
programme has 19 equality rows: 12 external/carry-over balances, two
recipient handoff balances, two within-period handoff continuities, two
interperiod carry-over continuities, and one fractional normalization. This
dimension count is fixed in the test and is independent of all production
layout objects.

## Exact primal certificate

Set $\tau=1$. In both periods, the supplier selects `P` with intensity one
and the recipient selects `O` with intensity one:

$$
(\lambda_P^{tS},\lambda_O^{tS})=(1,0),
\qquad
(\lambda_P^{tR},\lambda_O^{tR})=(0,1),
\qquad t=1,2.
$$

The supplier's external-input slack is two in each period. Every other slack
is zero. The handoff targets are one in period 1 and three in period 2 at
both endpoints. In the period-1 coordinates used by the transition rows,
both the supplier and recipient carry-over targets equal one on both sides
of their adjacent-period continuity equations.

The four input accounts are

$$
(A_{1S},A_{1R},A_{2S},A_{2R})
=\left(\frac13,1,\frac13,1\right),
$$

and every output account equals one. Hence

$$
\rho
=\frac{\tfrac14(1/3+1+1/3+1)}
       {\tfrac14(1+1+1+1)}
=\frac23.
$$

The corresponding period-process efficiency contributions are

$$
\frac1{12},\quad\frac14,\quad\frac1{12},\quad\frac14,
$$

which reconstruct the system score exactly.

## Exact dual lower bound

Use the equality-row sign convention $A v=b$ in the executable dense LP.
For a minimization problem with $v\geq0$, a dual vector $\pi$ is feasible
when $A^\mathsf{T}\pi\leq c$. The following rational multipliers are an
exact feasible dual certificate.

| Equality row | $\pi$ |
|:---|---:|
| period-1 supplier input balance | $-1/12$ |
| period-1 supplier output balance | $1/12$ |
| period-1 supplier carry-over balance | $1/12$ |
| period-1 recipient input balance | $-5/24$ |
| period-1 recipient output balance | $1/12$ |
| period-1 recipient carry-over balance | $1/12$ |
| period-1 recipient handoff balance | $-1/8$ |
| period-1 handoff continuity | $-1/12$ |
| period-2 supplier input balance | $-1/12$ |
| period-2 supplier output balance | $1/12$ |
| period-2 supplier carry-over balance | $1/12$ |
| period-2 recipient input balance | $-1/8$ |
| period-2 recipient output balance | $1/12$ |
| period-2 recipient carry-over balance | $1/18$ |
| period-2 recipient handoff balance | $-1/24$ |
| period-2 handoff continuity | $-1/36$ |
| supplier carry-over continuity | $0$ |
| recipient carry-over continuity | $1/12$ |
| fractional normalization | $2/3$ |

Every exact reduced cost $c-A^\mathsf{T}\pi$ is nonnegative. Only the
normalization row has a nonzero right-hand side, so the dual objective is
$b^\mathsf{T}\pi=2/3$. The feasible primal and dual objectives coincide;
therefore $2/3$ is the exact optimum rather than only a solver output.
The test performs these primal and dual checks with Python `Fraction` values
before comparing against the numerical LP and public estimator.

## Why this is a joint oracle

The two continuity mechanisms are not decorative constraints in this
fixture. Recompiling the same dense source programme after removing selected
continuity rows gives:

| Link continuity | Carry-over continuity | Exact feasible score returned by the dense LP |
|:---:|:---:|---:|
| enforced | enforced | $2/3$ |
| removed | enforced | $1/2$ |
| enforced | removed | $16/27$ |
| removed | removed | $8/17$ |

The test supplies an exact rational feasible primal witness for every row;
the independent dense solve returns the same value. Since the full programme
has the exact dual lower bound $2/3$, either single relaxation demonstrably
admits a strictly lower score even without treating the relaxed programmes
as public method variants. The certified public
case therefore cannot be reproduced by validating a static network alone or
a single-process dynamic path alone.

## Public validation contract

`tests/test_dynamic_network_sbm_independent_oracle.py` verifies:

1. the source compiler's AST, imports, and runtime closure remain independent
   of production layouts, references, compilers, and private helpers;
2. the exact rational primal and dual certificates for the 23-variable,
   19-row source programme;
3. the discriminating effect of the link and carry-over continuity rows;
4. the public system score, source objective, input and output accounts,
   active process-period intensities, and scored slacks;
5. the period-specific handoff targets and both adjacent carry-over
   continuity accounts; and
6. exact period-process component reconstruction and the package's existing
   solver-neutral and economic post-solve certification.

## Claim boundary

| Claim | Evidence | Exact scope |
|:---|:---|:---|
| joint system optimum $2/3$ | exact rational primal and dual | assessed trajectory `O`; two trajectories, two periods, two processes; non-oriented CRS base score; equal positive weights |
| within-period handoff continuity | direct endpoint targets plus exact source rows | one supplier-to-recipient as-input link in each period |
| interperiod state continuity | direct transition targets plus exact source rows | one good carry-over per process, one adjacent transition, `tone_tsutsui_2014_core` |
| objective and component reconstruction | direct account arithmetic and public result tables | four period-process accounts and their system contributions |
| jointness is discriminating | independently recompiled diagnostic relaxations | this fixture only; relaxed programmes are not public method identities |

This certificate is not a published numerical reproduction. It does not
claim other orientations, VRS or mixed RTS, unequal or zero weights, fixed,
free, or as-output links, bad, free, or fixed carry-overs, other boundary
rules, uniqueness for general data, free-account objective extensions,
productivity change, inference, or a new method identity. Targets and
subsystem accounts outside this fixture retain the public
`solver_selected_not_uniqueness_certified` qualification.
