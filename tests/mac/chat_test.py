"""
Test the Chat class.
"""

import functools
import os
import sqlite3
import stat
from typing import Any, Callable
from unittest.mock import patch

import pandas as pd
import pytest

from textsgpt.mac.chat import Chat
from textsgpt.mac.contact import Contact
from textsgpt.mac.group_chat import GroupChat
from textsgpt.mac.individual_chat import IndividualChat
from textsgpt.rules import Rule

from ..utils import assert_dataframes_equal
from .conftest import TEST_DB_FILE

# testing chat dictionary used to replace CHATS dictionary
test_chats = {
    "name": GroupChat(
        name="name",
        user_name="You",
        members=[
            Contact("Alice", ["(123)456-7890", "alice@email.com"]),
            Contact("Bob", ["100-000-0000"]),
        ],
    ),
    "alice": IndividualChat(
        user_name="You",
        other_person=Contact("Alice", ["(123)456-7890", "alice@email.com"]),
    ),
}


def get_test_db_file_path():
    """
    Returns the path to the testing DB.
    Used to replace `get_db_file_path` in the `Chat` class.
    """
    return TEST_DB_FILE


def with_patches(func: Callable[..., None]):
    """
    Decorator to apply patches to each test in this module.
    Patches:\n
        The CHATS dictionary with a testing chats dictionary.\n
        The path to the chat DB with the path to the testing DB.
    """

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any):
        with (
            patch("textsgpt.mac.chat.CHATS", test_chats),
            patch(
                "textsgpt.mac.chat.Chat.get_db_file_path", wraps=get_test_db_file_path
            ),
            patch("pathlib.Path.mkdir"),
            patch("pandas.DataFrame.to_csv"),
        ):
            func(*args, **kwargs)

    return wrapper


def fake_platform():
    """
    Returns a fake system platform ("Not Darwin") ("Darwin" is Mac).
    Used to replace `system.platform()` in testing.
    """
    return "Not Darwin"


def test_wrong_platform():
    """
    Test error handling when running on not a Mac.
    """
    with patch("textsgpt.mac.chat.platform.system", wraps=fake_platform):
        with pytest.raises(OSError) as e:
            Chat("name")
        assert "Not Darwin" in str(e.value)


@pytest.mark.parametrize(
    "chat_name,expected_data_dir",
    [
        ("name", "name"),
        ("name with spaces", "name_with_spaces"),
        ("name-with-dashes", "namewithdashes"),
        ("name_with_underscores", "name_with_underscores"),
        ("123", "123"),
        ("?", str(hash("?"))),
    ],
)
@with_patches
def test_create_data_dir(chat_name: str, expected_data_dir: str):
    """
    Test the data directory will be created at the right directories for a given chat name.
    """
    assert Chat.create_data_dir(chat_name) == f"data/{expected_data_dir}"


@with_patches
def test_connect_to_db__fail(test_db: sqlite3.Cursor):
    """
    Test error handling when connecting to the chat DB fails.
    Simulate failures by removing permissions on the testing DB.
    """
    # use argument to prevent warning
    # test_db is a fixture added as an argument so the test_db is created for this test
    _ = test_db

    # remove permissions on testing DB
    os.chmod(TEST_DB_FILE, 0)

    with pytest.raises(PermissionError) as e:
        Chat("name")
    # confirm instructions are printed in error message
    assert "Full Disk Access" in str(e.value)

    # restore original permissions (-rw-r--r--)
    os.chmod(TEST_DB_FILE, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)


@with_patches
def test_connect_to_db__success(test_db: sqlite3.Cursor):
    """
    Test that connections to the chat DB can be opened successfully.
    """
    # use argument to prevent warning
    # test_db is a fixture added as an argument so the test_db is created for this test
    _ = test_db
    chat = Chat("name")
    assert isinstance(chat.chat_db, sqlite3.Cursor)


@with_patches
def test_load_messages__chat_not_found():
    """
    Test error handling when the requested chat is not defined.
    """
    with pytest.raises(KeyError):
        Chat("fake name")


