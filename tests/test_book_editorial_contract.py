from __future__ import annotations

import ast
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BOOK_ROOT = ROOT / "book"
BOOK_INDEX = BOOK_ROOT / "index.md"
BOOK_ARCHITECTURE = ROOT / "specs" / "BOOK_ARCHITECTURE.md"
CORE_DELIVERY_MATRIX = ROOT / "specs" / "CORE_FAMILY_DELIVERY_MATRIX.md"
UNIFIED_FRAMEWORK = ROOT / "specs" / "UNIFIED_FRAMEWORK.md"
ARCHIVED_DRAFTS = ROOT / "specs" / "archive" / "book-drafts"

READER_FRONT_MATTER = (
    "preface.md",
    "reading-guide.md",
    "notation.md",
    "glossary.md",
    "citing.md",
)

CORE_CHAPTER_ROUTE = (
    "chapters/01-foundations/01-efficiency-productivity",
    "chapters/01-foundations/02-study-design",
    "chapters/01-foundations/02-production-frontier",
    "chapters/02-classical/03-classical-radial",
    "chapters/02-classical/scale-performance-management",
    "chapters/02-classical/04-sbm",
    "chapters/02-classical/05-directional-distance",
    "chapters/02-classical/economic-efficiency-under-prices",
    "chapters/03-environmental/06-undesirable-outputs-ddf",
    "chapters/03-environmental/07-undesirable-output-sbm",
    "chapters/04-productivity/malmquist-productivity-reference-information",
    "chapters/04-productivity/12-luenberger",
    "chapters/04-productivity/environmental-productivity-ml-common-reference",
    "chapters/04-productivity/17-hicks-moorsteen",
    "chapters/05-network/network-dea-organizations-links-responsibility",
    "chapters/05-network/20-network-sbm",
    "chapters/06-dynamic/dynamic-dea-carryovers-trajectories",
    "chapters/07-heterogeneity/23-metafrontier",
)

APPLIED_CAPSTONES = ("chapters/02-classical/community-hospital-capstone",)

PUBLISHED_CHAPTER_ROUTE = (
    *CORE_CHAPTER_ROUTE[:6],
    *APPLIED_CAPSTONES,
    *CORE_CHAPTER_ROUTE[6:],
)

DOCUMENTATION_ONLY_DRAFTS = frozenset(
    {
        "chapters/02-classical/04-multiplicative-efficiency.md",
        "chapters/02-classical/05-generalized-distance.md",
        "chapters/02-classical/05-range-directional-signed-data.md",
        "chapters/03-environmental/09-by-production-fgl.md",
        "chapters/03-environmental/10-material-balance.md",
        "chapters/04-productivity/14-biennial-malmquist.md",
        "chapters/05-network/21-sequential-network.md",
        "chapters/05-network/22-environmental-network.md",
        "chapters/06-dynamic/20-multiperiod-aggregation.md",
        "chapters/06-dynamic/22-dynamic-network-sbm.md",
    }
)

EVIDENCE_DEFERRED_DRAFTS = frozenset(
    {
        "chapters/02-classical/09-peer-appraisal.md",
        "chapters/02-classical/10-super-efficiency.md",
    }
)

SUPERSEDED_DRAFTS = frozenset(
    {
        "appendices/method-map.md",
        "chapters/02-classical/03-slacks-additive.md",
        "chapters/02-classical/06-cost-and-allocative-efficiency.md",
        "chapters/02-classical/07-revenue-and-output-allocative-efficiency.md",
        "chapters/02-classical/08-profit-and-nerlovian-efficiency.md",
        "chapters/02-classical/alternative-benchmark-technologies.md",
        "chapters/03-environmental/08-by-production.md",
        "chapters/04-productivity/11-malmquist.md",
        "chapters/04-productivity/13-global-malmquist.md",
        "chapters/04-productivity/15-malmquist-luenberger.md",
        "chapters/04-productivity/16-global-malmquist-luenberger.md",
        "chapters/05-network/17-two-stage-relational.md",
        "chapters/05-network/18-two-stage-additive.md",
        "chapters/05-network/19-general-additive-network.md",
        "chapters/06-dynamic/21-dynamic-sbm.md",
    }
)


def _published_entries() -> tuple[str, ...]:
    text = BOOK_INDEX.read_text(encoding="utf-8")
    return tuple(re.findall(r"(?m)^((?:chapters|appendices)/\S+)$", text))


def _active_reader_paths() -> tuple[Path, ...]:
    front_matter = tuple(BOOK_ROOT / name for name in READER_FRONT_MATTER)
    published = tuple(BOOK_ROOT / f"{entry}.md" for entry in _published_entries())
    return (*front_matter, *published)


def _sphinx_excludes() -> set[str]:
    tree = ast.parse((BOOK_ROOT / "conf.py").read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "exclude_patterns"
            for target in node.targets
        ):
            return set(ast.literal_eval(node.value))
    raise AssertionError("book/conf.py does not define exclude_patterns")


