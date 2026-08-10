# Tone--Tsutsui network SBM analytical oracle

**Method ID:** `network.sbm.tone_tsutsui_2009`  
**Certificate scope:** fixed-link base account and equations (26)--(27) accountable-link claims

**Published reproduction:** no  
**Production compiler reused:** no

## Claim boundary

This certificate covers one exact base Network SBM account and the two
oriented link-scoring extensions in the equation-complete Tone--Tsutsui
discussion paper:

- the fixed-link base score under the three source orientations;
- equation (26), where an incoming link is an input responsibility of the
  recipient process; and
- equation (27), where an outgoing link is an output responsibility of the
  supplier process.

It does not claim a reproduction of a published numerical table. The source
provides the complete programmes but no dedicated accountable-link table that
can be replayed from printed data and results. The fixtures below are derived
independently as exact fractions directly from the source
balances, not from the production implementation. The project service-chain
regressions are not published numerical reproductions and do not inherit a
literature-table claim.

Both fixtures contain two organizations, `A` and `B`, and two connected
processes:

```text
supplier -- handoff_quantity --> recipient
```

Each process receives equal declared importance weight, the technology is VRS,
and the one handoff remains one physical organizational account at both
endpoints.

## Fixed-link base account under all three orientations

The base certificate uses a fixed handoff of one and the following two
processes, each with one external input and one external output:

| DMU | upstream input | upstream output | handoff | downstream input | downstream output |
|---|---:|---:|---:|---:|---:|
| A | 2 | 1 | 1 | 2 | 1 |
| B | 1 | 2 | 1 | 1 | 2 |

Under VRS, B is an attainable reference for A in both processes. The fixed
handoff is already one for both organizations and therefore has no slack. In
each process, A's external input can fall from two to one and its external
output can rise from one to two.

For the input-oriented account, each process therefore has normalized input
slack $1/2$ and efficiency

$$
1-\frac{1}{2}=\frac{1}{2}.
$$

No convex reference can use less than the minimum observed input one, so this
is the exact lower bound and B attains it. Any positive division weights sum
to one and combine two identical process scores, giving system efficiency
$1/2$.

For the output-oriented account, the maximum observed output is two. Thus
each process has expansion account two and reciprocal efficiency $1/2$;
again B attains the exact bound. For the non-oriented account, each process
combines input account $1/2$ with output expansion account two, giving

$$
\rho=\frac{1/2}{2}=\frac{1}{4}.
$$

The input-, output-, and non-oriented exact system scores for A are therefore
$(1/2,1/2,1/4)$; B has score one in every orientation. This fixed-link claim
does not certify free-link target uniqueness or any published table.

## Equation (26): recipient input responsibility

The ordered columns are

```text
supplier_input, supplier_output, handoff_quantity,
recipient_input, recipient_output
```

with observations

| DMU | supplier input | supplier output | handoff | recipient input | recipient output |
|---|---:|---:|---:|---:|---:|
| A | 2 | 1 | 2 | 1 | 1 |
| B | 1 | 1 | 1 | 1 | 1 |

### Exact lower bound and attaining plan

Let $z$ denote the common supplier and recipient handoff target. VRS makes
each process reference plan a convex combination of A and B. The bilateral
continuity equation gives one shared $z$, and the two observed handoffs imply

$$
1\leq z\leq2.
$$

In this fixture the supplier's external input and handoff have identical
columns $(2,1)$, so its external-input target is also $z$. Its input slack is
$2-z$ and its equation-(26) process account is therefore

$$
A_o^{supplier}
=1-\frac{2-z}{2}
=\frac{z}{2}.
$$

The recipient's external input is one under every convex reference plan. Its
external-input slack is zero, while the single incoming accountable-link
slack is $2-z$. Because equation (26) averages the external input and incoming
link exactly once each, its account is

$$
A_o^{recipient}
=1-\frac{0/1+(2-z)/2}{2}
=\frac{1}{2}+\frac{z}{4}.
$$

Consequently every feasible plan has system objective

$$
\theta_A
=\frac{1}{2}\left(\frac{z}{2}\right)
+\frac{1}{2}\left(\frac{1}{2}+\frac{z}{4}\right)
=\frac{1}{4}+\frac{3z}{8}
\geq\frac{5}{8}.
$$

