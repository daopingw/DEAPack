# Glossary and Historical Names

DEA grew through several literatures, so the same idea is often encountered under
different names. This glossary points historical labels back to the economic or
managerial concept used consistently in this book. An alias listed here is a route
into the relevant model family, not evidence that every similarly named variant is
identical.

```{glossary}
:sorted:

Additive model
  A non-oriented DEA model that maximizes a weighted sum of input excesses and
  desirable-output shortfalls. Because its gaps retain physical units until weights
  are supplied, it should not be treated as the same numerical ruler as RAM or SBM.

Allocative efficiency
  The part of an economic-efficiency comparison associated with choosing an input or
  output mix under stated prices after the matched technical component has been
  accounted for. It is a counterfactual decomposition, not proof of managerial cause.

BCC model
  The Banker--Charnes--Cooper form of radial DEA under variable returns to scale
  (VRS). Input and output orientation remain separate choices.

Benchmark
  An attainable comparison plan supported by the declared technology and eligible
  reference observations. It need not be an observed organization, a unique target,
  or a plan that can be copied without adaptation.

Catch-up
  A traditional productivity-decomposition label for a change in benchmark-relative
  operating performance. This book states the underlying change first because the
  component does not identify why performance changed.

CCR model
  The Charnes--Cooper--Rhodes form of radial DEA under constant returns to scale
  (CRS). It is not a separate mother family from Farrell radial DEA under the same
  orientation and CRS assumptions.

Constant returns to scale (CRS)
  A technology assumption permitting proportional replication of an attainable
  activity. Whether replication is economically credible is a study-design question.

Data envelopment analysis (DEA)
  A family of nonparametric frontier methods that constructs production possibilities
  from observed activities and maintained assumptions, then evaluates organizations
  against those represented opportunities.

Decision-making unit (DMU)
  The organization, facility, programme, process system, or complete trajectory being
  evaluated. The label does not by itself establish a meaningful organizational
  boundary.

Directional distance function (DDF)
  A performance measure asking how many units of a pre-specified joint improvement
  programme are attainable. Its direction gives one programme unit and therefore
  carries economic meaning and units.

Disposability
  An assumption about whether inputs, desirable outputs, or undesirable outcomes may
  be reduced or expanded while retaining feasibility. Strong and weak disposal encode
  different production claims, especially for pollution.

Efficiency change
  The change in an organization's performance relative to its own-period benchmark in
  a productivity decomposition. It is often called catch-up, but it is not a causal
  explanation of operational improvement.

Efficient frontier
  The boundary of the represented production possibilities on which the relevant
  performance improvement cannot be continued under the maintained model.

Enhanced Russell graph (ERG) measure
  A historical label conditionally equivalent to the standard non-oriented SBM
  account on its stated positive-data domain. More general Russell graph measures
  require their own specification.

Free disposal hull (FDH)
  A non-convex observed-practice technology that permits ordinary disposal but does
  not create virtual peers by convexly mixing organizations.

Frontier shift
  A traditional productivity-decomposition label for a change in the production
  opportunities represented by dated technologies. It does not identify the cause of
  that change.

Hicks--Moorsteen productivity index
  A multiplicatively complete quantity index formed from an output quantity index and
  an input quantity index. It answers a different accounting question from treating a
  Malmquist distance index as its synonym.

Input orientation
  A performance question that protects output commitments and asks how much of the
  chosen input burden can be reduced.

Intensity
  A coefficient attached to a reference activity in an envelopment model. Positive
  intensities identify the selected peer combination but may be non-unique.

Luenberger productivity indicator
  An additive productivity-change account built from directional distances. Its
  values are measured in units of the declared improvement programme rather than as a
  multiplicative ratio.

Malmquist productivity index
  A multiplicative productivity-change account constructed from dated radial distance
  comparisons. Its reference-information policy and decomposition must be reported.

Metafrontier
  A pooled opportunity set used alongside declared group frontiers to distinguish
  within-group performance from proximity between represented group and pooled
  opportunities. It does not discover groups or estimate a causal environmental
  effect.

Multiplier form
  The value-weight representation dual to an envelopment formulation under the
  relevant regularity conditions. Endogenous DEA multipliers are not observed market
  prices unless the model explicitly supplies prices.

Network DEA
  DEA models that represent connected processes and enforce an organizational account
  for internal products or services. Independently scoring departments is not network
  DEA unless their plans form one feasible system.

Output orientation
  A performance question that protects the input envelope and asks how much desirable
  output can be expanded.

Peer
  A reference organization with a positive reported intensity in one selected
  benchmark plan. Peer status need not be unique across alternative optima.

Production possibility set
  The input--output plans treated as attainable under the data, organizational
  boundary, disposability, convexity, scale, and reference-set assumptions.

Projection
  A fitted target or benchmark plan associated with an evaluated organization. A
  projection can be non-unique and should not be presented automatically as a
  prescriptive implementation plan.

RAM
  The range-adjusted measure, which normalizes variable-specific slacks by sample
  ranges before aggregation. It shares a slack diagnosis with Additive and SBM models
  but uses a different reporting ruler.

Reference set
  The observations eligible to construct the comparison technology. This population
  is chosen before fitting and is distinct from the smaller set of active peers in one
  solution.

Returns to scale (RTS)
  Assumptions or local findings about how represented production responds when the
  overall size of an activity changes. CRS, VRS, NIRS, and NDRS alter the opportunity
  set; local RTS describes an efficient operating point.

Russell measure
  A family of componentwise contraction or expansion measures. The input and output
  Russell forms used in this book are exact conditional aliases of the corresponding
  standard oriented SBM programmes; the wider Russell family is not collapsed into
  that equivalence.

Scale efficiency
  A matched comparison of radial performance under CRS and VRS. It records an
  additional gap associated with scale assumptions, not a causal diagnosis of why an
  organization operates at its current size.

Slacks-based measure (SBM)
  A non-radial efficiency family that aggregates variable-specific input excesses and
  output shortfalls after normalizing them by the evaluated quantities.

Strong efficiency
  Pareto--Koopmans efficiency: no input can be reduced or desirable output increased
  without worsening another protected quantity under the declared technology. A
  radial score of one alone may establish only weak radial efficiency.

Technical change
  The part of a productivity decomposition associated with a change in represented
  production opportunities. It is a benchmark-accounting component, not by itself a
  measure of innovation or technological adoption.

Technical efficiency
  Performance relative to a production technology under a specified improvement
  criterion. The term is incomplete unless the orientation or measure, scale
  assumption, and reference population are known.

Technology gap ratio (TGR)
  A common historical name for the metatechnology ratio (MTR), comparing group-frontier
  and metafrontier performance under a matched radial specification.

Undesirable output
  A jointly produced outcome such as emissions, defects, or adverse events for which
  less is preferred. Its production role and disposal assumptions must be modelled;
  changing its sign does not settle those assumptions.

Variable returns to scale (VRS)
  A convex technology in which reference intensities sum to one, preventing unrestricted
  proportional replication of the complete observed activities.

Weak efficiency
  A boundary status under a particular radial or directional improvement in which no
  further movement is possible along that path, although variable-specific slacks may
  remain.
```

The notation table in {doc}`notation` supplies symbols and score directions. The
reader's map in {doc}`appendices/unified-framework` shows how these concepts combine
when choosing a model. Complete API names and technical variants remain in the
separate DEAPack Documentation.