def test_declared_handbook_chapter_count_matches_the_published_route() -> None:
    published_chapters = tuple(
        entry for entry in _published_entries() if entry.startswith("chapters/")
    )
    architecture = BOOK_ARCHITECTURE.read_text(encoding="utf-8")
    normalized = " ".join(architecture.split())
    match = re.search(
        r"current route contains (\d+) model and study-design chapter sources "
        r"and one applied-study chapter",
        normalized,
    )
    assert match is not None
    assert len(CORE_CHAPTER_ROUTE) == int(match.group(1))
    assert len(published_chapters) == int(match.group(1)) + 1
    assert published_chapters == PUBLISHED_CHAPTER_ROUTE


def test_published_route_is_the_reviewed_core_family_route() -> None:
    published_chapters = tuple(
        entry for entry in _published_entries() if entry.startswith("chapters/")
    )
    assert published_chapters == PUBLISHED_CHAPTER_ROUTE
    assert set(CORE_CHAPTER_ROUTE).issubset(published_chapters)


def test_book_scope_contract_is_family_based_not_paper_based() -> None:
    architecture = BOOK_ARCHITECTURE.read_text(encoding="utf-8")
    normalized = " ".join(architecture.split())

    assert "core model family" in normalized
    assert "not a named paper" in normalized
    assert "Citation volume cannot promote a redundant formulation" in normalized
    assert "source-specific implementation belongs only in Documentation" in normalized
    assert "not in a chapter, case, figure, or handbook appendix" in normalized


def test_unified_framework_does_not_use_appendices_as_a_variant_catalogue() -> None:
    framework = UNIFIED_FRAMEWORK.read_text(encoding="utf-8")
    normalized = " ".join(framework.split())

    assert "principal, transferable model families" in normalized
    assert "paper-specific direction, weight, normalization" in normalized
    assert "the handbook appendix is not an overflow catalogue" in normalized
    assert "method atlas and appendix" not in normalized


def test_delivery_matrix_audits_exactly_the_published_core_route() -> None:
    matrix = CORE_DELIVERY_MATRIX.read_text(encoding="utf-8")
    audited_routes = tuple(
        re.findall(
            r"(?m)^\| (?:I|II|III|IV|V|VI|VII) \| .*?\(`([^`]+)`\) \|",
            matrix,
        )
    )

    assert audited_routes == tuple(Path(route).name for route in CORE_CHAPTER_ROUTE)


def test_live_book_tree_contains_core_chapters_and_the_applied_capstone() -> None:
    expected = {f"{entry}.md" for entry in PUBLISHED_CHAPTER_ROUTE}
    live_chapters = {
        path.relative_to(BOOK_ROOT).as_posix()
        for path in (BOOK_ROOT / "chapters").rglob("*.md")
    }

    assert len(live_chapters) == 19
    assert live_chapters == expected


def test_archived_draft_inventory_preserves_all_scope_decisions() -> None:
    expected_by_status = {
        "documentation-only": DOCUMENTATION_ONLY_DRAFTS,
        "evidence-deferred": EVIDENCE_DEFERRED_DRAFTS,
        "superseded": SUPERSEDED_DRAFTS,
    }

    for status, expected in expected_by_status.items():
        status_root = ARCHIVED_DRAFTS / status
        actual = frozenset(
            path.relative_to(status_root).as_posix()
            for path in status_root.rglob("*.md")
        )
        assert actual == expected

    assert sum(map(len, expected_by_status.values())) == 27


def test_exactly_one_reader_appendix_is_published() -> None:
    published_appendices = tuple(
        entry for entry in _published_entries() if entry.startswith("appendices/")
    )
    assert published_appendices == ("appendices/unified-framework",)

    live_appendices = {
        path.relative_to(BOOK_ROOT).as_posix()
        for path in (BOOK_ROOT / "appendices").glob("*.md")
    }

    assert live_appendices == {"appendices/unified-framework.md"}


def test_reference_page_lists_only_works_cited_by_the_published_book() -> None:
    references = (BOOK_ROOT / "references.md").read_text(encoding="utf-8")

    assert references.count("```{bibliography}") == 1
    assert ":all:" not in references
    assert ":filter:" not in references


def test_contributor_readme_is_not_published_as_a_book_page() -> None:
    assert "README.md" in _sphinx_excludes()


def test_published_chapters_follow_the_reader_facing_contract() -> None:
    forbidden_internal_terms = (
        "method_id",
        "preset_id",
        "source_profile",
        "runtime profile",
        "implementation audit",
        "planned variants",
        "future leaf",
        "published reproduction",
    )

    for entry in _published_entries():
        if not entry.startswith("chapters/"):
            continue
        path = BOOK_ROOT / f"{entry}.md"
        text = path.read_text(encoding="utf-8")
        lowered = text.lower()

        assert not text.startswith(":orphan:"), path
        assert "```{figure}" in text, path
        for term in forbidden_internal_terms:
            assert term not in lowered, (path, term)


