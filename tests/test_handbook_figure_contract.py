from __future__ import annotations

import importlib.util
import re
from fractions import Fraction
from pathlib import Path
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parents[1]
ML_FIGURE = (
    ROOT / "book" / "_static" / "figures" / "malmquist-luenberger-frontier-account.svg"
)
ENVIRONMENTAL_DISTANCE_MATRIX = (
    ROOT / "book" / "_static" / "figures" / "environmental-four-distance-matrix.svg"
)
ENVIRONMENTAL_ML_PERFORMANCE_FIGURE = (
    ROOT / "book" / "_static" / "figures" / "environmental-ml-performance-result.svg"
)
ENVIRONMENTAL_PRODUCTIVITY_CHAPTER = (
    ROOT
    / "book"
    / "chapters"
    / "04-productivity"
    / "environmental-productivity-ml-common-reference.md"
)
ML_CHAPTER = (
    ROOT
    / "specs"
    / "archive"
    / "book-drafts"
    / "superseded"
    / "chapters"
    / "04-productivity"
    / "15-malmquist-luenberger.md"
)
MATERIAL_BALANCE_TARGETS = (
    ROOT / "book" / "_static" / "figures" / "material-balance-management-targets.svg"
)
MATERIAL_BALANCE_CHAPTER = (
    ROOT
    / "specs"
    / "archive"
    / "book-drafts"
    / "documentation-only"
    / "chapters"
    / "03-environmental"
    / "10-material-balance.md"
)
ECONOMIC_OBJECTIVES = (
    ROOT / "book" / "_static" / "figures" / "economic-objectives-management-map.svg"
)
PROFIT_RECOVERY_BRIDGE = (
    ROOT / "book" / "_static" / "figures" / "profit-recovery-bridge.svg"
)
ECONOMIC_CHAPTER = (
    ROOT / "book" / "chapters" / "02-classical" / "economic-efficiency-under-prices.md"
)
NETWORK_ACCOUNTS = (
    ROOT / "book" / "_static" / "figures" / "two-stage-accounting-choices.svg"
)
NETWORK_SYSTEM_FIGURE = (
    ROOT / "book" / "_static" / "figures" / "network-system-performance-result.svg"
)
NETWORK_CHAPTER = (
    ROOT
    / "book"
    / "chapters"
    / "05-network"
    / "network-dea-organizations-links-responsibility.md"
)
HICKS_MOORSTEEN_FIGURE = (
    ROOT / "book" / "_static" / "figures" / "hicks-moorsteen-accounting.svg"
)
HICKS_MOORSTEEN_PERFORMANCE_FIGURE = (
    ROOT / "book" / "_static" / "figures" / "hicks-moorsteen-performance-result.svg"
)
HICKS_MOORSTEEN_CHAPTER = (
    ROOT / "book" / "chapters" / "04-productivity" / "17-hicks-moorsteen.md"
)
LUENBERGER_LEDGER = (
    ROOT / "book" / "_static" / "figures" / "luenberger-programme-ledger.svg"
)
LUENBERGER_PERFORMANCE_FIGURE = (
    ROOT / "book" / "_static" / "figures" / "luenberger-performance-result.svg"
)
LUENBERGER_CHAPTER = ROOT / "book" / "chapters" / "04-productivity" / "12-luenberger.md"
METHOD_ATLAS = ROOT / "book" / "_static" / "figures" / "method-atlas-routes.svg"
NETWORK_SBM_GOVERNANCE = (
    ROOT / "book" / "_static" / "figures" / "network-sbm-governance.svg"
)
NETWORK_SBM_PROCESS_FIGURE = (
    ROOT / "book" / "_static" / "figures" / "three-process-service-account-result.svg"
)
NETWORK_SBM_PROCESS_CHAPTER = (
    ROOT / "book" / "chapters" / "05-network" / "20-network-sbm.md"
)
SBM_IMPROVEMENT_FIGURE = (
    ROOT / "book" / "_static" / "figures" / "sbm-slack-contrast-result.svg"
)
RADIAL_IMPROVEMENT_FIGURE = (
    ROOT / "book" / "_static" / "figures" / "radial-improvement-result.svg"
)
RADIAL_CHAPTER = ROOT / "book" / "chapters" / "02-classical" / "03-classical-radial.md"
DDF_IMPROVEMENT_FIGURE = (
    ROOT / "book" / "_static" / "figures" / "ddf-improvement-result.svg"
)
DDF_PROGRAMME_CONTRACTS_FIGURE = (
    ROOT / "book" / "_static" / "figures" / "ddf-programme-contracts-result.svg"
)
RANGE_DIRECTIONAL_SIGNED_FIGURE = (
    ROOT / "book" / "_static" / "figures" / "range-directional-signed-opportunity.svg"
)
DDF_CHAPTER = ROOT / "book" / "chapters" / "02-classical" / "05-directional-distance.md"
SLACK_FAMILY_RULERS_FIGURE = (
    ROOT / "book" / "_static" / "figures" / "slack-family-rulers-result.svg"
)
SBM_CHAPTER = ROOT / "book" / "chapters" / "02-classical" / "04-sbm.md"
SBM_MANAGEMENT_QUESTIONS = (
    ROOT / "book" / "_static" / "figures" / "sbm-management-questions.svg"
)
UNDESIRABLE_SBM_IMPROVEMENT_FIGURE = (
    ROOT / "book" / "_static" / "figures" / "undesirable-sbm-improvement-result.svg"
)
UNDESIRABLE_SBM_CHAPTER = (
    ROOT / "book" / "chapters" / "03-environmental" / "07-undesirable-output-sbm.md"
)
ENVIRONMENTAL_DDF_IMPROVEMENT_FIGURE = (
    ROOT / "book" / "_static" / "figures" / "environmental-ddf-improvement-result.svg"
)
ENVIRONMENTAL_DDF_CHAPTER = (
    ROOT / "book" / "chapters" / "03-environmental" / "06-undesirable-outputs-ddf.md"
)
WEAK_DISPOSAL_TECHNOLOGIES_FIGURE = (
    ROOT / "book" / "_static" / "figures" / "weak-disposal-technologies.svg"
)
RESULT_FIGURE_GENERATOR = ROOT / "book" / "figures" / "generate_result_figures.py"
RESULT_FIGURE_README = ROOT / "book" / "figures" / "FIGURE_WORKFLOW.md"
THREE_PERFORMANCE_ACCOUNTS_FIGURE = (
    ROOT / "book" / "_static" / "figures" / "three-performance-accounts-result.svg"
)
PEER_ELIGIBILITY_SENSITIVITY_FIGURE = (
    ROOT / "book" / "_static" / "figures" / "peer-eligibility-sensitivity-result.svg"
)
REFERENCE_FREQUENCY_FIGURE = (
    ROOT / "book" / "_static" / "figures" / "reference-frequency-result.svg"
)
DYNAMIC_TRAJECTORY_FIGURE = (
    ROOT / "book" / "_static" / "figures" / "carryover-portfolio-trajectory-result.svg"
)
DYNAMIC_SCORED_CARRYOVER_FIGURE = (
    ROOT / "book" / "_static" / "figures" / "dynamic-sbm-scored-backlog-result.svg"
)
DYNAMIC_TRAJECTORY_CHAPTER = (
    ROOT / "book" / "chapters" / "06-dynamic" / "dynamic-dea-carryovers-trajectories.md"
)
CRS_VRS_FRONTIERS = ROOT / "book" / "_static" / "figures" / "crs-vrs-frontiers.svg"
SCALE_EFFICIENCY_RESULT = (
    ROOT / "book" / "_static" / "figures" / "scale-efficiency-performance-result.svg"
)
METAFRONTIER_DECOMPOSITION_FIGURE = (
    ROOT / "book" / "_static" / "figures" / "metafrontier-decomposition-result.svg"
)
METAFRONTIER_CHAPTER = (
    ROOT / "book" / "chapters" / "07-heterogeneity" / "23-metafrontier.md"
)
MALMQUIST_PERFORMANCE_FIGURE = (
    ROOT / "book" / "_static" / "figures" / "trajectory-contrast-performance-result.svg"
)
MALMQUIST_REFERENCE_FIGURE = (
    ROOT / "book" / "_static" / "figures" / "reference-technology-windows.svg"
)
MALMQUIST_CHAPTER = (
    ROOT
    / "book"
    / "chapters"
    / "04-productivity"
    / "malmquist-productivity-reference-information.md"
)
COMMUNITY_HOSPITAL_CHAPTER = (
    ROOT / "book" / "chapters" / "02-classical" / "community-hospital-capstone.md"
)
COMMUNITY_HOSPITAL_SCREENING_FIGURE = (
    ROOT / "book" / "_static" / "figures" / "community-hospital-screening.svg"
)
COMMUNITY_HOSPITAL_PERFORMANCE_FIGURE = (
    ROOT / "book" / "_static" / "figures" / "community-hospital-performance.svg"
)
COMMUNITY_HOSPITAL_H048_FIGURE = (
    ROOT / "book" / "_static" / "figures" / "community-hospital-h048-improvement.svg"
)
COMMUNITY_HOSPITAL_SENSITIVITY_FIGURE = (
    ROOT / "book" / "_static" / "figures" / "community-hospital-roster-sensitivity.svg"
)

ACTIVE_RESULT_FIGURES = tuple(
    ROOT / "book" / "_static" / "figures" / name
    for name in (
        "ddf-improvement-result.svg",
        "ddf-programme-contracts-result.svg",
        "community-hospital-h048-improvement.svg",
        "community-hospital-performance.svg",
        "community-hospital-roster-sensitivity.svg",
        "community-hospital-screening.svg",
        "dynamic-sbm-scored-backlog-result.svg",
        "carryover-portfolio-trajectory-result.svg",
        "environmental-ddf-improvement-result.svg",
        "environmental-ml-performance-result.svg",
        "hicks-moorsteen-performance-result.svg",
        "luenberger-performance-result.svg",
        "trajectory-contrast-performance-result.svg",
        "metafrontier-decomposition-result.svg",
        "three-process-service-account-result.svg",
        "network-system-performance-result.svg",
        "peer-eligibility-sensitivity-result.svg",
        "radial-frontier-result.svg",
        "radial-improvement-result.svg",
        "reference-frequency-result.svg",
        "sbm-slack-contrast-result.svg",
        "scale-efficiency-performance-result.svg",
        "slack-family-rulers-result.svg",
        "three-performance-accounts-result.svg",
        "undesirable-sbm-improvement-result.svg",
    )
)


def _normalized_svg_text(path: Path) -> str:
    root = ElementTree.parse(path).getroot()
    return " ".join("".join(root.itertext()).split())


def _minimum_svg_font_at_rendered_width(path: Path, rendered_width: float) -> float:
    root = ElementTree.parse(path).getroot()
    viewbox = tuple(float(value) for value in root.attrib["viewBox"].split())
    source = path.read_text(encoding="utf-8")
    css_font_sizes = tuple(
        float(value) for value in re.findall(r"font-size:\s*([0-9.]+)px", source)
    )
    attribute_font_sizes = tuple(
        float(value) for value in re.findall(r'font-size=["\']([0-9.]+)["\']', source)
    )
    font_sizes = css_font_sizes + attribute_font_sizes
    assert font_sizes
    return min(font_sizes) * rendered_width / viewbox[2]


def test_dense_part_two_figures_remain_legible_at_handbook_column_width() -> None:
    for path in (
        RADIAL_IMPROVEMENT_FIGURE,
        DDF_PROGRAMME_CONTRACTS_FIGURE,
        SLACK_FAMILY_RULERS_FIGURE,
    ):
        assert _minimum_svg_font_at_rendered_width(path, 600.0) >= 9.0, path.name


