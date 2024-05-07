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
    # yield instead of return so the cleanup steps are run after the tests run
    yield test_db_cursor

    # delete DB after running all tests
    os.remove(test_db_file)


def create_handle_table(test_db_cursor: sqlite3.Cursor):
    """
    Create handle table in databse and add entries used for testing.
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