def test_community_hospital_capstone_is_a_management_study_not_a_model_catalogue() -> (
    None
):
    chapter = (
        BOOK_ROOT / "chapters/02-classical/community-hospital-capstone.md"
    ).read_text(encoding="utf-8")
    normalized = " ".join(chapter.split())

    for phrase in (
        "Begin with the decision, not the score",
        "Build the comparison group before seeing performance",
        "Turn one score into an operational inquiry",
        "Learn which conclusions survive alternative readings",
        "Prepare evidence for a management review",
        "not an instruction to copy its organization",
        "not next year's budget",
    ):
        assert phrase in normalized
    for route in (
        "BCCInput().fit(main_data)",
        'SBM(returns_to_scale="vrs").fit(main_data)',
        'scale_efficiency(main_data, orientation="input")',
        "primary_result.peers(focus)",
        "primary_result.targets_for(focus)",
        "primary_result.publish(",
    ):
        assert route in chapter
    for engineering_term in (
        "geometry",
        "arrow",
        "account",
        "contract",
        "declared",
        "represented",
    ):
        assert re.search(rf"\b{engineering_term}\b", chapter, re.IGNORECASE) is None


def test_reader_facing_book_does_not_narrate_internal_release_pipelines() -> None:
    forbidden_pipeline_language = (
        "postsolve_certified",
        "economic_postsolve_certified",
        "all_four_distance_programs_certified",
        "all_four_economic_distance_claims_certified",
        "multiplicative_account_certified",
        "additive_account_certified",
        "publication gate",
        "validity gate",
        "headline gate",
        "release check",
        "result-native",
        "public result table",
        "certificate = result.diagnostics",
        "solver-neutral postsolve",
    )

    for path in _active_reader_paths():
        lowered = path.read_text(encoding="utf-8").casefold()
        for term in forbidden_pipeline_language:
            assert term not in lowered, (path, term)


def test_reader_entry_pages_separate_the_book_from_project_governance() -> None:
    preface = (BOOK_ROOT / "preface.md").read_text(encoding="utf-8")
    guide = (BOOK_ROOT / "reading-guide.md").read_text(encoding="utf-8")
    citing = (BOOK_ROOT / "citing.md").read_text(encoding="utf-8")

    for term in (
        "unified Python architecture",
        "public API",
        "method registry",
        "result contract",
    ):
        assert term not in preface
    for term in ("will link", "should remain", "implemented and fully tested"):
        assert term not in guide
    for term in (
        "Archival publication plan",
        "reserve a DOI",
        "Zenodo",
        "Google Scholar",
        "Google Books",
    ):
        assert term not in citing

    assert "DEAPack is the computational companion to the book" in preface
    assert "## Numerical integrity without software plumbing" in guide
    assert "it remains missing; it is never\nreplaced by zero" in guide
    assert "The book and DEAPack are related but distinct scholarly works" in citing
    assert "FULL_COMMIT_HASH" in citing


def test_reading_guide_gives_unambiguous_first_and_second_pass_routes() -> None:
    guide = (BOOK_ROOT / "reading-guide.md").read_text(encoding="utf-8")
    normalized = " ".join(guide.split())

    for first_pass_step in (
        "Part I through the construction of the production frontier",
        "classical radial DEA",
        "Additive, RAM, and SBM measures",
        "the community-hospital efficiency study",
        "directional distance",
        "whichever applied part matches the production problem",
    ):
        assert first_pass_step in normalized
    assert "scale chapter is valuable but optional on this first pass" in normalized
    assert "Bootstrap inference" in normalized
    assert "researcher's second pass" in normalized
    assert "larger cases demonstrate" not in normalized
    assert "workflow template, not evidence about a real health system" in normalized
    assert "A publishable application must use defensible source data" in normalized


def test_glossary_routes_historical_names_to_core_concepts() -> None:
    glossary = (BOOK_ROOT / "glossary.md").read_text(encoding="utf-8")
    normalized = " ".join(glossary.split())

    assert "```{glossary}" in glossary
    for term in (
        "CCR model",
        "BCC model",
        "Free disposal hull (FDH)",
        "Additive model",
        "RAM",
        "Slacks-based measure (SBM)",
        "Directional distance function (DDF)",
        "Malmquist productivity index",
        "Network DEA",
        "Metafrontier",
        "Undesirable output",
    ):
        assert f"\n{term}\n" in glossary
    assert "not a separate mother family from Farrell radial DEA" in normalized
    assert "historical label conditionally equivalent" in normalized
    assert "Complete API names and technical variants remain" in normalized


def test_handbook_keeps_external_membership_and_numerical_fields_substantive() -> None:
    environmental = (
        BOOK_ROOT / "chapters/03-environmental/07-undesirable-output-sbm.md"
    ).read_text(encoding="utf-8")
    economic = (
        BOOK_ROOT / "chapters/02-classical/economic-efficiency-under-prices.md"
    ).read_text(encoding="utf-8")

    assert "externally evaluated plant" in environmental
    assert "self_in_reference" not in environmental
    assert "is_within_reference_technology" not in environmental
    assert '"reconstruction_residual"' not in economic


def test_editorial_contract_keeps_numerical_integrity_out_of_the_narrative() -> None:
    architecture = BOOK_ARCHITECTURE.read_text(encoding="utf-8")
    contributor_guide = (BOOK_ROOT / "CONTRIBUTING.md").read_text(encoding="utf-8")

    assert "Numerical integrity is a publication condition" in architecture
    assert "A failed or infeasible comparison remains unavailable" in architecture
    assert "the chapter explains the economic\ncondition" in architecture
    assert "Field-level\nsolver statuses" in contributor_guide
    assert "Never replace it with\nzero" in contributor_guide