def test_all_active_static_account_figures_rebuild_from_an_empty_directory(
    tmp_path: Path,
) -> None:
    generator_path = ROOT / "book" / "figures" / "generate_concept_figures.py"
    module_spec = importlib.util.spec_from_file_location(
        "deapack_book_foundation_figures",
        generator_path,
    )
    assert module_spec is not None and module_spec.loader is not None
    module = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(module)

    output = tmp_path / "empty-target"
    module.OUTPUT_DIR = output
    module.main()

    for name in (
        "dynamic-sbm-carryovers.svg",
        "metafrontier-management-account.svg",
        "sbm-management-questions.svg",
        "weak-disposal-technologies.svg",
    ):
        rebuilt = output / name
        checked_in = ROOT / "book" / "_static" / "figures" / name
        assert rebuilt.read_bytes() == checked_in.read_bytes()


def test_dense_part_three_figures_remain_legible_at_handbook_column_width() -> None:
    for path in (
        WEAK_DISPOSAL_TECHNOLOGIES_FIGURE,
        ENVIRONMENTAL_DDF_IMPROVEMENT_FIGURE,
        UNDESIRABLE_SBM_IMPROVEMENT_FIGURE,
    ):
        assert _minimum_svg_font_at_rendered_width(path, 600.0) >= 9.0, path.name


def test_portrait_figures_reserve_room_for_pdf_captions_and_page_furniture() -> None:
    directional = DDF_CHAPTER.read_text(encoding="utf-8")
    environmental = ENVIRONMENTAL_DDF_CHAPTER.read_text(encoding="utf-8")

    assert "ddf-programme-contracts-result.svg" in directional
    assert ":width: 78%" in directional
    assert "weak-disposal-technologies.svg" in environmental
    assert ":width: 72%" in environmental


def test_range_directional_signed_figure_is_original_exact_and_reproducible() -> None:
    generator_path = ROOT / "book" / "figures" / "generate_concept_figures.py"
    module_spec = importlib.util.spec_from_file_location(
        "deapack_book_rdm_figure",
        generator_path,
    )
    assert module_spec is not None and module_spec.loader is not None
    module = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(module)

    rebuilt = module.range_directional_signed_opportunity() + "\n"
    assert RANGE_DIRECTIONAL_SIGNED_FIGURE.read_text(encoding="utf-8") == rebuilt

    focus = (Fraction(-2), Fraction(1))
    north = (Fraction(-1), Fraction(5))
    east = (Fraction(4), Fraction(0))
    aspiration = (Fraction(4), Fraction(5))
    direction = tuple(
        best - observed for best, observed in zip(aspiration, focus, strict=True)
    )
    target = tuple(
        observed + Fraction(1, 2) * opportunity
        for observed, opportunity in zip(focus, direction, strict=True)
    )
    witness = tuple(
        Fraction(3, 5) * n_value + Fraction(2, 5) * e_value
        for n_value, e_value in zip(north, east, strict=True)
    )
    assert direction == (Fraction(6), Fraction(4))
    assert target == witness == (Fraction(1), Fraction(3))

    root = ElementTree.parse(RANGE_DIRECTIONAL_SIGNED_FIGURE).getroot()
    assert root.attrib["role"] == "img"
    assert root.attrib["aria-labelledby"] == "title description"
    text = _normalized_svg_text(RANGE_DIRECTIONAL_SIGNED_FIGURE)
    for phrase in (
        "project-designed signed example",
        "F (-2, 1)",
        "I - F = (4 - (-2), 5 - 1) = (6, 4)",
        "T = F + 1/2(I - F) = (1, 3)",
        "T = 0.6N + 0.4E",
        "RDM efficiency = 1 - β = 1/2",
        "no published empirical observations or source figure are reproduced",
    ):
        assert phrase in text

    forbidden = (
        "U3",
        "56.36%",
        "43.64%",
        "confidential bank-branch data",
        "Illustrative values follow Portela",
        "based on the paper's two-output illustration",
    )
    source = RANGE_DIRECTIONAL_SIGNED_FIGURE.read_text(encoding="utf-8")
    assert not any(fragment in source for fragment in forbidden)

    chapter = DDF_CHAPTER.read_text(encoding="utf-8")
    assert "range-directional-signed-opportunity.svg" in chapter
    assert "project-designed synthetic values" in chapter
    normalized_chapter = " ".join(chapter.split())
    assert (
        "no published empirical records or source figure are reproduced"
        in normalized_chapter
    )


def test_dense_part_four_figures_remain_legible_at_handbook_column_width() -> None:
    for path in (
        LUENBERGER_LEDGER,
        ML_FIGURE,
        HICKS_MOORSTEEN_FIGURE,
    ):
        assert _minimum_svg_font_at_rendered_width(path, 600.0) >= 9.0, path.name

    generator = (ROOT / "book" / "figures" / "generate_concept_figures.py").read_text(
        encoding="utf-8"
    )
    for call in (
        "luenberger_programme_ledger()",
        "malmquist_luenberger_frontier_account()",
        "hicks_moorsteen_accounting()",
    ):
        assert call in generator[generator.index("def main()") :]


def test_weak_disposal_map_preserves_the_three_technology_contracts() -> None:
    root = ElementTree.parse(WEAK_DISPOSAL_TECHNOLOGIES_FIGURE).getroot()
    assert root.attrib["role"] == "img"
    assert root.attrib["aria-labelledby"] == "title description"

    text = _normalized_svg_text(WEAK_DISPOSAL_TECHNOLOGIES_FIGURE)
    for phrase in (
        "Equality only",
        "Bλ = b̂",
        "does not, by itself, identify a named weak-disposal technology",
        "Common factor (CRS)",
        "one retention rate r",
        "linear source identity relies on CRS",
        "Activity-specific (VRS)",
        "different retention rates rj",
        "convex linearization retains VRS",
    ):
        assert phrase in text


def test_active_result_figures_keep_release_internals_out_of_reader_view() -> None:
    forbidden_fragments = (
        "method:",
        "reference:",
        "productivity.global_malmquist",
        "productivity.hicks_moorsteen",
        "productivity.luenberger",
        "productivity.malmquist",
        "analysis.scale_efficiency",
        "network.radial",
        "static.directional_distance",
        "static.radial",
        "static.sbm",
        "solver/certification unavailable",
        "solver=infeasible",
        "valid reported result",
        "headline results are unavailable",
        "public fits",
        "checked before rendering",
        "additional solve",
        "maximum reconstruction residual",
        "target status:",
        "solver-selected",
        "uniqueness-certified",
        "certified horizon",
        "dea-certified",
        "certified",
        "no new estimator or plot kind",
    )

    for path in ACTIVE_RESULT_FIGURES:
        text = _normalized_svg_text(path).casefold()
        leaked = tuple(fragment for fragment in forbidden_fragments if fragment in text)
        assert not leaked, f"{path.name} exposes internal release language: {leaked}"


def test_community_hospital_capstone_figures_are_reader_ready() -> None:
    expected = {
        COMMUNITY_HOSPITAL_SCREENING_FIGURE: (
            "Community-hospital study population screening",
            (
                "Who belongs in the community-hospital comparison?",
                "64 Raw records",
                "60 Usable records",
                "52 District-general hospitals",
                "48 Main comparison group",
                "Broad sensitivity group: all 52 district-general hospitals",
            ),
        ),
        COMMUNITY_HOSPITAL_PERFORMANCE_FIGURE: (
            "Primary efficiency distribution for 48 community hospitals",
            (
                "Resource stewardship across 48 community hospitals",
                "Input-oriented BCC",
                "Median 0.963",
                "Hospital-level differences",
                "H048 0.893",
                "12 hospitals score 1.000",
            ),
        ),
        COMMUNITY_HOSPITAL_H048_FIGURE: (
            "H048 peer and supported input reductions",
            (
                "H048: from an efficiency value to a management inquiry",
                "10,087 adjusted discharges",
                "44,371 outpatient encounters",
                "Selected peer H008 · weight 1.000",
                "Clinical staff",
                "Support staff",
                "Non-pay spend",
                "15.3% lower",
            ),
        ),
        COMMUNITY_HOSPITAL_SENSITIVITY_FIGURE: (
            "Community-hospital comparison-group sensitivity",
            (
                "How much depends on the hospital comparison group?",
                "42 of 48 values fall",
                "H048 0.893 → 0.865",
                "Mean change -3.3 points",
                "Largest fall -7.8 points",
            ),
        ),
    }

    for path, (title, phrases) in expected.items():
        root = ElementTree.parse(path).getroot()
        assert root.find("{http://www.w3.org/2000/svg}title").text == title
        text = _normalized_svg_text(path)
        for phrase in phrases:
            assert phrase in text, (path.name, phrase)
        assert _minimum_svg_font_at_rendered_width(path, 600.0) >= 9.0

    chapter = COMMUNITY_HOSPITAL_CHAPTER.read_text(encoding="utf-8")
    for path in expected:
        assert chapter.count(path.name) == 1


def test_community_hospital_figures_use_existing_public_model_families() -> None:
    source = RESULT_FIGURE_GENERATOR.read_text(encoding="utf-8")
    start = source.index("def _community_hospital_analysis()")
    end = source.index("\ndef main()", start)
    case = source[start:end]

    for public_call in (
        'load_dataset("community_hospital_capstone")',
        'dataset_info("community_hospital_capstone").roles',
        "DEAData.from_frame(",
        "BCCInput().fit(main_data)",
        'SBM(returns_to_scale="vrs").fit(main_data)',
        "BCCInput().fit(broad_data)",
        'scale_efficiency(main_data, orientation="input")',
        'primary_result.peers("H048")',
        'primary_result.targets_for("H048")',
    ):
        assert public_call in case

    main = source[source.index("def main()") :]
    for call in (
        "community_hospital_screening_figure()",
        "community_hospital_performance_figure()",
        "community_hospital_h048_improvement_figure()",
        "community_hospital_roster_sensitivity_figure()",
    ):
        assert call in main


def test_malmquist_chapter_keeps_one_core_result_plot_and_one_policy_check() -> None:
    adjacent_root = ElementTree.parse(MALMQUIST_PERFORMANCE_FIGURE).getroot()
    assert adjacent_root.find("{http://www.w3.org/2000/svg}title").text == (
        "Adjacent-period productivity change across service trajectories"
    )

    adjacent_text = _normalized_svg_text(MALMQUIST_PERFORMANCE_FIGURE)
    assert "Productivity change under adjacent-period benchmarks" in adjacent_text
    assert "Malmquist productivity index" in adjacent_text
    assert "1 → 2" in adjacent_text
    assert "Complete four-appraisal productivity account" in adjacent_text
    assert "Above 1: productivity growth; 1: no change; below 1: decline" in (
        adjacent_text
    )
    assert "each period-1 and period-2 operating plan is appraised against both" in (
        adjacent_text
    )

    chapter = MALMQUIST_CHAPTER.read_text(encoding="utf-8")
    assert "trajectory-contrast-performance-result.svg" in chapter
    assert "global-malmquist-performance-result.svg" not in chapter
    assert "result = FGNZMalmquist().fit(data)" in chapter
    assert "result = MalmquistDEA(" not in chapter
    assert "project-authored `multiperiod_trajectory_contrast`" in chapter
    assert "global_account = global_result.summary()" in chapter
    assert "Two global distances" in chapter
    assert "$GM=EC_G BPC_G$" in chapter
    for argument in (
        'kind="performance"',
        'metric="productivity_change"',
        "period=2",
        'view="points"',
    ):
        assert chapter.count(argument) == 1

    source = RESULT_FIGURE_GENERATOR.read_text(encoding="utf-8")
    start = source.index("def malmquist_figure()")
    end = source.index("\ndef hicks_moorsteen_figure()", start)
    figure_case = source[start:end]
    assert "adjacent = FGNZMalmquist().fit(data)" in figure_case
    assert "adjacent = MalmquistDEA(" not in figure_case


def test_malmquist_reference_figure_keeps_windows_inside_the_parent_family() -> None:
    root = ElementTree.parse(MALMQUIST_REFERENCE_FIGURE).getroot()
    assert root.tag.endswith("svg")
    assert root.attrib["role"] == "img"
    assert root.attrib["aria-labelledby"] == "title description"

    text = _normalized_svg_text(MALMQUIST_REFERENCE_FIGURE)
    assert "contemporaneous" in text.casefold()
    assert "global" in text.casefold()
    for excluded in (
        "biennial",
        "sequential",
        "rolling window",
        "B(t,t+1)",
        "B(t+1,t+2)",
    ):
        assert excluded.casefold() not in text.casefold()


