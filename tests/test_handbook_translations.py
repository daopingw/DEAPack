from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _load_checker() -> ModuleType:
    path = ROOT / "scripts" / "check_handbook_translations.py"
    specification = importlib.util.spec_from_file_location(
        "check_handbook_translations", path
    )
    assert specification is not None and specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    sys.modules["check_handbook_translations"] = module
    specification.loader.exec_module(module)
    return module


def _load_header_normalizer() -> ModuleType:
    path = ROOT / "scripts" / "normalize_handbook_po_headers.py"
    specification = importlib.util.spec_from_file_location(
        "normalize_handbook_po_headers", path
    )
    assert specification is not None and specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    sys.modules["normalize_handbook_po_headers"] = module
    specification.loader.exec_module(module)
    return module


def _load_math_localizer() -> ModuleType:
    path = ROOT / "scripts" / "localize_handbook_math_labels.py"
    specification = importlib.util.spec_from_file_location(
        "localize_handbook_math_labels", path
    )
    assert specification is not None and specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    sys.modules["localize_handbook_math_labels"] = module
    specification.loader.exec_module(module)
    return module


def _catalog(tmp_path: Path, body: str) -> Path:
    path = tmp_path / "chapter.po"
    path.write_text(
        'msgid ""\nmsgstr ""\n"Language: zh_CN\\n"\n\n' + body,
        encoding="utf-8",
    )
    return path


def test_parser_reads_multiline_message_and_flags(tmp_path: Path) -> None:
    module = _load_checker()
    path = _catalog(
        tmp_path,
        '#, fuzzy\nmsgid "A long "\n"source sentence."\nmsgstr "一条"\n"译文。"\n',
    )

    assert module.parse_po(path) == [
        module.POMessage(
            path=path,
            line=6,
            msgid="A long source sentence.",
            msgstr="一条译文。",
            fuzzy=True,
        )
    ]


def test_invariant_gate_preserves_citations_targets_code_and_math(
    tmp_path: Path,
) -> None:
    module = _load_checker()
    path = _catalog(tmp_path, 'msgid "x"\nmsgstr "x"\n')
    message = module.POMessage(
        path=path,
        line=1,
        msgid=(
            "See {cite:p}`farrell1957` and {doc}`chapter title <route>`; "
            "fit `BCCInput` at $d^t(z)$ first."
        ),
        msgstr=(
            "先在 $d^t(z)$ 下估计 `BCCInput`，参见 {cite:p}`farrell1957` "  # noqa: RUF001
            "和 {doc}`本章 <route>`。"
        ),
        fuzzy=False,
    )

    assert module.invariant_errors(message) == []
    changed = module.POMessage(
        path=path,
        line=1,
        msgid=message.msgid,
        msgstr=message.msgstr.replace("farrell1957", "farrell1958"),
        fuzzy=False,
    )
    assert "citation changed" in module.invariant_errors(changed)


def test_complete_gate_rejects_empty_fuzzy_or_english_prose(tmp_path: Path) -> None:
    module = _load_checker()
    _catalog(
        tmp_path,
        'msgid "A substantive English sentence remains here."\n'
        'msgstr "A substantive English sentence remains here."\n\n'
        'msgid "Another sentence needs translation."\nmsgstr ""\n',
    )

    report = module.audit(tmp_path)
    assert report.messages == 2
    assert report.untranslated == 1
    assert report.header_errors == 0
    assert report.prose_errors == 1
    assert not report.complete
    with pytest.raises(RuntimeError, match="translation gate failed"):
        module.audit(tmp_path, require_complete=True)


