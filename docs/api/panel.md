# Panel appraisal

```{eval-rst}
.. currentmodule:: deapack
```

## Park--Park multi-period aggregative DEA

```{autoclass} deapack.ParkParkMultiperiodAggregativeDEA
:members:
```

`MultiperiodAggregativeDEA` is an exact alias for
`ParkParkMultiperiodAggregativeDEA`. The acronym `MDEA` is deliberately not
exported because it is used for several non-equivalent methods.

The estimator consumes ordinary row-level `DEAData`, but the data must form a
complete balanced organization--period panel. It returns one summary row per
complete organization trajectory and period-specific explanatory accounts.

See {doc}`../panel/multiperiod-aggregative` for the exact score convention,
two-phase failure policy, published example, and method boundary.

