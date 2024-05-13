"""
Test set-up module.
pytest will automatically import fixtures defined in a file named conftest.py
to other test modules in the directory.
"""

import os
import sqlite3

import pytest


TEST_DB_FILE = "test_chat.db"


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
    if os.path.exists(TEST_DB_FILE):
        # remove and re-create DB if it exists
        os.remove(TEST_DB_FILE)

    test_db_cursor = sqlite3.connect(TEST_DB_FILE).cursor()
    create_handle_table(test_db_cursor)
    create_chat_table(test_db_cursor)
    create_message_table(test_db_cursor)
    create_chat_message_join_table(test_db_cursor)

    # yield instead of return so the cleanup steps are run after the tests run
    yield test_db_cursor

    # delete DB after running all tests
    os.remove(TEST_DB_FILE)


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
        (50, "unknown@email.com"),  # "unknown" contact in name2 chat
    ]
    test_db_cursor.executemany("INSERT INTO handle VALUES(?, ?)", handles)
    test_db_cursor.connection.commit()


def create_chat_table(test_db_cursor: sqlite3.Cursor):
    """
    Create chat table in database and add entries used for testing.
    """
    test_db_cursor.execute("CREATE TABLE chat(ROWID, display_name, chat_identifier)")
    # fmt: off
    chats = [
        (1, "name", "chat12345678"), # chat_identifier for group chats is `chat<random_number>`
        (2, "name2", "chat87654321"),
        (3, "", "+11234567890"),  # display_name is empty unless explicitly set
        (4, "name", "chat11235813"),  # second appearance
        (5, "", "+11000000000"), # chat_identifier looks like phone number
        (6, "", "+11234567890"),  # second appearance
    ]
    # fmt: on
    test_db_cursor.executemany("INSERT INTO chat VALUES(?, ?, ?)", chats)
    test_db_cursor.connection.commit()


def create_message_table(test_db_cursor: sqlite3.Cursor):
    """
    Create message table in database and add entries used for testing.
    """
    test_db_cursor.execute(
        "CREATE TABLE message(ROWID, handle_id, is_from_me, text, date, associated_message_type)"
    )
    # reaction messages (like, love, etc) have associated_message_type in the 2000s
    # normal messages have associated_message_type of 0
    # intentionally leaving dates unsorted - ordering should be handled by query
    # handle_id doesn't actually matter for individual chats - chat_message_join matters
    # fmt: off
    messages = [
        # chat: name
        (1, 0, 1, "hello alice and bob", 0, 0),  # from user
        (2, 1, 0, "hello user and bob", 10, 0),  # from alice's first ID
        (3, 2, 0, "hello user and alice", 20, 0),  # from bob
        (4, 4, 0, "Loved “hello user and alice”", 30, 2000),  # love reaction from alice's second ID
        # chat: name2
        (5, 0, 1, "hello a and b", 1, 0),  # from user
        (6, 1, 0, "hello u and b", 11, 0),  # from alice's first ID
        (7, 2, 0, "hello u and a", 21, 0),  # from bob
        (8, 4, 0, "Loved “hello u and a”", 31, 2000),  # love reaction from alice's second ID
        (9, 50, 0, "hello -anonymous", 41, 0),  # no contact associated with this sender
        # chat: alice
        (10, 3, 1, "hello alice", 2, 0),  # from user
        (11, 3, 0, "hello user", 12, 0),  # from alice
        (12, 6, 0, "Loved “hello alice”", 22, 2000),  # love reaction from alice's second chat ID
        # chat: bob
        (13, 5, 1, "hello bob", 3, 0),  # from user
        (14, 5, 0, "hello user", 13, 0),  # from bob
    ]
    # fmt: on
    test_db_cursor.executemany("INSERT INTO message VALUES(?, ?, ?, ?, ?, ?)", messages)
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
        # chat: alice
        (3, 10),
        (3, 11),
        (6, 12),
        # chat: bob
        (5, 13),
        (5, 14),
    ]
    test_db_cursor.executemany(
        "INSERT INTO chat_message_join VALUES(?, ?)", chats_messages
    )
    test_db_cursor.connection.commit()
