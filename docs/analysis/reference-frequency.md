# Selected-plan reference frequency

```{eval-rst}
.. currentmodule:: deapack
```

Reference frequency is a deterministic post-estimation account of **which
observed organizations recur in the peer plans selected by the solver**. It is
useful when a performance study moves from individual scores to a portfolio of
benchmark evidence: managers may want to know which organizations repeatedly
help support the model's operating comparisons and therefore merit closer
substantive investigation.

The account is intentionally narrower than an influence, outlier, or
statistical analysis. It performs no optimization and makes no claim that a
frequently selected organization is better managed, causally effective, or
operationally transferable.

## Fit once, then audit the selected peer plan

The bundled `slacks_2x2` teaching data contain eight service organizations,
two resources, and two services:

```python
from deapack import BCC, DEAData, dataset_info, load_dataset

frame = load_dataset("slacks_2x2")
roles = dataset_info("slacks_2x2").roles
data = DEAData.from_frame(
    frame,
    dmu=roles["dmu"],
    inputs=roles["inputs"],
    outputs=roles["outputs"],
)

result = BCC(compute_slacks=False).fit(data)
frequency = result.reference_frequency()
frequency.reference_frame[
    [
        "reference_dmu_id",
        "reference_frequency",
        "self_reference_frequency",
        "other_reference_frequency",
        "reference_rate",
    ]
]
```

The convenience method is exactly equivalent to the functional API:

```python
from deapack import reference_frequency

same_account = reference_frequency(result)
```

The selected BCC plan gives:

| Organization | Total frequency | Self | Other organizations | Rate of 8 evaluations |
|---|---:|---:|---:|---:|
| A | 1 | 1 | 0 | 0.125 |
| B | 4 | 1 | 3 | 0.500 |
| C | 5 | 1 | 4 | 0.625 |
| D | 2 | 1 | 1 | 0.250 |
| E | 0 | 0 | 0 | 0.000 |
| F | 0 | 0 | 0 | 0.000 |
| G | 0 | 0 | 0 | 0.000 |
| H | 0 | 0 | 0 | 0.000 |

Organizations B and C recur in several other organizations' comparator plans.
That recurrence is a useful audit lead: their represented resource--service
mixes have comparative reach within this fitted sample. A manager might next
check whether their measurement records are sound and whether the practices
behind those quantities are institutionally transferable. The frequency does
not answer either question by itself.

## What is counted

For evaluated organization $o$ and eligible reference organization $j$, let
$\lambda_{oj}$ be its intensity in the certified selected peer plan and let
$\tau_{\mathrm{peer}}$ be the `peer_tolerance` recorded by the source result.
DEAPack reports

$$
F_j=\sum_o \mathbf 1\{\lambda_{oj}>\tau_{\mathrm{peer}}\}.
$$

It then separates

$$
F_j^{\mathrm{self}}
=\mathbf 1\{\lambda_{jj}>\tau_{\mathrm{peer}}\},
\qquad
F_j^{\mathrm{other}}
=\sum_{o\ne j}\mathbf 1\{\lambda_{oj}>\tau_{\mathrm{peer}}\},
$$

so that $F_j=F_j^{\mathrm{self}}+F_j^{\mathrm{other}}$. The reported
`reference_rate` is $F_j/n$, where $n$ is the complete number of evaluated
organizations.

The statistic counts **reported active edges above the source peer-reporting
threshold**, not intensity magnitudes. It is not an exact mathematical-support
count at or below that threshold. DEAPack does not add $\lambda_{oj}$ across
different evaluated organizations: those intensities belong to different
convex-combination accounts and have no common cross-organization quantity
interpretation. The original reported intensities remain available in
`frequency.edge_frame` for observation-specific audit.

## Interpret recurrence as an audit lead

A high `other_reference_frequency` can indicate that one observed operation is
comparatively useful across several fitted plans. It may justify a closer data
audit, a qualitative study of operating practices, or a pre-specified
sensitivity analysis. It does **not** establish any of the following:

- superior management, service quality, or welfare;
- a causal effect of the organization's practices;
- feasibility of transferring those practices to another organization;
- an outlier, influential-observation, or data-error diagnosis;
- a statistically stable population result; or
- membership in the union of all optimal reference sets.

