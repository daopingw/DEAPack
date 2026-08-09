# Valuation-restriction API

This API contains source-qualified restrictions on the supporting valuations
used in DEA self-appraisal. It is separate from observed-price economic
efficiency and from unrestricted ordinary CCR multipliers.

```{autoclass} deapack.ConeRestrictionProvenance
:members:
```

```{autoclass} deapack.PolyhedralConeRatioDEA
:members:
```

```{autoclass} deapack.PolyhedralConeRatioResult
:members:
```

There is deliberately no generic `restrictions=` switch and no public alias.
AR-I, AR-II, cross-side restrictions, virtual shares, production trade-offs,
common weights, VRS, and output-oriented cone-ratio models are not options of
this class.
