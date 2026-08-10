#!/usr/bin/env python3
"""Smoke-test an installed wheel from outside the repository source tree."""

from __future__ import annotations

import json
import tempfile
import zipfile
from pathlib import Path

import deapack
from deapack import BCCInput, DEAData, dataset_info, load_dataset


def main() -> None:
    frame = load_dataset("slacks_2x2")
    roles = dataset_info("slacks_2x2").roles
    data = DEAData.from_frame(
        frame,
        dmu=roles["dmu"],
        inputs=roles["inputs"],
        outputs=roles["outputs"],
    )
    result = BCCInput().fit(data)
    if result.metadata["method_id"] != "static.radial":
        raise RuntimeError("installed radial fit lost its canonical method identity")
    frequency = result.reference_frequency()
    if len(frequency.reference_frame) != len(frame):
        raise RuntimeError("installed reference-frequency account is incomplete")

    with tempfile.TemporaryDirectory(prefix="deapack-wheel-smoke-") as directory:
        destination = result.export_bundle(Path(directory) / "audit.zip")
        with zipfile.ZipFile(destination) as archive:
            manifest = json.loads(archive.read("manifest.json"))
        if manifest["method_id"] != "static.radial":
            raise RuntimeError("installed audit bundle lost its method identity")
    print(
        f"installed-wheel smoke passed: DEAPack {deapack.__version__}, "
        f"{len(frame)} organizations"
    )


if __name__ == "__main__":
    main()