def test_method_atlas_shows_only_the_handbook_core_routes() -> None:
    root = ElementTree.parse(METHOD_ATLAS).getroot()
    assert root.tag.endswith("svg")
    assert root.attrib["role"] == "img"
    assert root.attrib["aria-labelledby"] == "title description"

    text = _normalized_svg_text(METHOD_ATLAS)
    for family in (
        "radial / FDH",
        "SBM / additive",
        "environmental DDF",
        "undesirable-output SBM",
        "by-production relation",
        "network SBM",
        "open / connected systems",
        "carry-over technology",
        "dynamic SBM",
        "Malmquist / Luenberger",
        "period / common reference",
        "Hicks\u2013Moorsteen",
        "self, process, metafrontier,",
        "or intertemporal comparison",
    ):
        assert family in text

    assert "material balance / treatment" not in text
    assert "dynamic network SBM" not in text
    assert "sequential / shared resources" not in text
    assert "global / biennial" not in text
    assert "peer appraisal" not in text
    assert "ranking, exclusion, or allocation" not in text

    appendix = (ROOT / "book" / "appendices" / "unified-framework.md").read_text(
        encoding="utf-8"
    )
    assert "method-atlas-routes.svg" in appendix
    assert "study-composition-map.svg" not in appendix


def test_network_sbm_governance_figure_keeps_only_fixed_and_free_links() -> None:
    root = ElementTree.parse(NETWORK_SBM_GOVERNANCE).getroot()
    assert root.tag.endswith("svg")
    assert root.attrib["role"] == "img"
    assert root.attrib["aria-labelledby"] == "title description"

    text = _normalized_svg_text(NETWORK_SBM_GOVERNANCE)
    assert "One handoff, two core governance questions" in text
    assert "FIXED · INHERIT THE COMMITMENT" in text
    assert "FREE · COORDINATE A REDESIGN" in text
    assert "AS INPUT" not in text
    assert "AS OUTPUT" not in text
    assert "ACCOUNTABLE" not in text


def test_dynamic_trajectory_figure_freezes_the_joint_horizon_story() -> None:
    root = ElementTree.parse(DYNAMIC_TRAJECTORY_FIGURE).getroot()
    assert root.tag.endswith("svg")
    assert root.find("{http://www.w3.org/2000/svg}title").text == (
        "Connected carry-over trajectory for a service path"
    )

    text = _normalized_svg_text(DYNAMIC_TRAJECTORY_FIGURE)
    assert "Connected carry-over trajectory for a service path" in text
    assert "Observed carry-over" in text
    assert "Selected outgoing target" in text
    assert "Inherited from preceding period" in text
    assert "Horizon performance" in text
    assert "not a period average" in text
    assert (
        "one jointly feasible horizon plan, not separate annual recommendations" in text
    )
    assert "free carry-over coordinates feasibility rather than entering the score" in (
        text
    )
    assert "period accounts describe the whole selected trajectory" in text
    assert "Input-oriented Dynamic SBM under CRS" in text
    assert "dynamic.sbm.tone_tsutsui_2010" not in text
    assert "score variant:" not in text
    assert "boundary:" not in text
    assert "selection:" not in text
    assert "solver_selected" not in text
    assert "dynamic.network" not in text

    chapter = DYNAMIC_TRAJECTORY_CHAPTER.read_text(encoding="utf-8")
    assert "carryover-portfolio-trajectory-result.svg" in chapter
    assert 'kind="trajectory"' in chapter
    assert 'dmu_id="path_04"' in chapter
    assert 'variable=roles["free_carryovers"][0]' in chapter


def test_dynamic_scored_carryover_figure_keeps_the_complete_period_account() -> None:
    root = ElementTree.parse(DYNAMIC_SCORED_CARRYOVER_FIGURE).getroot()
    assert root.tag.endswith("svg")
    assert root.find("{http://www.w3.org/2000/svg}title").text == (
        "Scored carry-over account for Strained"
    )

    text = _normalized_svg_text(DYNAMIC_SCORED_CARRYOVER_FIGURE)
    assert "Connected carry-over trajectory for Strained" in text
    assert "Backlog (original units)" in text
    assert "Complete period operating-plan account (all scored dimensions)" in text
    assert "Period operating-plan performance" in text
    assert "Horizon performance 0.500 (not a period average)" in text
    assert "Outgoing and inherited backlog targets form one jointly feasible" in text
    assert "Backlog enters every period's performance account" in text
    assert "horizon result is not an average of annual scores" in text
    assert "Adjacent balances close under non-oriented Dynamic SBM with VRS" in text
    assert "score variant:" not in text
    assert "boundary:" not in text
    assert "dynamic.sbm.tone_tsutsui_2010" not in text
    assert "selection:" not in text
    assert "solver_selected" not in text

    chapter = DYNAMIC_TRAJECTORY_CHAPTER.read_text(encoding="utf-8")
    assert "dynamic-sbm-scored-backlog-result.svg" in chapter
    assert 'dataset_name = "dynamic_capacity_backlog"' in chapter
    assert "roles = dataset_info(dataset_name).roles" in chapter
    assert 'orientation="non-oriented"' in chapter
    assert 'returns_to_scale="vrs"' in chapter
    assert 'score_variant="base"' not in chapter
    assert 'dmu_id="Strained"' in chapter
    assert 'variable="backlog"' in chapter
    assert "complete period\noperating-plan account" in chapter
    assert "not a backlog attribution" in chapter


def test_crs_vrs_figure_does_not_claim_a_deferred_mpss_estimate() -> None:
    text = _normalized_svg_text(CRS_VRS_FRONTIERS)

    assert "VRS" in text
    assert "CRS" in text
    assert "MPSS" not in text


def test_scale_chapter_uses_one_core_result_display_without_a_size_recommendation() -> (
    None
):
    text = _normalized_svg_text(SCALE_EFFICIENCY_RESULT)
    assert "Additional resource-use gap associated with operating scale" in text
    assert "Scale efficiency (CRS efficiency / VRS efficiency)" in text
    assert (
        "Higher values indicate a smaller additional CRS\N{EN DASH}VRS radial gap"
        in text
    )
    assert "1 means proportional replication creates no additional scale" in text
    assert "Input-oriented comparison of matched CRS and VRS benchmarks" in text

    chapter = (
        ROOT / "book" / "chapters" / "02-classical" / "scale-performance-management.md"
    ).read_text(encoding="utf-8")
    assert "scale-efficiency-performance-result.svg" in chapter
    assert 'kind="performance"' in chapter
    assert 'metric="scale_efficiency"' in chapter
    assert 'view="points"' in chapter
    assert '"score_valid"' not in chapter
    assert "Every ratio in the table rests on two available production" in chapter
    assert "does not recommend a new operating size" in chapter


def test_three_performance_accounts_keep_three_estimands_visibly_separate() -> None:
    root = ElementTree.parse(THREE_PERFORMANCE_ACCOUNTS_FIGURE).getroot()
    assert root.tag.endswith("svg")
    assert root.find("{http://www.w3.org/2000/svg}title").text == (
        "Three distinct performance accounts for four service plans"
    )

    text = _normalized_svg_text(THREE_PERFORMANCE_ACCOUNTS_FIGURE)
    for expected in (
        "Efficiency, productivity, and profitability are different accounts",
        "the numbers do not share a measurement scale",
        "INPUT-ORIENTED VRS EFFICIENCY",
        "RADIAL SCORE",
        "A and B: radial score 1.000",
        "Radial result; no slack completion",
        "PHYSICAL PRODUCTIVITY LEVEL",
        "Declared equal-count level",
        "A 2.00 > B 1.80",
        "A level, not productivity change",
        "RETURN-TO-DOLLAR PROFITABILITY",
        "B 3.70 > A 3.50",
        "Profit is reported separately as R - C",
        "THE A/B MANAGEMENT REVERSAL",
        "Same technical score",
        "A: higher physical throughput",
        "B: higher R/C and profit",
        "not a causal explanation, quality judgement, or management prescription",
        "the three accounts do not share one ranking scale",
    ):
        assert expected in text

    for heading in (
        "INPUT-ORIENTED VRS EFFICIENCY",
        "PHYSICAL PRODUCTIVITY LEVEL",
        "RETURN-TO-DOLLAR PROFITABILITY",
    ):
        assert text.count(heading) == 1
    font_sizes = tuple(
        float(value)
        for value in re.findall(
            r"font-size:\s*([0-9.]+)",
            THREE_PERFORMANCE_ACCOUNTS_FIGURE.read_text(encoding="utf-8"),
        )
    )
    assert font_sizes and min(font_sizes) >= 9.5
    assert "technically efficient" not in text.casefold()
    assert "pareto–koopmans efficient" not in text.casefold()  # noqa: RUF001
    assert "common score axis" not in text.casefold()


def test_three_performance_accounts_generator_fails_closed_on_public_accounts() -> None:
    source = RESULT_FIGURE_GENERATOR.read_text(encoding="utf-8")
    start = source.index("def three_performance_accounts_figure()")
    end = source.index("\ndef sbm_improvement_figure()", start)
    case = source[start:end]

    for public_call in (
        'load_dataset("economic_efficiency_4")',
        'BCC(\n        orientation="input",\n        compute_slacks=False,',
        'ReturnToDollarEfficiency(\n        returns_to_scale="vrs",',
        "PriceData.common(",
    ):
        assert public_call in case
    for gate in (
        'technical_metadata.get("method_id") == "static.radial"',
        'technical_metadata.get("solver_calls") == 4',
        'technical_metadata.get("phase_one_solver_calls") == 4',
        'technical_metadata.get("phase_two_solver_calls") == 0',
        'technical_estimator.get("estimator_id") == "estimator.full.dea"',
        'technical_estimator.get("kind") == "full_frontier"',
        'technical_estimator.get("family") == "dea_envelopment"',
        "score_valid",
        "raw_economic_postsolve_certified",
        "published_output_account_certified",
        '== "economic.profitability.return_to_dollar"',
        'profitability_metadata.get("solver_calls") == 0',
        'profitability_metadata.get("ratio_kernel_calls") == 1',
        '== "closed_form_extreme_ratio"',
        "ratio_reconstruction_residual",
        'selected_reference_dmu_id"].eq("B")',
        "7.0 / 12.0",
        "5.0 / 6.0",
        "37.0 / 10.0",
        "expected_quantities = np.asarray",
        "(4.0, 6.0, 2.0)",
        "(5.0, 4.0, 5.0)",
        "(3.0, 5.0, 1.0)",
        "(6.0, 3.0, 2.0)",
        'technical_diagnostics["dmu_id"].duplicated().any()',
        'set(technical_diagnostics["dmu_id"]) != set(plans)',
        'profitability_diagnostics["dmu_id"].duplicated().any()',
        'set(profitability_diagnostics["dmu_id"]) != set(plans)',
    ):
        assert gate in case

    assert case.index("technical.metadata") < case.index("technical.summary()")
    assert case.index("technical.summary()") < case.index("technical.diagnostics")
    assert case.index("profitability.metadata") < case.index("profitability.summary()")
    assert case.index("profitability.summary()") < case.index(
        "profitability.diagnostics"
    )
    assert case.index("profitability.diagnostics") < case.index("plt.figure")
    assert "ProfitEfficiency" not in case
    assert "result.plot(" not in case
    assert 'kind="three_' not in case
    assert "three_performance_accounts_figure()" in source[source.index("def main") :]

    provenance = " ".join(RESULT_FIGURE_README.read_text(encoding="utf-8").split())
    for statement in (
        "three-performance-accounts-result.svg",
        "package-driven composite rather than a new `DEAResult.plot()` kind",
        "input-oriented VRS radial score one",
        "no Pareto--Koopmans or slack-completion claim",
        "neither productivity change nor a DEA productivity index",
        "A has the higher equal-count physical productivity level",
        "B earns more revenue per unit of cost and more observed profit $(R-C)$",
        "The displayed $R/C$ ratio is not observed profit",
        "causal explanation, quality judgement, or management prescription",
    ):
        assert statement in provenance


