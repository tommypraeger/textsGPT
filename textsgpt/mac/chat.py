"""
Module that defines an iMessage chat.
Server as a wrapper for a group chat or individual chat.
"""

import pathlib
import platform
import re
import sqlite3

import pandas as pd

from textsgpt.rules import Rule

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
        data_dir (str):
            Directory containing the saved chat data.
    """

    def __init__(self, chat_name: str, user_name: str = "You"):
        if platform.system() != "Darwin":
            raise OSError(
                f"Can only read messages on Mac :/. "
                f"Detected that you are using {platform.system()}."
            )

        # set up required components
        try:
            self.chat = CHATS[chat_name]
        except KeyError as e:
            raise KeyError(f"Didn't find chat {chat_name}") from e
        self.chat.user_name = user_name
        self.chat_db = self.connect_to_db()

        # set up saved directories
        self.data_dir = self.create_data_dir(chat_name)

        self.messages = self.load_messages()

    def __del__(self):
        """
        Closes the connection to the chat DB.
        """
        try:
            self.chat_db.connection.close()
        except AttributeError:
            # assume chat_db failed to be initialized
            pass

    @staticmethod
    def create_data_dir(chat_name: str):
        """
        Create directory for storing chat data if it does not exist.
        This directory will be used to store messages and embeddings
        to prevent re-pulling data.
        The directory name uses the chat name, but
        spaces are replaced with underscores
        and non-alphanumeric characters (except underscores) are removed.
        If there are no non-alphanumeric characters in the chat name,
        the directory uses a hash of the chat name.

        Args:
            chat_name (str):
                The name of the chat.

        Returns:
            str:
                The relative path of the data directory for this chat.
        """
        # replace spaces with underscores
        friendly_name = re.sub(r"\s+", "_", chat_name)
        # replace non-alphanumeric characters with nothing
        friendly_name = re.sub(r"[\W]+", "", friendly_name)

        if len(friendly_name) == 0:
            # use a hash as backup
            friendly_name = str(hash(chat_name))

        data_dir = f"data/{friendly_name}"
        pathlib.Path(data_dir).mkdir(parents=True, exist_ok=True)
        return data_dir

    @staticmethod
    def get_db_file_path():
        """
        Returns the location of the chat DB on Mac.
        Mainly used so the location can be replaced in testing.

        Returns:
            str:
                Location of chat DB on Mac.
        """
        home_dir = pathlib.Path.home()
        return f"{home_dir}/Library/Messages/chat.db"

    def connect_to_db(self) -> sqlite3.Cursor:
        """
        Create a connection to chat.db.
        Check for permissions issues and give instructions for fixing them.

        Returns:
            sqlite3.Cursor:
                Connection to the chat DB.
        """
        try:
            chat_db = sqlite3.connect(self.get_db_file_path()).cursor()
            test_query = "SELECT * FROM handle LIMIT 1"
            chat_db.execute(test_query)
            return chat_db
        except sqlite3.OperationalError as e:
            raise PermissionError(
                "\n\n\n=====================================================================\n"
                "There was an error accessing the messages database.\n"
                "If you are using a Mac and want to access the messages database, "
                "follow these steps to give access to the messages database:\n"
                "1. Open System Preferences\n"
                "2. Go to Security and Privacy\n"
                "3. Go to Privacy\n"
                "4. Go to Full Disk Access\n"
                "5. Give whatever application you're running this from Full Disk Access, "
                "and then run the script again\n"
                "====================================================================="
            ) from e

    def load_messages(self) -> pd.DataFrame:
        """
        Load messages from chat database on Mac into a pandas DataFrame.
        Uses the respective method of the input chat class.
        If messages for this chat have been loaded previously,
        only return new messages since the last time these messages were loaded.
        The entire set of messages (old and new) will be saved to a CSV for future executions.

        Returns:
            pd.DataFrame:
                pandas DataFrame containing the messages of the chat.
                If existing messages are found for this chat, only new messages are returned.
        """
        # location of the CSV file containing messages for this chat
        messages_csv = f"{self.data_dir}/messages.csv"

        if pathlib.Path(messages_csv).exists():
            # load messages more recent than the last of the old messages
            earlier_messages = pd.read_csv(messages_csv)  # type: ignore
            latest_message_time = str(earlier_messages.iloc[-1]["time"])  # type: ignore
            new_messages = self.chat.load_messages(
                self.chat_db, since=latest_message_time
            )
            # write all messages to CSV, but only return new_messages from the function
            all_messages = pd.concat([earlier_messages, new_messages], axis=0)  # type: ignore
            all_messages.to_csv(messages_csv, index=False)
            return new_messages

        # no previous messages for this chat found
        # load them all
        messages = self.chat.load_messages(self.chat_db)
        messages.to_csv(messages_csv, index=False)
        return messages

    def apply_rules(self, *rules: Rule):
        """
        Applies rules to the messages DataFrame.
        Rules may filter or alter the DataFrame in some way.

        Args:
            *rules (Rule):
                Arbitrary list of rules to apply to the messages DataFrame.
                Rules are applied sequentially and each modify the DataFrame.
        """
        for rule in rules:
            func = rule.func
            kwargs = rule.kwargs
            self.messages = func(self.messages, **kwargs)
            self.messages.reset_index(drop=True, inplace=True)
