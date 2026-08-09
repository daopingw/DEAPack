# Models

The reader-facing model pages explain the economic question and result
semantics. This page lists the public Python classes, grouped by model family
so the classical radial entry point remains visible.

## Classical radial models and alternative hulls

```{autoclass} deapack.RadialDEA
:members:
```

```{autoclass} deapack.CCR
:members:
```

```{autoclass} deapack.BCC
:members:
```

```{autoclass} deapack.CCRInput
:members:
```

```{autoclass} deapack.CCROutput
:members:
```

```{autoclass} deapack.BCCInput
:members:
```

```{autoclass} deapack.BCCOutput
:members:
```

```{autoclass} deapack.FreeDisposalHullDEA
:members:
```

```{autoclass} deapack.FDH
:members:
```

```{autoclass} deapack.FreeCoordinationHullDEA
:members:
```

```{autoclass} deapack.FCH
:members:
```

```{autoclass} deapack.FreeReplicabilityHullDEA
:members:
```

```{autoclass} deapack.FRH
:members:
```

## Multiplicative models

```{autoclass} deapack.MultiplicativeDEA
:members:
```

```{autoclass} deapack.InvariantMultiplicativeDEA
:members:
```

```{autoclass} deapack.C2S2MultiplicativeDEA
:members:
```

## Additive and slack-based models

```{autoclass} deapack.AdditiveDEA
:members:
```

```{autoclass} deapack.WeightedAdditiveDEA
:members:
```

```{autoclass} deapack.RangeAdjustedDEA
:members:
```

```{autoclass} deapack.RAM
:members:
```

`AdditiveDEA` and `RangeAdjustedDEA` share one sparse primary-programme and
postsolve trust contract. A backend optimum is not, by itself, permission to
publish every result table. Inspect `score_valid`, `target_valid`,
`peer_valid`, and `dual_valid` for the specific claim being used; the matching
status fields explain why a narrower table may be unavailable while an
upstream claim remains certified. `solver_status`, `backend_solver_status`,
and `raw_solver_status` preserve the backend outcome. See
{doc}`../models/additive` for the raw/published original-unit accounts and the
one-primary-solve execution ledger.

```{autoclass} deapack.BoundedAdjustedDEA
:members:
```

```{autoclass} deapack.BAM
:members:
```

```{autoclass} deapack.SlacksBasedDEA
:members:
```

```{autoclass} deapack.InputOrientedSlacksBasedDEA
:members:
```

```{autoclass} deapack.InputSBM
:members:
```

```{autoclass} deapack.InputRussell
:members:
```

```{autoclass} deapack.OutputOrientedSlacksBasedDEA
:members:
```

```{autoclass} deapack.OutputSBM
:members:
```

```{autoclass} deapack.OutputRussell
:members:
```

```{autoclass} deapack.SBM
:members:
```

```{autoclass} deapack.ERG
:members:
```

## Declared-calibration epsilon-based measure

```{autoclass} deapack.DeclaredEBMCalibration
:members:
```

```{autoclass} deapack.InputOrientedEpsilonBasedDEA
:members:
```

This is the fixed CRS input-oriented evaluator with a required declared
calibration. It does not estimate the source affinity/PCA calibration; see
{doc}`../models/ebm` for its decision boundary and endpoint semantics.

## Directional and generalized-distance models

```{autoclass} deapack.DirectionalDistanceDEA
:members:
```

```{autoclass} deapack.DDF
:members:
```

```{autoclass} deapack.RangeDirectionalDEA
:members:
```

```{autoclass} deapack.RDM
:members:
```

```{autoclass} deapack.GeneralizedDistanceDEA
:members:
```

```{autoclass} deapack.ChavasCoxGDF
:members:
```

```{autoclass} deapack.GDF
:members:
```

## Environmental models

```{autoclass} deapack.UndesirableSlacksBasedDEA
:members:
```

```{autoclass} deapack.UndesirableSBM
:members:
```

```{autoclass} deapack.ToneNonSeparableSBM
:members:
```

```{autoclass} deapack.NonSeparableUndesirableSBM
:members:
```

```{autoclass} deapack.SBMNS
:members:
```

```{autoclass} deapack.EnvironmentalDirectionalDistanceDEA
:members:
```

```{autoclass} deapack.EnvironmentalDDF
:members:
```

```{autoclass} deapack.CommonFactorWeakDisposalDDF
:members:
```

```{autoclass} deapack.ChungFareGrosskopfDDF
:members:
```

```{autoclass} deapack.ZhouAngWangNonCHPEnergyCarbonDEA
:members:
```

```{autoclass} deapack.NonCHPEnergyCarbonDEA
:members:
```

```{autoclass} deapack.ActivitySpecificWeakDisposalDDF
:members:
```

```{autoclass} deapack.KuosmanenWeakDisposalDDF
:members:
```

```{autoclass} deapack.ByProductionDirectionalDistanceDEA
:members:
```

```{autoclass} deapack.ByProductionDDF
:members:
```

```{autoclass} deapack.ByProductionFareGrosskopfLovellDEA
:members:
```

```{autoclass} deapack.ByProductionFGL
:members:
```

```{autoclass} deapack.MaterialBalanceCoefficients
:members:
```

```{autoclass} deapack.MaterialBalanceDEA
:members:
```

```{autoclass} deapack.CoelliMaterialBalanceDEA
:members:
```

## Economic quantity models

```{autoclass} deapack.CostEfficiency
:members:
```

```{autoclass} deapack.RevenueEfficiency
:members:
```