def test_peer_eligibility_figure_separates_population_policy_from_active_peers() -> (
    None
):
    root = ElementTree.parse(PEER_ELIGIBILITY_SENSITIVITY_FIGURE).getroot()
    assert root.tag.endswith("svg")
    assert root.find("{http://www.w3.org/2000/svg}title").text == (
        "Same hospital record under two eligibility rules"
    )

    text = _normalized_svg_text(PEER_ELIGIBILITY_SENSITIVITY_FIGURE)
    for expected in (
        "Same hospital record, different eligibility rules",
        "The analyst declares who is eligible before DEA selects "
        "positive-intensity peers",
        "CANDIDATE ROSTER → PRE-DECLARED ELIGIBILITY RULE → "
        "ELIGIBLE POPULATION → ACTIVE PEERS",
        "LAKESIDE'S RECORDED OPERATION IS UNCHANGED",
        "120 clinical hours · 80 staffed bed-days · "
        "100 risk-adjusted completed episodes",
        "SAME SERVICE-CONTRACT RULE",
        "district + urban + common coding + standard contract",
        "Eligible population (3): Lakeside · North · East",
        "6.25%",
        "Radial score: 0.9375",
        "Active peers: North (1.000)",
        "SHARED DISTRICT-MISSION RULE",
        "West admitted after prior comparability review",
        "Eligible population (4): Same-contract three + West",
        "9.72%",
        "Radial score: 0.9028",
        "Active peers: 4/9 North + 5/9 West",
        "100 episodes protected · before slack completion",
        "INTERPRETATION BOUNDARY",
        "eligibility changes the resource-saving opportunity by 3.47 points",
        "practice transferability",
        "Teaching samples are tiny",
        "harm is outside this account",
        "no completed target",
        "Same hospital record",
        "only the pre-declared eligible population changes",
    ):
        assert expected in text

    assert text.count("COMMON PROPORTIONAL RESOURCE-SAVING OPPORTUNITY") == 2
    assert text.count("100 episodes protected · before slack completion") == 2
    font_sizes = tuple(
        float(value)
        for value in re.findall(
            r"font-size:\s*([0-9.]+)",
            PEER_ELIGIBILITY_SENSITIVITY_FIGURE.read_text(encoding="utf-8"),
        )
    )
    assert font_sizes and min(font_sizes) >= 9.5
    assert "contract caused Lakeside's gap" not in text
    assert "average score" not in text.casefold()


def test_peer_eligibility_generator_fails_closed_on_both_public_bcc_fits() -> None:
    source = RESULT_FIGURE_GENERATOR.read_text(encoding="utf-8")
    start = source.index("def peer_eligibility_sensitivity_figure()")
    end = source.index("\ndef sbm_improvement_figure()", start)
    case = source[start:end]

    for public_call in (
        "DEAData.from_frame(",
        'BCC(\n            orientation="input",\n            compute_slacks=False,',
        "result.summary()",
        'result.peers("Lakeside")',
    ):
        assert public_call in case
    for gate in (
        "frame.shape == (7, 9)",
        'tuple(frame["hospital"]) == candidate_roster',
        "expected_quantities = np.asarray",
        'frame["mission"].eq("district")',
        'frame["operating_environment"].eq("urban")',
        'frame["common_episode_definition"]',
        'frame["service_contract"].eq("standard")',
        '("Lakeside", "North", "East")',
        '("Lakeside", "North", "East", "West")',
        'metadata.get("method_id") == "static.radial"',
        'metadata.get("specialization_id") == "static.radial.vrs"',
        'metadata.get("target_completion_id") is None',
        'metadata.get("phase_one_solver_calls") == n_eligible',
        'metadata.get("phase_two_solver_calls") == 0',
        'metadata.get("solver_calls") == n_eligible',
        '"estimator_id": "estimator.full.dea"',
        'reference == {"kind": "global"}',
        "score_valid",
        "peer_valid",
        'peer_status"].eq("certified_primary_program")',
        "lp_postsolve_certified",
        "raw_economic_postsolve_certified",
        "published_output_account_certified",
        "published_peer_account_certified",
        "published_dual_account_certified",
        "15.0 / 16.0",
        "65.0 / 72.0",
        "4.0 / 9.0",
        "5.0 / 9.0",
        "965.0 / 9.0",
        "650.0 / 9.0",
        "same_contract_saving = 1.0 - same_contract_score",
        "district_mission_saving = 1.0 - district_mission_score",
        "1.0 / 16.0",
        "7.0 / 72.0",
        "5.0 / 144.0",
        'f"{100.0 * saving:.2f}%"',
        "result.targets.empty",
        "result.slacks.empty",
        "peer_activity",
    ):
        assert gate in case

    assert case.index("result.metadata") < case.index("result.summary()")
    assert case.index("result.summary()") < case.index("result.diagnostics")
    assert case.index("result.diagnostics") < case.index('result.peers("Lakeside")')
    assert case.index('result.peers("Lakeside")') < case.index("plt.figure")
    assert "result.plot(" not in case
    assert "ReferenceSpec" not in case
    assert "MetafrontierDEA" not in case
    assert "peer_eligibility_sensitivity_figure()" in source[source.index("def main") :]

    provenance = " ".join(RESULT_FIGURE_README.read_text(encoding="utf-8").split())
    for statement in (
        "peer-eligibility-sensitivity-result.svg",
        "package-driven composite",
        "holds Lakeside's recorded 120 clinical hours, 80 staffed bed-days, and 100",
        "same-contract rule retains Lakeside, North, and East",
        "broader district-mission rule also admits West",
        "0.902778",
        "$(4/9)North+(5/9)West$",
        "requests no slack completion, adds no post-fit solve",
        "3.47 percentage-point difference as sensitivity to two pre-declared "
        "comparison",
        "not a causal contract effect or evidence that West's practices will transfer",
        "Both populations are deliberately too small",
        "harm remains outside this narrow ordinary-BCC account",
    ):
        assert statement in provenance


def test_reference_frequency_figure_reads_as_an_audit_not_a_ranking() -> None:
    root = ElementTree.parse(REFERENCE_FREQUENCY_FIGURE).getroot()
    assert root.tag.endswith("svg")
    assert root.find("{http://www.w3.org/2000/svg}title").text == (
        "Selected-plan reference frequency for eight service organizations"
    )

    text = _normalized_svg_text(REFERENCE_FREQUENCY_FIGURE)
    for expected in (
        "How often each organization enters the selected peer plans",
        "One score-only BCC fit · reported-edge counts above the source "
        "threshold, not sums of λ",
        "Selected by other organizations",
        "Self-reference",
        "Number of reported peer accounts (8 evaluations)",
        "Organization",
        "0 other + 1 self",
        "3 other + 1 self",
        "4 other + 1 self",
        "1 other + 1 self",
        "0 reported edges",
        "repeated selection can flag comparative reach",
        "Not exact support below the reporting threshold",
        "not a superiority rank, outlier diagnosis, causal or transferability",
        "all-optima set",
    ):
        assert expected in text
    assert text.count("0 reported edges") == 4
    assert "best organization" not in text.casefold()
    assert "peer importance score" not in text.casefold()


def test_reference_frequency_generator_freezes_public_zero_solve_account() -> None:
    source = RESULT_FIGURE_GENERATOR.read_text(encoding="utf-8")
    start = source.index("def reference_frequency_figure()")
    end = source.index("\ndef slack_family_rulers_figure()", start)
    case = source[start:end]

    for public_call in (
        'load_dataset("slacks_2x2")',
        'dataset_info("slacks_2x2").roles',
        "DEAData.from_frame(",
        'BCC(\n        orientation="input",\n        compute_slacks=False,',
        "result.summary()",
        "result.diagnostics",
        "result.intensities",
        "result.reference_frequency()",
        "frequency.reference_frame",
        "frequency.edge_frame",
    ):
        assert public_call in case
    for gate in (
        "frame.shape == (8, 5)",
        'tuple(frame["dmu"]) == tuple("ABCDEFGH")',
        'result.metadata.get("method_id") == "static.radial"',
        'result.metadata.get("specialization_id") == "static.radial.vrs"',
        'result.metadata.get("phase_one_solver_calls") == 8',
        'result.metadata.get("phase_two_solver_calls") == 0',
        'result.metadata.get("solver_calls") == 8',
        'summary["peer_valid"].eq(True).all()',
        'summary["peer_status"].eq("certified_primary_program").all()',
        "lp_postsolve_certified",
        "published_output_account_certified",
        "published_peer_account_certified",
        "expected_edges = (",
        'source_peer_tolerance = float(result.metadata["peer_tolerance"])',
        "np.all(source_lambdas > source_peer_tolerance)",
        '== "analysis.reference_frequency.selected_plan"',
        '== "reported_active_solver_selected_peer_edge"',
        'frequency.metadata.get("source_peer_tolerance")',
        '== "all_evaluated_organizations"',
        'frequency.metadata.get("active_edge_count") == 12',
        'frequency.metadata.get("alternate_optima_assessed") is False',
        'frequency.metadata.get("global_reference_set_claim") is False',
        'frequency.metadata.get("outlier_claim") is False',
        'frequency.metadata.get("inference") == "none"',
        'frequency.metadata.get("additional_solver_calls") == 0',
        "expected_total = np.asarray((1, 4, 5, 2, 0, 0, 0, 0)",
        'account["reference_rate"]',
        'edges["lambda"]',
    ):
        assert gate in case

    assert case.index(").fit(data)") < case.index("result.summary()")
    assert case.index("result.summary()") < case.index("result.diagnostics")
    assert case.index("result.diagnostics") < case.index("result.intensities")
    assert case.index("result.intensities") < case.index("result.reference_frequency()")
    assert case.index("result.reference_frequency()") < case.index("plt.subplots(")
    assert "reference_frequency_figure()" in source[source.index("def main") :]

    provenance = " ".join(RESULT_FIGURE_README.read_text(encoding="utf-8").split())
    for statement in (
        "reference-frequency-result.svg",
        "package-driven selected-plan case account",
        '`DEAResult.plot(kind="references")` renderer',
        "explicit top-N/selected-row readability contract",
        "zero-frequency organizations remain visible",
        "calls `result.reference_frequency()`",
        "12 reported edges strictly above the source `peer_tolerance`",
        "no exact-support claim",
        "1/4/5/2/0/0/0/0 total frequencies",
        "self/other split",
        "zero-additional-solve ledger",
        "rather than sorting the bars into a league table",
        "comparative reach and an audit lead",
        "union of all optimal reference sets",
    ):
        assert statement in provenance


def test_study_design_embeds_frequency_without_adding_a_handbook_route() -> None:
    chapter = (
        ROOT / "book" / "chapters" / "01-foundations" / "02-study-design.md"
    ).read_text(encoding="utf-8")
    normalized_chapter = " ".join(chapter.split())
    for statement in (
        "### Repeated peer selection is an audit lead, not a trophy",
        "comparative reach",
        "Reference frequency simply counts appearances in the selected "
        "comparator plans",
        "Self-use is shown separately",
        "Adding the fitted intensity values across different plans would not "
        "improve this diagnostic",
        "The count tells the authority where to investigate, not what it will "
        "find there",
        "reference-frequency-result.svg",
        ":name: fig-reference-frequency-reader",
        "result.reference_frequency()",
        "frequency.reference_frame",
        "neither another efficiency score nor a quality-adjusted league table",
        "another equally good comparator plan",
        "A high count likewise says nothing by itself about superiority, causation",
        "Deleting a hospital merely because it is a demanding recurrent peer",
    ):
        assert " ".join(statement.split()) in normalized_chapter

    for technical_detail in (
        r"\tau_{\mathrm{peer}}",
        "peer_tolerance",
        "alternate_optima_assessed",
        "global_reference_set_claim",
        "outlier_claim",
        "exact mathematical support",
    ):
        assert technical_detail not in chapter
    assert chapter.count("reference-frequency-result.svg") == 1
    index = (ROOT / "book" / "index.md").read_text(encoding="utf-8")
    assert "reference-frequency" not in index