def test_published_section_headings_do_not_form_a_paper_catalogue() -> None:
    for entry in CORE_CHAPTER_ROUTE:
        path = BOOK_ROOT / f"{entry}.md"
        headings = re.findall(r"(?m)^#{2,3} .+$", path.read_text(encoding="utf-8"))

        for heading in headings:
            assert "{cite" not in heading, (path, heading)
            assert "et al." not in heading.lower(), (path, heading)
            assert re.search(r"\b(?:19|20)\d{2}\b", heading) is None, (path, heading)


def test_congestion_can_only_be_one_unnamed_scale_chapter_section() -> None:
    congestion_headings: list[tuple[str, str]] = []

    for entry in CORE_CHAPTER_ROUTE:
        path = BOOK_ROOT / f"{entry}.md"
        headings = re.findall(r"(?m)^#{2,3} .+$", path.read_text(encoding="utf-8"))
        congestion_headings.extend(
            (entry, heading) for heading in headings if "congestion" in heading.lower()
        )

    assert len(congestion_headings) <= 1
    for entry, heading in congestion_headings:
        assert entry.endswith("scale-performance-management")
        assert "fgl" not in heading.lower()
        assert "cooper" not in heading.lower()
        assert re.search(r"\b(?:19|20)\d{2}\b", heading) is None


def test_tau_is_reserved_for_reference_time_in_the_handbook() -> None:
    for entry in CORE_CHAPTER_ROUTE:
        if "/04-productivity/" in entry:
            continue
        text = (BOOK_ROOT / f"{entry}.md").read_text(encoding="utf-8")
        assert r"\tau" not in text, entry

    notation = (BOOK_ROOT / "notation.md").read_text(encoding="utf-8")
    assert r"$\tau\in\{1,\ldots,T\}$" in notation
    assert "the period supplying the reference technology" in notation
    assert r"\tau_{\mathrm{peer}}" not in notation


def test_part_v_to_vii_do_not_promote_cross_family_implementation_routes() -> None:
    published_text = {
        entry: (BOOK_ROOT / f"{entry}.md").read_text(encoding="utf-8")
        for entry in CORE_CHAPTER_ROUTE
    }

    for entry, text in published_text.items():
        assert "GeneralAdditiveNetworkDEA" not in text, entry

    network_sbm = published_text["chapters/05-network/20-network-sbm"]
    network_sbm_h3 = re.findall(r"(?m)^### .+$", network_sbm)
    assert not any(
        re.search(r"\bas[- ](?:input|output)\b", heading, flags=re.IGNORECASE)
        for heading in network_sbm_h3
    )

    dynamic = published_text["chapters/06-dynamic/dynamic-dea-carryovers-trajectories"]
    dynamic_h2 = re.findall(r"(?m)^## .+$", dynamic)
    assert not any("dynamic network" in heading.lower() for heading in dynamic_h2)


def test_metafrontier_chapter_separates_declared_groups_from_estimated_context() -> (
    None
):
    chapter = (BOOK_ROOT / "chapters/07-heterogeneity/23-metafrontier.md").read_text(
        encoding="utf-8"
    )
    boundary = chapter[
        chapter.index(
            "```{admonition} Known groups are not discovered groups"
        ) : chapter.index("## Two standards answer two different questions")
    ]

    assert "fixed before the\nfrontiers are estimated" in boundary
    assert "Clustering instead asks the data to discover groups" in boundary
    assert "a conditional frontier asks" in boundary
    assert "does neither" in boundary


def test_source_specific_api_routes_do_not_reenter_active_book() -> None:
    forbidden_routes = (
        "ActivitySpecificWeakDisposalDDF",
        "APZMalmquistLuenbergerDEA",
        "APZMalmquistLuenbergerProductivityIndex",
        "ChungFareGrosskopfDDF",
        "KuosmanenWeakDisposalDDF",
        "GeneralAdditiveNetworkDEA",
        "DynamicNetworkSBM",
    )

    for entry in CORE_CHAPTER_ROUTE:
        text = (BOOK_ROOT / f"{entry}.md").read_text(encoding="utf-8")
        for route in forbidden_routes:
            assert route not in text, (entry, route)

    environmental = (
        BOOK_ROOT / "chapters/03-environmental/06-undesirable-outputs-ddf.md"
    ).read_text(encoding="utf-8")
    assert "CommonFactorWeakDisposalDDF" in environmental
    assert 'input_direction="zeros"' in environmental
    assert 'output_direction="observed"' in environmental
    assert 'bad_output_direction="observed"' in environmental