@with_patches
def test_load_messages__group_chat():
    """
    Test that messages can be loaded for a group chat.
    """
    chat = Chat("name")
    assert_dataframes_equal(
        pd.DataFrame(
            [
                ["You", "hello alice and bob", "0", "0"],
                ["Alice", "hello user and bob", "10", "0"],
                ["Bob", "hello user and alice", "20", "0"],
                ["Alice", "Loved “hello user and alice”", "30", "2000"],
            ],
            columns=["sender", "text", "time", "type"],
        ),
        chat.messages,
    )


@with_patches
def test_load_messages__individual_chat():
    """
    Test that messages can be loaded for an individual chat.
    """
    chat = Chat("alice")
    assert_dataframes_equal(
        pd.DataFrame(
            [
                ["You", "hello alice", "2", "0"],
                ["Alice", "hello user", "12", "0"],
                ["Alice", "Loved “hello alice”", "22", "2000"],
                ["Alice", "hello from my email", "32", "0"],
            ],
            columns=["sender", "text", "time", "type"],
        ),
        chat.messages,
    )


@with_patches
@patch("pathlib.Path.exists", return_value=True)
@patch(
    "pandas.read_csv",
    return_value=pd.DataFrame(
        [
            ["You", "hello alice and bob", "0", "0"],
            ["Alice", "hello user and bob", "10", "0"],
        ],
        columns=["sender", "text", "time", "type"],
    ),
)
def test_load_messages__group_chat_since_timestamp(
    mocked_func1, mocked_func2  # type: ignore  pylint: disable=unused-argument
):
    """
    Test that only messages since the provided timestamp will be loaded for a group chat.
    """
    chat = Chat("name")
    assert_dataframes_equal(
        pd.DataFrame(
            [
                ["Bob", "hello user and alice", "20", "0"],
                ["Alice", "Loved “hello user and alice”", "30", "2000"],
            ],
            columns=["sender", "text", "time", "type"],
        ),
        chat.messages,
    )


@with_patches
@patch("pathlib.Path.exists", return_value=True)
@patch(
    "pandas.read_csv",
    return_value=pd.DataFrame(
        [
            ["You", "hello alice", "2", "0"],
            ["Alice", "hello user", "12", "0"],
        ],
        columns=["sender", "text", "time", "type"],
    ),
)
def test_load_messages__individual_chat_since_timestamp(
    mocked_func1, mocked_func2  # type: ignore  pylint: disable=unused-argument
):
    """
    Test that only messages since the provided timestamp will be loaded for an individual chat.
    """
    chat = Chat("alice")
    assert_dataframes_equal(
        pd.DataFrame(
            [
                ["Alice", "Loved “hello alice”", "22", "2000"],
                ["Alice", "hello from my email", "32", "0"],
            ],
            columns=["sender", "text", "time", "type"],
        ),
        chat.messages,
    )


### Rules ###


def remove_member(messages: pd.DataFrame, member: str) -> pd.DataFrame:
    """
    Simple rule used for testing.
    Removes messages from a specified member of the chat.
    """
    return messages[messages["sender"] != member]


def reverse_order(messages: pd.DataFrame) -> pd.DataFrame:
    """
    Simple rule used for testing. Reverses the order of the messages.
    """
    return messages.sort_values(by=["time"], ascending=False)  # type: ignore


@with_patches
def test_apply_rule():
    """
    Test that asserts a single rule can be applied successfully.
    Uses a rule that takes in a keyword arg.
    """
    chat = Chat("name")
    chat.apply_rules(Rule(remove_member, {"member": "Bob"}))
    assert_dataframes_equal(
        pd.DataFrame(
            [
                ["You", "hello alice and bob", "0", "0"],
                ["Alice", "hello user and bob", "10", "0"],
                ["Alice", "Loved “hello user and alice”", "30", "2000"],
            ],
            columns=["sender", "text", "time", "type"],
        ),
        chat.messages,
    )


@with_patches
def test_apply_rules():
    """
    Test that asserts multiple rules can be applied successfully.
    Uses one rule that takes in a keyword arg and one that doesn't.
    """
    chat = Chat("name")
    chat.apply_rules(Rule(remove_member, {"member": "Bob"}), Rule(reverse_order))
    assert_dataframes_equal(
        pd.DataFrame(
            [
                ["Alice", "Loved “hello user and alice”", "30", "2000"],
                ["Alice", "hello user and bob", "10", "0"],
                ["You", "hello alice and bob", "0", "0"],
            ],
            columns=["sender", "text", "time", "type"],
        ),
        chat.messages,
    )
