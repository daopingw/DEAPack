from __future__ import annotations

import importlib.util
import json
import re
import sys
from pathlib import Path
from types import ModuleType
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parents[1]


def _load_localizer() -> ModuleType:
    path = ROOT / "book" / "figures" / "localize_handbook_figures_zh.py"
    specification = importlib.util.spec_from_file_location(
        "localize_handbook_figures_zh", path
    )
    assert specification is not None and specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    sys.modules["localize_handbook_figures_zh"] = module
    specification.loader.exec_module(module)
    return module


def test_reviewed_chinese_figure_variants_are_complete_and_current() -> None:
    module = _load_localizer()
    diagnostics = module.generate(
        module.DEFAULT_CATALOG,
        module.DEFAULT_SOURCE_DIR,
        module.DEFAULT_OUTPUT_DIR,
        check=True,
    )

    assert len(diagnostics) == 53
    assert all(replacements > 0 for _name, replacements, _digest in diagnostics)
    assert all(len(digest) == 64 for _name, _replacements, digest in diagnostics)


def test_chinese_figure_catalog_has_explicit_translation_or_preservation() -> None:
    catalog_path = ROOT / "book" / "figures" / "zh_CN_labels.json"
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    assert catalog["schema_version"] == 1
    assert catalog["locale"] == "zh_CN"

    referenced: set[str] = set()
    for path in (ROOT / "book").rglob("*.md"):
        if "_archive" in path.parts:
            continue
        source = path.read_text(encoding="utf-8")
        referenced.update(
            Path(match).name
            for match in re.findall(
                r"^```\{(?:figure|image)\}\s+([^\s]+\.svg)\s*$",
                source,
                flags=re.MULTILINE,
            )
        )
    assert set(catalog["files"]) == referenced
    assert len(referenced) == 53

    for name, record in catalog["files"].items():
        assert len(record["source_sha256"]) == 64
        assert record["translations"]
        assert not set(record["translations"]).intersection(record["preserve"])
        localized = ROOT / "book" / "_static" / "figures" / "zh_CN" / name
        root = ElementTree.parse(localized).getroot()
        assert root.tag.endswith("svg")
        rendered_text = " ".join("".join(root.itertext()).split())
        assert any("\u3400" <= character <= "\u9fff" for character in rendered_text)

    output_names = {
        path.name
        for path in (ROOT / "book" / "_static" / "figures" / "zh_CN").glob("*.svg")
    }
    assert output_names == referenced


def test_chinese_sphinx_route_and_release_gate_select_localized_figures() -> None:
    configuration = (ROOT / "book" / "conf.py").read_text(encoding="utf-8")
    makefile = (ROOT / "book" / "Makefile").read_text(encoding="utf-8")
    workflow = (ROOT / ".github" / "workflows" / "documentation.yml").read_text(
        encoding="utf-8"
    )

    assert (
        'figure_language_filename = "{path}{language}/{basename}{ext}"' in configuration
    )
    assert "figures/localize_handbook_figures_zh.py" in makefile
    assert "localize_handbook_figures_zh.py --check" in workflow
