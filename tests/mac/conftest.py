"""
Test set-up module.
pytest will automatically import fixtures defined in a file named conftest.py
to other test modules in the directory.
"""

import os
import sqlite3

import pytest


# scope="session" will cause the same DB connection to be used throughout the test session
@pytest.fixture(scope="session")
def test_db():
    """
    Create a testing DB and saves it to a file.
    Return a cursor to the database. The same DB/cursor will be used each time.
    Delete the testing DB file after tests complete.

    Returns:
        sqlite3.Cursor:
            Cursor to the testing DB.
    """
    test_db_file = "test_chat.db"
    if os.path.exists(test_db_file):
        # remove and re-create DB if it exists
        os.remove(test_db_file)

    test_db_cursor = sqlite3.connect(test_db_file).cursor()
    create_handle_table(test_db_cursor)
    create_chat_table(test_db_cursor)
    create_message_table(test_db_cursor)
    create_chat_message_join_table(test_db_cursor)

    # yield instead of return so the cleanup steps are run after the tests run
    yield test_db_cursor

    # delete DB after running all tests
    os.remove(test_db_file)


def create_handle_table(test_db_cursor: sqlite3.Cursor):
    """
    Create handle table in database and add entries used for testing.
    """
    test_db_cursor.execute("CREATE TABLE handle(ROWID, id)")
    handles = [
        (1, "+11234567890"),
        (2, "+11000000000"),
        (3, "email@notaphonenumber.net"),
        (4, "+11234567890"),  # second appearance
        (5, "12345"),
    ]
    test_db_cursor.executemany("INSERT INTO handle VALUES(?, ?)", handles)
    test_db_cursor.connection.commit()


def create_chat_table(test_db_cursor: sqlite3.Cursor):
    """
    Create chat table in database and add entries used for testing.
    """
    test_db_cursor.execute("CREATE TABLE chat(ROWID, display_name)")
    chats = [
        (1, "name"),
        (2, "name2"),
        (3, ""),  # display name is empty unless explicitly set
        (4, "name"),  # second appearance
        (5, ""),
    ]
    test_db_cursor.executemany("INSERT INTO chat VALUES(?, ?)", chats)
    test_db_cursor.connection.commit()


def create_message_table(test_db_cursor: sqlite3.Cursor):
    """
    Create message table in database and add entries used for testing.
    """
    test_db_cursor.execute(
        "CREATE TABLE message(ROWID, handle_id, text, date, associated_message_type)"
    )
    # reaction messages (like, love, etc) have associated_message_type in the 2000s
    # normal messages have associated_message_type of 0
    # intentionally leaving dates unsorted - ordering should be handled by query
    # fmt: off
    messages = [
        # chat: name
        (1, 0, "hello alice and bob", 0, 0),  # from user
        (2, 1, "hello user and bob", 10, 0),  # from alice's first ID
        (3, 2, "hello user and alice", 20, 0),  # from bob
        (4, 4, "Loved “hello user and alice”", 30, 2000),  # love reaction from alice's second ID
        # chat: name2
        (5, 0, "hello a and b", 1, 0),  # from user
        (6, 1, "hello u and b", 11, 0),  # from alice's first ID
        (7, 2, "hello u and a", 21, 0),  # from bob
        (8, 4, "Loved “hello u and a”", 31, 2000),  # love reaction from alice's second ID
        (9, 50, "hello -anonymous", 41, 0),  # no contact associated with this sender
    ]
    # fmt: on
    test_db_cursor.executemany("INSERT INTO message VALUES(?, ?, ?, ?, ?)", messages)
    test_db_cursor.connection.commit()


def create_chat_message_join_table(test_db_cursor: sqlite3.Cursor):
    """
    Create chat_message_join table in database and add entries used for testing.
    This depends on the values in the chat and message tables.
    """
    test_db_cursor.execute("CREATE TABLE chat_message_join(chat_id, message_id)")
    chats_messages = [
        # chat: name
        (1, 1),
        (1, 2),
        (1, 3),
        (4, 4),  # second chat ID for name
        # chat: name2
        (2, 5),
        (2, 6),
        (2, 7),
        (2, 8),
        (2, 9),
    ]
    test_db_cursor.executemany(
        "INSERT INTO chat_message_join VALUES(?, ?)", chats_messages
    )
    test_db_cursor.connection.commit()
