# Ray directional super-efficiency: independent project-case oracle

**Method ID:** `evaluation.super.directional.ray_2008`  
**Validation kind:** `analytical`  
**Published-table reproduction:** no  
**Production compiler reused:** no

The defining equation and interpretation boundary remain source-qualified in
`specs/source_protocols/ray_2008_directional_super_efficiency.md`. Numerical
regression uses the independently designed
`directional_super_multivariate_stress` case rather than redistributing a
published table.

## Programme checked

For focal row $o$, the test uses variables $z=[\lambda_{-o},\beta]$ and the
source-shaped constraints

$$
\begin{bmatrix}
-Y_{-o}^{\mathsf T} & y_o\\
 X_{-o}^{\mathsf T} & x_o
\end{bmatrix}z
\leq
\begin{bmatrix}-y_o\\x_o\end{bmatrix},
\qquad
\begin{bmatrix}\mathbf1^{\mathsf T}&0\end{bmatrix}z=1,
$$

with $\lambda\geq0$ and unrestricted $\beta$. Public tests independently check
the sparse dimensions, leave-one-out equation, target and peer-account
reconstruction, coordinate-unit invariance, and fail-closed certificate
handling. The scalar identity $NL=1-\beta$ is checked without freezing a
published result vector.

## Claim boundary

| Claim | Evidence | Certified scope |
|---|---|---|
| programme transcription | matrix-structure and account tests | observed direction, VRS, leave-one-row-out |
| native score and sign | scalar identity and project stress case | `beta` and `NL=1-beta` |
| peer activity and target boundary | reconstructed project-case accounts | no peer-plan uniqueness claim |
| invalid projection handling | deliberately stressed project row | raw scalar retained; invalid quantity interpretation rejected |
| unit behavior | positive coordinate-rescaling test | quantities and observed directions co-scale |

The certificate does not cover arbitrary directions, other returns to scale,
zero-input repairs, undesirable outputs, networks, panels, productivity,
prices, uncertainty, or statistical outlier claims.
