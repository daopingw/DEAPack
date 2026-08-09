# Chambers--Färe--Grosskopf ordinary Luenberger source protocol

## Source identity and gate decision

The source-qualified core is frozen from primary sources:

- R. G. Chambers, R. Färe, and S. Grosskopf, “Productivity Growth in
  APEC Countries,” *Pacific Economic Review* 1 (1996), 181--190,
  [DOI 10.1111/j.1468-0106.1996.tb00184.x](https://doi.org/10.1111/j.1468-0106.1996.tb00184.x).
- The open University of Maryland working-paper version, WP 96-21,
  [DOI 10.22004/ag.econ.197843](https://doi.org/10.22004/ag.econ.197843),
  preserves the numbered equations used below.
- R. G. Chambers, “Exact Nonradial Input, Output, and Productivity
  Measurement,” *Economic Theory* 20 (2002), 751--765,
  [DOI 10.1007/s001990100231](https://doi.org/10.1007/s001990100231),
  supplies the later exact-indicator treatment.
- Chambers, Chung, and Färe (1996),
  [DOI 10.1006/jeth.1996.0096](https://doi.org/10.1006/jeth.1996.0096),
  is the primary directional-distance foundation.

The 2002 abstract alone is not enough to reconstruct the executable
four-task decomposition. The gate closes because the primary APEC paper
states the directional distance in equation (2), the four-evaluation
Luenberger indicator in equation (8), its two additive components in
equations (9)--(10), the CRS free-disposal technology in equation (11), and
the DEA programme in equation (12). The working-paper printed pages 2--7
contain the same sequence. No secondary formula is used to fill a gap.

## Frozen economic and technology account

For a reference-period technology $T^r$, an evaluated plan $z=(x,y)$, and
one nonzero direction $g=(g^x,g^y)$, equation (2) defines

$$
\vec D^r(x,y;g^x,g^y)
=\sup\{\beta:(x-\beta g^x,y+\beta g^y)\in T^r\}.
$$

The direction contains nonnegative magnitudes for resource saving and
desirable-service expansion. The same direction supplies the cardinal unit
in every task below. Equation (2) does not restrict $\beta$ to be
nonnegative. Equation (3) states that a plan in its reference technology has
a nonnegative distance. Consequently, a finite negative cross-period value
is retained when an evaluated plan outside the other period's technology can
be made feasible only by reversing part of the declared programme.

The source's empirical technology in equation (11) is the CRS conical hull
with free disposal. For reference observations $(x_j^r,y_j^r)$, equation
(12) is frozen as

$$
\begin{aligned}
\max_{\lambda,\beta}\quad &\beta\\
\text{s.t.}\quad
&\sum_j\lambda_jx_j^r\le x_o-\beta g^x,\\
&\sum_j\lambda_jy_j^r\ge y_o+\beta g^y,\\
&\lambda_j\ge0,\qquad \beta\in\mathbb R.
\end{aligned}
$$

There is no intensity-sum equation. VRS, NIRS, NDRS, nonconvex
technologies, undesirable outputs, and alternative disposal systems are not
certified by this source leaf.

## Four directional appraisals

Let $z^t=(x^t,y^t)$ and $z^{t+1}=(x^{t+1},y^{t+1})$. The four tasks are

$$
\begin{aligned}
D_{t\mid t}&=\vec D^t(z^t;g),
&D_{t+1\mid t}&=\vec D^t(z^{t+1};g),\\
D_{t\mid t+1}&=\vec D^{t+1}(z^t;g),
&D_{t+1\mid t+1}&=\vec D^{t+1}(z^{t+1};g).
\end{aligned}
$$

Equation (8) gives the adjacent-period indicator

$$
L^{t,t+1}
=\frac12\left[
D_{t\mid t}-D_{t+1\mid t}
+D_{t\mid t+1}-D_{t+1\mid t+1}
\right].
$$

The source explicitly assigns positive values to improvement and negative
values to decline. The arithmetic mean gives the two period technologies
equal standing; it is not a multiplicative Malmquist ratio.

## Source-defined additive decomposition

Equations (9)--(10) define

$$
EC_L^{t,t+1}=D_{t\mid t}-D_{t+1\mid t+1},
$$

and

$$
TC_L^{t,t+1}
=\frac12\left[
D_{t+1\mid t+1}-D_{t+1\mid t}
+D_{t\mid t+1}-D_{t\mid t}
\right].
$$

Therefore

$$
L^{t,t+1}=EC_L^{t,t+1}+TC_L^{t,t+1}.
$$

The source describes the first component as change in proximity to the two
period technologies and the second as the average difference between those
technologies. DEAPack reports them as relative operating-performance change
and represented-opportunity change; neither label is a causal claim.

## Oracle and claim boundary

The independent analytical certificate is
`specs/oracles/chambers_fare_grosskopf_1996_luenberger.md`. Its dense LP
compiler reconstructs equation (12) directly from raw fixture arrays and
does not call DEAPack's reference compiler, directional problem builder, or
productivity engine.

The certificate covers only:

- adjacent periods and contemporaneous reference technologies;
- CRS, convex envelopment, and ordinary free disposal;
- nonnegative inputs and desirable outputs;
- one common direction $g=(0,1)$ across organizations, periods, and tasks;
- the four directional distances, signed cross-period values, $L$, $EC_L$,
  $TC_L$, and their additive identity.

It does not certify the package's full-sample mean default, observation-
specific directions, non-CRS sensitivity settings, environmental
productivity, scale decompositions, inference, peers, prices, or causal
interpretations. Those claims cannot inherit this oracle.