def test_scale_chapter_treats_unbounded_support_as_a_checked_boundary() -> None:
    chapter = (
        ROOT / "book" / "chapters" / "02-classical" / "scale-performance-management.md"
    ).read_text(encoding="utf-8")
    assert '"support_interval_valid"' not in chapter
    assert "does\n**not** mean infinite physical productivity" in chapter
    assert "neither the interval nor the classification\nis justified" in chapter


def test_metafrontier_figure_keeps_one_core_group_meta_account() -> None:
    root = ElementTree.parse(METAFRONTIER_DECOMPOSITION_FIGURE).getroot()
    assert root.tag.endswith("svg")
    assert root.find("{http://www.w3.org/2000/svg}title").text == (
        "Within-group performance and pooled-opportunity comparison"
    )

    text = _normalized_svg_text(METAFRONTIER_DECOMPOSITION_FIGURE)
    assert "Declared-group efficiency" in text
    assert "Pooled-frontier efficiency" in text
    assert "Link between benchmark results" in text
    assert text.count("MTR 0.50") == 3
    assert text.count("MTR 1.00") == 3
    assert "Meta efficiency = group efficiency \N{MULTIPLICATION SIGN} MTR" in text
    assert "MTR is their ratio" in text
    assert "neither component identifies causes or assigns management blame" in text
    assert "pooled convex opportunity set" in text
    for excluded in (
        "network metafrontier",
        "meta-sbm",
        "environmental metafrontier",
        "paper-specific",
    ):
        assert excluded not in text.casefold()

    chapter = METAFRONTIER_CHAPTER.read_text(encoding="utf-8")
    assert "metafrontier-decomposition-result.svg" in chapter
    assert 'kind="metafrontier"' in chapter


def test_environmental_ml_figure_keeps_one_adjacent_period_result_screen() -> None:
    root = ElementTree.parse(ENVIRONMENTAL_ML_PERFORMANCE_FIGURE).getroot()
    assert root.tag.endswith("svg")
    assert root.find("{http://www.w3.org/2000/svg}title").text == (
        "Adjacent-period environmental productivity change across plants, 2020-2021"
    )

    text = _normalized_svg_text(ENVIRONMENTAL_ML_PERFORMANCE_FIGURE)
    for expected in (
        "Adjacent-period environmental productivity change, 2020\N{EN DASH}2021",
        "Malmquist\N{EN DASH}Luenberger environmental productivity index",
        "2020 → 2021",
        "South",
        "East",
        "Central",
        "Coastal",
        "Above 1: environmental productivity improvement",
        "Complete four-appraisal environmental productivity account",
        "CRS common-factor weak-disposal programme holds inputs fixed while "
        "electricity expands and CO₂ contracts",
        "North and West are unavailable because at least one required "
        "cross-period production comparison is infeasible",
    ):
        assert expected in text
    for unavailable in ("North", "West"):
        assert text.count(unavailable) == 1
    for excluded in ("global", "GML", "full-horizon"):
        assert excluded.casefold() not in text.casefold()

    chapter = ENVIRONMENTAL_PRODUCTIVITY_CHAPTER.read_text(encoding="utf-8")
    assert chapter.startswith(
        "# Environmental Productivity over Time with Adjacent-Period ML"
    )
    assert chapter.count("environmental-ml-performance-result.svg") == 1
    for argument in (
        'kind="performance"',
        'metric="productivity_change"',
        'view="points"',
    ):
        assert chapter.count(argument) == 2
    for period in ("period=2021", "period=2023"):
        assert chapter.count(period) == 1
    assert "comparison_pairs=((2020, 2023),)" in chapter
    assert "environmental-gml-performance-result.svg" not in chapter
    assert "global-malmquist-luenberger-performance-result.svg" not in chapter
    assert "| Two contemporaneous technologies | 1.045057 |" in chapter
    assert "| One full-horizon technology | 1.004603 |" in chapter
    assert "GlobalMalmquistLuenbergerDEA().fit(data)" in chapter
    assert chapter.count("GML") == 2
    for excluded in (
        "## A common reference is an information policy",
        "### Circularity comes with an information-vintage obligation",
        "GML^{t,t+1}",
        "reference-technology-windows.svg",
        "| Policy question | Adjacent-period ML | Global ML |",
        "Use the common reference",
        "common-reference constructor",
    ):
        assert excluded not in chapter
    normalized_chapter = " ".join(chapter.split())
    for statement in (
        "Their absence is not zero productivity change or evidence of poor management",
        "cannot be represented by the 2021 technology",
        "neither period's plan can be represented by the other period's technology",
        "conditional production comparisons, not causal ratings",
    ):
        assert statement in normalized_chapter
    assert "\n### Adjacent-period result figure" not in chapter


def test_environmental_ml_book_generator_gates_tasks_before_public_plot() -> None:
    source = RESULT_FIGURE_GENERATOR.read_text(encoding="utf-8")
    start = source.index("def environmental_ml_performance_figure()")
    end = source.index("\ndef malmquist_figure()", start)
    case = source[start:end]

    assert case.index("result.available_plots()") < case.index("result.metadata")
    assert case.index("result.metadata") < case.index("result.summary()")
    assert case.index("result.summary()") < case.index("result.diagnostics")
    assert case.index("result.diagnostics") < case.index("figure = result.plot(")
    for field in (
        "score_valid",
        "multiplicative_account_certified",
        "economic_postsolve_certified",
        "postsolve_certified",
        "all_four_distance_programs_certified",
        "all_four_economic_distance_claims_certified",
        "lp_certified_distance_count",
        "economic_certified_distance_count",
        "failed_distance_count",
        "failed_distance_roles",
        "lp_postsolve_certified",
        "raw_economic_postsolve_certified",
        "published_output_account_certified",
        "backend_solver_status",
        "raw_solver_status",
    ):
        assert field in case
    for exact in (
        "1.0389691188594246",
        "1.0442445917035588",
        "1.0450571237979644",
        "1.0516193681210393",
        '"North": (1, {"base_on_comparison"})',
        '"West": (2, {"comparison_on_base", "base_on_comparison"})',
    ):
        assert exact in case
    assert "peer_valid" not in case
    assert "all_four_peer_accounts_certified" not in case
    assert "GlobalMalmquistLuenbergerDEA" not in case
    assert "GML" not in case
    assert 'kind="environmental_performance"' not in case
    assert 'tasks["backend_solver_status"].eq("optimal").all()' in case
    assert 'tasks["raw_solver_status"].eq("optimal").all()' in case
    assert "environmental_ml_performance_figure()" in source[source.index("def main") :]

    provenance = RESULT_FIGURE_README.read_text(encoding="utf-8")
    normalized_provenance = " ".join(provenance.split())
    for statement in (
        "environmental-ml-performance-result.svg",
        "all four LP and environmental quantity certificates",
        "North and West are intentionally not plotted as points",
        "neither zero productivity changes nor numerical solver malfunctions",
        "no second GML result figure is generated",
    ):
        assert statement in normalized_provenance


def test_network_sbm_process_figure_keeps_one_core_reporting_institution() -> None:
    root = ElementTree.parse(NETWORK_SBM_PROCESS_FIGURE).getroot()
    assert root.tag.endswith("svg")
    assert root.find("{http://www.w3.org/2000/svg}title").text == (
        "One connected operating account for a service plan"
    )

    text = _normalized_svg_text(NETWORK_SBM_PROCESS_FIGURE)
    assert "One connected operating account for a service plan" in text
    assert "Where the joint plan locates input burden" in text
    assert "How the system score is formed" in text
    assert "Selected internal handoffs in their original units" in text
    assert "one jointly feasible Network SBM plan" in text
    assert "Free handoffs preserve supplier\N{EN DASH}recipient continuity" in text
    assert "not unique, causal, or prescriptive recommendations" in text
    assert "Input-oriented VRS comparison" in text
    assert "relational" not in text.casefold()
    assert "additive" not in text.casefold()
    assert "accountable" not in text.casefold()

    chapter = NETWORK_SBM_PROCESS_CHAPTER.read_text(encoding="utf-8")
    assert "three-process-service-account-result.svg" in chapter
    assert 'kind="process"' in chapter
    assert 'dmu_id="resource_drag"' in chapter


def test_radial_book_generator_fails_closed_before_public_plot() -> None:
    source = RESULT_FIGURE_GENERATOR.read_text(encoding="utf-8")
    start = source.index("def radial_improvement_figure()")
    end = source.index("\ndef scale_efficiency_figure()", start)
    case = source[start:end]

    assert case.index("BCCInput().fit(data)") < case.index("result.summary(copy=True)")
    assert case.index("result.summary(copy=True)") < case.index("result.diagnostics")
    assert case.index("result.diagnostics") < case.index('result.targets_for("C")')
    assert case.index('result.targets_for("C")') < case.index(
        'result.plot(kind="improvement", dmu_id="C")'
    )
    for field in (
        "static.radial",
        "static.radial.vrs.input",
        "native_score",
        "compute_slacks",
        "evaluation.target_completion.pareto_koopmans",
        "target_completion_scale_anchor",
        "maximize_row_scaled_sum",
        "phase_one_solver_calls",
        "phase_two_solver_calls",
        "solver_calls",
        "score_valid",
        "is_radially_efficient",
        "is_efficient",
        "is_within_reference_technology",
        "completion_valid",
        "target_valid",
        "lp_postsolve_certified",
        "raw_economic_postsolve_certified",
        "economic_postsolve_certified",
        "published_output_account_certified",
        "max_slack",
        "max_scaled_slack",
        "scaled_slack",
    ):
        assert field in case
    for exact in (
        '"branch": ("A", "B", "C")',
        '"resource": (1.0, 2.0, 1.0)',
        '"service": (1.0, 1.0, 0.5)',
        '("input", "resource"): (1.0, 1.0, 0.0, 0.0)',
        '("output", "service"): (0.5, 1.0, 0.5, 0.5)',
    ):
        assert exact in case
    assert 'metadata_before.get("phase_one_solver_calls") == 3' in case
    assert 'metadata_before.get("phase_two_solver_calls") == 3' in case
    assert 'metadata_before.get("solver_calls") == 6' in case
    assert "additional_solver_calls" not in case
    assert "peer_valid" not in case
    assert "dual_valid" not in case
    assert "plt." not in case
    assert "radial_improvement_figure()" in source[source.index("def main") :]

    chapter = RADIAL_CHAPTER.read_text(encoding="utf-8")
    normalized_chapter = " ".join(chapter.split())
    assert chapter.count("radial-improvement-result.svg") == 1
    assert "radial-and-slack.svg" not in chapter
    assert chapter.count('result.plot(kind="improvement", dmu_id="C")') == 1
    for statement in (
        "One observed operation, two supported conclusions",
        "$\\theta_C=1$ leaves the phase-one plan at resource $1$ and service $0.5$",
        "service slack of $0.5$",
        "C is radially efficient but not strongly efficient",
        "`targets` table reports the hatted plan",
        "not an implementation sequence or management order",
    ):
        assert statement in normalized_chapter

    provenance = " ".join(RESULT_FIGURE_README.read_text(encoding="utf-8").split())
    for statement in (
        "radial-improvement-result.svg",
        "exact three-branch public BCC-I case",
        "$3+3=6$ fitted solve count",
        "public final target $(1,1)$",
        "Peer and dual publication are not required",
        "not claimed to be unique, closest, least-cost, causal, or prescriptive",
    ):
        assert statement in provenance


