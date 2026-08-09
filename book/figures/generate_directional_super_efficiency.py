"""Generate Ray's package-native peer-replacement result figure."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np

from deapack import (
    DEAData,
    RayDirectionalSuperEfficiency,
    dataset_info,
    load_dataset,
)

OUTPUT = (
    Path(__file__).resolve().parents[1]
    / "_static"
    / "figures"
    / "directional-super-stress-result.svg"
)

matplotlib.rcParams["svg.hashsalt"] = "deapack-book-directional-super-stress"
matplotlib.rcParams["svg.fonttype"] = "none"


def directional_super_efficiency_figure() -> None:
    """Render the neutral multivariate peer-replacement stress result."""
    frame = load_dataset("directional_super_multivariate_stress")
    roles = dataset_info("directional_super_multivariate_stress").roles
    data = DEAData.from_frame(
        frame,
        dmu=roles["dmu"],
        inputs=roles["inputs"],
        outputs=roles["outputs"],
    )
    result = RayDirectionalSuperEfficiency().fit(data)
    summary = result.summary()
    assert len(summary) == len(frame)
    assert np.isfinite(summary["nl_super_efficiency"].to_numpy(dtype=np.float64)).all()
    assert summary["ranking_value_valid"].all()
    assert summary["score_valid"].sum() == len(frame) - 1

    figure = result.plot(
        kind="performance",
        metric="nl_super_efficiency",
        theme="deapack",
    )
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(
        OUTPUT,
        format="svg",
        bbox_inches="tight",
        metadata={
            "Title": "Peer-replacement exposure in a multivariate stress case",
            "Date": None,
        },
    )
    plt.close(figure)


def main() -> None:
    directional_super_efficiency_figure()


if __name__ == "__main__":
    main()
