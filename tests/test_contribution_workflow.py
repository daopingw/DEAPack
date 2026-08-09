from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load_dco_module():
    path = ROOT / "scripts" / "check_dco.py"
    specification = importlib.util.spec_from_file_location("check_dco_test", path)
    assert specification is not None and specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def test_public_contribution_entries_are_linked() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    docs_index = (ROOT / "docs" / "index.md").read_text(encoding="utf-8")
    book_index = (ROOT / "book" / "index.md").read_text(encoding="utf-8")
    preface = (ROOT / "book" / "preface.md").read_text(encoding="utf-8")

    assert "[contribution guide](CONTRIBUTING.md)" in readme
    assert "developer/contributing" in docs_index
    assert "project-contributions" in book_index
    assert "{doc}`project-contributions`" in preface


def test_model_proposal_form_keeps_the_source_and_oracle_gate_visible() -> None:
    path = ROOT / ".github" / "ISSUE_TEMPLATE" / "model-proposal.yml"
    source = path.read_text(encoding="utf-8")

    for identifier in ("question", "distinction", "sources", "data_domain", "oracle"):
        assert f"    id: {identifier}\n" in source
    assert "complete primary citation" in source
    assert "independent" in source.lower()
    assert "redistributed" in source


def test_issue_forms_and_pull_request_template_cover_open_contribution_types() -> None:
    issue_dir = ROOT / ".github" / "ISSUE_TEMPLATE"
    for name in (
        "bug-report.yml",
        "data-contribution.yml",
        "documentation-translation.yml",
        "model-proposal.yml",
    ):
        source = (issue_dir / name).read_text(encoding="utf-8")
        assert source.startswith("name: ")
        assert "\ndescription: " in source
        assert "\nbody:\n" in source

    pull_request = (ROOT / ".github" / "PULL_REQUEST_TEMPLATE.md").read_text(
        encoding="utf-8"
    )
    for contribution in (
        "Dataset or provenance",
        "Visualization or reporting",
        "Package Documentation",
        "Chinese Handbook translation",
    ):
        assert contribution in pull_request
    assert "redistribution license" in pull_request
    assert "Signed-off-by" in pull_request
    assert "CC-BY-NC-SA-4.0" in pull_request
    assert "professionally reviewed contribution agreement" in pull_request


def test_contribution_policy_does_not_promise_automatic_authorship() -> None:
    root_guide = (ROOT / "CONTRIBUTING.md").read_text(encoding="utf-8")
    book_page = (ROOT / "book" / "project-contributions.md").read_text(encoding="utf-8")
    docs_page = (ROOT / "docs" / "developer" / "contributing.md").read_text(
        encoding="utf-8"
    )

    assert "does not automatically" in root_guide
    assert "not assigned automatically" in book_page
    assert "not automatic" in docs_page
    assert "citation alone is not permission" in root_guide
    assert "git commit --signoff" in root_guide
    assert "inbound = outbound" in root_guide
    assert "three\n  exact external fingerprints" in root_guide
    assert "no\n  project-created dataset has an active mapping yet" in root_guide
    assert "not accepted" in " ".join(root_guide.split())


def test_handbook_contribution_policy_is_fail_closed_not_a_contract() -> None:
    policy = (ROOT / "book" / "HANDBOOK_CONTRIBUTION_POLICY.md").read_text(
        encoding="utf-8"
    )
    assert "not a copyright-assignment agreement" in policy
    assert "professional review" in policy
    assert "only after the final reviewed instrument is" in policy
    assert "will not merge pull requests" in policy
    assert "does not retroactively assign" in policy


def test_dco_status_checks_every_exact_pull_request_commit_without_running_it() -> None:
    workflow = (ROOT / ".github" / "workflows" / "dco.yml").read_text(encoding="utf-8")
    guide = (ROOT / "CONTRIBUTING.md").read_text(encoding="utf-8")
    pull_request = (ROOT / ".github" / "PULL_REQUEST_TEMPLATE.md").read_text(
        encoding="utf-8"
    )

    assert "pull_request_target:" in workflow
    assert "contents: read" in workflow
    assert "pull-requests: read" in workflow
    assert "persist-credentials: false" in workflow
    assert "pull/${PR_NUMBER}/head:refs/remotes/origin/deapack-dco-head" in workflow
    assert "python -I -S scripts/check_dco.py" in workflow
    assert '--base "$PR_BASE_SHA"' in workflow
    assert '--head "$PR_HEAD_SHA"' in workflow
    assert "pip install" not in workflow
    assert "Every pull-request\ncommit" in guide
    assert "Every commit in this pull request" in pull_request


def test_dco_parser_accepts_only_the_final_git_trailer_block() -> None:
    module = _load_dco_module()

    body_only = (
        "Explain an example.\n\n"
        "Signed-off-by: Quoted Person <quoted@example.test>\n\n"
        "This final paragraph is ordinary prose.\n"
    )
    quoted = (
        "Discuss a prior message.\n\n"
        "> Signed-off-by: Quoted Person <quoted@example.test>\n"
    )
    valid = (
        "Implement the change.\n\n"
        "Reviewed-by: Reviewer <reviewer@example.test>\n"
        "Signed-off-by: Contributor <contributor@example.test>\n"
    )

    assert module.signed_off_by_trailers(body_only) == ()
    assert module.signed_off_by_trailers(quoted) == ()
    assert module.signed_off_by_trailers(valid) == (
        "Signed-off-by: Contributor <contributor@example.test>",
    )