def test_radial_improvement_figure_separates_factor_from_target_completion() -> None:
    root = ElementTree.parse(RADIAL_IMPROVEMENT_FIGURE).getroot()
    assert root.tag.endswith("svg")
    assert root.find("{http://www.w3.org/2000/svg}title").text == (
        "Radial and completed operating accounts for branch C"
    )

    text = _normalized_svg_text(RADIAL_IMPROVEMENT_FIGURE)
    for expected in (
        "Radial performance account for C",
        "Two-stage radial operating account",
        "θ = 1.000000",
        "Radially efficient: YES",
        "Strongly efficient (score + slacks): NO",
        "Observed operation",
        "Phase-one radial target",
        "Selected completed target",
        "No common resource saving",
        "Phase-two service gain +0.500000",
        "θ = 1 leaves no common resource-saving opportunity for branch C",
        "phase two records the remaining service opportunity",
        "completed input-oriented VRS plan is feasible",
        "need not be unique or least-cost",
        "neither causal nor prescriptive",
    ):
        assert expected in text


def test_sbm_improvement_figure_keeps_the_classic_variable_account() -> None:
    root = ElementTree.parse(SBM_IMPROVEMENT_FIGURE).getroot()
    assert root.tag.endswith("svg")
    assert root.find("{http://www.w3.org/2000/svg}title").text == (
        "Selected variable-specific SBM operating plan for the uneven service plan"
    )

    text = _normalized_svg_text(SBM_IMPROVEMENT_FIGURE)
    assert "Where the selected plan locates operating gaps" in text
    assert "Resource · resource b" in text
    assert "Service · quality service" in text
    assert "Benchmark gap" in text
    assert "Input-retention account" in text
    assert "Output-expansion account" in text
    assert "One selected feasible CRS plan" in text
    assert "alternative peers or targets may support the same score" in text
    assert "resource savings and service gains are benchmark opportunities" in text
    assert "not causal or prescriptive instructions" in text
    assert "Quantities retain their original units" in text
    for excluded in ("environmental", "network", "dynamic", "super-efficiency"):
        assert excluded not in text.casefold()

    chapter = SBM_CHAPTER.read_text(encoding="utf-8")
    assert "sbm-slack-contrast-result.svg" in chapter
    assert 'kind="improvement"' in chapter
    assert 'dmu_id="Uneven"' in chapter


def test_ordinary_ddf_figure_separates_programme_from_slack_completion() -> None:
    root = ElementTree.parse(DDF_IMPROVEMENT_FIGURE).getroot()
    assert root.tag.endswith("svg")
    assert root.find("{http://www.w3.org/2000/svg}title").text == (
        "DEA benchmark account for organization E's declared and completed targets"
    )

    text = _normalized_svg_text(DDF_IMPROVEMENT_FIGURE)
    for expected in (
        "Directional benchmark account for E",
        "Benchmark account for a declared improvement programme",
        "β = 0.247253",
        "is the largest multiple represented as feasible by the fitted DEA "
        "technology; βg is reported below in each variable's original unit",
        "Resource contraction · Desirable-service expansion",
        "Observed operation",
        "Target promised by βg",
        "Selected completed target",
        "Labor Resource 2 1.505495 1.505495",
        "Capital Resource 2.800000 2.107692 2.107692",
        "Service Desirable service 1.300000 1.621429 1.652747",
        "Quality Desirable service 0.620000 0.773297 0.830549",
        "Declared resource saving −0.494505",  # noqa: RUF001
        "Declared resource saving −0.692308",  # noqa: RUF001
        "Declared service addition +0.321429",
        "Declared service addition +0.153297",
        "Slack completion +0.031319",
        "Slack completion +0.057253",
        "Each row keeps its original physical unit",
        "β measures attainable units of the declared resource-saving and "
        "service-expansion programme",
        "later variable-specific completion is reported separately",
        "completed VRS plan is feasible for organization E within the declared "
        "peer population",
        "need not be unique or least-cost",
        "neither causal nor prescriptive",
    ):
        assert expected in text
    assert text.count("Slack completion") == 4
    for excluded in (
        "1 / (1 + β)",
        "environmental",
        "undesirable residual",
        "weak disposal",
        "network",
        "dynamic",
        "caused by management",
    ):
        assert excluded.casefold() not in text.casefold()


def test_ordinary_ddf_book_generator_fails_closed_before_public_plot() -> None:
    source = RESULT_FIGURE_GENERATOR.read_text(encoding="utf-8")
    start = source.index("def directional_distance_figure()")
    end = source.index("\ndef ddf_programme_contracts_figure()", start)
    case = source[start:end]

    assert case.index("result.available_plots()") < case.index("result.summary()")
    assert case.index("result.summary()") < case.index("result.diagnostics")
    assert case.index("result.diagnostics") < case.index("result.targets_for")
    assert case.index("result.targets_for") < case.index(
        'result.plot(kind="improvement"'
    )
    for field in (
        "score_valid",
        "completion_valid",
        "target_valid",
        "lp_postsolve_certified",
        "postsolve_certified",
        "raw_economic_postsolve_certified",
        "published_output_account_certified",
        "economic_postsolve_certified",
        "directional_change",
        "slack_scale",
        "scaled_slack",
        "additional_solver_calls",
        "max_slack",
        "max_scaled_slack",
    ):
        assert field in case
    for exact in (
        "0.2472527472527472",
        "1.5054945054945055",
        "2.1076923076923078",
        "1.6214285714285714",
        "0.031318681318681346",
        "1.6527472527472529",
        "0.7732967032967033",
        "0.05725274725274716",
        "0.8305494505494505",
        "0.06090717792845443",
    ):
        assert exact in case
    assert 'metadata.get("method_id") == "static.directional_distance"' in case
    assert 'metadata.get("input_direction") == "observed"' in case
    assert 'metadata.get("output_direction") == "observed"' in case
    for invariant in (
        "declared_operating_improvement_programme",
        "black_box",
        "estimator.full.dea",
        "evaluation.target_completion.pareto_koopmans",
        "maximize_row_scaled_slacks",
        "slack_target_unit_invariant",
    ):
        assert invariant in case
    assert "peer_valid" not in case
    assert "dual_valid" not in case
    assert "ddf-performance-result.svg" not in case
    assert 'kind="directional_improvement"' not in case
    assert case.count('result.plot(kind="improvement", dmu_id=focus)') == 1
    assert "plt." not in case
    assert "directional_distance_figure()" in source[source.index("def main") :]

    chapter = DDF_CHAPTER.read_text(encoding="utf-8")
    normalized_chapter = " ".join(chapter.split())
    assert chapter.count("ddf-improvement-result.svg") == 1
    assert "ddf-performance-result.svg" not in chapter
    call = 'result.plot(kind="improvement", dmu_id="E")'
    assert chapter.count(call) == 1
    assert 'kind="directional_improvement"' not in chapter
    for statement in (
        "entries form a benchmark accounting sequence, not a claim that any "
        "change has already been implemented",
        "observed quantity is the baseline",
        "directional target shows exactly what $\\beta_E g$ promises",
        "original unit",
        "not evidence that the observed gaps were caused by management",
        "does not show that the target is unique, least costly, operationally "
        "preferred, or prescriptive",
        "| Input | Labor | 2.000000 | 1.505495 | 0.000000 | 1.505495 |",
        "| Input | Capital | 2.800000 | 2.107692 | 0.000000 | 2.107692 |",
        "| Output | Service | 1.300000 | 1.621429 | 0.031319 | 1.652747 |",
        "| Output | Quality | 0.620000 | 0.773297 | 0.057253 | 0.830549 |",
    ):
        assert statement in normalized_chapter

    provenance = " ".join(RESULT_FIGURE_README.read_text(encoding="utf-8").split())
    for statement in (
        "ddf-improvement-result.svg",
        "public ordinary-DDF result",
        "labor and capital contract to 1.505495 and 2.107692",
        "service and quality expand to 1.621429 and 0.773297",
        "adds 0.031319 service and 0.057253 quality",
        "positive slack scale, normalized slack identity, and target",
        "Peer and dual release are not required because neither claim is displayed.",
        "not a causal explanation, a least-cost transition, or a management "
        "prescription",
    ):
        assert statement in provenance


def test_ddf_programme_contracts_keep_three_management_questions_separate() -> None:
    root = ElementTree.parse(DDF_PROGRAMME_CONTRACTS_FIGURE).getroot()
    assert root.tag.endswith("svg")
    assert root.find("{http://www.w3.org/2000/svg}title").text == (
        "Three DDF operating contracts for organization E"
    )

    text = _normalized_svg_text(DDF_PROGRAMME_CONTRACTS_FIGURE)
    for expected in (
        "Three DDF contracts for the same organization E",
        "VRS benchmark · same observed operation · only the phase-one "
        "improvement programme changes",
        "FIXED OBSERVED RECORD",
        "Labor 2.000000 · Capital 2.800000 · Service 1.300000 · Quality 0.620000",
        "RESOURCE-SAVING CONTRACT",
        "Protect recorded services; test a common observed-input contraction.",
        "g = (observed inputs, zero outputs)",
        "SERVICE-EXPANSION CONTRACT",
        "Protect recorded resources; test a common observed-output expansion.",
        "g = (zero inputs, observed outputs)",
        "JOINT CONTRACT",
        " ".join(
            (
                "Test resource saving and service expansion as one",
                "observed-quantity package.",
            )
        ),
        "g = (observed inputs, observed outputs)",
        "Labor save 0.494505 → 1.505495",
        "Capital save 0.692308 → 2.107692",
        "Service output floor 1.300000; no gain required",
        "Quality output floor 0.620000; no gain required",
        "Labor budget cap 2.000000; no saving required",
        "Capital budget cap 2.800000; no saving required",
        "Service add 0.545161 → 1.845161",
        "Quality add 0.260000 → 0.880000",
        "Service add 0.321429 → 1.621429",
        "Quality add 0.153297 → 0.773297",
        "Service add 0.352747 · Quality add 0.210549",
        "Capital save 1.125000 · Service add 0.054839",
        "Service add 0.031319 · Quality add 0.057253",
        "β is contract-specific: the three β values do not share a generic "
        "efficiency scale.",
        "A zero direction requires no phase-1 change: an observed input remains "
        "a cap and an output a floor.",
        "Slack completion is selected only after βg; no causal, implementation-"
        "order, or priority conclusion follows.",
        "Organization E · VRS technology · the observed operation and comparison "
        "population stay fixed across all three contracts",
    ):
        assert expected in text
    assert text.count("β = 0.247253") == 2
    assert text.count("β = 0.419355") == 1
    assert text.count("PHASE 1 · βg IN ORIGINAL UNITS") == 3
    assert text.count("PHASE 2 · SELECTED SLACK COMPLETION AFTER βg") == 3
    for excluded in (
        "1 / (1 + β)",
        "better contract",
        "preferred contract",
        "recommended sequence",
        "caused by management",
        "generic inefficiency percentage",
    ):
        assert excluded.casefold() not in text.casefold()


