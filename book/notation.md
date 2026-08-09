# Notation at a Glance

This page is a reading aid, not a list to memorize before beginning the book.
Most chapters use only a small part of it and introduce any additional symbols
when they are needed. When reading an equation, first ask:

1. What is the organization required to preserve?
2. What may change in the performance comparison?
3. Which organizations and periods supply the benchmark?

Those questions give the symbols their economic meaning.

## Organizations, variables, and time

| Symbol | Meaning |
|---|---|
| $j=1,\ldots,n$ | an organization in the reference sample |
| $o$ | the organization currently being evaluated |
| $i=1,\ldots,m$ | an input or resource |
| $r=1,\ldots,s$ | a desirable output, service, or outcome |
| $h=1,\ldots,q$ | an undesirable output or burden |
| $t=1,\ldots,T$ | a time period |
| $\sigma\in\{1,\ldots,T\}$ | the period of an operating plan being evaluated in generic cross-period notation |
| $\tau\in\{1,\ldots,T\}$ | the period supplying the reference technology in generic cross-period notation |
| $\kappa=1,\ldots,G$ | a declared operating or technology group |
| $k,\ell=1,\ldots,K$ | processes or divisions inside an organization |

The book retains **DMU** when referring to the standard DEA term
*decision-making unit*. In applications, more concrete words such as
hospital, plant, bank, municipality, or organization are usually more
informative.

For organization $j$ in period $t$, the standard positive-quantity chapters
write

$$
x_j^t\in\mathbb R_+^m,\qquad
y_j^t\in\mathbb R_+^s,\qquad
b_j^t\in\mathbb R_+^q
$$

denote inputs, desirable outputs, and undesirable outputs. When pollution or
another undesirable output is absent, the $b$ term is omitted rather than
carried through the equations as an empty object.

Signed accounts, quasi-fixed resources, and other specialized data roles have
additional domain requirements. The relevant chapter introduces their economic
meaning and notation; the DEAPack Documentation gives the corresponding data
requirements and parameter definitions.

Reference matrices place organizations in columns:

$$
X=[x_1,\ldots,x_n],\qquad
Y=[y_1,\ldots,y_n],\qquad
B=[b_1,\ldots,b_n].
$$

User data are ordinarily arranged the other way around, with one organization
or organization-period observation per row. DEAPack accepts this row-oriented
form and constructs the reference matrices used by the model.

The candidate roster assembled during a data audit is not automatically the
reference sample. Only observations that pass the study's pre-declared
eligibility rule enter $X$, $Y$, and, where relevant, $B$. Among those
eligible observations, the fitted plan's nonzero $\lambda_j$ values identify
the active peers for organization $o$. Candidate record, eligible comparator,
and active peer are therefore three different statuses.

For a group/metafrontier comparison, $X_\kappa,Y_\kappa$ retain only eligible
observations from declared group $\kappa$, while $X_M,Y_M$ pool eligible
observations from every declared group. The subscript $M$ means
*metafrontier*; it is not a time period.

## Production opportunities and comparator weights

The production technology

$$
\mathcal T=\{(x,y):x\text{ can produce }y\}
$$

collects the operating plans treated as attainable under the assumptions of
the study. With undesirable outputs it is written
$\mathcal T=\{(x,y,b):x\text{ can jointly produce }(y,b)\}$.
The hat in $\widehat{\mathcal T}$ emphasizes that the technology has been
estimated from a sample.

The vector $\lambda\geq0$ combines observed activities into a comparator
plan. Nonzero $\lambda_j$ values identify the observations contributing to
that plan; they are not instructions to merge organizations literally.

The activity-specific weak-disposal construction instead decomposes a
reference activity into retained and curtailed parts, $\mu_j$ and $\eta_j$.
When $\mu_j+\eta_j>0$, its retained activity rate is
$r_j=\mu_j/(\mu_j+\eta_j)$. The symbol $r_j$ is kept distinct from the Farrell
input score $\theta_o$.

