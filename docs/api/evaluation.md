# Peer-appraisal API

The classes on this page implement evaluation protocols applied to declared
DEA technologies. Some use multiplier programmes and others use envelopment
programmes; none should be confused with a universal technical-efficiency
measure.

```{eval-rst}
.. autoclass:: deapack.LiangWuCookZhuGameCrossEfficiency
   :members:
   :show-inheritance:

.. autoclass:: deapack.RayDirectionalSuperEfficiency
   :members:
   :show-inheritance:

.. autoclass:: deapack.NerloveLuenbergerSuperEfficiency
   :members:
   :show-inheritance:

.. autoclass:: deapack.ToneSuperSBM
   :members:
   :show-inheritance:

.. autoclass:: deapack.SuperSBM
   :members:
   :show-inheritance:
```

Ordinary CRS cross-efficiency is retained as an internal prototype and has no
current public API. Its defining-source boundary and reopening gate are
recorded in the
[ordinary cross-efficiency source protocol](https://github.com/daopingw/DEAPack/blob/main/specs/source_protocols/ordinary_crs_cross_efficiency.md).

Andersen--Petersen radial super-efficiency is likewise an internal prototype
with no current public API. The defining article was identified but not
obtained in full during the source-freeze cycle, so the method is deferred to
the next version. Its evidence boundary is recorded in the
[Andersen--Petersen source protocol](https://github.com/daopingw/DEAPack/blob/main/specs/source_protocols/andersen_petersen_1993_super_efficiency.md).

`GameCrossEfficiency` is the exact public alias of
`LiangWuCookZhuGameCrossEfficiency`.
`NerloveLuenbergerSuperEfficiency` is the exact source-name alias of
`RayDirectionalSuperEfficiency`.
`SuperSBM` is the exact public alias of `ToneSuperSBM`.