def test_ddf_programme_contracts_generator_fails_closed_before_drawing() -> None:
    source = RESULT_FIGURE_GENERATOR.read_text(encoding="utf-8")
    start = source.index("def ddf_programme_contracts_figure()")
    end = source.index("\ndef radial_frontier_figure()", start)
    case = source[start:end]

    assert case.index("result.summary(copy=True)") < case.index(
        "result.diagnostics.copy(deep=True)"
    )
    assert case.index("result.diagnostics.copy(deep=True)") < case.index(
        "prepare_directional_ddf_improvement_data("
    )
    assert case.index("prepare_directional_ddf_improvement_data(") < case.index(
        "figure = plt.figure("
    )
    assert case.count("DDF(") == 1
    assert case.count(").fit(data)") == 1
    assert case.count("prepare_directional_ddf_improvement_data(") == 1
    assert "compute_slacks=" not in case
    for direction_pair in (
        '("input_direction": "observed",\n            "output_direction": "zeros")',
        '("input_direction": "zeros",\n            "output_direction": "observed")',
        '("input_direction": "observed",\n            "output_direction": "observed")',
    ):
        assert direction_pair.strip("()") in case
    for exact in (
        "0.24725274725274718",
        "0.4193548387096773",
        "0.2472527472527472",
        "0.49450549450549436",
        "0.6923076923076921",
        "0.5451612903225805",
        "0.25999999999999995",
        "0.4945054945054944",
        "0.6923076923076922",
        "0.3214285714285714",
        "0.15329670329670328",
    ):
        assert exact in case
    for release_gate in (
        "phase_one_solver_calls",
        "phase_two_solver_calls",
        "solver_calls",
        "additional_solver_calls",
        "score_valid",
        "completion_valid",
        "target_valid",
        "lp_postsolve_certified",
        "postsolve_certified",
        "raw_economic_postsolve_certified",
        "published_output_account_certified",
        "economic_postsolve_certified",
        "certified_slack_completion",
        "prepared.max_reconstruction_residual",
        "prepared.provenance",
        'variables["directional_change"]',
        'variables["slack_completion"]',
        'variables["target"]',
        "solve_account_after == solve_account_before",
    ):
        assert release_gate in case
    assert 'metadata_before.get("solver_calls") == 16' in case
    assert 'metadata_before.get("additional_solver_calls") == 0' in case
    assert 'postsolve_before.get("additional_solver_calls") == 0' in case
    assert "result.plot" not in case
    assert "kind=" not in case
    main = source[source.index("def main()") :]
    assert main.count("ddf_programme_contracts_figure()") == 1


def test_slack_family_figure_holds_the_plan_fixed_across_three_rulers() -> None:
    root = ElementTree.parse(SLACK_FAMILY_RULERS_FIGURE).getroot()
    assert root.tag.endswith("svg")
    assert root.find("{http://www.w3.org/2000/svg}title").text == (
        "One operating plan under three slack-reporting rulers"
    )

    text = _normalized_svg_text(SLACK_FAMILY_RULERS_FIGURE)
    for expected in (
        "One operating plan, three reporting rulers",
        "Organization E · one feasible VRS plan · the physical evidence stays fixed",
        "Selected peers 0.25 × B + 0.75 × C",  # noqa: RUF001
        "Variable",
        "Role",
        "Labor",
        "Capital",
        "Service",
        "Quality",
        "Same peers · same slacks · same selected targets",
        "ADDITIVE · ORIGINAL-UNIT WEIGHTS",
        "1.985",
        "best 0 · lower is closer",
        "RAM · SAMPLE-RANGE RULER",
        "0.506250",
        "best 1 · higher is closer",
        "SBM · OWN-OPERATION RULER",
        "0.554763",
        "same plan does not mean the same estimand",
        "Organization E · Additive, RAM, and SBM · same VRS technology, peers, "
        "slacks, and selected target",
    ):
        assert expected in text

    assert text.count("1.125") == 1
    assert text.count("0.600") == 1
    assert text.count("0.260") == 1
    assert "shared score axis" not in text.casefold()

    chapter = SBM_CHAPTER.read_text(encoding="utf-8")
    assert "### One operating plan, three reporting rulers" in chapter
    assert "\n## One operating plan, three reporting rulers" not in chapter
    assert "slack-family-rulers-result.svg" in chapter
    assert 'load_dataset("slacks_2x2")' in chapter
    for estimator in ("AdditiveDEA", "RAM", "SBM"):
        assert estimator in chapter
    for claim in ('"score_valid"', '"target_valid"', '"peer_valid"'):
        assert claim not in chapter
    assert 'sbm_phase_one["postsolve_certified"]' not in chapter
    assert 'sbm_phase_one["economic_postsolve_certified"]' not in chapter
    assert "all three selected plans are feasible" in chapter
    assert "each observed--slack--target identity closes" in chapter
    assert "| Additive weighted slack total | 1.985000 |" in chapter
    assert "| RAM efficiency | 0.506250 |" in chapter
    assert "| SBM efficiency | 0.554763 |" in chapter
    assert "not competing estimates of one universal efficiency" in " ".join(
        chapter.split()
    )
    assert "The durable lesson is not to memorize three historically named recipes" in (
        " ".join(chapter.split())
    )
    assert "belong in one slack family" in chapter
    assert 'kind="slack_family"' not in chapter


def test_sbm_management_map_names_the_nonoriented_score() -> None:
    text = _normalized_svg_text(SBM_MANAGEMENT_QUESTIONS)
    assert "ρᴺᴼ = (1−Lˣ)/(1+Lʸ)" in text  # noqa: RUF001
    assert "ρ = (1−Lˣ)/(1+Lʸ)" not in text  # noqa: RUF001


def test_undesirable_sbm_figure_keeps_one_mainstream_environmental_account() -> None:
    root = ElementTree.parse(UNDESIRABLE_SBM_IMPROVEMENT_FIGURE).getroot()
    assert root.tag.endswith("svg")
    assert root.find("{http://www.w3.org/2000/svg}title").text == (
        "Selected environmental operating plan for plant C"
    )

    text = _normalized_svg_text(UNDESIRABLE_SBM_IMPROVEMENT_FIGURE)
    assert (
        "Fitted resource-service-residual account under separable strong disposal"
        in text
    )
    assert "Resource · resource" in text
    assert "Service · service" in text
    assert "Undesirable residual · residual" in text
    assert text.count("-50.0%") == 2
    assert "+100.0%" in text
    assert "saving 1" in text
    assert "service gain 1" in text
    assert "residual reduction 1" in text
    assert "Input-retention account 0.500" in text
    assert "Service-gain/residual-reduction account 1.750" in text
    assert "SBM efficiency 0.286" in text
    assert "One selected feasible VRS plan under separability and strong" in text
    assert "alternative peers or targets may support the same score" in text
    assert "not a damage valuation, causal conclusion, or prescription" in text
    assert "Quantities retain their original units" in text
    for excluded in ("nonseparable", "weak disposal", "network", "dynamic"):
        assert excluded not in text.casefold()

    chapter = UNDESIRABLE_SBM_CHAPTER.read_text(encoding="utf-8")
    assert "undesirable-sbm-improvement-result.svg" in chapter
    assert 'kind="improvement"' in chapter
    assert 'dmu_id="C"' in chapter
    assert "$2/7=(1-1/2)/(1+3/4)$" in chapter


def test_environmental_ddf_figure_keeps_one_conditional_management_plan() -> None:
    root = ElementTree.parse(ENVIRONMENTAL_DDF_IMPROVEMENT_FIGURE).getroot()
    assert root.tag.endswith("svg")
    assert root.find("{http://www.w3.org/2000/svg}title").text == (
        "Conditional environmental improvement plan for Central in 2020"
    )

    text = _normalized_svg_text(ENVIRONMENTAL_DDF_IMPROVEMENT_FIGURE)
    for expected in (
        "Environmental directional improvement for Central · period 2020",
        "Common directional improvement programme",
        "β = 0.083815",
        "sets one common ambition level across the declared commitments",
        "Fixed resources",
        "Energy",
        "Labor",
        "Desirable-service expansion",
        "Electricity",
        "+6.652902",
        "Undesirable-residual reduction",
        "CO2",
        "−23.897341",  # noqa: RUF001
        "Slack completion",
        "After declared programme",
        "Selected benchmark plan",
        "keeps energy and labour fixed while electricity rises and carbon dioxide "
        "falls in the declared proportion",
        "same-year CRS weak-disposal benchmark supports this feasible plan",
        "not a claim of uniqueness, causation, minimum cost, or managerial "
        "prescription",
    ):
        assert expected in text
    for excluded in (
        "chung",
        "fare",
        "grosskopf",
        "by-production",
        "network",
        "dynamic",
    ):
        assert excluded not in text.casefold()

    chapter = ENVIRONMENTAL_DDF_CHAPTER.read_text(encoding="utf-8")
    assert "environmental-ddf-improvement-result.svg" in chapter
    call = 'result.plot(kind="improvement", dmu_id="Central", period=2020)'
    assert chapter.count(call) == 1
    assert 'kind="environmental_improvement"' not in chapter
    assert "## Environmental DDF improvement" not in chapter
    assert "### Environmental DDF improvement" not in chapter
    for exact in (
        "6.652902",
        "23.897341",
        "zero extra slack",
        "not a unique operating plan, engineering implementation, causal effect, "
        "or cost",
    ):
        assert exact in " ".join(chapter.split())


def test_environmental_ddf_book_generator_fails_closed_before_public_plot() -> None:
    source = RESULT_FIGURE_GENERATOR.read_text(encoding="utf-8")
    start = source.index("def environmental_ddf_improvement_figure()")
    end = source.index("\ndef luenberger_figure()", start)
    case = source[start:end]

    assert case.index("result.available_plots()") < case.index("result.summary()")
    assert case.index("result.summary()") < case.index("result.diagnostics")
    assert case.index("result.diagnostics") < case.index("result.targets_for")
    assert case.index("result.targets_for") < case.index(
        'result.plot(kind="improvement"'
    )
    for field in (
        "score_valid",
        "completion_valid",
        "target_valid",
        "lp_postsolve_certified",
        "postsolve_certified",
        "raw_economic_postsolve_certified",
        "published_output_account_certified",
        "economic_postsolve_certified",
        "directional_change",
        "slack_allowed",
        "scaled_slack",
    ):
        assert field in case
    for exact in (
        "0.08381502890173406",
        "6.652901734104043",
        "23.897341040462415",
        "86.02890173410405",
        "261.22265895953757",
    ):
        assert exact in case
    assert "peer_valid" not in case
    assert "dual_valid" not in case
    assert 'kind="environmental_improvement"' not in case
    assert "plt." not in case
    assert (
        "environmental_ddf_improvement_figure()" in source[source.index("def main") :]
    )

    provenance = RESULT_FIGURE_README.read_text(encoding="utf-8")
    for statement in (
        "environmental-ddf-improvement-result.svg",
        "weak common-factor disposal, CRS, and a contemporaneous reference",
        "adds 6.652902 units of electricity",
        "removes 23.897341 units of carbon dioxide",
        "Peer and dual release are not required because neither claim is displayed.",
        "not a unique plan, engineering design, causal effect, or cost conclusion",
    ):
        assert statement in " ".join(provenance.split())


def test_ml_exact_account_figure_is_accessible_and_freezes_oracle() -> None:
    root = ElementTree.parse(ML_FIGURE).getroot()
    assert root.tag.endswith("svg")
    assert root.attrib["role"] == "img"
    assert root.attrib["aria-labelledby"] == "title description"

    text = _normalized_svg_text(ML_FIGURE)
    assert "Two exact Malmquist-Luenberger change accounts" in text
    assert "The same relevant opportunity determines all four comparisons." in text
    assert "ML = 6/5 = EC 6/5" in text
    assert "ML = 2 = EC 1" in text
    assert "new-opportunity projection · D = 3/5" in text
    assert "old-opportunity replay" in text
    assert "D = 3/5" in text
    assert "neither identifies the cause of change" in text

    matrix_text = _normalized_svg_text(ENVIRONMENTAL_DISTANCE_MATRIX)
    assert "Four environmental benchmark evaluations" in matrix_text
    assert "D^t(z^t)" in matrix_text
    assert "D^(t+1)(z^(t+1))" in matrix_text
    assert "d^t(z^t)" not in matrix_text


def test_hicks_moorsteen_figure_uses_the_book_time_and_quantity_notation() -> None:
    root = ElementTree.parse(HICKS_MOORSTEEN_FIGURE).getroot()
    assert root.tag.endswith("svg")
    assert root.attrib["role"] == "img"
    assert root.attrib["aria-labelledby"] == "title description"

    text = _normalized_svg_text(HICKS_MOORSTEEN_FIGURE)
    assert "HM^(t,t+1) = output quantity index Q_y^(t,t+1)" in text
    assert "input quantity index Q_x^(t,t+1)" in text
    assert "Base-period perspective: \U0001d4af^t" in text
    assert "Comparison-period perspective: \U0001d4af^(t+1)" in text
    assert "Output quantity, Q_y^t" in text
    assert "Input quantity, Q_x^(t+1)" in text
    assert "Q_y^(t,t+1) = √(Q_y^t \u00d7 Q_y^(t+1))" in text
    assert "Q_x^(t,t+1) = √(Q_x^t \u00d7 Q_x^(t+1))" in text
    assert "Period-s" not in text
    assert "Q(s)" not in text
    assert "X(s)" not in text

    chapter = HICKS_MOORSTEEN_CHAPTER.read_text(encoding="utf-8")
    assert "hicks-moorsteen-accounting.svg" in chapter
    assert "Q_y^{t,t+1}" in chapter
    assert "Q_x^{t,t+1}" in chapter


