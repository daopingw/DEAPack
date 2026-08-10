"""Keep locally retained private review material outside the public test suite."""

collect_ignore = [
    "release_candidates",
    "test_book_editorial_contract.py",
    "test_build_automation.py",
    "test_handbook_examples.py",
    "test_handbook_figure_contract.py",
    "test_handbook_figure_localization.py",
    "test_handbook_translations.py",
    "test_pdf_release_quality.py",
    "test_release_dataset_audit.py",
    "test_release_signoff_record.py",
]