def test_display_equations_are_preserved_but_do_not_require_chinese_prose(
    tmp_path: Path,
) -> None:
    module = _load_checker()
    equation = (
        "\n"
        "s^-\\geq0\\quad\\text{for input excess},\\qquad\n"
        "s^+\\geq0\\quad\\text{for output shortfall}.\n"
    )
    message = module.POMessage(
        path=_catalog(tmp_path, 'msgid "x"\nmsgstr "x"\n'),
        line=1,
        msgid=equation,
        msgstr=equation,
        fuzzy=False,
    )

    assert module._is_display_math(equation)
    assert not module._requires_chinese_prose(message)
    assert (
        sum(
            "mathematical text label untranslated" in error
            for error in module.invariant_errors(message)
        )
        == 2
    )

    localized = module.POMessage(
        path=message.path,
        line=message.line,
        msgid=message.msgid,
        msgstr=(
            message.msgstr.replace("input excess", "投入冗余").replace(
                "output shortfall", "产出不足"
            )
        ),
        fuzzy=False,
    )
    assert module.invariant_errors(localized) == []

    untranslated = module.POMessage(
        path=message.path,
        line=message.line,
        msgid=message.msgid,
        msgstr=message.msgstr,
        fuzzy=False,
    )
    assert any(
        "mathematical text label untranslated" in error
        for error in module.invariant_errors(untranslated)
    )

    changed_math = module.POMessage(
        path=message.path,
        line=message.line,
        msgid=message.msgid,
        msgstr=localized.msgstr.replace("s^+", "s^b"),
        fuzzy=False,
    )
    assert (
        "displayed mathematics changed outside text labels"
        in module.invariant_errors(changed_math)
    )

    compact_equation = module.POMessage(
        path=message.path,
        line=message.line,
        msgid="\nz^\\sigma=(x^\\sigma,y^\\sigma,b^\\sigma),\n",
        msgstr="\nz^\\sigma=(x^\\sigma,y^\\sigma,b^\\sigma),\n",
        fuzzy=False,
    )
    assert not module._requires_chinese_prose(compact_equation)


def test_current_catalog_inventory_is_auditable() -> None:
    module = _load_checker()
    report = module.audit(ROOT / "book" / "locale" / "zh_CN" / "LC_MESSAGES")

    assert report.catalogs == 31  # 30 reader sources plus one theme-UI catalog
    assert report.messages > 2_500
    assert report.translated + report.untranslated == report.messages


def test_source_sync_gate_rejects_stale_or_missing_catalog_messages(
    tmp_path: Path,
) -> None:
    module = _load_checker()
    locale_root = tmp_path / "locale"
    template_root = tmp_path / "gettext"
    locale_root.mkdir()
    template_root.mkdir()
    _catalog(
        locale_root,
        'msgid "Current source message."\nmsgstr "当前源消息。"\n',
    )
    template = template_root / "chapter.pot"
    template.write_text(
        'msgid ""\nmsgstr ""\n\nmsgid "Current source message."\nmsgstr ""\n',
        encoding="utf-8",
    )

    report = module.audit(locale_root, template_root=template_root)
    assert report.source_sync_errors == 0
    assert report.complete

    template.write_text(
        'msgid ""\nmsgstr ""\n\nmsgid "Changed source message."\nmsgstr ""\n',
        encoding="utf-8",
    )
    report = module.audit(locale_root, template_root=template_root)
    assert report.source_sync_errors == 2
    assert not report.complete
    with pytest.raises(RuntimeError, match="translation gate failed"):
        module.audit(
            locale_root,
            template_root=template_root,
            require_complete=True,
        )


def test_chinese_theme_interface_labels_are_explicit() -> None:
    catalog = (
        ROOT / "book" / "locale" / "zh_CN" / "LC_MESSAGES" / "sphinx.po"
    ).read_text(encoding="utf-8")
    conf = (ROOT / "book" / "conf.py").read_text(encoding="utf-8")

    assert 'msgstr "收起侧栏"' in catalog
    assert 'msgstr "展开侧栏"' in catalog
    assert 'msgstr "颜色模式"' in catalog
    assert 'msgstr "跟随系统"' in catalog
    assert 'html_theme_options["header_dropdown_text"] = "更多"' in conf


def test_documentation_ci_builds_both_handbook_languages() -> None:
    workflow = (ROOT / ".github" / "workflows" / "documentation.yml").read_text(
        encoding="utf-8"
    )

    assert "check_handbook_translations.py --require-complete" in workflow
    assert "--template-root _build/handbook-gettext" in workflow
    assert "-b gettext book _build/handbook-gettext" in workflow
    assert "localize_handbook_math_labels.py --check" in workflow
    assert "DEAPACK_BOOK_LANGUAGE=zh_CN" in workflow
    assert "book _site/book/zh_CN" in workflow
    assert "make -C book pdf-zh" in workflow
    assert "texlive-lang-chinese" in workflow
    assert "texlive-xetex" in workflow
    assert "book/_build/pdf/*.pdf" in workflow