| Scale assumption | Restriction on $\lambda$ | Management reading |
|---|---|---|
| CRS | $\lambda\geq0$ | proportional replication is admitted |
| VRS | $\mathbf 1^\top\lambda=1$ | best practice may vary with operating scale |
| NIRS | $\mathbf 1^\top\lambda\leq1$ | unrestricted expansion is not admitted |
| NDRS | $\mathbf 1^\top\lambda\geq1$ | unrestricted contraction is not admitted |

These are assumptions about attainable production, not devices for obtaining a
preferred ranking.

## Scores describe different performance questions

The same technology can support several legitimate measures. Their symbols and
numerical directions should not be interchanged.

| Quantity | Best value or direction | Interpretation |
|---|---|---|
| $\theta_o$ | $1$; higher is better on a within-technology appraisal | Farrell input factor: the retained common share of inputs in the ordinary self-inclusive case |
| $\phi_o$ | $1$; smaller is better when a within-technology appraisal gives $\phi_o\geq1$ | Farrell output expansion factor |
| $1/\phi_o$ | $1$; higher is better on a within-technology appraisal | standardized output-oriented Farrell efficiency; bounded by one only when the evaluated plan belongs to the reference technology |
| $E_o^G,E_o^M$ | $1$; higher is better | radial efficiency against the focal organization's group frontier and the pooled metafrontier |
| $MTR_o=E_o^M/E_o^G$ | $1$; higher means a smaller opportunity gap | metatechnology ratio, historically also called the technology gap ratio (TGR) |
| $\rho_o^I,\rho_o^O,\rho_o^{NO}$ | $1$; higher is better | input-, output-, and non-oriented SBM efficiency scores |
| $\rho_o^B$ | $1$; higher is better | separable strong-disposal undesirable-output SBM efficiency score |
| $\rho_o^{RAM}$ | $1$; higher is better | range-adjusted efficiency relative to the declared sample ranges |
| $\delta_o^{RAM}=1-\rho_o^{RAM}$ | $0$; lower is better | range-adjusted inefficiency relative to the declared sample ranges |
| $\beta_o$ | $0$ is the contemporaneous boundary; larger values mean more remaining attainable improvement under the same direction | directional distance under the declared programme; a signed cross-technology value may be negative |
| $\delta_o$ | $0$; larger values mean more weighted slack | an additive inefficiency quantity |
| $M_o^{t,t+1}$ | $1$; values above one mean growth | a multiplicative productivity-change index |
| $L_o^{t,t+1}$ | $0$; positive values mean improvement | an additive productivity-change indicator |
| $Q_{y,o}^{t,t+1}$ | $1$; values above one mean aggregate output growth | Hicks--Moorsteen output quantity index |
| $Q_{x,o}^{t,t+1}$ | $1$; values above one mean aggregate input growth | Hicks--Moorsteen input quantity index |
| $HM_o^{t,t+1}=Q_{y,o}^{t,t+1}/Q_{x,o}^{t,t+1}$ | $1$; values above one mean productivity growth | complete output-quantity growth relative to input-quantity growth |

Farrell measures ask for common proportional input saving or output expansion
{cite:p}`farrell1957`. A directional distance instead evaluates a declared
bundle of quantity changes; its direction and units are part of the result
{cite:p}`chambers1996`. SBM values variable-specific proportional slacks
{cite:p}`tone2001`. Productivity indexes compare operating performance across
time rather than reporting a static efficiency level {cite:p}`fare1994`.

Throughout the book, lowercase $d$ identifies an efficiency-form
radial evaluation, while unarrowed uppercase $D$ with a declared direction $g$
identifies a directional evaluation. When the two temporal roles must be
distinguished, the full forms are
$d^\tau(z^\sigma)$ and $D^\tau(z^\sigma;g^\sigma)$. Their compact forms are
$d_\sigma^\tau$ and $D_\sigma^\tau$. In either form, the superscript $\tau$
identifies the period supplying the reference technology, while $\sigma$
identifies the period of the operating plan being evaluated. A superscript $G$
identifies a declared full-horizon global technology rather than a calendar
period. When one common physical programme is deliberately used for every
period, as in the ordinary Luenberger account, it remains $g$ without a time
superscript.

