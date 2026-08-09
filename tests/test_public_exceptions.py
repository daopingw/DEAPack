"""Public exception hierarchy tests."""

import deapack


def test_exception_hierarchy_is_available_from_the_top_level_api() -> None:
    assert issubclass(deapack.DataValidationError, deapack.DEAPackError)
    assert issubclass(deapack.DataValidationError, ValueError)
    assert issubclass(deapack.ModelSpecificationError, deapack.DEAPackError)
    assert issubclass(deapack.ModelSpecificationError, ValueError)
    assert issubclass(deapack.SolverError, deapack.DEAPackError)
    assert issubclass(deapack.SolverError, RuntimeError)


def test_all_public_exceptions_are_exported() -> None:
    names = {
        "DEAPackError",
        "DataValidationError",
        "ModelSpecificationError",
        "SolverError",
    }
    assert names <= set(deapack.__all__)
