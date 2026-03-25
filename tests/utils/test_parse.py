from pathlib import Path

import pytest

from sachmis.config.model import Geminis, Groks, ModelFamily
from sachmis.utils.parse import reversed_name_from_unique

# good test

all_families: list[type[ModelFamily]] = [
    # PLUG: family for test
    Geminis,
    Groks,
]

all_models: list[ModelFamily] = [
    model  #
    for family in all_families
    for model in family
]


# GOOD TESTS
for model in all_models:
    string_to_test: str = model.unique
    result: ModelFamily | None = reversed_name_from_unique(
        model_unique=string_to_test
    )
    assert model == result

# BAD TESTS
fail_cases = [
    "xx-ff",  # Unknown family prefix
    "c-44-44",  # Too many parts
    "c",  # Too few parts
    "g-gg",  # Valid family, invalid model name
    "",  # Empty string
    "g-",  # Missing model name
    "-g3",  # Missing family prefix
    233,
    Path("x-g420"),
]


@pytest.mark.parametrize("expected_model", all_models)
def test_reversed_name_success(expected_model: ModelFamily):
    """
    Test that every valid ModelFamily member can be parsed back
    from its .unique string property.
    """
    # Act
    result = reversed_name_from_unique(expected_model.unique)

    # Assert
    assert result == expected_model
    assert isinstance(result, ModelFamily)


@pytest.mark.parametrize("invalid_input", fail_cases)
def test_reversed_name_failures(invalid_input: str):
    """
    Test that invalid strings return None and do not raise Exceptions.
    """
    # Act
    result = reversed_name_from_unique(invalid_input)

    # Assert
    assert result is None


def test_reversed_name_type_safety():
    """
    Specific check for return types on a known good value.
    """
    result = reversed_name_from_unique("g-g3")
    assert isinstance(result, Geminis)
    assert result == Geminis.G3
