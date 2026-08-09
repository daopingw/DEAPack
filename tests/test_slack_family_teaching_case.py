from __future__ import annotations

import numpy as np

from deapack import (
    RAM,
    SBM,
    AdditiveDEA,
    DEAData,
    dataset_info,
    load_dataset,
)


def test_slack_family_book_case_holds_the_physical_plan_fixed() -> None:
    frame = load_dataset("slacks_2x2")
    roles = dataset_info("slacks_2x2").roles
    data = DEAData.from_frame(
        frame,
        dmu=roles["dmu"],
        inputs=roles["inputs"],
        outputs=roles["outputs"],
    )

    fits = {
        "additive": AdditiveDEA(returns_to_scale="vrs").fit(data),
        "ram": RAM().fit(data),
        "sbm": SBM(returns_to_scale="vrs").fit(data),
    }
    rows = {
        name: result.summary().set_index("dmu_id").loc["E"]
        for name, result in fits.items()
    }

    assert np.isclose(rows["additive"]["distance"], 1.985)
    assert np.isclose(rows["ram"]["score"], 0.50625)
    assert np.isclose(rows["sbm"]["score"], 0.5547634428448381)

    for result in fits.values():
        peers = result.peers("E").set_index("reference_dmu_id")["lambda"]
        assert np.isclose(peers.loc["B"], 0.25)
        assert np.isclose(peers.loc["C"], 0.75)

        slacks = result.slacks.query("dmu_id == 'E'").set_index(["role", "variable"])
        assert np.isclose(slacks.loc[("input", "labor"), "slack"], 0.0)
        assert np.isclose(slacks.loc[("input", "capital"), "slack"], 1.125)
        assert np.isclose(slacks.loc[("output", "service"), "slack"], 0.6)
        assert np.isclose(slacks.loc[("output", "quality"), "slack"], 0.26)
