"""
Test rules. Rules are used to filter or alter the messages DataFrame.
"""

from typing import Any, Callable

import pandas as pd
import pytest

from textsgpt import rules

from .utils import assert_dataframes_equal


def example_rule_func(df: pd.DataFrame) -> pd.DataFrame:
    """
    No-op function used to test rule initialization.
    """
    return df


@pytest.mark.parametrize(
    "rule,expected_func,expected_kwargs",
    [
        (rules.Rule(example_rule_func), example_rule_func, {}),
        (
            rules.Rule(example_rule_func, {"key": "value"}),
            example_rule_func,
            {"key": "value"},
        ),
    ],
)
def test_rule_initialization(
    rule: rules.Rule,
    expected_func: Callable[..., pd.DataFrame],
    expected_kwargs: dict[str, Any],
):
    """
    Test that a rule can be initialized as expected.
    Includes cases for when kwargs is left empty and when kwargs is passed.
    """
    assert rule.func == expected_func
    assert rule.kwargs == expected_kwargs


@pytest.mark.parametrize(
    "initial,expected",
    [
        ({"text": []}, {"text": []}),
        ({"text": ["hello", ""]}, {"text": ["hello"]}),
        ({"text": [""]}, {"text": []}),
        ({"text": ["12345", "   ", " ", "hello", ""]}, {"text": ["12345", "hello"]}),
        ({"text": ["🧌", "+?!#@$%^&*([|])"]}, {"text": []}),
    ],
)
def test_remove_non_alphanumeric_messages__empty_message(
    initial: dict[str, Any], expected: dict[str, Any]
):
    """
    Test a rule that removes messages that do not contain any alphanumeric characters.
    """
    assert_dataframes_equal(
        pd.DataFrame(expected),
        rules.remove_non_alphanumeric_messages(pd.DataFrame(initial)),
    )


@pytest.mark.parametrize(
    "initial,expected",
    [
        ({"text": []}, {"text": []}),
        ({"type": ["0", "0"]}, {"type": ["0", "0"]}),
        ({"type": ["0", "2000", "0"]}, {"type": ["0", "0"]}),
        ({"type": ["2001"]}, {"type": []}),
    ],
)
def test_remove_non_standard_imessages(
    initial: dict[str, Any], expected: dict[str, Any]
):
    """
    Test a rule that removes iMessage reaction messages (like, love, emphasize, etc).
    Messages with type != 0 are reactions.
    """
    assert_dataframes_equal(
        pd.DataFrame(expected),
        rules.remove_non_standard_imessages(pd.DataFrame(initial)),
    )


@pytest.mark.parametrize(
    "initial,expected",
    [
        ({"text": []}, {"text": []}),
        ({"text": ["hello"]}, {"text": ["hello"]}),
        ({"text": ["https://github.com/tommypraeger/textsGPT"]}, {"text": [""]}),
        (
            {
                "text": [
                    "look at this link: https://github.com/tommypraeger/textsGPT",
                    "nice",
                ]
            },
            {"text": ["look at this link: ", "nice"]},
        ),  # the rest of the text is retained
        (
            {"text": ["github.com"]},
            {"text": ["github.com"]},
        ),  # not quite counting this as link
    ],
)
def test_remove_links(initial: dict[str, Any], expected: dict[str, Any]):
    """
    Test a rule that removes links from messages.
    """
    assert_dataframes_equal(
        pd.DataFrame(expected),
        rules.remove_links(pd.DataFrame(initial)),
    )
