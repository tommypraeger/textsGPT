"""
Test the IndividualChat class.
"""

import sqlite3

import pandas as pd
import pytest

from textsgpt.mac.contact import Contact
from textsgpt.mac.individual_chat import IndividualChat

from ..utils import assert_dataframes_equal

alice = Contact("Alice", ["(123)456-7890", "alice@email.com"])
bob = Contact("Bob", ["100-000-0000"])


def test_get_chat_ids__chat_not_found(test_db: sqlite3.Cursor):
    """
    Test that get_chat_ids raises an error when the chat ID(s) can't be found.
    """
    chat = IndividualChat(other_person=Contact("Fake Person", ["5555555555"]))
    with pytest.raises(ValueError) as e:
        chat.get_chat_ids(test_db)
    assert "not found" in str(e.value)


def test_get_chat_ids__single_chat_id(test_db: sqlite3.Cursor):
    """
    Test that a single chat ID will be found.
    """
    chat = IndividualChat(other_person=bob)
    chat_ids = chat.get_chat_ids(test_db)
    assert chat_ids == ["5"]


def test_get_chat_ids__multiple_chat_ids(test_db: sqlite3.Cursor):
    """
    Test that a multiple chat IDs will be found.
    """
    chat = IndividualChat(other_person=alice)
    chat_ids = chat.get_chat_ids(test_db)
    assert chat_ids == ["3", "6", "7"]


def test_individual_chat__create_success():
    """
    Test that individual chat can be created successfully with expected attributes.
    """
    chat = IndividualChat(other_person=alice)
    assert chat.other_person is alice
    assert chat.user_name == "You"


def test_load_messages__multiple_contact_ids(test_db: sqlite3.Cursor):
    """
    Test that messages can be loaded from a group chat into a pandas DataFrame.
    The other person in this chat has multiple contact IDs.
    """
    chat = IndividualChat(other_person=alice)
    messages = chat.load_messages(test_db)
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
        messages,
    )


def test_load_messages__single_contact_id(test_db: sqlite3.Cursor):
    """
    Tests that messages can be loaded from a chat into a pandas DataFrame.
    The other person in this chat has a single contact ID.
    """
    chat = IndividualChat(other_person=bob)
    messages = chat.load_messages(test_db)
    assert_dataframes_equal(
        pd.DataFrame(
            [
                ["You", "hello bob", "3", "0"],
                ["Bob", "hello user", "13", "0"],
            ],
            columns=["sender", "text", "time", "type"],
        ),
        messages,
    )