A zero frequency is equally limited. It says that the organization has no
reported edge strictly above $\tau_{\mathrm{peer}}$ in this selected plan; it
does not establish exact zero mathematical support. The organization was still
part of the eligible technology and may constrain the frontier, become active
under another valid specification, or appear in an alternative optimum.

## One selected optimum, not every optimal reference set

DEA peer intensities can be nonunique even when the headline efficiency is
unique. This diagnostic describes the one complete, certified plan published
by the fitted result. It does not run secondary programs to enumerate possible
peers or measure how often an organization appears across alternate optima.

The limitation is machine-readable:

```python
frequency.metadata["alternate_optima_assessed"]       # False
frequency.metadata["global_reference_set_claim"]      # False
frequency.metadata["outlier_claim"]                   # False
frequency.metadata["inference"]                       # "none"
frequency.metadata["additional_solver_calls"]         # 0
frequency.metadata["source_peer_tolerance"]            # source threshold
frequency.metadata["reference_rate_denominator"]       # all evaluated organizations
```

Here “global” in the source model means that every organization in the single
cross-section is eligible for every evaluation. It must not be confused with a
claim about a *global reference set* formed by the union of peers across every
optimal solution.

## Relation to broader benchmark-identification methods

The idea that an efficient organization can be important because it repeatedly
serves as a benchmark has a longer ranking lineage. Torgersen, Førsund, and
Kittelsen develop a fuller slack-adjusted efficiency and benchmark-importance
procedure ([1996, DOI 10.1007/BF00162048](https://doi.org/10.1007/BF00162048)).
Doyle and Green describe cross-evaluation as an extension of reference-set
counting
([1995, DOI 10.1080/03155986.1995.11732281](https://doi.org/10.1080/03155986.1995.11732281)).
The present function implements neither ranking procedure and performs no
cross-appraisal.

Mehdiloozad and coauthors distinguish unary, maximal, and global reference
sets when a projection or its representation is nonunique
([2015, DOI 10.1016/j.ejor.2015.03.029](https://doi.org/10.1016/j.ejor.2015.03.029)).
`reference_frequency` does not solve their identification problem. It counts
the reported active edges above the source threshold in the one certified plan
already published by DEAPack, which is why `global_reference_set_claim`
remains false.

## Applicability and failure contract

This release accepts only a `DEAResult` that proves all of the following:

- one static, ungrouped, black-box cross-section;
- a global, self-appraisal reference policy;
- a continuous convex full-DEA envelopment estimator;
- a direct deterministic model fit rather than a composed analysis;
- one ordinary intensity account with columns `dmu_id`, `period`,
  `reference_dmu_id`, `reference_period`, and `lambda`;
- finite reported intensities strictly above the source `peer_tolerance`; and
- `peer_valid=True`, a certified `peer_status`, and an optimal semantic solver
  status for **every** evaluated organization.

Consequently, the function rejects FDH, FCH, FRH, panel, network, dynamic,
productivity, super-efficiency, cross-appraisal, grouped/metafrontier, and
role-specific multi-intensity results. Those designs require different
denominators or peer meanings and must not be collapsed into this count.

The release gate is atomic. If even one evaluated organization lacks a
certified active peer account, {func}`reference_frequency` raises
`ModelSpecificationError`; it does not drop that row and silently reduce the
denominator. The input `DEAResult` is not mutated.

## Returned tables

{class}`ReferenceFrequencyResult` contains four public objects:

| Object | Contents |
|---|---|
| `reference_frame` | one row for every organization in the global cross-section, including zero-frequency organizations |
| `edge_frame` | every certified reported selected-plan edge above the source threshold, its original `lambda`, and `is_self_reference` |
| `diagnostics` | one row per evaluation with active, self, and other peer counts and the source peer status |
| `metadata` | immutable method identity, counts, source identity, zero-solve ledger, and interpretation boundaries |

`frequency.summary()` returns a copy of `reference_frame`, and
`frequency.edges()` returns a copy of `edge_frame`. See {doc}`../api/analysis`
for the generated signatures and {doc}`../user-guide/results` for the parent
`DEAResult` contract.

For a concise shared rendering, use the public result interface:

```python
figure = result.plot(kind="references")
```

The renderer keeps self-selection distinct from selection by other
organizations and applies an explicit top-row readability rule for large
rosters. See {doc}`../user-guide/visualization` for the plotting contract. The
table above remains the complete eight-organization account.
