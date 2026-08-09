"""Independent source oracle for Charnes et al. (1990) Example 2."""

from __future__ import annotations

import numpy as np
from scipy.optimize import linprog


def _example_two() -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    inputs = np.asarray(
        [
            [10, 10],
            [20, 5],
            [30, 4],
            [27, 9],
            [14, 8],
            [5, 20],
            [4, 20],
            [12, 18],
            [8, 12],
            [4, 30],
            [6, 15],
            [25, 4],
            [7, 13],
            [40, 5],
            [20.5, 4.9],
            [4.1, 19.5],
            [5, 15],
        ],
        dtype=np.float64,
    )
    outputs = np.full((17, 1), 2.0, dtype=np.float64)
    input_generators = np.asarray([[1.0, 0.01], [0.01, 1.0]])
    output_generators = np.asarray([[1.0]])
    return inputs, outputs, input_generators, output_generators


def _independent_envelopment(
    inputs: np.ndarray,
    outputs: np.ndarray,
    input_generators: np.ndarray,
    output_generators: np.ndarray,
) -> np.ndarray:
    """Transcribe source equation (6), without importing production helpers."""
    transformed_inputs = np.asarray(
        [
            [
                sum(ray[q] * row[q] for q in range(inputs.shape[1]))
                for ray in input_generators
            ]
            for row in inputs
        ],
        dtype=np.float64,
    )
    transformed_outputs = np.asarray(
        [
            [
                sum(ray[r] * row[r] for r in range(outputs.shape[1]))
                for ray in output_generators
            ]
            for row in outputs
        ],
        dtype=np.float64,
    )
    scores = []
    for focal in range(inputs.shape[0]):
        objective = np.zeros(inputs.shape[0] + 1)
        objective[-1] = 1.0
        input_rows = np.column_stack([transformed_inputs.T, -transformed_inputs[focal]])
        output_rows = np.column_stack(
            [-transformed_outputs.T, np.zeros(transformed_outputs.shape[1])]
        )
        result = linprog(
            objective,
            A_ub=np.vstack([input_rows, output_rows]),
            b_ub=np.concatenate(
                [
                    np.zeros(transformed_inputs.shape[1]),
                    -transformed_outputs[focal],
                ]
            ),
            bounds=[(0.0, None)] * (inputs.shape[0] + 1),
            method="highs",
        )
        assert result.success
        scores.append(result.fun)
    return np.asarray(scores)


def _independent_multiplier(
    inputs: np.ndarray,
    outputs: np.ndarray,
    input_generators: np.ndarray,
    output_generators: np.ndarray,
) -> np.ndarray:
    """Transcribe equation (5) directly, independently of the CR-E assembly."""
    n_input_generators = input_generators.shape[0]
    n_output_generators = output_generators.shape[0]
    scores = []
    for focal in range(inputs.shape[0]):
        objective = np.zeros(n_input_generators + n_output_generators)
        for output_ray in range(n_output_generators):
            objective[n_input_generators + output_ray] = -sum(
                output_generators[output_ray, r] * outputs[focal, r]
                for r in range(outputs.shape[1])
            )
        inequalities = []
        for row in range(inputs.shape[0]):
            alpha_part = [
                -sum(
                    input_generators[ray, q] * inputs[row, q]
                    for q in range(inputs.shape[1])
                )
                for ray in range(n_input_generators)
            ]
            gamma_part = [
                sum(
                    output_generators[ray, r] * outputs[row, r]
                    for r in range(outputs.shape[1])
                )
                for ray in range(n_output_generators)
            ]
            inequalities.append(alpha_part + gamma_part)
        normalization = np.zeros(n_input_generators + n_output_generators)
        for ray in range(n_input_generators):
            normalization[ray] = sum(
                input_generators[ray, q] * inputs[focal, q]
                for q in range(inputs.shape[1])
            )
        result = linprog(
            objective,
            A_ub=np.asarray(inequalities),
            b_ub=np.zeros(inputs.shape[0]),
            A_eq=normalization.reshape(1, -1),
            b_eq=np.ones(1),
            bounds=[(0.0, None)] * objective.size,
            method="highs",
        )
        assert result.success
        scores.append(-result.fun)
    return np.asarray(scores)


def test_example_two_independent_multiplier_oracle_reproduces_source_values() -> None:
    inputs, outputs, input_generators, output_generators = _example_two()
    multiplier = _independent_multiplier(
        inputs,
        outputs,
        input_generators,
        output_generators,
    )
    envelopment = _independent_envelopment(
        inputs,
        outputs,
        input_generators,
        output_generators,
    )

    np.testing.assert_allclose(multiplier, envelopment, atol=2e-12, rtol=0.0)
    assert abs(multiplier[2] - 85.0 / 86.0) <= 1e-12
    assert abs(multiplier[9] - 42.0 / 43.0) <= 1e-12
    assert round(float(multiplier[2]), 4) == 0.9884
    assert round(float(multiplier[9]), 4) == 0.9767


__all__ = [
    "_example_two",
    "_independent_envelopment",
    "_independent_multiplier",
]
