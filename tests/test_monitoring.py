"""Distribution diagnostics should expose change without asserting causality."""

import numpy as np
import pytest

from src.monitoring.drift import population_stability_index


def test_identical_distributions_have_zero_psi():
    values = np.arange(100)
    assert population_stability_index(values, values) == pytest.approx(0)


def test_large_distribution_shift_has_larger_psi():
    values = np.arange(100)
    assert population_stability_index(values, values + 1000) > population_stability_index(values, values + 1)


def test_empty_and_nonfinite_samples_are_rejected():
    with pytest.raises(ValueError):
        population_stability_index([], [1])
    with pytest.raises(ValueError):
        population_stability_index([1, np.inf], [1])