The same Greek letter can appear in a cited paper with a different local
meaning. Each chapter states any source-specific notation before using it.
Across chapters, always rely on the quantity's full name and superscript, not
on a bare letter alone.

## Productivity levels and observed prices

In a one-input, one-output account, the observed average product of
organization $j$ is

$$
AP_j=\frac{y_j}{x_j}.
$$

This is a quantity ratio for the observed plan, not a frontier-efficiency
score. With several inputs or outputs there is no unique physical counterpart
until the study declares how quantities are aggregated. A superscript records
a case-specific rule: for example, $AP_j^{eq}$ in the opening chapter counts
its two service categories equally.

For the classic ratios and public models used in this book,
$w_o\in\mathbb R_{++}^m$ denotes strictly positive input prices and
$p_o\in\mathbb R_{++}^s$ denotes strictly positive desirable-output prices for
organization $o$.
The corresponding value accounts are

$$
C_o=w_o^\top x_o,\qquad
R_o=p_o^\top y_o,\qquad
\Pi_o=R_o-C_o,\qquad
\rho_o^{RTD}=\frac{R_o}{C_o}.
$$

$C_o$, $R_o$, and $\Pi_o$ are cost, revenue, and profit. The return-to-dollar
quantity $\rho_o^{RTD}$ is revenue per unit of cost; it is not a profit ratio.
Observed prices remain separate from DEA multiplier weights and constraint
marginals.

For the Nerlovian bridge from a declared operating programme to foregone
profit, $\nu_o=w_o^\top g_o^x+p_o^\top g_o^y$ is the value of one programme
unit and $NI_o=G_o^\Pi/\nu_o$ is profit inefficiency measured in those units.
The symbol $q$ remains reserved for the number of undesirable outputs.

## Slacks, targets, and peers

The standard slack notation is

$$
s^-\geq0
\quad\text{for input excess},\qquad
s^+\geq0
\quad\text{for desirable-output shortfall},\qquad
s^b\geq0
\quad\text{for undesirable-output excess}.
$$

For the familiar desirable-output balance,

$$
X\lambda+s^-=x_o,\qquad
Y\lambda-s^+=y_o,
$$

the corresponding target is

$$
\widehat x_o=x_o-s^-,
\qquad
\widehat y_o=y_o+s^+.
$$

A target is a model-supported comparator under the maintained assumptions. It
is not automatically a forecast, a unique prescription, or evidence that the
change can be implemented without adjustment cost.

Network chapters add process superscripts and directed links. An ordered pair
$(k,\ell)$ means that process $k$ supplies an internal quantity to process
$\ell$. When a source uses different letters, the chapter translates them
to this system or provides an explicit crosswalk. Dynamic chapters add
period-specific peer plans and carry-overs between
adjacent periods. Those chapters introduce their link and stock notation where
the economic roles are defined.

## Read the economic quantity before the numerical label

A reported number may be a bounded efficiency, an expansion factor, a distance,
an additive indicator, or a multiplicative index. Its neutral value and direction
must therefore travel with it. A value of one means best represented static
performance for several efficiency measures, but no productivity change for a
multiplicative index. A value of zero means no remaining directional improvement or
no additive productivity change, depending on the account.

Figures and tables should name the full quantity rather than relying on a generic
column headed “score.” When the maintained analysis has not established strong
efficiency, uniqueness, feasibility, or a causal interpretation, the absence of that
claim must not be converted into its opposite.

## Notation beyond this map

Network, dynamic, environmental, and productivity chapters introduce additional
symbols where their organizational or temporal roles are defined. The DEAPack
Documentation gives the associated returned quantities, data conditions, and
compatibility guidance. This page supplies the common language needed to read the
book; each chapter still defines its own production account.