Putting unit intensity on B in both process technologies gives $z=1$,
satisfies every external balance and the bilateral link equation, and attains
that lower bound. Thus $5/8$ is the optimum, not merely the value of one
feasible plan.

At this optimum the supplier can save one half of its observed external
input, so its process account is

$$
1-\frac{1}{2}=\frac{1}{2}.
$$

The recipient has no external-input excess. Its incoming observed handoff is
2 while the coordinated reference handoff is 1, giving link excess 1. Because
the recipient owns two input dimensions in equation (26)—one external input
and one incoming link—its account is

$$
1-\frac{0/1+1/2}{2}=\frac{3}{4}.
$$

With equal process weights, the system score is therefore

$$
\frac{1}{2}\left(\frac{1}{2}\right)
+\frac{1}{2}\left(\frac{3}{4}\right)
=\frac{5}{8}.
$$

The exact responsible-link witness is:

- owner: recipient;
- role: `link_input`;
- slack: 1;
- accountability target: 1;
- supplier target: 1;
- recipient target: 1; and
- continuity and accountability-balance residuals: 0.

B has system score 1, link slack 0, and target 1.

The same A observation answers different management questions under the other
source link policies: its free-link score is $3/4$, while its fixed-link score
is 1. The three policies are therefore not aliases.

## Equation (27): supplier output responsibility

The observations are

| DMU | supplier input | supplier output | handoff | recipient input | recipient output |
|---|---:|---:|---:|---:|---:|
| A | 1 | 1 | 1 | 1 | 1 |
| B | 1 | 1 | 2 | 1 | 2 |

### Exact upper bound and attaining plan

Again let $z$ be the common handoff target. VRS and the observed handoffs
imply $1\leq z\leq2$. The supplier's external output is one under every
convex reference plan, while its accountable outgoing-link shortfall is
$z-1$. Its equation-(27) expansion account is therefore

$$
B_o^{supplier}
=1+\frac{0/1+(z-1)/1}{2}
=\frac{z+1}{2}.
$$

The recipient's final output and the handoff have identical columns $(1,2)$,
so its output target is $z$ and its one-dimensional expansion account is
$B_o^{recipient}=z$. Hence every feasible plan has system expansion account

$$
q_A
=\frac{1}{2}\left(\frac{z+1}{2}\right)
+\frac{1}{2}z
=\frac{3z+1}{4}
\leq\frac{7}{4}.
$$

Putting unit intensity on B in both process technologies gives $z=2$,
satisfies every external and link balance, and attains the upper bound.
Therefore the optimal reciprocal system efficiency is
$\tau_A=1/q_A=4/7$.

At this optimum the supplier has no shortfall in its external output and a
link shortfall of 1. Equation (27) counts its external output and outgoing
link once each, giving expansion account

$$
1+\frac{0/1+1/1}{2}=\frac{3}{2}
$$

and process efficiency $2/3$. The recipient's external output can double, so
its expansion account is 2 and its process efficiency is $1/2$. The system
expansion account and reciprocal efficiency are

$$
\frac{1}{2}\left(\frac{3}{2}\right)
+\frac{1}{2}(2)
=\frac{7}{4},
\qquad
\tau_A=\frac{4}{7}.
$$

The exact responsible-link witness is:

- owner: supplier;
- role: `link_output`;
- slack: 1;
- accountability target: 2;
- supplier target: 2;
- recipient target: 2; and
- continuity and accountability-balance residuals: 0.

B has system score 1, link slack 0, and target 2. A's matched free-link score
is $2/3$, while its fixed-link score is 1.

## Executable evidence

The controlling tests are in
`tests/test_network_sbm_accountable_links_project_case.py`. They verify:

- both exact rational system and process accounts against the independently
  derived lower/upper bounds above;
- responsibility ownership and single-count dimension weights;
- equality of supplier, recipient, and accountability targets;
- zero continuity, balance, and reconstruction residuals;
- non-equivalence to free and fixed policies;
- independent positive unit rescaling;
- failure-closed orientation and link-kind combinations; and
- one sparse compilation per reference population and one primary LP per
  evaluated organization.

The source boundary remains strict. Equation (26) supports input orientation,
equation (27) supports output orientation, and neither is promoted to a
non-oriented accountable-link formula.