def test_opening_separates_benchmark_quantity_and_price_accounts() -> None:
    chapter = (
        BOOK_ROOT / "chapters/01-foundations/01-efficiency-productivity.md"
    ).read_text(encoding="utf-8")
    notation = (BOOK_ROOT / "notation.md").read_text(encoding="utf-8")
    matrix = CORE_DELIVERY_MATRIX.read_text(encoding="utf-8")
    normalized = " ".join(chapter.split())

    assert chapter.startswith("# Efficiency, Productivity, and Profitability\n")
    assert chapter.count("three-performance-accounts-result.svg") == 1
    assert "observed physical productivity" in normalized
    assert (
        "not a unique multi-output productivity measure supplied by DEA" in normalized
    )
    assert "Profit is a monetary difference" in normalized
    assert "endogenous DEA multipliers as observed prices" in normalized
    assert "net profit" not in normalized
    assert "ReturnToDollarEfficiency" in chapter
    assert r"AP_j=\frac{y_j}{x_j}" in chapter
    assert r"AP_j^{eq}" in chapter
    assert r"\rho_o^{RTD}=\frac{R_o}{C_o}" in chapter

    assert "## Productivity levels and observed prices" in notation
    assert r"AP_j=\frac{y_j}{x_j}" in notation
    assert r"AP_j^{eq}" in notation
    assert r"\rho_o^{RTD}=\frac{R_o}{C_o}" in notation
    assert "efficiency, productivity, and profitability" in matrix


def test_study_design_separates_candidates_eligible_references_and_active_peers() -> (
    None
):
    chapter = (BOOK_ROOT / "chapters/01-foundations/02-study-design.md").read_text(
        encoding="utf-8"
    )
    notation = (BOOK_ROOT / "notation.md").read_text(encoding="utf-8")
    reference_docs = (ROOT / "docs" / "user-guide" / "reference-sets.md").read_text(
        encoding="utf-8"
    )
    normalized = " ".join(chapter.split())

    assert chapter.count("peer-eligibility-sensitivity-result.svg") == 1
    for distinction in (
        "candidate roster",
        "eligible reference population",
        "active peer plan",
    ):
        assert distinction in normalized.casefold()
    for exact in (
        "holds Lakeside's recorded operation fixed",
        "strict same-contract rule",
        "broader district-mission rule",
        "0.9375",
        "0.902778",
        "6.25 percent common proportional resource-saving opportunity",
        "9.72 percent opportunity",
        "before slack completion",
        "$4/9$ for North and $5/9$ for West",
        "cannot support a quality conclusion",
        "neither makes a Pareto--Koopmans or slack-completed target claim",
        'BCC(\n        orientation="input",\n        compute_slacks=False,',
        'district_mission_result.peers("Lakeside")',
    ):
        assert exact in normalized if "\n" not in exact else exact in chapter
    assert "Neither rule is automatically correct" in chapter
    assert "comparison-eligibility ledger" in chapter
    assert "Eligibility decision" in chapter
    assert "same_contract_eligible" in chapter
    assert "role_declared_data" in chapter
    assert "will stop with a specification error" in normalized
    assert "same_contract_peer" not in chapter
    assert "eligible set of eligible organizations" not in normalized
    assert "excluding West only after it becomes" in normalized
    assert (
        "Scores from the two eligibility rules should be reported side by side"
        in normalized
    )
    assert (
        "metafrontier"
        not in " ".join(
            chapter[
                chapter.index("Three groups of organizations") : chapter.index(
                    "Eligibility also has a dimensional consequence"
                )
            ].split()
        ).casefold()
    )

    assert "Candidate record, eligible comparator, and active peer" in " ".join(
        notation.split()
    )
    assert "construct `DEAData` only from rows that pass" in reference_docs
    assert "three different objects" in reference_docs
    assert "deleting a demanding\nobservation" in reference_docs


def test_part_i_moves_from_performance_question_to_design_to_opportunity_set() -> None:
    performance = (
        BOOK_ROOT / "chapters/01-foundations/01-efficiency-productivity.md"
    ).read_text(encoding="utf-8")
    design = (BOOK_ROOT / "chapters/01-foundations/02-study-design.md").read_text(
        encoding="utf-8"
    )
    technology = (
        BOOK_ROOT / "chapters/01-foundations/02-production-frontier.md"
    ).read_text(encoding="utf-8")
    study_map = (BOOK_ROOT / "_static/figures/study-composition-map.svg").read_text(
        encoding="utf-8"
    )

    # The opening chapter separates the managerial accounts before it formalizes
    # the production set; the second chapter settles study design before method
    # choice; the third turns those choices into an attainable-opportunity claim.
    assert performance.index("A hospital board") < performance.index(
        "## Production possibilities and resource responsibility"
    )
    production_possibilities = performance.index(
        "## Production possibilities and resource responsibility"
    )
    assert production_possibilities < performance.index(
        "## What may management change?"
    )

    design_markers = (
        "## Begin with the decision the organization actually faces",
        "## Where does one hospital begin and end?",
        "## A column acquires meaning from the production story",
        "## Comparison eligibility is an institutional claim",
        "## Only then choose the method family",
        "## Read the eventual score inside its comparison contract",
    )
    design_positions = tuple(design.index(marker) for marker in design_markers)
    assert design_positions == tuple(sorted(design_positions))

    normalized_technology = " ".join(technology.casefold().split())
    assert "sits between study design and efficiency measurement" in (
        normalized_technology
    )
    assert "resource commitments" in normalized_technology
    assert "service capability" in normalized_technology
    assert "organizational divisibility" in normalized_technology

    # Each step remains attached to a concrete reader-facing hospital or branch
    # example and to its existing explanatory figure.
    assert performance.count("three-performance-accounts-result.svg") == 1
    assert "hospital board" in performance.casefold()
    assert design.count("study-composition-map.svg") == 1
    assert design.count("peer-eligibility-sensitivity-result.svg") == 1
    assert "Lakeside" in design
    assert technology.count("convex-virtual-dmu.svg") == 1
    assert technology.count("crs-vrs-frontiers.svg") == 1
    assert "a and d as two complete annual operating accounts" in (
        normalized_technology
    )
    assert "point m" in normalized_technology
    assert "branch b" in normalized_technology
    assert "branch d" in normalized_technology

    assert "Comparison contract" in study_map
    assert "Every result is conditional on the comparison contract" in study_map
    for internal_label in (
        "Expanded study specification",
        "system graph + data roles",
        "frontier estimator",
        "Historical model name",
    ):
        assert internal_label not in study_map


