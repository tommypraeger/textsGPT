"""
Test the GroupChat class.
"""

import sqlite3

import pandas as pd
import pytest

from textsgpt.mac.contact import Contact
from textsgpt.mac.group_chat import GroupChat

from ..utils import assert_dataframes_equal

alice = Contact("Alice", "(123)456-7890")
bob = Contact("Bob", "100-000-0000")


def test_get_chat_ids__chat_not_found(test_db: sqlite3.Cursor):
    """
    Test that get_chat_ids raises an error when the chat ID(s) can't be found.
    """
    gc = GroupChat("fake_name", members=[alice, bob])
    with pytest.raises(ValueError) as e:
        gc.get_chat_ids(test_db)
    assert "not found" in str(e.value)


def test_get_chat_ids__single_chat_id(test_db: sqlite3.Cursor):
    """
    Test that a single chat ID will be found.
    """
    gc = GroupChat("name2", members=[alice, bob])
    chat_ids = gc.get_chat_ids(test_db)
    assert chat_ids == ["2"]


def test_get_chat_ids__multiple_chat_ids(test_db: sqlite3.Cursor):
    """
    Test that a multiple chat IDs will be found.
    """
    gc = GroupChat("name", members=[alice, bob])
    chat_ids = gc.get_chat_ids(test_db)
    assert chat_ids == ["1", "4"]


def test_group_chat__create_success():
    """
    Test that group chat can be created successfully with expected attributes.
    """
    gc = GroupChat(name="name", members=[alice, bob])
    assert gc.name == "name"
    assert alice in gc.members
    assert bob in gc.members
    assert gc.user_name == "You"


def test_load_messages__name(test_db: sqlite3.Cursor):
    """
    Test that messages can be loaded from a group chat into a pandas DataFrame.
    The group chat in this test has multiple chat IDs
    and members with single and multiple contact IDs.
    """
    gc = GroupChat("name", members=[alice, bob])
    messages = gc.load_messages(test_db)
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
        messages,
    )


def test_load_messages__name2(
    test_db: sqlite3.Cursor, capsys: pytest.CaptureFixture[str]
):
    """
    Tests that messages can be loaded from a group chat into a pandas DataFrame.
    The group chat in this test has a message from a sender not associated with a contact.
    """
    gc = GroupChat("name2", members=[alice, bob])
    messages = gc.load_messages(test_db)
    out, _ = capsys.readouterr()
    assert_dataframes_equal(
        pd.DataFrame(
            [
                ["You", "hello a and b", "1", "0"],
                ["Alice", "hello u and b", "11", "0"],
                ["Bob", "hello u and a", "21", "0"],
                ["Alice", "Loved “hello u and a”", "31", "2000"],
                ["unknown@email.com", "hello -anonymous", "41", "0"],
            ],
            columns=["sender", "text", "time", "type"],
        ),
        messages,
    )
    assert "[WARN]" in out
    assert "unknown@email.com" in out
