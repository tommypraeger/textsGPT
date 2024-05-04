"""
Module that defines an iMessage chat.
Server as a wrapper for a group chat or individual chat.
"""

import pathlib
import platform
import sqlite3

import pandas as pd

from .my_chats import CHATS


class Chat:
    """
    A class for loading messages in a chat in the Messages app.

    Args:
        chat_name (str):
            The chat to load from messages from.
            Key from the user-defined CHATS dictionary.
        user_name (str):
            Your name. Used to label messages you sent.
            Defaults to "You".

    Attributes:
        chat (GroupChat | IndividualChat):
            Representation of either a group chat or individual chat that this class wraps.
        chat_db (sqlite3.Cursor):
            sqlite cursor used to interact with the chat database on Mac.
        messages (pd.DataFrame):
            pandas DataFrame to hold the messages from the chat.
    """

    def __init__(self, chat_name: str, user_name: str = "You"):
        if platform.system() != "Darwin":
            raise OSError(
                f"Can only read messages on Mac :/. "
                f"Detected that you are using {platform.system()}."
            )
        try:
            self.chat = CHATS[chat_name]
        except KeyError as e:
            raise KeyError(f"Didn't find chat {chat_name}") from e
        self.chat.user_name = user_name
        self.chat_db = self.connect_to_db()
        self.messages = self.load_messages()

    def __del__(self):
        """
        Closes the connection to the chat DB.
        """
        self.chat_db.close()

    def connect_to_db(self) -> sqlite3.Cursor:
        """
        Create a connection to chat.db.
        Check for permissions issues and give instructions for fixing them.

        Returns:
            sqlite3.Cursor:
                Connection to the chat DB.
        """
        home_dir = pathlib.Path.home()
        chat_db = sqlite3.connect(f"{home_dir}/Library/Messages/chat.db").cursor()
        try:
            test_query = "SELECT * FROM handle LIMIT 1"
            chat_db.execute(test_query)
            return chat_db
        except sqlite3.OperationalError as e:
            raise PermissionError(
                "There was an error accessing the messages database.\n"
                "If you are using a Mac and want to access the messages database, "
                "follow these steps to give access to the messages database:\n"
                "1. Open System Preferences\n"
                "2. Go to Security and Privacy\n"
                "3. Go to Privacy\n"
                "4. Go to Full Disk Access\n"
                "5. Give whatever application you're running this from Full Disk Access, ",
                "and then run the script again\n",
            ) from e

    def load_messages(self) -> pd.DataFrame:
        """
        Load messages from chat database on Mac into a pandas DataFrame.
        Uses the respective method of the input chat class.

        Returns:
            pd.DataFrame:
                pandas DataFrame containing the messages of the chat.
        """
        return self.chat.load_messages(self.chat_db)