def test_hicks_moorsteen_result_figure_is_one_productivity_screen() -> None:
    root = ElementTree.parse(HICKS_MOORSTEEN_PERFORMANCE_FIGURE).getroot()
    assert root.tag.endswith("svg")
    assert root.find("{http://www.w3.org/2000/svg}title").text == (
        "Hicks-Moorsteen productivity change across organizations, 2020-2021"
    )

    text = _normalized_svg_text(HICKS_MOORSTEEN_PERFORMANCE_FIGURE)
    assert (
        "Hicks\N{EN DASH}Moorsteen total-factor productivity change, "
        "2020\N{EN DASH}2021" in text
    )
    assert "Hicks\N{EN DASH}Moorsteen TFP index" in text
    assert "2020 → 2021" in text
    assert "Complete output-and-input quantity account" in text
    assert "Above 1: total-factor productivity growth" in text
    assert "output-quantity growth divided by input-quantity growth" in text
    assert "under the two VRS technologies" in text
    for excluded in (
        "efficiency change",
        "technical change",
        "price recovery",
        "fare-primont",
    ):
        assert excluded not in text.casefold()

    chapter = HICKS_MOORSTEEN_CHAPTER.read_text(encoding="utf-8")
    assert "hicks-moorsteen-performance-result.svg" in chapter
    assert 'kind="performance"' in chapter
    assert 'metric="productivity_change"' in chapter
    assert "period=2021" in chapter
    assert 'view="points"' in chapter
    normalized_chapter = " ".join(chapter.split())
    assert "complete eight-distance quantity account" in normalized_chapter
    assert "not a ranking of causes or managerial merit" in normalized_chapter


def test_ml_chapter_maps_all_four_public_distance_fields() -> None:
    chapter = ML_CHAPTER.read_text(encoding="utf-8")
    assert "malmquist-luenberger-frontier-account.svg" in chapter
    assert "environmental-four-distance-matrix.svg" in chapter
    for field in (
        "distance_base_on_base",
        "distance_comparison_on_base",
        "distance_base_on_comparison",
        "distance_comparison_on_comparison",
    ):
        assert f"`{field}`" in chapter
    assert "observation-scaled" in chapter
    assert "does **not** establish why" in chapter


def test_material_balance_case_figure_freezes_the_exact_management_account() -> None:
    root = ElementTree.parse(MATERIAL_BALANCE_TARGETS).getroot()
    assert root.tag.endswith("svg")
    assert root.attrib["role"] == "img"
    assert root.attrib["aria-labelledby"] == "title description"

    text = _normalized_svg_text(MATERIAL_BALANCE_TARGETS)
    assert "Technical saving and material-mix improvement" in text
    assert "common resource saving" in text
    assert "TE = 0.50" in text
    assert "lower-material mix" in text
    assert "EAE = 0.75" in text
    assert "EE = 6/16 = 0.375" in text
    assert all(label in text for label in ("A", "B", "C", "D"))

    chapter = MATERIAL_BALANCE_CHAPTER.read_text(encoding="utf-8")
    assert "material-balance-management-targets.svg" in chapter


def test_economic_objective_map_freezes_the_shared_four_plan_case() -> None:
    root = ElementTree.parse(ECONOMIC_OBJECTIVES).getroot()
    assert root.tag.endswith("svg")
    assert root.attrib["role"] == "img"
    assert root.attrib["aria-labelledby"] == "title description"

    text = _normalized_svg_text(ECONOMIC_OBJECTIVES)
    assert (
        "One operating plan, three core price-informed decisions and one "
        "directional bridge" in text
    )
    assert all(
        label in text for label in ("Minimum cost", "Maximum revenue", "Maximum profit")
    )
    assert "SECONDARY INTERPRETIVE BRIDGE" in text
    assert "four price-informed benchmark questions" not in text
    assert "minimum cost = 7" in text
    assert "revenue efficiency = 19/37" in text
    assert "maximum profit = 27" in text
    assert "x̂ = 3.5 · ŷ = (4.75, 2)" in text
    assert "Directional target T: x̂ = 4.4 · ŷ = (4.6, 3.6)" in text
    assert "ν = 10" in text  # noqa: RUF001
    assert "NI = 2.0 = 1.6 + 0.4 programme units" in text
    assert "x*" not in text
    assert "y*" not in text
    assert "neither identify the cause of a gap" in text

    chapter = ECONOMIC_CHAPTER.read_text(encoding="utf-8")
    assert "economic-objectives-management-map.svg" in chapter
    assert 'load_dataset("economic_efficiency_4")' in chapter


def test_profit_recovery_bridge_is_used_in_the_shared_economic_case() -> None:
    root = ElementTree.parse(PROFIT_RECOVERY_BRIDGE).getroot()
    assert root.tag.endswith("svg")
    assert root.attrib["role"] == "img"
    assert root.attrib["aria-labelledby"] == "title description"

    text = _normalized_svg_text(PROFIT_RECOVERY_BRIDGE)
    for account in (
        "Current Plan D",
        "Operating benchmark T",
        "Profit-maximizing Plan B",
        "Profit = 7",
        "Profit = 23",
        "Profit = 27",
        "+16 operating recovery",
        "+4 allocation recovery",
    ):
        assert account in text

    chapter = ECONOMIC_CHAPTER.read_text(encoding="utf-8")
    assert "profit-recovery-bridge.svg" in chapter
    assert "reconciles two counterfactuals" in " ".join(chapter.split())


def test_network_account_figure_uses_family_level_reporting_labels() -> None:
    root = ElementTree.parse(NETWORK_ACCOUNTS).getroot()
    assert root.tag.endswith("svg")
    assert root.attrib["role"] == "img"
    assert root.attrib["aria-labelledby"] == "title description"

    text = _normalized_svg_text(NETWORK_ACCOUNTS)
    assert "Three performance accounts for one connected organization" in text
    assert "SYSTEM-ONLY RADIAL" in text
    assert "RELATIONAL PRODUCT" in text
    assert "ADDITIVE PROCESS ATTRIBUTION" in text
    assert "no process score" in text
    assert "not a transfer price" in text
    assert "not a budget or priority" in text
    assert "KAO" not in text
    assert "CHEN" not in text

    chapter = NETWORK_CHAPTER.read_text(encoding="utf-8")
    assert "two-stage-accounting-choices.svg" in chapter
    assert "Figure revision before publication" not in chapter


def test_network_core_case_uses_one_system_result_plot() -> None:
    root = ElementTree.parse(NETWORK_SYSTEM_FIGURE).getroot()
    assert root.tag.endswith("svg")
    assert root.find("{http://www.w3.org/2000/svg}title").text == (
        "System radial efficiency across research organizations"
    )

    text = _normalized_svg_text(NETWORK_SYSTEM_FIGURE)
    assert "Connected-system resource-use performance" in text
    assert "System input efficiency" in text
    assert "Represented system-wide resource-saving opportunity (E < 1)" in text
    assert "Higher values mean less proportional external-resource saving remains" in (
        text
    )
    assert "1 means no represented system-wide saving opportunity" in text
    assert "Input-oriented CRS benchmark with protected final outcomes" in text

    chapter = NETWORK_CHAPTER.read_text(encoding="utf-8")
    assert "network-system-performance-result.svg" in chapter
    assert "FareGrosskopfNetworkRadialDEA" in chapter
    assert 'kind="performance"' in chapter
    assert 'metric="system_efficiency"' in chapter
    assert 'view="points"' in chapter
    assert "does not assign the gap" in chapter


def test_network_core_case_compares_mainstream_accounts_inside_one_route() -> None:
    chapter = NETWORK_CHAPTER.read_text(encoding="utf-8")

    assert "### Same graph, different responsibility accounts" in chapter
    assert "KaoHwangRelationalDEA" in chapter
    assert "TwoStageAdditiveDecompositionDEA" in chapter
    assert chapter.count('projection="none"') == 2
    assert (
        "* - System-only radial\n  - 0.8333\n  - not applicable\n"
        "  - not applicable" in chapter
    )
    assert "* - Relational product\n  - 0.8333\n  - 0.8333\n  - 1.0000" in chapter
    assert (
        "* - Additive process attribution\n  - 0.9091\n  - 0.8333\n  - 1.0000"
        in chapter
    )
    assert "$0.8333\\times1.0000=0.8333$" in chapter
    assert "$0.5455\\times0.8333+0.4545\\times1.0000=0.9091$" in chapter
    assert "does not make their system\nmeasures interchangeable" in chapter


def test_luenberger_figure_uses_one_programme_and_directional_distances() -> None:
    root = ElementTree.parse(LUENBERGER_LEDGER).getroot()
    assert root.tag.endswith("svg")
    assert root.attrib["role"] == "img"
    assert root.attrib["aria-labelledby"] == "title description"

    text = _normalized_svg_text(LUENBERGER_LEDGER)
    assert "One declared programme, four benchmark appraisals" in text
    assert "ONE COMMON PROGRAMME UNIT g" in text
    assert "D^t(z^t; g)" in text
    assert "D^t(z^(t+1); g)" in text
    assert "OLD OPPORTUNITIES \U0001d4af^t" in text
    assert "NEW OPPORTUNITIES \U0001d4af^(t+1)" in text
    assert "D^(t+1)(z^t; g)" in text
    assert "D^(t+1)(z^(t+1); g)" in text
    assert "may be negative" in text
    assert "L = 1/2 [P^t + P^(t+1)] = EC_L + TC_L" in text
    assert "does not identify management or technology causes" in text

    chapter = LUENBERGER_CHAPTER.read_text(encoding="utf-8")
    assert "luenberger-programme-ledger.svg" in chapter
    assert "four-distance-matrix.svg" not in chapter

    documentation = (ROOT / "docs" / "analysis" / "luenberger.md").read_text(
        encoding="utf-8"
    )
    assert r"\vec D" not in documentation
    assert r"distance $D^\tau(z^\sigma;g)$" in documentation


def test_luenberger_result_figure_keeps_absolute_programme_units() -> None:
    root = ElementTree.parse(LUENBERGER_PERFORMANCE_FIGURE).getroot()
    assert root.tag.endswith("svg")
    assert root.find("{http://www.w3.org/2000/svg}title").text == (
        "Luenberger programme-unit change across hospitals, 2020-2021"
    )

    text = _normalized_svg_text(LUENBERGER_PERFORMANCE_FIGURE)
    assert "Treatment-expansion programme change, 2020\N{EN DASH}2021" in text
    assert "Additional treatment-batch programme units realized" in text
    assert "2020 → 2021" in text
    assert "Complete four-appraisal programme-change account" in text
    assert "Positive means more of the declared treatment programme" in text
    assert "One unit is one additional treatment batch with staff fixed" in text
    assert "appraised against both adjacent-period CRS technologies" in text
    assert "absolute units, not percentages" in text

    chapter = LUENBERGER_CHAPTER.read_text(encoding="utf-8")
    assert "luenberger-performance-result.svg" in chapter
    for argument in (
        'kind="performance"',
        'metric="productivity_change"',
        "period=2021",
        'view="points"',
    ):
        assert chapter.count(argument) == 1
    normalized_chapter = " ".join(chapter.split())
    assert "absolute programme units" in normalized_chapter
    assert "does **not** mean that B is twice as productive as A" in normalized_chapter
    assert "all four appraisals to be available under the same programme" in (
        normalized_chapter
    )
    assert "additive_account_certified=True" not in normalized_chapter
    assert "If either condition fails, there is no productivity conclusion" in (
        normalized_chapter
    )