def test_production_technology_states_the_economic_rights_behind_the_frontier() -> None:
    chapter = (
        BOOK_ROOT / "chapters/01-foundations/02-production-frontier.md"
    ).read_text(encoding="utf-8")
    normalized = " ".join(chapter.casefold().split())

    section_markers = (
        "## A technology is a claim about attainable operating plans",
        "## Free disposal: feasibility is not approval",
        "## Convexity: may practices be combined?",
        "### FDH when only complete observed practices may teach",
        "## Returns to scale: may an operating pattern be replicated?",
        "## Orientation identifies the commitment to protect",
    )
    section_positions = tuple(chapter.index(marker) for marker in section_markers)
    assert section_positions == tuple(sorted(section_positions))

    # Observed feasibility and free disposal are opportunity-set assumptions,
    # not endorsements of waste or service withdrawal.
    assert "every admitted observation must belong to the empirical technology" in (
        normalized
    )
    assert "leave some resource capacity idle" in normalized
    assert "waste is costless" in normalized
    assert "reducing service is acceptable" in normalized

    # Convexity grants a right to form virtual operating plans; the A--D--M
    # example must also warn readers that this is not an implementation recipe.
    assert "weighted average of feasible activities" in normalized
    assert "m is not a third observed organization" in normalized
    assert "may not be managerially attainable" in normalized
    assert "not a causal recipe" in normalized
    assert "$m=0.5a+0.5d=(2.5,2.4)$" in normalized

    # FDH withholds synthetic averaging, whereas CRS and VRS grant different
    # scale-replication rights. These are economic claims, not score labels.
    assert "does not fill the gaps between observations" in normalized
    assert "one complete observed practice" in normalized
    assert "without the restriction $\\mathbf 1^\\top\\lambda=1$" in normalized
    assert "replicated while preserving its input--output proportions" in normalized
    assert "vrs withdraws the right of unrestricted proportional replication" in (
        normalized
    )
    assert "crs and vrs grant different replication rights" in normalized


def test_radial_separates_the_proportional_claim_from_completion() -> None:
    chapter = (BOOK_ROOT / "chapters/02-classical/03-classical-radial.md").read_text(
        encoding="utf-8"
    )
    radial_docs = (ROOT / "docs" / "models" / "radial.md").read_text(encoding="utf-8")
    visualization_docs = (ROOT / "docs" / "user-guide" / "visualization.md").read_text(
        encoding="utf-8"
    )
    matrix = CORE_DELIVERY_MATRIX.read_text(encoding="utf-8")
    normalized = " ".join(chapter.split())
    lowered = normalized.casefold()
    normalized_radial_docs = " ".join(radial_docs.split())
    normalized_matrix = " ".join(matrix.split())

    assert chapter.count("radial-improvement-result.svg") == 1
    assert "radial-and-slack.svg" not in chapter
    assert chapter.count('result.plot(kind="improvement", dmu_id="C")') == 1
    assert normalized.index("## Read the movement as an operating comparison") < (
        normalized.index("## When a score of one does not close the operating account")
    )
    for concept in (
        "phase-one radial plan",
        "slacks and completed target",
        "service slack of $0.5$",
        "radially efficient but not strongly efficient",
        "selected completed plan",
    ):
        assert concept in lowered
    for formula in (
        "$\\theta_C=1$",
        "x_o^{R}=\\theta_o x_o",
        "\\widehat x_o=x_o^{R}-s_o^-",
    ):
        assert formula in normalized
    assert re.search(
        r"completion.{0,160}(?:never|does not).{0,80}(?:revise|change).{0,20}"
        r"(?:\\theta|\\phi|radial score)",
        normalized,
        flags=re.IGNORECASE,
    )
    assert re.search(
        r"(?:not|neither).{0,120}(?:implementation|management).{0,30}"
        r"(?:order|prescription)",
        normalized,
        flags=re.IGNORECASE,
    )

    assert "## Operating-plan visualization" in radial_docs
    assert 'kind="improvement"' in radial_docs
    assert "public `targets` table contains the completed target" in (
        normalized_radial_docs
    )
    assert "## Separate the radial factor from target completion" in (
        visualization_docs
    )
    assert "result-native ledger" in matrix
    assert "no model, method identity, parameter, plot kind" in normalized_matrix


