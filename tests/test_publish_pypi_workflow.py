"""Release-workflow regressions for supported-Python wheel validation."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_production_publish_smokes_one_wheel_on_every_supported_python() -> None:
    workflow = (ROOT / ".github" / "workflows" / "publish-pypi.yml").read_text(
        encoding="utf-8"
    )

    assert 'python-version: ["3.10", "3.11", "3.12", "3.13"]' in workflow
    assert "needs: [build, wheel-smoke]" in workflow
    assert "Download the validated distributions" in workflow
    assert "scripts/smoke_installed_distribution.py" in workflow
    assert workflow.count("deapack-${{ inputs.version }}-distributions") >= 3


def test_installed_wheel_smoke_covers_the_documented_top_level_import() -> None:
    smoke = (ROOT / "scripts" / "smoke_installed_distribution.py").read_text(
        encoding="utf-8"
    )

    assert "from deapack import BCCInput, DEAData, dataset_info, load_dataset" in smoke
    assert "BCCInput().fit(data)" in smoke