def test_chinese_read_the_docs_entry_point_is_explicit() -> None:
    configuration = (ROOT / "book" / ".readthedocs-zh.yaml").read_text(encoding="utf-8")
    conf = (ROOT / "book" / "conf_zh.py").read_text(encoding="utf-8")

    assert "configuration: book/conf_zh.py" in configuration
    assert "check_handbook_translations.py --require-complete" in configuration
    assert "--template-root book/_build/gettext" in configuration
    assert "localize_handbook_math_labels.py --check" in configuration
    assert "install:" in configuration
    assert "post_install:" in configuration
    assert "post_create_environment:" not in configuration
    assert "--no-build-isolation --requirement book/requirements.txt" in configuration
    assert (
        "release_toolchain.py verify-installed --profile docs --require-ci-platform"
        in configuration
    )
    assert "requirements:" not in configuration
    assert 'os.environ["DEAPACK_BOOK_LANGUAGE"] = "zh_CN"' in conf


def test_chinese_browser_search_uses_the_embedded_stemmer_name(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("DEAPACK_BOOK_LANGUAGE", "zh_CN")
    path = ROOT / "book" / "conf.py"
    specification = importlib.util.spec_from_file_location("book_conf_zh_test", path)
    assert specification is not None and specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)

    registered: list[type] = []

    class App:
        @staticmethod
        def add_search_language(language_class: type) -> None:
            registered.append(language_class)

    module.setup(App())

    from sphinx.search.zh import SearchChinese

    if SearchChinese.js_stemmer_rawcode == "english-stemmer.js":
        assert len(registered) == 1
        assert registered[0].lang == "zh"
        assert registered[0].language_name == "English"
    else:
        assert registered == []


def test_po_header_normalizer_removes_placeholders_and_license_inference(
    tmp_path: Path,
) -> None:
    module = _load_header_normalizer()
    path = _catalog(tmp_path, 'msgid "Question"\nmsgstr "问题"\n')
    text = path.read_text(encoding="utf-8")
    text = (
        "# SOME DESCRIPTIVE TITLE.\n"
        "# This file is distributed under the same license as the package.\n"
        + text.replace(
            '"Language: zh_CN\\n"',
            '"Project-Id-Version: PROJECT VERSION\\n"\n'
            '"Report-Msgid-Bugs-To: \\n"\n'
            '"POT-Creation-Date: 2026-08-09 00:31+0100\\n"\n'
            '"PO-Revision-Date: YEAR-MO-DA HO:MI+ZONE\\n"\n'
            '"Last-Translator: FULL NAME <EMAIL@ADDRESS>\\n"\n'
            '"Language: zh_CN\\n"\n'
            '"Language-Team: zh_CN <LL@li.org>\\n"\n'
            '"Plural-Forms: nplurals=1; plural=0;\\n"\n'
            '"MIME-Version: 1.0\\n"\n'
            '"Content-Type: text/plain; charset=utf-8\\n"\n'
            '"Content-Transfer-Encoding: 8bit\\n"\n'
            '"Generated-By: Babel 2.18.0\\n"',
        )
    )
    path.write_text(text, encoding="utf-8")

    assert module.normalize(path, revision_date="2026-08-09 03:00+0100")
    normalized = path.read_text(encoding="utf-8")
    assert "same license" not in normalized
    assert "EMAIL@ADDRESS" not in normalized
    assert "LL@li.org" not in normalized
    assert "DEAPack Handbook Preview 1" in normalized
    assert "PO-Revision-Date: 2026-08-09 03:00+0100" in normalized
    assert "component license is pending maintainer approval" in normalized
    assert module.normalize(path, revision_date="2026-08-09 03:00+0100") is False


def test_current_po_headers_have_no_template_people_or_license_claim() -> None:
    catalogs = sorted((ROOT / "book" / "locale" / "zh_CN").rglob("*.po"))
    assert catalogs
    for path in catalogs:
        source = path.read_text(encoding="utf-8")
        assert "SOME DESCRIPTIVE TITLE" not in source
        assert "FIRST AUTHOR" not in source
        assert "EMAIL@ADDRESS" not in source
        assert "LL@li.org" not in source
        assert "same license as" not in source


def test_equation_label_localizer_changes_prose_but_not_mathematics() -> None:
    module = _load_math_localizer()
    checker = _load_checker()
    source = (
        "\n"
        "s^-\\geq0\\quad\\text{for input excess},\\qquad\n"
        "s^+\\geq0\\quad\\text{for desirable-output shortfall}.\n"
    )
    used: set[str] = set()
    translated = module.expected_translation(source, source, used=used)

    assert "表示投入冗余" in translated
    assert "表示合意产出不足" in translated
    assert used == {"for input excess", "for desirable-output shortfall"}
    assert checker._math_skeleton(translated) == checker._math_skeleton(source)