def test_ddf_opens_with_planning_contracts_instead_of_geometry() -> None:
    chapter = (
        BOOK_ROOT / "chapters/02-classical/05-directional-distance.md"
    ).read_text(encoding="utf-8")
    directional_docs = (ROOT / "docs" / "models" / "directional.md").read_text(
        encoding="utf-8"
    )
    matrix = CORE_DELIVERY_MATRIX.read_text(encoding="utf-8")
    normalized = " ".join(chapter.split())

    assert chapter.count("ddf-programme-contracts-result.svg") == 1
    assert "ddf-directions.svg" not in chapter
    introduction = " ".join(
        chapter[: chapter.index("## What one unit of the improvement")].split()
    )
    for concept in (
        "operating-improvement package",
        "before the model is fitted",
        "management is responsible for changing",
        "decision horizon",
        "economic specification of the proposed improvement",
        "fixed before the results are known",
    ):
        assert concept in introduction
    for numerical_contract in ("$\\beta=0.247253$", "$\\beta=0.419355$"):
        assert numerical_contract in normalized
    assert normalized.count("specified package") >= 5
    assert "different packages do not provide a common ranking" in normalized
    assert re.search(
        r"zero direction.{0,100}no change required.{0,80}first-stage package",
        normalized,
        flags=re.IGNORECASE,
    )
    assert re.search(
        r"do not revise.{0,20}\\beta_o.{0,30}change.{0,20}\$g\$.{0,80}"
        r"management programme",
        normalized,
        flags=re.IGNORECASE,
    )

    assert "## Three observed-direction contracts" in directional_docs
    for direction_pair in (
        'input_direction="observed",\n        output_direction="zeros"',
        'input_direction="zeros",\n        output_direction="observed"',
        'input_direction="observed",\n        output_direction="observed"',
    ):
        assert direction_pair in directional_docs
    assert "same-operation, three-programme composite" in matrix


def test_core_explanations_lead_with_operating_meaning_before_formal_geometry() -> None:
    radial = (BOOK_ROOT / "chapters/02-classical/03-classical-radial.md").read_text(
        encoding="utf-8"
    )
    scale = (
        BOOK_ROOT / "chapters/02-classical/scale-performance-management.md"
    ).read_text(encoding="utf-8")
    ddf = (BOOK_ROOT / "chapters/02-classical/05-directional-distance.md").read_text(
        encoding="utf-8"
    )
    environmental = (
        BOOK_ROOT / "chapters/03-environmental/06-undesirable-outputs-ddf.md"
    ).read_text(encoding="utf-8")

    normalized_radial = " ".join(radial.split())
    normalized_scale = " ".join(scale.split())
    normalized_ddf = " ".join(ddf.split())
    normalized_environmental = " ".join(environmental.split())

    assert "feasible operating plan" in normalized_radial
    assert "Each arrow begins" not in radial
    assert "result-native" not in radial.casefold()

    assert "## What one unit of the improvement programme changes" in ddf
    assert "one programme unit is a physical commitment" in normalized_ddf
    assert normalized_ddf.index(
        "One unit of the operating-improvement package"
    ) < normalized_ddf.index(r"D_{\mathcal T}(x_o,y_o;g)")

    assert "copied at another organizational size" in normalized_scale
    assert "responds to a small proportional change in organizational size" in (
        normalized_scale
    )
    assert scale.index("At some efficient plans") < scale.index(
        "Banker--Thrall procedure"
    )
    assert "support_interval_valid" not in scale
    assert '"analysis_status"' not in scale

    management_question = environmental.index("The first management question")
    weak_disposal_formula = environmental.index(r"(\alpha y,\alpha b)\in P(x)")
    assert management_question < weak_disposal_formula
    assert "lowering pollution requires curtailing the joint production activity" in (
        normalized_environmental
    )


def test_part_ii_slack_family_merges_aliases_without_merging_estimands() -> None:
    chapter = (BOOK_ROOT / "chapters/02-classical/04-sbm.md").read_text(
        encoding="utf-8"
    )
    normalized = " ".join(chapter.split())

    headings = (
        "## Begin with one feasible operating plan",
        "## The same gaps under three reporting rulers",
        "## One SBM family, three management mandates",
        "## Keep radial, slack, and directional claims distinct",
    )
    positions = tuple(chapter.index(heading) for heading in headings)
    assert positions == tuple(sorted(positions))

    for symbol in (
        r"\delta_o^{RAM}",
        r"\rho_o^{RAM}=1-\delta_o^{RAM}",
        r"\rho_o^I=1-L_o^x",
        r"\rho_o^O",
        r"\rho_o^{NO}",
        r"\widehat x_o=x_o-s^-",
        r"\widehat y_o=y_o+s^+",
    ):
        assert symbol in chapter
    assert "x_o^*" not in chapter
    assert "y_o^*" not in chapter

    for conditional_alias in (
        "input Russell measure",
        "output Russell expansion account",
        "enhanced Russell graph (ERG)",
        "conditional aliases",
    ):
        assert conditional_alias in normalized

    for ram_contract in (
        "self-inclusive VRS comparison",
        "same reference population",
        "finite signed data",
        "zero range contributes zero",
    ):
        assert ram_contract in normalized
    assert "standard RAM and SBM accounts" in normalized
    assert "first-stage changes in that package" in normalized
    assert "different estimands" in normalized


def test_part_ii_economic_family_closes_theory_practice_and_symbols() -> None:
    chapter = (
        BOOK_ROOT / "chapters/02-classical/economic-efficiency-under-prices.md"
    ).read_text(encoding="utf-8")
    notation = (BOOK_ROOT / "notation.md").read_text(encoding="utf-8")
    conventions = (ROOT / "specs" / "CONVENTIONS.md").read_text(encoding="utf-8")
    nerlovian_docs = (ROOT / "docs" / "models" / "nerlovian.md").read_text(
        encoding="utf-8"
    )
    normalized = " ".join(chapter.split())

    headings = (
        "## Cost: protect the service commitment",
        "## Revenue: use the available capacity well",
        "## Profit: choose the operating plan jointly",
        "## A directional bridge to the profit gap",
        "## Reproduce the account with DEAPack",
    )
    positions = tuple(chapter.index(heading) for heading in headings)
    assert positions == tuple(sorted(positions))

    for identity in (
        r"CE_o=TE_o^I AE_o^C",
        r"RE_o=TE_o^OAE_o^R",
        r"G_o^\Pi=\Pi_o^*-\Pi_o",
        r"NI_o:=\frac{G_o^\Pi}{\nu_o}",
    ):
        assert identity in chapter
    assert r"G_o^\pi" not in chapter
    assert r"\pi_o" not in chapter

    for practice_element in (
        "NerlovianProfitInefficiency",
        'input_direction={"resource": 1.0}',
        '"technical_efficiency", "allocative_efficiency"',
        '"technical_inefficiency", "allocative_inefficiency"',
        "$NI=2.0=1.6+0.4$",
    ):
        assert practice_element in chapter

    assert "whose valuation they represent" in normalized
    assert "not the endogenous multiplier weights" in normalized
    assert "profit gap" in normalized
    assert "ratio can become undefined or reverse" in normalized

    for source in (notation, conventions, nerlovian_docs):
        assert r"\nu_o=w_o^\top g_o^x+p_o^\top g_o^y" in source
        assert r"q_o=w_o^\top g_o^x+p_o^\top g_o^y" not in source
    assert r"\mathbb R_{++}^m" in notation
    assert r"\mathbb{R}_{++}^m" in conventions
    assert r"\mathcal P_o=\{j:\lambda_j^*>0\}" in conventions
    assert r"$R_o=\{j:\lambda_j^*>0\}" not in conventions


def test_part_ii_scale_contract_separates_scores_targets_and_congestion() -> None:
    radial = (BOOK_ROOT / "chapters/02-classical/03-classical-radial.md").read_text(
        encoding="utf-8"
    )
    scale = (
        BOOK_ROOT / "chapters/02-classical/scale-performance-management.md"
    ).read_text(encoding="utf-8")
    normalized_radial = " ".join(radial.split())
    normalized_scale = " ".join(scale.split())

    for external_boundary in (
        "external or leave-group-out reference",
        "$\\theta$ can exceed one",
        "$\\phi$ can fall below one",
        "do not inherit the usual $[0,1]$ efficiency interpretation",
    ):
        assert external_boundary in normalized_radial
    assert "public peer rows belong to the selected slack-completed target" in (
        normalized_radial
    )
    assert "unique intensity solution to the phase-one programme" in normalized_radial

    assert "two matched radial score accounts" in normalized_scale
    assert "does not perform slack completion" in normalized_scale
    assert "separately selected Pareto-efficient VRS target" in normalized_scale
    assert r"(\widehat x_o,\widehat y_o)" in scale
    assert "valid positive ratio remains at most one" in normalized_scale
    assert "leaving `is_scale_efficient` missing" in normalized_scale
    assert "reducing a particular excessive input can raise attainable output" in (
        normalized_scale
    )
    for insufficient_congestion_evidence in (
        "decreasing returns",
        "ordinary input slack",
        "CRS--VRS scale ratio",
    ):
        assert insufficient_congestion_evidence in normalized_scale


def test_productivity_components_are_explained_as_economic_accounts() -> None:
    malmquist = (
        BOOK_ROOT
        / "chapters/04-productivity/malmquist-productivity-reference-information.md"
    ).read_text(encoding="utf-8")
    luenberger = (BOOK_ROOT / "chapters/04-productivity/12-luenberger.md").read_text(
        encoding="utf-8"
    )
    environmental = (
        BOOK_ROOT
        / "chapters/04-productivity/environmental-productivity-ml-common-reference.md"
    ).read_text(encoding="utf-8")

    assert malmquist.index("the measured operating shortfall has narrowed") < (
        malmquist.index("The traditional word *catch-up*")
    )
    assert "but should not be mistaken for an explanation" in malmquist
    assert "DEA alone cannot decide among them" in malmquist

    assert luenberger.index("the contemporaneous shortfall became smaller") < (
        luenberger.index("“Catch-up” is often used")
    )
    assert "represented production opportunities" in luenberger
    assert "institutional evidence is needed to explain its cause" in luenberger

    assert "**best-practice-opportunity change**" in environmental
    assert "The component does not reveal why the benchmark\nchanged" in environmental
    assert "accounting description rather than a causal allocation" in environmental
